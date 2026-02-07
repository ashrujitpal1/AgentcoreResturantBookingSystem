#!/usr/bin/env python3
"""
Test booking flow and verify DynamoDB record creation.
"""
import sys
sys.path.insert(0, '/Users/USER/Work/AI/AgentCore/AgentcoreResturantBookingSystem')

from src.workflows import RestaurantBookingWorkflow
from src.tools.mcp_client import get_mcp_tools
import boto3
import json
from datetime import datetime

print("=" * 80)
print("BOOKING FLOW TEST WITH DYNAMODB VERIFICATION")
print("=" * 80)

# Initialize
mcp_tools = get_mcp_tools()
workflow = RestaurantBookingWorkflow(mcp_tools)
dynamodb = boto3.resource('dynamodb')
bookings_table = dynamodb.Table('Bookings')

user_id = f"test_user_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
session_id = "test_session_" + "x" * 25

print(f"\n✅ Test User: {user_id}")

# Step 1: Search for restaurants
print("\n" + "=" * 80)
print("STEP 1: Search for Restaurants")
print("=" * 80)

result1 = workflow.invoke(
    user_message="Find Italian restaurants in Boston",
    user_id=user_id,
    session_id=session_id
)

restaurants = result1.get('restaurants', [])
print(f"✅ Found {len(restaurants)} restaurants")

if restaurants:
    selected = restaurants[0]
    print(f"\n📍 Selected Restaurant:")
    print(f"   ID: {selected.get('restaurantId')}")
    print(f"   Name: {selected.get('name')}")
    print(f"   City: {selected.get('city')}")

# Step 2: Make a booking
print("\n" + "=" * 80)
print("STEP 2: Make a Booking")
print("=" * 80)

booking_message = f"Book a table at {selected.get('name')} for 4 people tomorrow at 7pm"
print(f"Request: {booking_message}")

result2 = workflow.invoke(
    user_message=booking_message,
    user_id=user_id,
    session_id=session_id
)

print(f"\n✅ Intent: {result2.get('intent')}")
print(f"✅ Agent: {result2.get('current_agent')}")
print(f"✅ Booking ID: {result2.get('booking_id')}")
print(f"✅ Token Amount: ${result2.get('token_amount')}")

# Step 3: Verify DynamoDB record
print("\n" + "=" * 80)
print("STEP 3: Verify DynamoDB Record")
print("=" * 80)

if result2.get('booking_id'):
    booking_id = result2.get('booking_id')
    
    try:
        response = bookings_table.get_item(
            Key={'bookingId': booking_id}
        )
        
        if 'Item' in response:
            booking = response['Item']
            print(f"\n✅ BOOKING RECORD FOUND IN DYNAMODB!")
            print(f"\n📋 Booking Details:")
            print(json.dumps(booking, indent=2, default=str))
            
            print(f"\n🎯 Key Fields:")
            print(f"   Booking ID: {booking.get('bookingId')}")
            print(f"   Restaurant ID: {booking.get('restaurantId')}")
            print(f"   User ID: {booking.get('userId')}")
            print(f"   Party Size: {booking.get('partySize')}")
            print(f"   Booking Date: {booking.get('bookingDate')}")
            print(f"   Booking Time: {booking.get('bookingTime')}")
            print(f"   Status: {booking.get('status')}")
            print(f"   Token Amount: ${booking.get('tokenAmount')}")
            print(f"   Created At: {booking.get('createdAt')}")
            
        else:
            print(f"❌ No booking found with ID: {booking_id}")
            
    except Exception as e:
        print(f"❌ Error querying DynamoDB: {e}")
else:
    print("⚠️  No booking ID returned - checking recent bookings...")
    
    # Scan for recent bookings by this user
    try:
        response = bookings_table.scan(
            FilterExpression='userId = :uid',
            ExpressionAttributeValues={':uid': user_id},
            Limit=5
        )
        
        if response['Items']:
            print(f"\n✅ Found {len(response['Items'])} booking(s) for user {user_id}:")
            for booking in response['Items']:
                print(f"\n📋 Booking:")
                print(json.dumps(booking, indent=2, default=str))
        else:
            print(f"❌ No bookings found for user {user_id}")
            
    except Exception as e:
        print(f"❌ Error scanning DynamoDB: {e}")

print("\n" + "=" * 80)
print("✅ TEST COMPLETE")
print("=" * 80)
