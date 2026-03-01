# AgentCore Gateway Invocation - The Correct Approach

## Your Question is 100% Correct!

You asked: **"Are we getting authenticated in the AgentCore Gateway before calling Lambda?"**

**Answer:** NO - and that's the problem we need to fix!

## Current (Wrong) Architecture

```
AgentCore Runtime
    ↓
mcp_client.py → boto3.client('lambda').invoke()  ❌ BYPASSES GATEWAY
    ↓
Lambda Functions (direct)
```

**Problems:**
- ❌ No Gateway authentication
- ❌ No centralized rate limiting
- ❌ No unified observability
- ❌ Gateway infrastructure unused

## Correct Architecture (What We Need)

```
AgentCore Runtime
    ↓
mcp_client.py → boto3.client('bedrock-agentcore').invoke_gateway()  ✅ THROUGH GATEWAY
    ↓
AgentCore Gateway (authenticates, logs, routes)
    ↓
Lambda Functions
```

**Benefits:**
- ✅ Gateway handles authentication
- ✅ Centralized rate limiting
- ✅ Unified observability
- ✅ Proper use of deployed infrastructure

## The Correct boto3 API

Based on the available services, we should use:

```python
import boto3

# Correct client for Gateway invocation
client = boto3.client('bedrock-agentcore', region_name='us-east-1')

# Invoke Gateway (which then calls Lambda)
response = client.invoke_gateway(
    gatewayIdentifier='restaurant-booking-gateway-e7trb0r5cm',
    targetIdentifier='<target-name>',  # e.g., 'fetchRestaurantDetails-target'
    input={
        'city': 'New York',
        'cuisine': 'Italian'
    }
)
```

## Why We're Currently Calling Lambda Directly

**Reason:** The Gateway MCP protocol and boto3 API for `bedrock-agentcore` is not well documented, and we hit errors when trying to use it.

**But this is WRONG** - we should fix it to use Gateway properly!

## Next Steps - Fix This Properly

### Option 1: Use bedrock-agentcore Client (Recommended)

```python
# src/tools/mcp_client.py
import boto3
import json
import os

class MCPToolClient:
    def __init__(self):
        self.gateway_client = boto3.client('bedrock-agentcore', region_name=os.getenv('AWS_REGION'))
        self.gateway_id = os.getenv('GATEWAY_ID')  # restaurant-booking-gateway-e7trb0r5cm
    
    def invoke_tool(self, tool_name: str, payload: dict):
        # Find target ID for this tool
        target_id = f"{tool_name}-target"
        
        response = self.gateway_client.invoke_gateway(
            gatewayIdentifier=self.gateway_id,
            targetIdentifier=target_id,
            input=payload
        )
        
        return response['output']
```

### Option 2: Research Proper MCP Protocol

The Gateway expects MCP protocol format. We need to:
1. Check AWS documentation for `bedrock-agentcore` API
2. Find correct method to invoke Gateway targets
3. Understand input/output format

## Action Items

1. **Research** - Find correct boto3 API for Gateway invocation
2. **Test** - Try `invoke_gateway()` or similar method
3. **Fix** - Update `mcp_client.py` to use Gateway
4. **Redeploy** - Deploy updated Runtime
5. **Verify** - Confirm Gateway is being used (check CloudWatch logs)

## Why This Matters

**Current state:** We deployed Gateway infrastructure but aren't using it = wasted resources

**Correct state:** Runtime → Gateway → Lambda = proper architecture with auth, rate limiting, observability

---

**You're absolutely right to question this!** We need to fix it to use Gateway properly, not bypass it with direct Lambda calls.
