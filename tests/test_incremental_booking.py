#!/usr/bin/env python3
"""
Test incremental booking with missing field detection
"""
import sys
sys.path.insert(0, '/Users/USER/Work/AI/AgentCore/AgentcoreResturantBookingSystem')

from src.workflows import RestaurantBookingWorkflow
from src.tools.mcp_client import get_mcp_tools

print("=" * 80)
print("TEST: Incremental Booking Flow")
print("=" * 80)

mcp_tools = get_mcp_tools()
workflow = RestaurantBookingWorkflow(mcp_tools)

user_id = "test_user_incremental"
session_id = "session_incremental_" + "x" * 17

# TURN 1: Search
print("\n" + "=" * 80)
print("TURN 1: Search for restaurants")
print("=" * 80)
msg1 = "Looking for Indian restaurant in San Francisco"
print(f"👤 User: {msg1}")
r1 = workflow.invoke(msg1, user_id, session_id)
print(f"🤖 Assistant: {r1.get('final_response', '')}")

# TURN 2: Book without details
print("\n" + "=" * 80)
print("TURN 2: Book without providing details")
print("=" * 80)
msg2 = "Book for Curry Leaf"
print(f"👤 User: {msg2}")
r2 = workflow.invoke(msg2, user_id, session_id)
print(f"🤖 Assistant: {r2.get('final_response', '')}")

# TURN 3: Provide partial info
print("\n" + "=" * 80)
print("TURN 3: Provide name and phone")
print("=" * 80)
msg3 = "My name is John and phone is 5551234567"
print(f"👤 User: {msg3}")
r3 = workflow.invoke(msg3, user_id, session_id)
print(f"🤖 Assistant: {r3.get('final_response', '')}")

# TURN 4: Provide remaining info
print("\n" + "=" * 80)
print("TURN 4: Provide date, time, guests")
print("=" * 80)
msg4 = "Book for 4 people on 2026-03-15 at 19:00"
print(f"👤 User: {msg4}")
r4 = workflow.invoke(msg4, user_id, session_id)
print(f"🤖 Assistant: {r4.get('final_response', '')}")

if r4.get('booking_id'):
    print(f"\n✅ SUCCESS: Booking created: {r4.get('booking_id')}")
else:
    print(f"\n⚠️  Status: {r4.get('final_response', 'Unknown')}")

print("\n" + "=" * 80)
