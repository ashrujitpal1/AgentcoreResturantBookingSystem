#!/usr/bin/env python3
"""
Multi-turn booking with explicit booking intent.
"""
import sys
sys.path.insert(0, '/Users/USER/Work/AI/AgentCore/AgentcoreResturantBookingSystem')

from src.workflows import RestaurantBookingWorkflow
from src.tools.mcp_client import get_mcp_tools
import boto3
import json

print("=" * 80)
print("MULTI-TURN BOOKING: Ashrujit's Reservation")
print("=" * 80)

mcp_tools = get_mcp_tools()
workflow = RestaurantBookingWorkflow(mcp_tools)
dynamodb = boto3.resource('dynamodb')
bookings_table = dynamodb.Table('Bookings')

user_id = "ashrujit_user"
session_id = "session_ashrujit_" + "x" * 17

print(f"\n👤 User: Ashrujit\n")

# TURN 1: Search
print("=" * 80)
print("TURN 1: Search for restaurants")
print("=" * 80)
msg1 = "Find Italian restaurants in Boston"
print(f"👤 User: {msg1}")
r1 = workflow.invoke(msg1, user_id, session_id)
print(f"🤖 Assistant: {r1.get('final_response', '')[:200]}...")
restaurant_name = r1.get('restaurants', [{}])[0].get('name', 'Sakura Omakase')
print(f"\n📍 Available: {restaurant_name}")

# TURN 2: Choose restaurant
print("\n" + "=" * 80)
print("TURN 2: Choose restaurant by name")
print("=" * 80)
msg2 = restaurant_name
print(f"👤 User: {msg2}")
r2 = workflow.invoke(msg2, user_id, session_id)
print(f"🤖 Assistant: {r2.get('final_response', '')[:200]}...")

# TURN 3: Book with name and party size
print("\n" + "=" * 80)
print("TURN 3: Book table - provide name and party size")
print("=" * 80)
msg3 = f"I want to book a table at {restaurant_name}. I am Ashrujit and we are three people"
print(f"👤 User: {msg3}")
r3 = workflow.invoke(msg3, user_id, session_id)
print(f"🤖 Assistant: {r3.get('final_response', '')[:300]}...")

# TURN 4: Provide date, time, phone
print("\n" + "=" * 80)
print("TURN 4: Provide date, time, and phone")
print("=" * 80)
msg4 = "Tomorrow at 7pm, my phone number is +1-555-0123"
print(f"👤 User: {msg4}")
r4 = workflow.invoke(msg4, user_id, session_id)
print(f"🤖 Assistant: {r4.get('final_response', '')[:400]}...")

booking_id = r4.get('booking_id')
print(f"\n✅ Booking ID: {booking_id}")

# VERIFY DATABASE
print("\n" + "=" * 80)
print("DATABASE VERIFICATION")
print("=" * 80)

if booking_id:
    response = bookings_table.get_item(Key={'bookingId': booking_id})
    if 'Item' in response:
        b = response['Item']
        print(f"\n✅ BOOKING CONFIRMED IN DATABASE!\n")
        print(f"📋 Details:")
        print(f"   ID: {b.get('bookingId')}")
        print(f"   Restaurant: {b.get('restaurantId')}")
        print(f"   Name: {b.get('userName')}")
        print(f"   Phone: {b.get('userMobileNo')}")
        print(f"   Guests: {b.get('noOfGuests')}")
        print(f"   Date: {b.get('bookingDate')}")
        print(f"   Time: {b.get('bookingTime')}")
        print(f"   Status: {b.get('bookingStatus')}")
        print(f"   Amount: ${b.get('tokenAmount')}")
        print(f"\n📄 Full Record:")
        print(json.dumps(b, indent=2, default=str))
else:
    # Search by name
    response = bookings_table.scan(
        FilterExpression='userName = :n',
        ExpressionAttributeValues={':n': 'Ashrujit'},
        Limit=3
    )
    if response['Items']:
        print(f"\n✅ Found {len(response['Items'])} booking(s) for Ashrujit:")
        for b in response['Items']:
            print(f"\n📋 Booking {b.get('bookingId')}:")
            print(json.dumps(b, indent=2, default=str))
    else:
        print("\n⚠️  No bookings found")

print("\n" + "=" * 80)
print("✅ TEST COMPLETE")
print("=" * 80)
