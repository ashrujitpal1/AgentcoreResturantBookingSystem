#!/usr/bin/env python3
"""Test parameter extraction"""
import sys
sys.path.insert(0, '/Users/USER/Work/AI/AgentCore/AgentcoreResturantBookingSystem')

from src.agents.booking_agent import BookingAgent
from src.tools.mcp_client import get_mcp_tools
import json

mcp_tools = get_mcp_tools()
agent = BookingAgent(mcp_tools)

# Simulate Turn 2: user provides name and phone
existing_params = {
    "restaurantId": "rest_123",
    "restaurantName": "Curry Leaf",
    "cityName": "San Francisco"
}

context = {"partial_params": existing_params}
user_message = "For booking: John Smith, phone 5551234567"

print("Existing params:")
print(json.dumps(existing_params, indent=2))
print(f"\nUser message: {user_message}")

params = agent._extract_booking_params(user_message, context, "test_001")

print(f"\nExtracted params:")
print(json.dumps(params, indent=2))

missing = agent._check_missing_fields(params)
print(f"\nMissing fields: {missing}")
