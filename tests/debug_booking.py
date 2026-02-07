#!/usr/bin/env python3
"""Debug booking agent to see full response"""
import sys
sys.path.insert(0, '/Users/USER/Work/AI/AgentCore/AgentcoreResturantBookingSystem')

from src.agents.booking_agent import BookingAgent
from src.tools.mcp_client import get_mcp_tools
import json

print("=" * 80)
print("DEBUG BOOKING AGENT")
print("=" * 80)

mcp_tools = get_mcp_tools()
agent = BookingAgent(mcp_tools)

# Test booking
result = agent.process(
    user_message="Book a table at restaurant rest_006 for 4 people on 2026-02-10 at 19:00",
    correlation_id="test_debug_001",
    context={
        "restaurants": [{"restaurantId": "rest_006", "name": "Spice Symphony"}]
    }
)

print("\n📋 Full Agent Response:")
print(json.dumps(result, indent=2, default=str))

print("\n🔍 Key Fields:")
print(f"   Success: {result.get('success')}")
print(f"   Booking ID: {result.get('booking_details', {}).get('booking_id')}")
print(f"   Token Amount: {result.get('booking_details', {}).get('token_amount')}")
print(f"   Error: {result.get('error')}")
print(f"   Content: {result.get('content', '')[:200]}")
