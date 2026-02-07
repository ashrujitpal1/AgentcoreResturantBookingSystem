#!/usr/bin/env python3
"""Test Restaurant Finder Agent directly"""
import sys
sys.path.insert(0, '/Users/USER/Work/AI/AgentCore/AgentcoreResturantBookingSystem')

from src.agents.restaurant_finder import RestaurantFinderAgent
from src.tools.mcp_client import get_mcp_tools
import json

print("=" * 80)
print("TESTING RESTAURANT FINDER AGENT")
print("=" * 80)

# Get MCP tools
mcp_tools = get_mcp_tools()

# Create agent
agent = RestaurantFinderAgent(mcp_tools)

print(f"\n✅ Agent created: {agent.name}")

# Test process
print("\n" + "=" * 80)
print("TEST: Process user message")
print("=" * 80)

try:
    result = agent.process(
        user_message="Find Italian restaurants in Boston",
        correlation_id="test_agent_001"
    )
    
    print(f"\n✅ Agent Result:")
    print(json.dumps(result, indent=2, default=str))
    
except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 80)
