#!/usr/bin/env python3
"""Test incremental booking with explicit booking intent"""
import sys
sys.path.insert(0, '/Users/USER/Work/AI/AgentCore/AgentcoreResturantBookingSystem')

from src.workflows import RestaurantBookingWorkflow
from src.tools.mcp_client import get_mcp_tools

print("=" * 80)
print("TEST: Incremental Booking with Memory Persistence")
print("=" * 80)

mcp_tools = get_mcp_tools()
workflow = RestaurantBookingWorkflow(mcp_tools)

user_id = "john_memory_test"
session_id = "session_memory_" + "x" * 17

# TURN 1: Search
print("\n" + "=" * 80)
print("TURN 1: Search")
print("=" * 80)
msg1 = "Find Indian restaurants in San Francisco"
print(f"👤 User: {msg1}")
r1 = workflow.invoke(msg1, user_id, session_id)
print(f"🤖 Assistant: {r1.get('final_response', '')[:150]}...")

# TURN 2: Book - provide restaurant
print("\n" + "=" * 80)
print("TURN 2: Book - provide restaurant name")
print("=" * 80)
msg2 = "I want to book a table at Curry Leaf"
print(f"👤 User: {msg2}")
r2 = workflow.invoke(msg2, user_id, session_id)
print(f"🤖 Assistant: {r2.get('final_response', '')}")

# TURN 3: Book - provide name and phone
print("\n" + "=" * 80)
print("TURN 3: Book - provide name and phone")
print("=" * 80)
msg3 = "For the booking: my name is John Smith, phone 5551234567"
print(f"👤 User: {msg3}")
r3 = workflow.invoke(msg3, user_id, session_id)
print(f"🤖 Assistant: {r3.get('final_response', '')}")

# TURN 4: Book - provide date, time, guests
print("\n" + "=" * 80)
print("TURN 4: Book - provide date, time, guests")
print("=" * 80)
msg4 = "For the booking: 4 people on 2026-03-15 at 19:00"
print(f"👤 User: {msg4}")
r4 = workflow.invoke(msg4, user_id, session_id)
print(f"🤖 Assistant: {r4.get('final_response', '')}")

if r4.get('booking_id'):
    print(f"\n✅ SUCCESS: Booking {r4.get('booking_id')}")
    print(f"💰 Token: ${r4.get('token_amount')}")
else:
    print(f"\n⚠️  Status: {r4.get('final_response', '')[:100]}")

print("\n" + "=" * 80)
