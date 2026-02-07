# Strands Agent Pattern - Quick Reference

## Core Pattern: Orchestrator + Sub-Agents as Tools

```
┌─────────────────────────────────────────────────────────────┐
│                    AgentCore Runtime                         │
│  ┌───────────────────────────────────────────────────────┐  │
│  │              Orchestrator Agent                        │  │
│  │  - Routes queries to specialized sub-agents           │  │
│  │  - Integrates AgentCore Memory                        │  │
│  │  - Uses MCP Gateway tools                             │  │
│  └───────────────────────────────────────────────────────┘  │
│           │              │              │                    │
│           ▼              ▼              ▼                    │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐        │
│  │ Sub-Agent 1  │ │ Sub-Agent 2  │ │ MCP Tools    │        │
│  │ (@tool)      │ │ (@tool)      │ │ (Gateway)    │        │
│  └──────────────┘ └──────────────┘ └──────────────┘        │
└─────────────────────────────────────────────────────────────┘
```

---

## 1. Orchestrator Structure

```python
from bedrock_agentcore import BedrockAgentCoreApp
from strands import Agent
from strands.tools.mcp import MCPClient

app = BedrockAgentCoreApp()

@app.entrypoint
def invoke(payload: Dict[str, Any], context: Any) -> Dict[str, Any]:
    # 1. Extract parameters
    user_message = payload.get("inputText")
    user_id = payload.get("user_id")
    session_id = context.session_id  # Min 33 chars
    
    # 2. Setup memory
    memory_config = AgentCoreMemoryConfig(
        memory_id=get_memory_id(),
        session_id=session_id,
        actor_id=user_id,
        retrieval_config={
            "/app/{actorId}/{sessionId}": RetrievalConfig(top_k=5),
            "/app/{actorId}/preferences": RetrievalConfig(top_k=5)
        }
    )
    session_manager = AgentCoreMemorySessionManager(memory_config, region)
    
    # 3. Create orchestrator with tools
    with mcp_client:
        mcp_tools = mcp_client.list_tools_sync()
        all_tools = [sub_agent_1, sub_agent_2] + mcp_tools
        
        orchestrator = Agent(
            model="openai.gpt-oss-20b-1:0",
            system_prompt=ORCHESTRATOR_PROMPT,
            tools=all_tools,
            session_manager=session_manager
        )
        
        response = orchestrator(user_message)
    
    return {"result": response.message}
```

---

## 2. Sub-Agent as Tool

```python
from strands import Agent, tool

@tool
def restaurant_finder(query: str, user_id: str = None) -> str:
    """Find restaurants based on user preferences"""
    
    # Create specialized agent
    agent = Agent(
        model="openai.gpt-oss-20b-1:0",
        system_prompt="You are a restaurant search assistant...",
        tools=[]  # Can include MCP tools if needed
    )
    
    # Invoke agent
    response = agent(query)
    
    return str(response)
```

---

## 3. MCP Gateway Integration

```python
from strands.tools.mcp import MCPClient
from mcp.client.streamable_http import streamablehttp_client

# Get Cognito token
token = utils.get_cognito_token()

# Create MCP client
def create_transport():
    return streamablehttp_client(
        gateway_url,
        headers={"Authorization": f"Bearer {token}"}
    )

mcp_client = MCPClient(create_transport)

# Use in context manager
with mcp_client:
    tools = mcp_client.list_tools_sync()
```

---

## 4. Memory Configuration

```python
from bedrock_agentcore.memory.integrations.strands.session_manager import (
    AgentCoreMemorySessionManager
)
from bedrock_agentcore.memory.integrations.strands.config import (
    AgentCoreMemoryConfig,
    RetrievalConfig
)

memory_config = AgentCoreMemoryConfig(
    memory_id="RestaurantBookingMemory-xxx",
    session_id=session_id,
    actor_id=user_id,
    retrieval_config={
        "/restaurant-booking/{actorId}/{sessionId}": RetrievalConfig(
            top_k=5,
            relevance_score=0.7
        ),
        "/restaurant-booking/{actorId}/preferences": RetrievalConfig(
            top_k=5,
            relevance_score=0.7
        )
    }
)

session_manager = AgentCoreMemorySessionManager(memory_config, region)
```

---

## 5. System Prompt Pattern

```python
ORCHESTRATOR_PROMPT = """You are a Restaurant Booking Orchestrator.

AVAILABLE TOOLS:
1. restaurant_finder - Search restaurants
2. booking_agent - Create reservations
3. fetchRestaurantDetails - MCP tool from Gateway
4. bookATable - MCP tool from Gateway

ROUTING LOGIC:
- "Find Italian restaurants" → restaurant_finder
- "Book a table" → booking_agent
- For specific data needs → Use MCP tools directly

MEMORY:
- You remember previous conversations
- Reference user preferences from memory
- Provide personalized recommendations
"""
```

---

## Key Implementation Rules

### ✅ DO:
1. Use `@app.entrypoint` for main function
2. Extract `session_id` from `context.session_id`
3. Use `with mcp_client:` context manager
4. Pass `session_manager` to Agent constructor
5. Return dict with `result` key
6. Use placeholders `{actorId}` and `{sessionId}` in namespaces

### ❌ DON'T:
1. Hardcode session IDs (must be 33+ chars)
2. Use MCP client outside context manager
3. Forget to pass session_manager to Agent
4. Hardcode actor IDs in namespace patterns
5. Return raw string (must be dict)

---

## Restaurant Booking Implementation Plan

### File Structure:
```
src/agents/
├── orchestrator_restaurant_booking.py  # Main orchestrator
├── restaurant_finder_agent.py          # @tool for search
├── booking_agent.py                    # @tool for reservations
└── utils.py                            # Cognito, SSM helpers
```

### Orchestrator:
```python
# Sub-agent tools
from restaurant_finder_agent import find_restaurants
from booking_agent import create_booking

# MCP tools from Gateway
# - fetchRestaurantDetails
# - bookATable
# - paymentAPI
# - etc.

@app.entrypoint
def invoke(payload, context):
    # Setup memory
    # Create orchestrator with tools
    # Return response
```

### Sub-Agents:
```python
@tool
def find_restaurants(query: str, user_id: str) -> str:
    """Search restaurants using MCP tools"""
    # Can call MCP tools internally
    # Or create specialized Agent
    pass

@tool
def create_booking(query: str, user_id: str) -> str:
    """Handle booking flow"""
    # Multi-step: validate → calculate → book → pay
    pass
```

---

## Deployment Commands

```bash
# 1. Deploy orchestrator to AgentCore Runtime
bedrock-agentcore deploy \
  --runtime-file src/agents/orchestrator_restaurant_booking.py \
  --name "RestaurantBookingOrchestrator" \
  --region us-east-1

# 2. Invoke agent
aws bedrock-agentcore-runtime invoke-agent \
  --agent-id <agent-id> \
  --agent-alias-id <alias-id> \
  --session-id "session_$(uuidgen)" \
  --input-text "Find Italian restaurants in NYC"
```

---

## Critical Differences: Strands vs LangGraph

| Aspect | Strands | LangGraph |
|--------|---------|-----------|
| Framework | AWS proprietary | Open source |
| Agent | `Agent(model, tools, system_prompt)` | `StateGraph` with nodes |
| Tools | `@tool` decorator | Plain functions |
| Memory | `AgentCoreMemorySessionManager` | Custom state |
| Orchestration | Automatic (LLM decides) | Manual (conditional edges) |
| Deployment | AgentCore Runtime | Self-hosted |

**Key Insight:** Strands is simpler - the LLM automatically routes to tools based on system prompt. No manual graph construction needed.

---

## Next Steps

1. ✅ Memory deployed: `RestaurantBookingMemory-h16ClnB6f7`
2. ✅ Gateway deployed: `restaurant-booking-gateway-e7trb0r5cm`
3. 🔄 **Next:** Create orchestrator + sub-agents
4. 🔄 **Then:** Deploy to AgentCore Runtime
5. 🔄 **Finally:** Test end-to-end

Ready to implement the orchestrator!
