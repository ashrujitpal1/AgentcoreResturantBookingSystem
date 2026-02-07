#!/usr/bin/env python3
"""
Test booking with all details provided at once
"""
import sys
sys.path.insert(0, '/Users/USER/Work/AI/AgentCore/AgentcoreResturantBookingSystem')

from src.workflows import RestaurantBookingWorkflow
from src.tools.mcp_client import get_mcp_tools

print("=" * 80)
print("TEST: Complete Booking in One Message")
print("=" * 80)

mcp_tools = get_mcp_tools()
workflow = RestaurantBookingWorkflow(mcp_tools)

user_id = "test_user_complete"
session_id = "session_complete_" + "x" * 17

# TURN 1: Search
print("\n" + "=" * 80)
print("TURN 1: Search for restaurants")
print("=" * 80)
msg1 = "Find Indian restaurants in San Francisco"
print(f"👤 User: {msg1}")
r1 = workflow.invoke(msg1, user_id, session_id)
print(f"🤖 Assistant: {r1.get('final_response', '')[:200]}...")

# TURN 2: Book with all details
print("\n" + "=" * 80)
print("TURN 2: Book with complete information")
print("=" * 80)
msg2 = """Book a table at Curry Leaf
Name: John Smith
Phone: 5551234567
Date: 2026-03-15
Time: 19:00
Guests: 4 people"""

print(f"👤 User: {msg2}")
r2 = workflow.invoke(msg2, user_id, session_id)
print(f"🤖 Assistant: {r2.get('final_response', '')}")

if r2.get('booking_id'):
    print(f"\n✅ SUCCESS: Booking {r2.get('booking_id')}")
elif r2.get('error'):
    print(f"\n❌ ERROR: {r2.get('error')}")
else:
    print(f"\n⚠️  Status: Needs more info")

print("\n" + "=" * 80)
