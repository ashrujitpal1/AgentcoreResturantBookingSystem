#!/usr/bin/env python3
"""
Multi-turn booking conversation with incremental information gathering.
Simulates realistic user interaction where details are provided step-by-step.
"""
import sys
sys.path.insert(0, '/Users/USER/Work/AI/AgentCore/AgentcoreResturantBookingSystem')

from src.workflows import RestaurantBookingWorkflow
from src.tools.mcp_client import get_mcp_tools
import boto3
import json
from datetime import datetime

print("=" * 80)
print("MULTI-TURN BOOKING CONVERSATION TEST")
print("=" * 80)

# Initialize
mcp_tools = get_mcp_tools()
workflow = RestaurantBookingWorkflow(mcp_tools)
dynamodb = boto3.resource('dynamodb')
bookings_table = dynamodb.Table('Bookings')

user_id = "ashrujit_test_user"
session_id = "test_session_" + "x" * 25

print(f"\n👤 User: Ashrujit")
print(f"📱 Session: {session_id}\n")

# ========== TURN 1: Search Restaurants ==========
print("=" * 80)
print("TURN 1: User searches for restaurants")
print("=" * 80)

user_msg_1 = "Find Italian restaurants in Boston"
print(f"\n👤 User: {user_msg_1}")

result1 = workflow.invoke(
    user_message=user_msg_1,
    user_id=user_id,
    session_id=session_id
)

print(f"\n🤖 Assistant: {result1.get('final_response', '')[:300]}...")
restaurants = result1.get('restaurants', [])
print(f"\n✅ Found {len(restaurants)} restaurants")

if restaurants:
    selected_restaurant = restaurants[0]
    restaurant_name = selected_restaurant.get('name')
    restaurant_id = selected_restaurant.get('restaurantId')
    print(f"📍 First restaurant: {restaurant_name} (ID: {restaurant_id})")

# ========== TURN 2: Choose Restaurant (Name Only) ==========
print("\n" + "=" * 80)
print("TURN 2: User chooses restaurant by name only")
print("=" * 80)

user_msg_2 = restaurant_name
print(f"\n👤 User: {user_msg_2}")

result2 = workflow.invoke(
    user_message=user_msg_2,
    user_id=user_id,
    session_id=session_id
)

print(f"\n🤖 Assistant: {result2.get('final_response', '')[:300]}...")

# ========== TURN 3: Provide Name and Party Size ==========
print("\n" + "=" * 80)
print("TURN 3: User provides name and party size")
print("=" * 80)

user_msg_3 = "I am Ashrujit and we are three"
print(f"\n👤 User: {user_msg_3}")

result3 = workflow.invoke(
    user_message=user_msg_3,
    user_id=user_id,
    session_id=session_id
)

print(f"\n🤖 Assistant: {result3.get('final_response', '')[:300]}...")

# ========== TURN 4: Provide Date, Time, and Phone ==========
print("\n" + "=" * 80)
print("TURN 4: User provides date, time, and phone number")
print("=" * 80)

user_msg_4 = "Tomorrow at 7pm, my phone is +1-555-0123"
print(f"\n👤 User: {user_msg_4}")

result4 = workflow.invoke(
    user_message=user_msg_4,
    user_id=user_id,
    session_id=session_id
)

print(f"\n🤖 Assistant: {result4.get('final_response', '')[:500]}...")

booking_id = result4.get('booking_id')
token_amount = result4.get('token_amount')

print(f"\n✅ Booking ID: {booking_id}")
print(f"✅ Token Amount: ${token_amount}")

# ========== VERIFY DYNAMODB RECORD ==========
print("\n" + "=" * 80)
print("VERIFY: Check DynamoDB for booking record")
print("=" * 80)

if booking_id:
    try:
        response = bookings_table.get_item(Key={'bookingId': booking_id})
        
        if 'Item' in response:
            booking = response['Item']
            print(f"\n✅ BOOKING RECORD FOUND IN DYNAMODB!\n")
            print(f"📋 Booking Details:")
            print(f"   Booking ID: {booking.get('bookingId')}")
            print(f"   Restaurant ID: {booking.get('restaurantId')}")
            print(f"   User Name: {booking.get('userName')}")
            print(f"   Phone: {booking.get('userMobileNo')}")
            print(f"   Party Size: {booking.get('noOfGuests')}")
            print(f"   Date: {booking.get('bookingDate')}")
            print(f"   Time: {booking.get('bookingTime')}")
            print(f"   Status: {booking.get('bookingStatus')}")
            print(f"   Token Amount: ${booking.get('tokenAmount')}")
            print(f"   Reference: {booking.get('bookingReference')}")
            
            print(f"\n📄 Full Record:")
            print(json.dumps(booking, indent=2, default=str))
        else:
            print(f"❌ Booking not found: {booking_id}")
    except Exception as e:
        print(f"❌ Error: {e}")
else:
    print("⚠️  No booking ID returned")
    
    # Check for any bookings by this user
    try:
        response = bookings_table.scan(
            FilterExpression='userName = :name',
            ExpressionAttributeValues={':name': 'Ashrujit'},
            Limit=5
        )
        
        if response['Items']:
            print(f"\n✅ Found {len(response['Items'])} booking(s) for Ashrujit:")
            for booking in response['Items']:
                print(f"\n📋 Booking {booking.get('bookingId')}:")
                print(json.dumps(booking, indent=2, default=str))
        else:
            print("❌ No bookings found for Ashrujit")
    except Exception as e:
        print(f"❌ Scan error: {e}")

# ========== SUMMARY ==========
print("\n" + "=" * 80)
print("CONVERSATION SUMMARY")
print("=" * 80)

print(f"\n📊 Conversation Flow:")
print(f"   Turn 1: Searched for Italian restaurants in Boston")
print(f"   Turn 2: Selected '{restaurant_name}'")
print(f"   Turn 3: Provided name (Ashrujit) and party size (3)")
print(f"   Turn 4: Provided date, time, and phone number")
print(f"\n✅ Result: Booking {'CONFIRMED' if booking_id else 'PENDING'}")

print("\n" + "=" * 80)
print("✅ MULTI-TURN TEST COMPLETE")
print("=" * 80)
