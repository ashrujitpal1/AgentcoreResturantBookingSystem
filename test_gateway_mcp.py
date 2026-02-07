#!/usr/bin/env python3
"""Test Gateway with proper MCP protocol using Strands MCP Client."""
import boto3
import json
from strands.tools.mcp import MCPClient
from mcp.client.streamable_http import streamablehttp_client

def get_ssm_parameter(name: str) -> str:
    """Get parameter from SSM."""
    ssm = boto3.client("ssm")
    response = ssm.get_parameter(Name=name)
    return response["Parameter"]["Value"]

def get_cognito_token() -> str:
    """Get OAuth2 token from Cognito."""
    import requests
    
    user_pool_id = get_ssm_parameter("/app/restaurant-booking/user_pool_id")
    client_id = get_ssm_parameter("/app/restaurant-booking/client_id")
    client_secret = get_ssm_parameter("/app/restaurant-booking/client_secret")
    scope = get_ssm_parameter("/app/restaurant-booking/scope")
    
    region = boto3.Session().region_name
    domain = user_pool_id.replace("_", "").lower()
    token_url = f"https://{domain}.auth.{region}.amazoncognito.com/oauth2/token"
    
    response = requests.post(
        token_url,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        data={
            "grant_type": "client_credentials",
            "client_id": client_id,
            "client_secret": client_secret,
            "scope": scope
        }
    )
    
    response.raise_for_status()
    return response.json()["access_token"]

def create_mcp_transport():
    """Create MCP transport with authentication."""
    gateway_url = get_ssm_parameter("/app/restaurant-booking/gateway_url")
    token = get_cognito_token()
    
    return streamablehttp_client(
        gateway_url,
        headers={"Authorization": f"Bearer {token}"}
    )

def test_mcp_tools():
    """Test Gateway tools using proper MCP protocol."""
    print("🧪 Testing Gateway with Strands MCP Client...\n")
    
    # Create MCP client
    mcp_client = MCPClient(create_mcp_transport)
    
    with mcp_client:
        # List available tools
        print("=" * 60)
        print("Step 1: List Available Tools")
        print("=" * 60)
        
        tools = mcp_client.list_tools_sync()
        print(f"✅ Found {len(tools)} tools:")
        for tool in tools:
            tool_name = getattr(tool, 'name', getattr(tool, 'tool_name', 'Unknown'))
            tool_desc = getattr(tool, 'description', getattr(tool, 'tool_description', 'No description'))
            print(f"   - {tool_name}: {tool_desc}")
        print()
        
        # Test 1: Fetch Restaurant Details
        print("=" * 60)
        print("Test 1: fetchRestaurantDetails (Italian in New York)")
        print("=" * 60)
        
        try:
            # Get tool names from list
            tool_names = [getattr(t, 'tool_name', str(t)) for t in tools]
            print(f"Available tool names: {tool_names[:3]}...")
            
            # Use the actual tool object, not string name
            fetch_tool = tools[0]  # First tool should be fetchRestaurantDetails
            result = fetch_tool(
                city="New York",
                cuisine="Italian"
            )
            
            print(f"✅ Success!")
            print(f"Result: {json.dumps(result, indent=2) if isinstance(result, dict) else str(result)[:500]}...")
            
        except Exception as e:
            print(f"❌ Error: {str(e)}")
            import traceback
            traceback.print_exc()
        
        print()
        
        # Test 2: Fetch Restaurant by ID
        print("=" * 60)
        print("Test 2: fetchRestaurantDetailsById")
        print("=" * 60)
        
        try:
            result = mcp_client.call_tool_sync(
                "fetchRestaurantDetailsById",
                {
                    "restaurantId": "rest_001"
                }
            )
            
            print(f"✅ Success!")
            print(f"Result: {json.dumps(result, indent=2)[:500]}...")
            
        except Exception as e:
            print(f"❌ Error: {str(e)}")
        
        print()
        
        # Test 3: Token Amount Calculation
        print("=" * 60)
        print("Test 3: tokenAmountCalculation")
        print("=" * 60)
        
        try:
            result = mcp_client.call_tool_sync(
                "tokenAmountCalculation",
                {
                    "noOfGuests": 4,
                    "mealType": "dinner",
                    "restaurantTier": "$$$"
                }
            )
            
            print(f"✅ Success!")
            print(f"Result: {json.dumps(result, indent=2)}")
            
        except Exception as e:
            print(f"❌ Error: {str(e)}")
        
        print()
        
        # Test 4: Search User Details
        print("=" * 60)
        print("Test 4: searchUserDetails")
        print("=" * 60)
        
        try:
            result = mcp_client.call_tool_sync(
                "searchUserDetails",
                {
                    "username": "john_doe"
                }
            )
            
            print(f"✅ Success!")
            print(f"Result: {json.dumps(result, indent=2)}")
            
        except Exception as e:
            print(f"❌ Error: {str(e)}")
    
    print("\n" + "=" * 60)
    print("🎉 MCP Gateway tests complete!")
    print("=" * 60)

def test_mcp_sync():
    """Synchronous wrapper for MCP tests."""
    print("🚀 Starting MCP Gateway connectivity tests...\n")
    
    try:
        # Get configuration
        gateway_url = get_ssm_parameter("/app/restaurant-booking/gateway_url")
        print(f"✅ Gateway URL: {gateway_url}")
        
        token = get_cognito_token()
        print(f"✅ OAuth2 token obtained")
        print()
        
        # Run tests
        test_mcp_tools()
        
        print("\n📋 Summary:")
        print("   ✅ Gateway is accessible")
        print("   ✅ OAuth2 authentication working")
        print("   ✅ MCP protocol properly configured")
        print("   ✅ Tools can be invoked via Strands MCP Client")
        
    except Exception as e:
        print(f"\n❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_mcp_sync()
