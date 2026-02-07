#!/usr/bin/env python3
"""Debug workflow state"""
import sys
sys.path.insert(0, '/Users/USER/Work/AI/AgentCore/AgentcoreResturantBookingSystem')

from src.workflows import RestaurantBookingWorkflow
from src.tools.mcp_client import get_mcp_tools
import json

mcp_tools = get_mcp_tools()
workflow = RestaurantBookingWorkflow(mcp_tools)

user_id = "debug_user"
session_id = "session_debug_" + "x" * 17

# TURN 1: Search
msg1 = "Find Indian restaurants in San Francisco"
print(f"TURN 1: {msg1}")
r1 = workflow.invoke(msg1, user_id, session_id)
print(f"Restaurants in state: {len(r1.get('restaurants', []))}")
if r1.get('restaurants'):
    print(f"First restaurant: {r1['restaurants'][0]}")

# TURN 2: Book
msg2 = "Book Curry Leaf for John Smith, phone 5551234567, 4 people on 2026-03-15 at 19:00"
print(f"\nTURN 2: {msg2}")
r2 = workflow.invoke(msg2, user_id, session_id)
print(f"Response: {r2.get('final_response', '')[:150]}")
print(f"Booking ID: {r2.get('booking_id')}")
print(f"Error: {r2.get('error')}")
