# Migration to Strands Agent with MCP Gateway

## Overview

The Restaurant Booking System has been refactored to use **Strands Agent** with built-in **MCP (Model Context Protocol) Gateway** support, following the reference architecture from `agentcore-for-education`.

## Architecture Changes

### Before (Custom Implementation)
```
User Request
    ↓
Orchestrator (orchestrator.py)
    ↓
LangGraph Workflow
    ↓
Custom Strands Agents (Intent Classifier, Restaurant Finder, Booking Agent)
    ↓
Custom MCP Client (mcp_client.py)
    ↓
Direct Lambda Invocation (SigV4 Auth)
```

### After (Strands + MCP Gateway)
```
User Request
    ↓
Orchestrator (orchestrator.py)
    ↓
Strands Agent (single unified agent)
    ↓
MCP Gateway Client (mcp_gateway_client.py)
    ↓
AgentCore Gateway (Bearer Token Auth)
    ↓
Lambda Functions
```

## Key Benefits

### 1. **Simplified Architecture**
- Single Strands Agent instead of multiple custom agents
- No need for LangGraph workflow orchestration
- Agent handles tool calling automatically

### 2. **Built-in MCP Support**
- Uses Strands' native MCP client
- Automatic tool discovery via `list_tools_sync()`
- Tools passed directly to Agent

### 3. **Better Authentication**
- Bearer token (Cognito OAuth2) instead of SigV4
- Follows AWS best practices for Gateway authentication
- Token refresh support (implement in production)

### 4. **Cleaner Code**
- Less boilerplate code
- Framework handles tool invocation
- Easier to maintain and extend

## Implementation Details

### MCP Gateway Client (`src/tools/mcp_gateway_client.py`)

```python
from strands.tools.mcp import MCPClient
from mcp.client.streamable_http import streamablehttp_client

# Create transport with Bearer token
def create_streamable_http_transport():
    return streamablehttp_client(
        gateway_url,
        headers={"Authorization": f"Bearer {token}"}
    )

# Initialize MCP client
mcp_client = MCPClient(create_streamable_http_transport)
```

### Orchestrator (`src/orchestrator.py`)

```python
from strands import Agent
from src.tools.mcp_gateway_client import get_mcp_client

def handler(event, context):
    mcp_client = get_mcp_client()
    
    with mcp_client:
        # Get tools from Gateway
        mcp_tools = mcp_client.list_tools_sync()
        
        # Create agent with tools
        agent = Agent(
            model="anthropic.claude-3-5-sonnet-20241022-v2:0",
            system_prompt=system_prompt,
            tools=mcp_tools
        )
        
        # Invoke agent
        response = agent(user_message)
        return {"response": response.message}
```

## Configuration

### Environment Variables

```bash
# Gateway URL (from AgentCore Gateway deployment)
GATEWAY_URL=https://gateway-url.execute-api.us-east-1.amazonaws.com

# Cognito Access Token (Bearer token for Gateway auth)
COGNITO_ACCESS_TOKEN=eyJraWQiOiJ...

# Or store in SSM Parameter Store
# /restaurant-booking/cognito/access-token
```

### SSM Parameters

```bash
# Store Gateway URL
aws ssm put-parameter \
  --name /restaurant-booking/gateway/url \
  --value "https://gateway-url..." \
  --type String

# Store Cognito token
aws ssm put-parameter \
  --name /restaurant-booking/cognito/access-token \
  --value "eyJraWQiOiJ..." \
  --type SecureString
```

## MCP Tools Available

The agent automatically discovers these tools from the Gateway:

1. **fetchRestaurantDetails** - Search restaurants
2. **getCurrentDateTime** - Get current date/time
3. **searchUserDetails** - Check user existence
4. **registerUser** - Register new user
5. **tokenAmountCalculation** - Calculate deposit
6. **bookATable** - Create reservation
7. **paymentAPI** - Process payment

## Date Handling

The agent now handles relative dates correctly:

```
User: "Book a table for tomorrow at 7 PM"
    ↓
Agent calls getCurrentDateTime → "2026-02-11"
    ↓
Agent calculates: tomorrow = 2026-02-12
    ↓
Agent calls bookATable with date="2026-02-12", time="19:00"
```

## Migration Steps

1. ✅ Created `mcp_gateway_client.py` with Strands MCPClient
2. ✅ Updated `orchestrator.py` to use Strands Agent
3. ✅ Updated `requirements.txt` with Strands dependencies
4. ⏳ Deploy AgentCore Gateway (if not already deployed)
5. ⏳ Configure Cognito OAuth2 for Gateway authentication
6. ⏳ Update environment variables
7. ⏳ Deploy updated AgentCore Runtime

## Testing

```bash
# Test with Strands Agent
python3 tests/test_orchestrator.py

# Test date handling
python3 -c "
from src.orchestrator import handler

event = {
    'inputText': 'Book a table for tomorrow at 7 PM',
    'userId': 'test_user',
    'sessionId': 'test_session'
}

class Context:
    aws_request_id = 'test_123'

result = handler(event, Context())
print(result)
"
```

## Rollback Plan

If issues occur, the old implementation is preserved in:
- `src/workflows/` - LangGraph workflow
- `src/agents/` - Custom Strands agents
- `src/tools/mcp_client.py` - Old MCP client

To rollback, revert `src/orchestrator.py` to use the workflow.

## Next Steps

1. **Implement Token Refresh**: Add OAuth2 token refresh logic
2. **Add Memory Integration**: Integrate AgentCore Memory for conversation context
3. **Enhance System Prompt**: Add more detailed instructions for complex scenarios
4. **Add Observability**: Integrate with CloudWatch for tool call tracking
5. **Performance Testing**: Benchmark against old implementation

## References

- [agentcore-for-education](../agentcore-for-education/) - Reference implementation
- [Strands Documentation](https://github.com/aws-samples/strands-agents)
- [MCP Protocol](https://modelcontextprotocol.io/)
- [AgentCore Gateway](https://docs.aws.amazon.com/bedrock/latest/userguide/agentcore-gateway.html)
