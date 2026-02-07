#!/usr/bin/env python3
"""Test memory with delays for indexing"""
import sys
sys.path.insert(0, '/Users/USER/Work/AI/AgentCore/AgentcoreResturantBookingSystem')

from dotenv import load_dotenv
load_dotenv()

from src.workflows import RestaurantBookingWorkflow
from src.tools.mcp_client import get_mcp_tools
import time

mcp_tools = get_mcp_tools()
workflow = RestaurantBookingWorkflow(mcp_tools)

user_id = "memory_delay_test"
session_id = "session_delay_" + "x" * 17

# TURN 1
print("TURN 1: Book - provide restaurant")
r1 = workflow.invoke("Book Curry Leaf", user_id, session_id)
print(f"Response: {r1.get('final_response', '')[:80]}...")
print(f"Partial params: {r1.get('partial_booking_params')}")

print("\nWaiting 3 seconds for memory indexing...")
time.sleep(3)

# TURN 2
print("\nTURN 2: Book - provide name and phone")
r2 = workflow.invoke("For booking: John Smith, phone 5551234567", user_id, session_id)
print(f"Response: {r2.get('final_response', '')[:80]}...")
print(f"Partial params: {r2.get('partial_booking_params')}")

print("\nWaiting 3 seconds...")
time.sleep(3)

# TURN 3
print("\nTURN 3: Book - provide date, time, guests")
r3 = workflow.invoke("For booking: 4 people on 2026-03-15 at 19:00", user_id, session_id)
print(f"Response: {r3.get('final_response', '')[:150]}...")
print(f"Booking ID: {r3.get('booking_id')}")
