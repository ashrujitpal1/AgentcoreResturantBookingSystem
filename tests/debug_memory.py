#!/usr/bin/env python3
"""Debug memory storage and retrieval"""
import sys
sys.path.insert(0, '/Users/USER/Work/AI/AgentCore/AgentcoreResturantBookingSystem')

from dotenv import load_dotenv
load_dotenv()

import os
print(f"MEMORY_ID from env: {os.getenv('MEMORY_ID')}")

from src.workflows import RestaurantBookingWorkflow
from src.tools.mcp_client import get_mcp_tools
import json

mcp_tools = get_mcp_tools()
workflow = RestaurantBookingWorkflow(mcp_tools)

user_id = "debug_memory_user"
session_id = "session_debug_mem_" + "x" * 17

# TURN 1
print("TURN 1: Search")
r1 = workflow.invoke("Find Indian restaurants in San Francisco", user_id, session_id)
print(f"Restaurants stored: {len(r1.get('restaurants', []))}")

# Check memory after Turn 1
print("\nRetrieving memory after Turn 1...")
mem1 = workflow._retrieve_memory(user_id, session_id)
print(f"Memory restaurants: {len(mem1.get('restaurants', []))}")
print(f"Memory booking_params: {mem1.get('booking_params')}")

# TURN 2
print("\n\nTURN 2: Book")
r2 = workflow.invoke("Book Curry Leaf", user_id, session_id)
print(f"Partial params in state: {r2.get('partial_booking_params')}")

# Check memory after Turn 2
print("\nRetrieving memory after Turn 2...")
mem2 = workflow._retrieve_memory(user_id, session_id)
print(f"Memory restaurants: {len(mem2.get('restaurants', []))}")
print(f"Memory booking_params: {json.dumps(mem2.get('booking_params'), indent=2)}")
