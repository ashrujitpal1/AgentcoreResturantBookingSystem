#!/usr/bin/env python3
"""Test AgentCore Gateway integration with MCPToolClient."""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

from src.tools.mcp_client import get_mcp_tools
import json

def test_gateway_integration():
    """Test all MCP tools through Gateway."""
    print("🧪 Testing AgentCore Gateway Integration\n")
    print(f"Gateway URL: {os.getenv('GATEWAY_URL')}")
    print(f"User Pool ID: {os.getenv('USER_POOL_ID')}")
    print(f"Client ID: {os.getenv('CLIENT_ID')}\n")
    
    tools = get_mcp_tools()
    
    # Test 1: getCurrentDateTime (simplest tool)
    print("=" * 60)
    print("Test 1: getCurrentDateTime")
    print("=" * 60)
    try:
        result = tools['getCurrentDateTime'](timezone='America/New_York')
        print(f"✅ SUCCESS: {json.dumps(result, indent=2)}\n")
    except Exception as e:
        print(f"❌ FAILED: {str(e)}\n")
    
    # Test 2: fetchRestaurantDetails
    print("=" * 60)
    print("Test 2: fetchRestaurantDetails")
    print("=" * 60)
    try:
        result = tools['fetchRestaurantDetails'](
            city='New York',
            cuisine='Italian',
            requestId='test_gateway_001'
        )
        print(f"✅ SUCCESS: Found {len(result.get('restaurants', []))} restaurants")
        if result.get('restaurants'):
            print(f"   First: {result['restaurants'][0].get('name')}\n")
    except Exception as e:
        print(f"❌ FAILED: {str(e)}\n")
    
    # Test 3: searchUserDetails
    print("=" * 60)
    print("Test 3: searchUserDetails")
    print("=" * 60)
    try:
        result = tools['searchUserDetails'](
            userMobileNo='5551234567',
            requestId='test_gateway_002'
        )
        print(f"✅ SUCCESS: {json.dumps(result, indent=2)}\n")
    except Exception as e:
        print(f"❌ FAILED: {str(e)}\n")
    
    # Test 4: tokenAmountCalculation
    print("=" * 60)
    print("Test 4: tokenAmountCalculation")
    print("=" * 60)
    try:
        result = tools['tokenAmountCalculation'](
            noOfGuests=4,
            requestId='test_gateway_003'
        )
        print(f"✅ SUCCESS: Token amount = ${result.get('tokenAmount')}\n")
    except Exception as e:
        print(f"❌ FAILED: {str(e)}\n")
    
    print("=" * 60)
    print("🎉 Gateway Integration Test Complete!")
    print("=" * 60)

if __name__ == "__main__":
    test_gateway_integration()
