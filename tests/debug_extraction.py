#!/usr/bin/env python3
"""Debug booking parameter extraction"""
import sys
sys.path.insert(0, '/Users/USER/Work/AI/AgentCore/AgentcoreResturantBookingSystem')

from src.agents.booking_agent import BookingAgent
from src.tools.mcp_client import get_mcp_tools
import json

mcp_tools = get_mcp_tools()
agent = BookingAgent(mcp_tools)

user_message = """Book a table at Curry Leaf
Name: John Smith
Phone: 5551234567
Date: 2026-03-15
Time: 19:00
Guests: 4 people"""

context = {
    "restaurants": [{
        "restaurantId": "rest_123",
        "name": "Curry Leaf",
        "city": "San Francisco"
    }]
}

print("Testing parameter extraction...")
print(f"User message: {user_message}")
print(f"Context: {json.dumps(context, indent=2)}")

params = agent._extract_booking_params(user_message, context, "test_001")

print(f"\nExtracted params:")
print(json.dumps(params, indent=2))

missing = agent._check_missing_fields(params)
print(f"\nMissing fields: {missing}")
