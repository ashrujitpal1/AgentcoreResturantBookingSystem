#!/usr/bin/env python3
"""Complete end-to-end test with single-turn booking"""
import sys
sys.path.insert(0, '/Users/USER/Work/AI/AgentCore/AgentcoreResturantBookingSystem')

from src.workflows.restaurant_workflow import RestaurantBookingWorkflow
import uuid

print("\n" + "=" * 80)
print("🧪 COMPLETE RESTAURANT BOOKING SYSTEM TEST")
print("=" * 80)

workflow = RestaurantBookingWorkflow(mcp_tools={})
user_id = f"test_{uuid.uuid4().hex[:8]}"
session_id = f"sess_{uuid.uuid4().hex[:8]}"

# Test 1: Search
print("\n\n📋 TEST 1: Restaurant Search")
print("-" * 80)
result = workflow.invoke(
    user_message="Find Indian restaurants in New York",
    user_id=user_id,
    session_id=session_id
)
print(f"Response: {result.get('final_response', '')[:200]}...")
print(f"Restaurants found: {len(result.get('restaurants', []))}")
if result.get('restaurants'):
    for r in result['restaurants'][:2]:
        print(f"  - {r.get('name')} ({r.get('restaurantId')})")

# Test 2: Complete booking in one message
print("\n\n📋 TEST 2: Complete Booking (Single Turn)")
print("-" * 80)
user_id2 = f"test_{uuid.uuid4().hex[:8]}"
session_id2 = f"sess_{uuid.uuid4().hex[:8]}"

# First search to get restaurant
search_result = workflow.invoke(
    user_message="Find Indian restaurants in New York",
    user_id=user_id2,
    session_id=session_id2
)

if search_result.get('restaurants'):
    restaurant = search_result['restaurants'][0]
    print(f"Found restaurant: {restaurant.get('name')} (ID: {restaurant.get('restaurantId')})")
    
    # Now book with all details
    booking_result = workflow.invoke(
        user_message=f"Book {restaurant.get('name')} for tomorrow at 7pm for 2 people. My name is John Doe, phone +1234567890",
        user_id=user_id2,
        session_id=session_id2,
        restaurants=[restaurant],
        selected_restaurant=restaurant
    )
    
    print(f"\nBooking Response: {booking_result.get('final_response', '')[:300]}...")
    
    if booking_result.get('booking_id'):
        print(f"\n✅ SUCCESS!")
        print(f"   Booking ID: {booking_result['booking_id']}")
        print(f"   Token Amount: ${booking_result.get('token_amount', 0)}")
    elif booking_result.get('partial_booking_params'):
        print(f"\n⏳ Partial booking - missing fields")
        print(f"   Collected: {booking_result['partial_booking_params']}")
    else:
        print(f"\n❌ Booking failed")
        if booking_result.get('error'):
            print(f"   Error: {booking_result['error']}")

# Test 3: Out of scope
print("\n\n📋 TEST 3: Out of Scope Handling")
print("-" * 80)
result = workflow.invoke(
    user_message="What's the weather?",
    user_id=f"test_{uuid.uuid4().hex[:8]}",
    session_id=f"sess_{uuid.uuid4().hex[:8]}"
)
print(f"Response: {result.get('final_response', '')[:200]}...")

print("\n" + "=" * 80)
print("✅ TESTS COMPLETED")
print("=" * 80)
