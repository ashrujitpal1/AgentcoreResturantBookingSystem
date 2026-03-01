# MCP Gateway Authentication - Correct Implementation

## Summary

After analyzing the **agentcore-for-education** reference implementation, the correct authentication pattern for AgentCore Runtime → Gateway communication is:

**Cognito OAuth2 Bearer Token (dynamically fetched)**

## Key Findings

### 1. Authentication Flow

```
AgentCore Runtime → Get Cognito Token → Call Gateway with Bearer Token → Gateway validates JWT → Invoke Lambda Tools
```

### 2. Token Retrieval (Dynamic)

The token is **NOT hardcoded** but fetched dynamically using OAuth2 client_credentials flow:

```python
def get_cognito_token() -> str:
    """Get Cognito OAuth2 access token using client_credentials flow."""
    # Get credentials from SSM
    user_pool_id = get_ssm_parameter("/app/restaurant-booking/user_pool_id")
    client_id = get_ssm_parameter("/app/restaurant-booking/client_id")
    client_secret = get_ssm_parameter("/app/restaurant-booking/client_secret")
    scope_string = get_ssm_parameter("/app/restaurant-booking/scope")
    
    # Request token from Cognito
    token_url = f"https://{user_pool_id_clean}.auth.{region}.amazoncognito.com/oauth2/token"
    response = requests.post(
        token_url,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        data={
            "grant_type": "client_credentials",
            "client_id": client_id,
            "client_secret": client_secret,
            "scope": scope_string
        }
    )
    
    return response.json()["access_token"]
```

### 3. MCP Client Configuration

```python
from strands.tools.mcp import MCPClient
from mcp.client.streamable_http import streamablehttp_client

def create_streamable_http_transport():
    gateway_url = get_ssm_parameter("/app/restaurant-booking/gateway_url")
    token = get_cognito_token()  # Dynamic token fetch
    
    return streamablehttp_client(
        gateway_url,
        headers={"Authorization": f"Bearer {token}"}
    )

mcp_client = MCPClient(create_streamable_http_transport)
```

### 4. Gateway Configuration

Gateway is configured with **CUSTOM_JWT** authorizer:

```python
auth_config = {
    "customJWTAuthorizer": {
        "allowedClients": [client_id],
        "discoveryUrl": f"https://cognito-idp.{region}.amazonaws.com/{user_pool_id}/.well-known/openid-configuration"
    }
}

gateway_client.create_gateway(
    name='restaurant-booking-gateway',
    roleArn=role_arn,
    protocolType='MCP',
    authorizerType='CUSTOM_JWT',  # JWT-based auth
    authorizerConfiguration=auth_config
)
```

### 5. Cognito Setup

The deployment creates:
- **User Pool**: For identity management
- **Resource Server**: Defines scopes (e.g., `restaurant-booking-auth/invoke`)
- **M2M Client**: Machine-to-machine client with client_credentials flow
- **Scope**: Stored in SSM for token requests

## Why This Approach?

1. **Security**: Tokens are short-lived and automatically refreshed
2. **No Hardcoding**: Credentials stored securely in SSM Parameter Store
3. **Standard OAuth2**: Uses industry-standard client_credentials flow
4. **Gateway Validation**: Gateway validates JWT against Cognito discovery URL

## Deployment Flow

1. **Deploy Cognito User Pool** → Creates user pool, resource server, M2M client
2. **Store in SSM** → user_pool_id, client_id, client_secret, scope
3. **Deploy Gateway** → Configured with CUSTOM_JWT authorizer
4. **Runtime Invocation** → Fetches token dynamically, calls Gateway with Bearer token

## SSM Parameters

```
/app/restaurant-booking/user_pool_id      → us-east-1_XXXXXXXXX
/app/restaurant-booking/client_id         → 7rfbikfsm51j2fpaggacgng84g
/app/restaurant-booking/client_secret     → <secret>
/app/restaurant-booking/scope             → restaurant-booking-auth/invoke
/app/restaurant-booking/gateway_url       → https://...gateway.bedrock-agentcore...
```

## Implementation Files

- **src/tools/mcp_gateway_client.py**: MCP client with dynamic token fetch
- **deploy-scripts/deploy_cognito_user_pool.py**: Cognito setup
- **deploy-scripts/deploy_agentcore_gateway.py**: Gateway with CUSTOM_JWT auth
- **src/orchestrator.py**: Uses MCP client to get tools from Gateway

## Comparison: SigV4 vs Bearer Token

| Aspect | SigV4 (IAM) | Bearer Token (Cognito OAuth2) |
|--------|-------------|-------------------------------|
| **Use Case** | Service-to-service (AWS internal) | Application-to-service (with auth) |
| **Token** | AWS credentials (access key/secret) | JWT access token |
| **Validation** | IAM policies | Cognito JWT validation |
| **Expiration** | Long-lived credentials | Short-lived tokens (1 hour) |
| **AgentCore Pattern** | ❌ Not used in reference | ✅ Used in agentcore-for-education |

## Conclusion

Your initial understanding was **partially correct**: the token should be fetched dynamically, but it's done **within the application code** (not by AgentCore infrastructure). The `get_cognito_token()` function handles dynamic token retrieval using OAuth2 client_credentials flow with credentials stored in SSM.

This pattern provides:
- ✅ Dynamic token fetching (no hardcoding)
- ✅ Secure credential storage (SSM)
- ✅ Standard OAuth2 flow
- ✅ Gateway JWT validation
- ✅ Follows AWS reference implementation
