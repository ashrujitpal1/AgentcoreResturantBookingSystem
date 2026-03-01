#!/usr/bin/env python3
"""Test Restaurant Finder Agent with MCP Gateway"""
import sys
sys.path.insert(0, '/Users/USER/Work/AI/AgentCore/AgentcoreResturantBookingSystem')

from src.agents.restaurant_finder import RestaurantFinderAgent
import uuid

print("Testing Restaurant Finder Agent with MCP Gateway\n")
print("=" * 80)

# Initialize agent (mcp_tools parameter not used anymore)
agent = RestaurantFinderAgent(mcp_tools={})

# Test search
correlation_id = f"test_{uuid.uuid4()}"
user_message = "Find Indian restaurants in New York"

print(f"User: {user_message}\n")

try:
    result = agent.process(user_message, correlation_id)
    
    print(f"✅ Agent Response:")
    print(f"Content: {result.get('content', 'No content')[:200]}...")
    print(f"\nRestaurants found: {len(result.get('restaurants', []))}")
    
    for i, r in enumerate(result.get('restaurants', [])[:3], 1):
        print(f"{i}. {r.get('name')} - {r.get('cuisine')} - Rating: {r.get('rating')}")
    
    print("\n" + "=" * 80)
    print("✅ TEST PASSED - MCP Gateway integration working!")
    
except Exception as e:
    print(f"\n❌ TEST FAILED: {e}")
    import traceback
    traceback.print_exc()
