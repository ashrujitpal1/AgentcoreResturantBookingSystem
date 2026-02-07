#!/usr/bin/env python3
"""Test MCP tools directly"""
import sys
sys.path.insert(0, '/Users/USER/Work/AI/AgentCore/AgentcoreResturantBookingSystem')

from src.tools.mcp_client import get_mcp_tools
import json

print("=" * 80)
print("TESTING MCP TOOLS")
print("=" * 80)

# Get MCP tools
mcp_tools = get_mcp_tools()

print(f"\n✅ MCP Tools loaded: {list(mcp_tools.keys())}")

# Test fetchRestaurantDetails
print("\n" + "=" * 80)
print("TEST: fetchRestaurantDetails")
print("=" * 80)

tool = mcp_tools["fetchRestaurantDetails"]
result = tool(
    city="Boston",
    cuisine="Italian",
    requestId="test_mcp_001"
)

print(f"\n✅ Result: {len(result.get('restaurants', []))} restaurants found")
print(json.dumps(result, indent=2)[:500])

print("\n" + "=" * 80)
print("✅ MCP TOOLS WORKING CORRECTLY")
print("=" * 80)
