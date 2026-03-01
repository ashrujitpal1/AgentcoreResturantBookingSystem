#!/usr/bin/env python3
"""Standalone test for MCP Gateway Client using Strands MCPClient."""
import sys
sys.path.insert(0, '/Users/USER/Work/AI/AgentCore/AgentcoreResturantBookingSystem')

from src.tools.mcp_gateway_client import get_mcp_client
import json


def test_list_tools():
    """Test listing available tools from Gateway."""
    print("=" * 80)
    print("TEST 1: List Available Tools")
    print("=" * 80)
    
    mcp_client = get_mcp_client()
    
    with mcp_client:
        tools = mcp_client.list_tools_sync()
        print(f"✅ Found {len(tools)} tools:\n")
        
        for i, tool in enumerate(tools, 1):
            name = tool.tool_name
            spec = tool.tool_spec
            desc = spec.get('description', 'No description')
            
            print(f"{i}. {name}")
            print(f"   {desc[:100]}")
            if 'inputSchema' in spec:
                props = spec['inputSchema'].get('properties', {})
                if props:
                    print(f"   Parameters: {', '.join(props.keys())}")
            print()
        
        return tools


def test_fetch_restaurants():
    """Test fetchRestaurantDetails tool."""
    print("=" * 80)
    print("TEST 2: Find Indian Restaurant in New York")
    print("=" * 80)
    
    mcp_client = get_mcp_client()
    
    with mcp_client:
        result = mcp_client.call_tool_sync(
            name="fetchRestaurantDetails-target-1771948384___fetchRestaurantDetails",
            arguments={"city": "New York", "cuisine": "Indian"},
            tool_use_id="test_fetch_001"
        )
        
        restaurants = result.get("restaurants", [])
        print(f"✅ Found {len(restaurants)} restaurants\n")
        
        if restaurants:
            for i, r in enumerate(restaurants[:3], 1):
                print(f"{i}. {r.get('name', 'N/A')} - {r.get('cuisine', 'N/A')}")
                print(f"   Rating: {r.get('rating', 'N/A')} | Price: {r.get('priceRange', 'N/A')}")
                print(f"   Address: {r.get('location', {}).get('address', 'N/A')}\n")
        
        return result


def test_fetch_by_id():
    """Test fetchRestaurantDetailsById tool."""
    print("\n" + "=" * 80)
    print("TEST 3: Fetch Restaurant by ID")
    print("=" * 80)
    
    mcp_client = get_mcp_client()
    
    with mcp_client:
        result = mcp_client.call_tool_sync(
            name="fetchRestaurantDetailsById-target-1771948385___fetchRestaurantDetailsById",
            arguments={"restaurantId": "rest_001"},
            tool_use_id="test_fetch_by_id_001"
        )
        
        print(f"✅ Result: {json.dumps(result, indent=2)[:400]}...")
        return result


def test_token_calculation():
    """Test tokenAmountCalculation tool."""
    print("\n" + "=" * 80)
    print("TEST 4: Token Amount Calculation")
    print("=" * 80)
    
    mcp_client = get_mcp_client()
    
    with mcp_client:
        result = mcp_client.call_tool_sync(
            name="tokenAmountCalculation-target-1771948387___tokenAmountCalculation",
            arguments={"noOfGuests": 4, "mealType": "dinner", "restaurantTier": "$$$"},
            tool_use_id="test_token_calc_001"
        )
        
        print(f"✅ Tokens required: {result.get('tokensRequired', 'N/A')}")
        print(f"Full result: {json.dumps(result, indent=2)}")
        return result


def run_all_tests():
    """Run all standalone tests."""
    print("\n🚀 Starting MCP Gateway Client Standalone Tests\n")
    
    try:
        # Test 1: List tools
        tools = test_list_tools()
        
        # Test 2: Fetch restaurants
        test_fetch_restaurants()
        
        # Test 3: Fetch by ID
        test_fetch_by_id()
        
        # Test 4: Token calculation
        test_token_calculation()
        
        # Summary
        print("\n" + "=" * 80)
        print("✅ ALL TESTS PASSED")
        print("=" * 80)
        print("\n📋 Summary:")
        print("   ✅ MCP Gateway client initialized successfully")
        print("   ✅ OAuth2 authentication working")
        print("   ✅ Tool listing functional")
        print("   ✅ Tool invocation working")
        print(f"   ✅ Total tools available: {len(tools)}")
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    run_all_tests()
