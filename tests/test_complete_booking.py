#!/usr/bin/env python3
"""
Complete booking flow: Search → Select → Book with all details
"""
import sys
sys.path.insert(0, '/Users/USER/Work/AI/AgentCore/AgentcoreResturantBookingSystem')

from src.workflows import RestaurantBookingWorkflow
from src.tools.mcp_client import get_mcp_tools
import boto3
import json

print("=" * 80)
print("COMPLETE BOOKING FLOW: Ashrujit's Reservation")
print("=" * 80)

mcp_tools = get_mcp_tools()
workflow = RestaurantBookingWorkflow(mcp_tools)
dynamodb = boto3.resource('dynamodb')
bookings_table = dynamodb.Table('Bookings')

user_id = "ashrujit_complete"
session_id = "session_complete_" + "x" * 17

# TURN 1: Search
print("\n" + "=" * 80)
print("TURN 1: Search for restaurants")
print("=" * 80)
msg1 = "Find restaurants in New York"
print(f"👤 Ashrujit: {msg1}")
r1 = workflow.invoke(msg1, user_id, session_id)
print(f"🤖 Assistant: {r1.get('final_response', '')[:250]}...")

restaurants = r1.get('restaurants', [])
if restaurants:
    selected = restaurants[0]
    restaurant_name = selected.get('name')
    restaurant_id = selected.get('restaurantId')
    print(f"\n📍 Selected: {restaurant_name} (ID: {restaurant_id})")

# TURN 2: Book with complete details
print("\n" + "=" * 80)
print("TURN 2: Book table with complete information")
print("=" * 80)

booking_msg = f"""Book a table at {restaurant_name} (restaurant ID: {restaurant_id})
Name: Ashrujit
Party size: 3 people
Date: 2026-02-15
Time: 19:00
Phone: 5550123456"""

print(f"👤 Ashrujit:\n{booking_msg}")

r2 = workflow.invoke(booking_msg, user_id, session_id)

print(f"\n🤖 Assistant: {r2.get('final_response', '')[:500]}")
print(f"\n📊 Result:")
print(f"   Intent: {r2.get('intent')}")
print(f"   Agent: {r2.get('current_agent')}")
print(f"   Booking ID: {r2.get('booking_id')}")
print(f"   Token Amount: ${r2.get('token_amount')}")

# VERIFY DATABASE
print("\n" + "=" * 80)
print("DATABASE VERIFICATION")
print("=" * 80)

booking_id = r2.get('booking_id')

if booking_id:
    response = bookings_table.get_item(Key={'bookingId': booking_id})
    if 'Item' in response:
        b = response['Item']
        print(f"\n✅ BOOKING CONFIRMED IN DYNAMODB!\n")
        print(f"📋 Booking Details:")
        print(f"   Booking ID: {b.get('bookingId')}")
        print(f"   Restaurant: {b.get('restaurantId')}")
        print(f"   Customer: {b.get('userName')}")
        print(f"   Phone: {b.get('userMobileNo')}")
        print(f"   Party Size: {b.get('noOfGuests')} guests")
        print(f"   Date: {b.get('bookingDate')}")
        print(f"   Time: {b.get('bookingTime')}")
        print(f"   Status: {b.get('bookingStatus')}")
        print(f"   Token Amount: ${b.get('tokenAmount')}")
        print(f"   Reference: {b.get('bookingReference')}")
        print(f"   Created: {b.get('createdAt')}")
        
        print(f"\n📄 Complete DynamoDB Record:")
        print(json.dumps(b, indent=2, default=str))
        
        print(f"\n✅ SUCCESS: Booking for Ashrujit confirmed!")
    else:
        print(f"❌ Booking ID {booking_id} not found in database")
else:
    print("⚠️  No booking ID returned, searching by name...")
    response = bookings_table.scan(
        FilterExpression='userName = :n',
        ExpressionAttributeValues={':n': 'Ashrujit'},
        Limit=5
    )
    
    if response['Items']:
        print(f"\n✅ Found {len(response['Items'])} booking(s) for Ashrujit:")
        for b in response['Items']:
            print(f"\n📋 Booking {b.get('bookingId')}:")
            print(f"   Restaurant: {b.get('restaurantId')}")
            print(f"   Date: {b.get('bookingDate')} at {b.get('bookingTime')}")
            print(f"   Guests: {b.get('noOfGuests')}")
            print(f"   Status: {b.get('bookingStatus')}")
            print(f"\n   Full Record:")
            print(json.dumps(b, indent=2, default=str))
    else:
        print("❌ No bookings found for Ashrujit")

print("\n" + "=" * 80)
print("✅ TEST COMPLETE")
print("=" * 80)
