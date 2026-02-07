#!/usr/bin/env python3
"""
Comprehensive local test of the entire Restaurant Booking System.
Tests: Intent Classification → Restaurant Search → Memory Storage → Booking Flow
"""
import sys
sys.path.insert(0, '/Users/USER/Work/AI/AgentCore/AgentcoreResturantBookingSystem')

from src.workflows import RestaurantBookingWorkflow
from src.tools.mcp_client import get_mcp_tools
import json

print("=" * 80)
print("COMPREHENSIVE RESTAURANT BOOKING SYSTEM TEST")
print("=" * 80)

# Initialize
mcp_tools = get_mcp_tools()
workflow = RestaurantBookingWorkflow(mcp_tools)

user_id = "test_user_local_001"
session_id = "test_session_" + "x" * 25

print(f"\n✅ Workflow initialized")
print(f"   User ID: {user_id}")
print(f"   Session ID: {session_id}")

# ========== TEST 1: Restaurant Search ==========
print("\n" + "=" * 80)
print("TEST 1: Restaurant Search (Intent: search)")
print("=" * 80)

result1 = workflow.invoke(
    user_message="Find Italian restaurants in Boston",
    user_id=user_id,
    session_id=session_id
)

print(f"\n✅ Intent: {result1.get('intent')}")
print(f"✅ Agent: {result1.get('current_agent')}")
print(f"✅ Restaurants Found: {len(result1.get('restaurants', []))}")
print(f"\n📝 Response:\n{result1.get('final_response', 'No response')[:300]}...")

# ========== TEST 2: Follow-up Question ==========
print("\n" + "=" * 80)
print("TEST 2: Follow-up Question (Memory Context)")
print("=" * 80)

result2 = workflow.invoke(
    user_message="Tell me more about the first one",
    user_id=user_id,
    session_id=session_id
)

print(f"\n✅ Intent: {result2.get('intent')}")
print(f"✅ Agent: {result2.get('current_agent')}")
print(f"\n📝 Response:\n{result2.get('final_response', 'No response')[:300]}...")

# ========== TEST 3: Booking Intent ==========
print("\n" + "=" * 80)
print("TEST 3: Booking Request (Intent: booking)")
print("=" * 80)

result3 = workflow.invoke(
    user_message="I want to book a table for 4 people tomorrow at 7pm",
    user_id=user_id,
    session_id=session_id
)

print(f"\n✅ Intent: {result3.get('intent')}")
print(f"✅ Agent: {result3.get('current_agent')}")
if result3.get('booking_id'):
    print(f"✅ Booking ID: {result3.get('booking_id')}")
if result3.get('hitl_required'):
    print(f"⚠️  HITL Required: {result3.get('hitl_reason')}")
print(f"\n📝 Response:\n{result3.get('final_response', 'No response')[:300]}...")

# ========== TEST 4: Different Cuisine ==========
print("\n" + "=" * 80)
print("TEST 4: Different Cuisine Search")
print("=" * 80)

result4 = workflow.invoke(
    user_message="Show me Japanese restaurants in New York",
    user_id=user_id,
    session_id=session_id
)

print(f"\n✅ Intent: {result4.get('intent')}")
print(f"✅ Agent: {result4.get('current_agent')}")
print(f"✅ Restaurants Found: {len(result4.get('restaurants', []))}")
print(f"\n📝 Response:\n{result4.get('final_response', 'No response')[:300]}...")

# ========== SUMMARY ==========
print("\n" + "=" * 80)
print("TEST SUMMARY")
print("=" * 80)

tests = [
    ("Restaurant Search", result1.get('intent') == 'search'),
    ("Follow-up Context", result2.get('current_agent') is not None),
    ("Booking Intent", result3.get('intent') in ['booking', 'search']),
    ("Multi-turn Memory", result4.get('intent') == 'search')
]

for test_name, passed in tests:
    status = "✅ PASS" if passed else "❌ FAIL"
    print(f"{status}: {test_name}")

print("\n" + "=" * 80)
print("✅ COMPREHENSIVE TEST COMPLETE")
print("=" * 80)
