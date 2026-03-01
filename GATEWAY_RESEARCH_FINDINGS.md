# AgentCore Gateway Configuration - Research Findings

## Key Discovery

**The AgentCore Runtime does NOT automatically use the Gateway for tool invocations.**

You must explicitly configure tools to be invoked through the Gateway using the `bedrock-agentcore` client.

## Correct Implementation

### Method 1: Use boto3 bedrock-agentcore Client (CORRECT)

```python
# src/tools/mcp_client.py
import boto3
import json
import os

class MCPToolClient:
    """Client for invoking tools through AgentCore Gateway."""
    
    def __init__(self):
        # Use bedrock-agentcore client (NOT lambda client)
        self.client = boto3.client('bedrock-agentcore', region_name=os.getenv('AWS_REGION', 'us-east-1'))
        self.gateway_id = os.getenv('GATEWAY_ID')  # restaurant-booking-gateway-e7trb0r5cm
        self.runtime_arn = os.getenv('AGENT_RUNTIME_ARN')
        
        print(f"[INFO] MCPToolClient using Gateway: {self.gateway_id}")
    
    def invoke_tool_via_gateway(self, tool_name: str, payload: dict) -> dict:
        """Invoke tool through Gateway using invoke_agent_runtime."""
        
        # MCP protocol request format
        mcp_request = {
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {
                "name": tool_name,
                "arguments": payload
            },
            "id": 1
        }
        
        try:
            print(f"[DEBUG] Invoking via Gateway: {tool_name}")
            
            # Invoke the Runtime with Gateway URL
            response = self.client.invoke_agent_runtime(
                runtimeIdentifier=self.runtime_arn,
                contentType='application/json',
                accept='application/json',
                body=json.dumps(mcp_request)
            )
            
            # Parse streaming response
            result = json.loads(response['body'].read())
            print(f"[DEBUG] Gateway response: {json.dumps(result, default=str)[:200]}...")
            
            # Extract result from MCP response
            if 'result' in result:
                return result['result']
            return result
            
        except Exception as e:
            print(f"[ERROR] Gateway invocation failed: {e}")
            return {"error": str(e)}
```

### Method 2: Direct Gateway Target Invocation (ALTERNATIVE)

The Gateway targets are Lambda functions. We need to invoke them through the Gateway's MCP endpoint:

```python
import requests
from botocore.auth import SigV4Auth
from botocore.awsrequest import AWSRequest
import boto3

class MCPToolClient:
    def __init__(self):
        self.gateway_url = os.getenv('GATEWAY_URL')
        self.session = boto3.Session()
        self.credentials = self.session.get_credentials()
        self.region = os.getenv('AWS_REGION', 'us-east-1')
    
    def invoke_tool(self, tool_name: str, payload: dict):
        # MCP protocol format
        mcp_request = {
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {
                "name": tool_name,
                "arguments": payload
            },
            "id": 1
        }
        
        # Create signed request
        request = AWSRequest(
            method='POST',
            url=self.gateway_url,
            data=json.dumps(mcp_request),
            headers={'Content-Type': 'application/json'}
        )
        
        # Sign with SigV4
        SigV4Auth(self.credentials, 'bedrock-agentcore', self.region).add_auth(request)
        
        # Send request
        response = requests.post(
            request.url,
            headers=dict(request.headers),
            data=request.body
        )
        
        return response.json()
```

## Gateway Configuration Details

From research:

1. **Gateway URL:** `https://restaurant-booking-gateway-e7trb0r5cm.gateway.bedrock-agentcore.us-east-1.amazonaws.com/mcp`
2. **Protocol:** MCP (Model Context Protocol)
3. **Authentication:** Custom JWT (Cognito) OR IAM (SigV4)
4. **Targets:** Lambda functions registered as MCP tools

## MCP Protocol Format

The Gateway expects JSON-RPC 2.0 format:

```json
{
  "jsonrpc": "2.0",
  "method": "tools/call",
  "params": {
    "name": "fetchRestaurantDetails",
    "arguments": {
      "city": "New York",
      "cuisine": "Italian"
    }
  },
  "id": 1
}
```

Response format:

```json
{
  "jsonrpc": "2.0",
  "result": {
    "restaurants": [...]
  },
  "id": 1
}
```

## Implementation Decision

**Recommended: Method 2 (Direct Gateway with SigV4)**

Why:
- ✅ Explicit Gateway usage
- ✅ Works in Lambda (automatic credentials)
- ✅ Proper authentication
- ✅ Clear error handling
- ✅ No dependency on Runtime invoke method

## Next Steps

1. Implement Method 2 in `mcp_client.py`
2. Add `botocore` and `requests` to requirements
3. Redeploy Runtime
4. Test with Streamlit
5. Verify Gateway logs in CloudWatch

## References

- Gateway ARN: `arn:aws:bedrock-agentcore:us-east-1:696072349808:gateway/restaurant-booking-gateway-e7trb0r5cm`
- Gateway URL: `https://restaurant-booking-gateway-e7trb0r5cm.gateway.bedrock-agentcore.us-east-1.amazonaws.com/mcp`
- Protocol: MCP (JSON-RPC 2.0)
- Auth: IAM SigV4 or Cognito JWT
