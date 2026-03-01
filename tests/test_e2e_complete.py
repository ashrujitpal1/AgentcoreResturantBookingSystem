#!/usr/bin/env python3
"""End-to-end test for Restaurant Booking System"""
import sys
sys.path.insert(0, '/Users/USER/Work/AI/AgentCore/AgentcoreResturantBookingSystem')

from src.workflows.restaurant_workflow import RestaurantBookingWorkflow
import uuid

def test_scenario(scenario_name: str, messages: list):
    """Test a complete booking scenario"""
    print("\n" + "=" * 80)
    print(f"SCENARIO: {scenario_name}")
    print("=" * 80)
    
    # Initialize workflow
    workflow = RestaurantBookingWorkflow(mcp_tools={})
    
    user_id = f"test_user_{uuid.uuid4().hex[:8]}"
    session_id = f"session_{uuid.uuid4().hex[:8]}"
    
    for i, message in enumerate(messages, 1):
        print(f"\n--- Turn {i} ---")
        print(f"User: {message}")
        
        result = workflow.invoke(
            user_message=message,
            user_id=user_id,
            session_id=session_id,
            is_first_message=(i == 1)
        )
        
        print(f"Assistant: {result.get('final_response', 'No response')[:300]}...")
        
        if result.get('restaurants'):
            print(f"Restaurants: {len(result['restaurants'])} found")
        
        if result.get('booking_id'):
            print(f"✅ Booking ID: {result['booking_id']}")
            print(f"💰 Token Amount: ${result.get('token_amount', 0)}")
        
        if result.get('error'):
            print(f"❌ Error: {result['error']}")
    
    return result


print("\n🧪 RESTAURANT BOOKING SYSTEM - END-TO-END TESTS")
print("=" * 80)

try:
    # Test 1: Simple search
    print("\n\n📋 TEST 1: Restaurant Search")
    test_scenario(
        "Search for restaurants",
        [
            "Find Indian restaurants in New York"
        ]
    )
    
    # Test 2: Search + Booking (multi-turn)
    print("\n\n📋 TEST 2: Search and Book")
    test_scenario(
        "Search and complete booking",
        [
            "Find Japanese restaurants in New York",
            "Book Sakura Omakase for tomorrow at 7pm for 2 people. My name is John Doe and phone is +1234567890"
        ]
    )
    
    # Test 3: Incremental booking
    print("\n\n📋 TEST 3: Incremental Booking")
    test_scenario(
        "Provide booking details incrementally",
        [
            "I want to book a table at Spice Symphony",
            "Tomorrow at 7pm",
            "For 2 people",
            "My name is Jane Smith and phone is +1987654321"
        ]
    )
    
    # Test 4: Out of scope
    print("\n\n📋 TEST 4: Out of Scope Query")
    test_scenario(
        "Handle out of scope",
        [
            "What's the weather today?"
        ]
    )
    
    print("\n\n" + "=" * 80)
    print("✅ ALL END-TO-END TESTS COMPLETED")
    print("=" * 80)
    
except Exception as e:
    print(f"\n❌ TEST FAILED: {e}")
    import traceback
    traceback.print_exc()
