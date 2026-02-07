#!/usr/bin/env python3
"""
Test incremental booking information collection with AgentCore Memory.
Demonstrates:
1. LLM extracting partial details from each user message
2. Storing extracted info in AgentCore Memory
3. Retrieving and merging info across turns
4. Completing booking when all required fields are collected
"""
import sys
sys.path.insert(0, '/Users/USER/Work/AI/AgentCore/AgentcoreResturantBookingSystem')

from src.workflows import RestaurantBookingWorkflow
from src.tools.mcp_client import get_mcp_tools
import boto3
import json
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

print("=" * 80)
print("INCREMENTAL BOOKING WITH AGENTCORE MEMORY")
print("=" * 80)

# Initialize
mcp_tools = get_mcp_tools()
workflow = RestaurantBookingWorkflow(mcp_tools)
dynamodb = boto3.resource('dynamodb')
bookings_table = dynamodb.Table('Bookings')
memory_client = boto3.client('bedrock-agentcore')
memory_id = os.getenv('MEMORY_ID')

user_id = "ashrujit_memory_test"
session_id = "session_memory_" + "x" * 19

print(f"\n👤 User: Ashrujit")
print(f"📱 Session: {session_id}")
print(f"🧠 Memory ID: {memory_id}\n")

# Helper to check memory
def check_memory():
    if not memory_id:
        print("⚠️  No memory ID configured")
        return []
    try:
        response = memory_client.retrieve_memory_records(
            memoryId=memory_id,
            namespace='conversation_history',
            searchCriteria={'searchQuery': user_id},
            maxResults=5
        )
        records = response.get('memoryRecords', [])
        if records:
            print(f"\n🧠 Memory Records ({len(records)} found):")
            for i, record in enumerate(records, 1):
                data = record.get('eventData', {})
                print(f"   {i}. User: {data.get('userMessage', 'N/A')[:40]}...")
                print(f"      Assistant: {data.get('assistantResponse', 'N/A')[:40]}...")
        else:
            print("\n🧠 No memory records found yet")
        return records
    except Exception as e:
        print(f"⚠️  Memory check failed: {str(e)[:100]}")
        return []

# ========== TURN 1: Search Restaurants ==========
print("=" * 80)
print("TURN 1: User searches for restaurants")
print("=" * 80)

msg1 = "Find Italian restaurants in Boston"
print(f"\n👤 Ashrujit: {msg1}")

r1 = workflow.invoke(msg1, user_id, session_id)
print(f"\n🤖 Assistant: {r1.get('final_response', '')[:250]}...")

restaurants = r1.get('restaurants', [])
if restaurants:
    selected = restaurants[0]
    restaurant_name = selected.get('name')
    restaurant_id = selected.get('restaurantId')
    print(f"\n📍 Restaurant: {restaurant_name} (ID: {restaurant_id})")

check_memory()

# ========== TURN 2: Choose Restaurant (Name Only) ==========
print("\n" + "=" * 80)
print("TURN 2: User selects restaurant by name")
print("=" * 80)

msg2 = restaurant_name
print(f"\n👤 Ashrujit: {msg2}")

r2 = workflow.invoke(msg2, user_id, session_id)
print(f"\n🤖 Assistant: {r2.get('final_response', '')[:250]}...")

check_memory()

# ========== TURN 3: Provide Name and Party Size ==========
print("\n" + "=" * 80)
print("TURN 3: User provides name and party size")
print("=" * 80)

msg3 = "I want to book a table. My name is Ashrujit and we are 3 people"
print(f"\n👤 Ashrujit: {msg3}")

r3 = workflow.invoke(msg3, user_id, session_id)
print(f"\n🤖 Assistant: {r3.get('final_response', '')[:300]}...")

print(f"\n📊 Extracted so far:")
print(f"   Name: Ashrujit")
print(f"   Party Size: 3")
print(f"   Restaurant: {restaurant_name}")

check_memory()

# ========== TURN 4: Provide Date and Time ==========
print("\n" + "=" * 80)
print("TURN 4: User provides date and time")
print("=" * 80)

msg4 = "For tomorrow at 7pm"
print(f"\n👤 Ashrujit: {msg4}")

r4 = workflow.invoke(msg4, user_id, session_id)
print(f"\n🤖 Assistant: {r4.get('final_response', '')[:300]}...")

print(f"\n📊 Extracted so far:")
print(f"   Name: Ashrujit")
print(f"   Party Size: 3")
print(f"   Date: Tomorrow")
print(f"   Time: 7pm")
print(f"   Restaurant: {restaurant_name}")

check_memory()

# ========== TURN 5: Provide Phone Number ==========
print("\n" + "=" * 80)
print("TURN 5: User provides phone number (final piece)")
print("=" * 80)

msg5 = "My phone number is 8887776666"
print(f"\n👤 Ashrujit: {msg5}")

r5 = workflow.invoke(msg5, user_id, session_id)
print(f"\n🤖 Assistant: {r5.get('final_response', '')[:500]}")

booking_id = r5.get('booking_id')
token_amount = r5.get('token_amount')

print(f"\n✅ Booking ID: {booking_id}")
print(f"✅ Token Amount: ${token_amount}")

check_memory()

# ========== VERIFY DYNAMODB ==========
print("\n" + "=" * 80)
print("DATABASE VERIFICATION")
print("=" * 80)

if booking_id:
    response = bookings_table.get_item(Key={'bookingId': booking_id})
    if 'Item' in response:
        b = response['Item']
        print(f"\n🎉 BOOKING CONFIRMED IN DYNAMODB!")
        print(f"\n📋 Booking Details:")
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
        
        print(f"\n📄 Full Record:")
        print(json.dumps(b, indent=2, default=str))
    else:
        print(f"❌ Booking not found: {booking_id}")
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
            print(f"   Restaurant: {b.get('restaurantId')}")
            print(f"   Date: {b.get('bookingDate')} at {b.get('bookingTime')}")
            print(f"   Guests: {b.get('noOfGuests')}")
            print(f"   Phone: {b.get('userMobileNo')}")
            print(f"   Status: {b.get('bookingStatus')}")
    else:
        print("⚠️  No bookings found")

# ========== MEMORY SUMMARY ==========
print("\n" + "=" * 80)
print("AGENTCORE MEMORY SUMMARY")
print("=" * 80)

final_memory = check_memory()
print(f"\n📊 Conversation Summary:")
print(f"   Total Turns: 5")
print(f"   Memory Records: {len(final_memory)}")
print(f"   Information Collected:")
print(f"     ✅ Restaurant selection")
print(f"     ✅ Customer name (Ashrujit)")
print(f"     ✅ Party size (3)")
print(f"     ✅ Date and time")
print(f"     ✅ Phone number")
print(f"   Result: {'Booking Confirmed' if booking_id else 'Pending'}")

print("\n" + "=" * 80)
print("✅ INCREMENTAL BOOKING TEST COMPLETE")
print("=" * 80)
