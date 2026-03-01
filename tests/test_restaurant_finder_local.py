#!/usr/bin/env python3
"""Local test for Restaurant Finder Agent"""
import sys
sys.path.insert(0, '/Users/USER/Work/AI/AgentCore/AgentcoreResturantBookingSystem')

from src.agents.restaurant_finder import RestaurantFinderAgent
import uuid

def test_query(query: str):
    """Test a single query"""
    print("\n" + "=" * 80)
    print(f"Query: {query}")
    print("=" * 80)
    
    agent = RestaurantFinderAgent(mcp_tools={})
    correlation_id = f"test_{uuid.uuid4()}"
    
    result = agent.process(query, correlation_id)
    
    print(f"\n✅ Response:")
    print(result.get('content', 'No content'))
    
    restaurants = result.get('restaurants', [])
    print(f"\n📊 Found {len(restaurants)} restaurant(s):")
    for i, r in enumerate(restaurants, 1):
        print(f"  {i}. {r.get('name')} - {r.get('cuisine')} - Rating: {r.get('rating')}/5")
        print(f"     Location: {r.get('city')} | ID: {r.get('restaurantId')}")
    
    if result.get('handoff_to'):
        print(f"\n🔄 Handoff to: {result['handoff_to']}")
    
    return result

# Run tests
print("\n🧪 RESTAURANT FINDER AGENT - LOCAL TESTS")
print("=" * 80)

try:
    # Test 1: Indian in New York
    test_query("Find Indian restaurants in New York")
    
    # Test 2: Italian in Boston
    test_query("Show me Italian restaurants in Boston")
    
    # Test 3: Japanese (any city)
    test_query("I want Japanese food")
    
    # Test 4: Cheap restaurants in Chicago
    test_query("Find cheap restaurants in Chicago")
    
    # Test 5: High-rated in San Francisco
    test_query("Show highly rated restaurants in San Francisco")
    
    print("\n" + "=" * 80)
    print("✅ ALL TESTS COMPLETED SUCCESSFULLY")
    print("=" * 80)
    
except Exception as e:
    print(f"\n❌ TEST FAILED: {e}")
    import traceback
    traceback.print_exc()
