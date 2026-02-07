# Strands Agent Implementation Pattern Analysis

## Overview: agentcore-for-education Architecture

The education sample demonstrates **AWS Strands framework** (NOT LangGraph) for building multi-agent systems with AgentCore Runtime.

---

## Key Architecture Components

### 1. **Orchestrator Agent** (Main Coordinator)
**File:** `orchestrator_agentcore_runtime_gateway.py`

**Pattern:** Hub-and-spoke architecture where orchestrator routes to specialized sub-agents

**Key Features:**
- `@app.entrypoint` decorator for AgentCore Runtime deployment
- AgentCore Memory integration via `AgentCoreMemorySessionManager`
- MCP Gateway integration for Lambda tools
- Sub-agents registered as `@tool` decorated functions
- Persona-based access control

---

## Implementation Pattern Breakdown

### Pattern 1: AgentCore Runtime Entrypoint

```python
from bedrock_agentcore import BedrockAgentCoreApp

app = BedrockAgentCoreApp()

@app.entrypoint
def invoke(payload: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    AgentCore Runtime entrypoint - called when agent is invoked
    
    Payload:
        - inputText/prompt: User query
        - persona: User role (student/teacher/administrator)
        - user_id: Unique user identifier
        - persona_id: Optional persona-specific ID
        
    Context:
        - session_id: Session identifier (min 33 chars)
    """
    # Extract parameters
    user_message = payload.get("inputText") or payload.get("prompt")
    persona = payload.get("persona")
    user_id = payload.get("user_id")
    session_id = context.session_id
    
    # Get memory_id from SSM or payload
    memory_id = get_memory_id(payload)
    
    # Create memory session manager
    session_manager = AgentCoreMemorySessionManager(memory_config, region_name=region)
    
    # Create and invoke orchestrator
    result = create_orchestrator_agent_runtime(
        query=user_message,
        persona=persona,
        session_manager=session_manager
    )
    
    return {"result": result.message}
```

**Key Points:**
- `@app.entrypoint` makes function callable by AgentCore Runtime
- `payload` contains user input and metadata
- `context.session_id` provides session continuity
- Returns dict with `result` key

---

### Pattern 2: AgentCore Memory Integration

```python
from bedrock_agentcore.memory.integrations.strands.session_manager import (
    AgentCoreMemorySessionManager
)
from bedrock_agentcore.memory.integrations.strands.config import (
    AgentCoreMemoryConfig,
    RetrievalConfig
)

# Configure memory with namespace patterns
memory_config = AgentCoreMemoryConfig(
    memory_id=memory_id,
    session_id=session_id,
    actor_id=user_id,
    retrieval_config={
        # Long-term preferences (cross-session)
        "/octank-edu/{actorId}/preferences": RetrievalConfig(
            top_k=5,
            relevance_score=0.7
        ),
        # Long-term facts (cross-session)
        "/octank-edu/{actorId}/facts": RetrievalConfig(
            top_k=5,
            relevance_score=0.7
        ),
        # Short-term session (current conversation)
        "/octank-edu/{actorId}/{sessionId}": RetrievalConfig(
            top_k=5,
            relevance_score=0.7
        )
    }
)

# Create session manager
session_manager = AgentCoreMemorySessionManager(
    memory_config,
    region_name=region
)
```

**Key Points:**
- `{actorId}` and `{sessionId}` are placeholders replaced at runtime
- `RetrievalConfig` controls how many memories to retrieve (top_k)
- `relevance_score` filters memories by similarity threshold
- Session manager automatically handles memory read/write

---

### Pattern 3: MCP Gateway Integration

```python
from strands.tools.mcp import MCPClient
from mcp.client.streamable_http import streamablehttp_client

# Get OAuth2 token from Cognito
token = utils.get_cognito_token()

# Create MCP client with authentication
def create_streamable_http_transport():
    return streamablehttp_client(
        utils.get_ssm_parameter("/app/octank/agentcore/gatewayURL"),
        headers={"Authorization": f"Bearer {token}"}
    )

mcp_client = MCPClient(create_streamable_http_transport)

# Use MCP client in context manager
with mcp_client:
    # Get tools from Gateway
    mcp_tools = mcp_client.list_tools_sync()
    
    # Combine with base tools
    all_tools = base_tools + mcp_tools
    
    # Create agent with all tools
    orchestrator = Agent(
        model=MODEL_ID,
        tools=all_tools,
        session_manager=session_manager
    )
```

**Key Points:**
- MCP client requires OAuth2 token from Cognito
- `list_tools_sync()` discovers tools from Gateway
- Must use `with mcp_client:` context manager
- Tools are automatically invoked by Strands framework

---

### Pattern 4: Orchestrator Agent Creation

```python
from strands import Agent

def create_orchestrator_agent_runtime(
    query: str,
    persona: str,
    session_manager: AgentCoreMemorySessionManager
) -> Any:
    """Create orchestrator that coordinates sub-agents"""
    
    # Define system prompt with routing logic
    orchestrator_system_prompt = f"""You are an Educational System Orchestrator.

AVAILABLE SPECIALIZED AGENTS (as tools):
1. answer_student_questions - Educational Assistant
2. answer_teacher_questions - Teacher Assistant
3. answer_payment_questions - Financial Assistant
4. answer_admin_questions - Virtual Secretary
5. answer_general_questions - General Questions

ROUTING LOGIC:
- Student academic queries → answer_student_questions
- Teacher queries → answer_teacher_questions
- Payment queries → answer_payment_questions
- Admin queries → answer_admin_questions
- General queries → answer_general_questions

IMPORTANT: Always pass persona="{persona}" when invoking tools.
"""
    
    # Register sub-agent tools
    base_tools = [
        answer_student_questions,
        answer_teacher_questions,
        answer_payment_questions,
        answer_admin_questions,
        answer_general_questions
    ]
    
    # Create orchestrator with MCP tools
    with mcp_client:
        mcp_tools = mcp_client.list_tools_sync()
        all_tools = base_tools + mcp_tools
        
        orchestrator = Agent(
            model="openai.gpt-oss-20b-1:0",
            system_prompt=orchestrator_system_prompt,
            tools=all_tools,
            session_manager=session_manager  # Enable memory
        )
        
        # Invoke orchestrator
        response = orchestrator(query)
        
        return response
```

**Key Points:**
- System prompt defines routing logic
- Sub-agents are registered as tools
- `session_manager` enables memory
- Orchestrator automatically routes to appropriate sub-agent

---

### Pattern 5: Sub-Agent as Tool

```python
from strands import Agent, tool

@tool
def answer_student_questions(
    query: str, 
    student_id: str = None, 
    persona: str = "student"
) -> str:
    """Tool that handles student academic questions.
    
    Args:
        query: The student's question
        student_id: Optional student ID for personalized data
        persona: The persona type making the request
    
    Returns:
        String response from the educational assistant agent
    """
    # Persona-based access control
    if persona not in ["student", "administrator"]:
        return f"Access denied: This tool is only available for student and administrator personas."
    
    # Generate mock data (or fetch from database)
    student_data = generate_student_data(student_id)
    
    # Create specialized agent
    educational_agent = Agent(
        model="openai.gpt-oss-20b-1:0",
        tools=[retrieve],  # Can use Knowledge Base retrieve tool
        system_prompt="""You are an Educational Assistant that helps students.
        
You can provide information about:
- Pending tasks and assignments
- Enrolled courses and teachers
- Current grades
- Subjects requiring focus

Use the mock data provided to answer student questions.
"""
    )
    
    # Inject data into query context
    context = f"""Mock Academic Data for {student_data.student_name}:

Enrolled Courses: {student_data.enrolled_courses}
Current Grades: {student_data.grades}
Pending Tasks: {student_data.pending_tasks}

Student Query: {query}
"""
    
    # Get response from agent
    response = educational_agent(context)
    
    return str(response)
```

**Key Points:**
- `@tool` decorator makes function callable by orchestrator
- Implements persona-based access control
- Creates specialized Agent for specific domain
- Can use additional tools (e.g., Knowledge Base retrieve)
- Returns string response

---

## Critical Implementation Details

### 1. **Session ID Requirements**
```python
# Session ID must be minimum 33 characters
session_id = f"session_{uuid.uuid4()}"  # ✅ Valid (40+ chars)
session_id = "short_id"  # ❌ Invalid (< 33 chars)
```

### 2. **Memory Namespace Patterns**
```python
# Use placeholders {actorId} and {sessionId}
namespaces = [
    "/app-name/{actorId}/{sessionId}",  # ✅ Correct
    "/app-name/user123/session456"       # ❌ Wrong (hardcoded)
]
```

### 3. **Tool Parameter Passing**
```python
# Orchestrator must pass parameters to sub-agents
system_prompt = f"""
When invoking tools, pass:
- persona="{persona}"
- student_id="{persona_id}"
"""
```

### 4. **MCP Client Context Manager**
```python
# MUST use context manager
with mcp_client:
    tools = mcp_client.list_tools_sync()  # ✅ Correct

# DON'T use outside context
tools = mcp_client.list_tools_sync()  # ❌ Will fail
```

### 5. **SSM Parameter Store Usage**
```python
# Store configuration in SSM
def get_memory_id_from_ssm(param_name: str) -> str:
    ssm = boto3.client("ssm")
    response = ssm.get_parameter(Name=param_name)
    return response["Parameter"]["Value"]

# Priority: payload > SSM > environment
memory_id = (
    payload.get("memory_id") or 
    get_memory_id_from_ssm() or 
    os.getenv("MEMORY_ID")
)
```

---

## Deployment Flow

### 1. **Deploy Infrastructure**
```bash
# Deploy Memory
python3 deploy_agentcore_memory.py

# Deploy Cognito User Pool
python3 deploy_cognito_user_pool.py

# Deploy Gateway
python3 deploy_agentcore_gateway.py
```

### 2. **Deploy AgentCore Runtime**
```bash
# Using bedrock-agentcore CLI
bedrock-agentcore deploy \
  --runtime-file orchestrator_agentcore_runtime_gateway.py \
  --name "OctankEduOrchestrator" \
  --region us-east-1
```

### 3. **Invoke Agent**
```python
import boto3

client = boto3.client('bedrock-agentcore-runtime')

response = client.invoke_agent(
    agentId="agent-id",
    agentAliasId="alias-id",
    sessionId="session_" + str(uuid.uuid4()),
    inputText="What are my pending tasks?",
    sessionState={
        "sessionAttributes": {
            "persona": "student",
            "user_id": "user123",
            "persona_id": "STU-001"
        }
    }
)
```

---

## Key Differences: Strands vs LangGraph

| Feature | Strands (AWS) | LangGraph |
|---------|---------------|-----------|
| **Framework** | AWS proprietary | Open source |
| **Agent Creation** | `Agent(model, tools, system_prompt)` | `StateGraph` with nodes |
| **Tool Definition** | `@tool` decorator | Plain Python functions |
| **Memory** | `AgentCoreMemorySessionManager` | Custom state management |
| **Orchestration** | Automatic via system prompt | Manual with conditional edges |
| **Deployment** | AgentCore Runtime | Self-hosted |
| **MCP Integration** | Native `MCPClient` | Manual implementation |

---

## Summary: What You Need for Restaurant Booking

### 1. **Orchestrator Agent**
- `@app.entrypoint` for AgentCore Runtime
- Memory integration with `AgentCoreMemorySessionManager`
- MCP Gateway integration for Lambda tools
- System prompt with routing logic

### 2. **Sub-Agents (as @tool functions)**
- `restaurant_finder_agent` - Search restaurants
- `booking_agent` - Handle reservations
- `payment_agent` - Process payments (optional, can use MCP tool directly)

### 3. **Configuration**
- Memory ID in SSM: `/restaurant-booking/agentcore/memory_id`
- Gateway URL in SSM: `/restaurant-booking/agentcore/gateway_url`
- Cognito credentials in SSM

### 4. **Deployment**
```bash
# Deploy orchestrator to AgentCore Runtime
bedrock-agentcore deploy \
  --runtime-file orchestrator_restaurant_booking.py \
  --name "RestaurantBookingOrchestrator"
```

---

## Next Steps

1. Create `orchestrator_restaurant_booking.py` following this pattern
2. Create sub-agent tools: `restaurant_finder_agent.py`, `booking_agent.py`
3. Deploy to AgentCore Runtime
4. Test with sample invocations

**Ready to implement?** The pattern is clear and well-documented in the education sample!
