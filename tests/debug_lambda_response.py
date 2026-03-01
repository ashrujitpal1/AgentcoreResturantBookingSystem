#!/usr/bin/env python3
"""Debug test to see parameter extraction and Lambda response"""
import sys
sys.path.insert(0, '/Users/USER/Work/AI/AgentCore/AgentcoreResturantBookingSystem')

from src.agents.restaurant_finder import RestaurantFinderAgent
from src.tools.mcp_gateway_client import get_mcp_client
import uuid
import json

print("=" * 80)
print("DEBUG: Parameter Extraction and Lambda Response")
print("=" * 80)

# Test 1: Check parameter extraction
agent = RestaurantFinderAgent(mcp_tools={})
correlation_id = f"debug_{uuid.uuid4()}"
user_message = "Find Indian restaurants in New York"

print(f"\n1. Extracting parameters from: '{user_message}'")
extracted = agent._extract_search_params(user_message, correlation_id)
print(f"   Extracted params: {json.dumps(extracted, indent=2)}")

# Test 2: Call Lambda directly with extracted params
print(f"\n2. Calling Lambda with extracted params...")
mcp_client = get_mcp_client()

with mcp_client:
    result = mcp_client.call_tool_sync(
        name="fetchRestaurantDetails-target-1771948384___fetchRestaurantDetails",
        arguments={
            "city": extracted.get("city"),
            "cuisine": extracted.get("cuisine"),
            "priceRange": extracted.get("priceRange"),
            "minRating": extracted.get("minRating")
        },
        tool_use_id=f"debug_{uuid.uuid4()}"
    )
    
    print(f"   Lambda response status: {result.get('status', 'unknown')}")
    print(f"   Restaurants count: {len(result.get('restaurants', []))}")
    
    if result.get('restaurants'):
        print(f"\n   First restaurant:")
        print(f"   {json.dumps(result['restaurants'][0], indent=4)}")
    else:
        print(f"\n   Full response: {json.dumps(result, indent=2)}")

# Test 3: Try without filters to see all data
print(f"\n3. Calling Lambda WITHOUT filters (city only)...")
with mcp_client:
    result = mcp_client.call_tool_sync(
        name="fetchRestaurantDetails-target-1771948384___fetchRestaurantDetails",
        arguments={"city": "New York"},
        tool_use_id=f"debug_{uuid.uuid4()}"
    )
    
    restaurants = result.get('restaurants', [])
    print(f"   Total restaurants in New York: {len(restaurants)}")
    
    if restaurants:
        cuisines = set(r.get('cuisine', 'Unknown') for r in restaurants)
        print(f"   Available cuisines: {sorted(cuisines)}")
        
        # Check for Indian
        indian = [r for r in restaurants if 'indian' in r.get('cuisine', '').lower()]
        print(f"   Indian restaurants: {len(indian)}")
        
        if indian:
            print(f"\n   Sample Indian restaurant:")
            print(f"   {json.dumps(indian[0], indent=4)}")

print("\n" + "=" * 80)
