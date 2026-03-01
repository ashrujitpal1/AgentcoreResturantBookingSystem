"""MCP Gateway Client using Strands MCPClient with dynamic Cognito OAuth2 token."""
import os
import boto3
import requests
from strands.tools.mcp import MCPClient
from mcp.client.streamable_http import streamablehttp_client


def get_ssm_parameter(name: str) -> str:
    """Retrieve parameter from SSM Parameter Store."""
    ssm = boto3.client("ssm")
    response = ssm.get_parameter(Name=name)
    return response["Parameter"]["Value"]


def get_cognito_token() -> str:
    """
    Get Cognito OAuth2 access token using client_credentials flow.
    Token is obtained dynamically from Cognito using credentials stored in SSM.
    """
    region = boto3.Session().region_name
    
    # Get credentials from SSM
    user_pool_id = get_ssm_parameter("/app/restaurant-booking/user_pool_id")
    client_id = get_ssm_parameter("/app/restaurant-booking/client_id")
    client_secret = get_ssm_parameter("/app/restaurant-booking/client_secret")
    scope_string = get_ssm_parameter("/app/restaurant-booking/scope")
    
    # Build token endpoint URL
    user_pool_id_clean = user_pool_id.replace("_", "")
    token_url = f"https://{user_pool_id_clean}.auth.{region}.amazoncognito.com/oauth2/token"
    
    # Request token using client_credentials grant
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
    response.raise_for_status()
    
    return response.json()["access_token"]


def create_streamable_http_transport():
    """Create streamable HTTP transport with Bearer token authentication."""
    gateway_url = get_ssm_parameter("/app/restaurant-booking/gateway_url")
    token = get_cognito_token()
    
    return streamablehttp_client(
        gateway_url,
        headers={"Authorization": f"Bearer {token}"}
    )


# Initialize global MCP client
mcp_client = MCPClient(create_streamable_http_transport)


def get_mcp_client() -> MCPClient:
    """Get the global MCP client instance."""
    return mcp_client
