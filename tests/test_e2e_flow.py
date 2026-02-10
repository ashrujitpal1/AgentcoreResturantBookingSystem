"""
Complete end-to-end booking flow test.
Tests: Search → Select → Book → Payment
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.workflows import RestaurantBookingWorkflow
from src.tools.mcp_client import get_mcp_tools
from dotenv import load_dotenv

load_dotenv()

def test_complete_flow():
    """Test complete booking flow"""
    print("\n" + "=" * 80)
    print("COMPLETE END-TO-END BOOKING FLOW TEST")
    print("=" * 80)
    
    mcp_tools = get_mcp_tools()
    workflow = RestaurantBookingWorkflow(mcp_tools)
    session_id = "e2e_test_session"
    user_id = "test_user_123"
    
    # Step 1: Search for restaurant
    print("\n[STEP 1] Search for Indian restaurant in New York")
    print("-" * 80)
    result1 = workflow.invoke(
        "Find Indian restaurant in New York",
        user_id,
        session_id
    )
    print(f"Intent: {result1.get('intent')}")
    print(f"Restaurants: {len(result1.get('restaurants', []))}")
    print(f"Response: {result1.get('final_response')[:200]}...")
    
    restaurants = result1.get('restaurants', [])
    if not restaurants:
        print("❌ No restaurants found")
        return False
    
    # Step 2: Select restaurant and provide booking details
    print("\n[STEP 2] Book the first restaurant")
    print("-" * 80)
    selected = restaurants[0]
    result2 = workflow.invoke(
        f"Book {selected['name']} for 3 people tomorrow at 7pm. My name is John Doe and phone is +1234567890",
        user_id,
        session_id,
        restaurants=restaurants,
        selected_restaurant=selected
    )
    print(f"Intent: {result2.get('intent')}")
    print(f"Agent: {result2.get('current_agent')}")
    print(f"Response: {result2.get('final_response')[:300]}...")
    
    # Check if booking succeeded or needs more info
    if result2.get('partial_booking_params'):
        print(f"Partial params collected: {result2.get('partial_booking_params')}")
    
    if result2.get('booking_id'):
        print(f"✅ Booking ID: {result2.get('booking_id')}")
        print(f"✅ Token Amount: ${result2.get('token_amount')}")
        return True
    
    # Step 3: If missing info, provide it
    if "need" in result2.get('final_response', '').lower():
        print("\n[STEP 3] Provide missing information")
        print("-" * 80)
        result3 = workflow.invoke(
            "My name is John Doe, phone +1234567890, 3 guests, tomorrow at 7pm",
            user_id,
            session_id,
            restaurants=restaurants,
            selected_restaurant=selected
        )
        print(f"Response: {result3.get('final_response')[:300]}...")
        
        if result3.get('booking_id'):
            print(f"✅ Booking ID: {result3.get('booking_id')}")
            return True
    
    return False


def test_date_normalization():
    """Test date normalization with getCurrentDateTime"""
    print("\n" + "=" * 80)
    print("DATE NORMALIZATION TEST")
    print("=" * 80)
    
    mcp_tools = get_mcp_tools()
    workflow = RestaurantBookingWorkflow(mcp_tools)
    
    # Get a restaurant first
    result1 = workflow.invoke(
        "Find Indian restaurant in New York",
        "date_test_user",
        "date_test_session"
    )
    
    restaurants = result1.get('restaurants', [])
    if not restaurants:
        print("❌ No restaurants found")
        return False
    
    selected = restaurants[0]
    
    # Test with "tomorrow"
    print("\n[TEST] Booking with 'tomorrow'")
    print("-" * 80)
    result2 = workflow.invoke(
        f"Book {selected['name']} for tomorrow at 7pm, 2 people, John Doe, +1234567890",
        "date_test_user",
        "date_test_session",
        restaurants=restaurants,
        selected_restaurant=selected
    )
    
    print(f"Response: {result2.get('final_response')[:200]}...")
    
    if "2026" in result2.get('final_response', ''):
        print("✅ Date normalized correctly (contains 2026)")
        return True
    else:
        print("⚠️  Date normalization unclear")
        return False


def test_session_limit():
    """Test one booking per session limit"""
    print("\n" + "=" * 80)
    print("SESSION BOOKING LIMIT TEST")
    print("=" * 80)
    
    mcp_tools = get_mcp_tools()
    workflow = RestaurantBookingWorkflow(mcp_tools)
    session_id = "limit_test_session"
    
    # First booking
    print("\n[ATTEMPT 1] First booking")
    result1 = workflow.invoke(
        "Find Indian restaurant in New York",
        "limit_user",
        session_id
    )
    
    restaurants = result1.get('restaurants', [])
    if restaurants:
        selected = restaurants[0]
        result2 = workflow.invoke(
            f"Book {selected['name']} for 2 people tomorrow at 7pm, John Doe, +1234567890",
            "limit_user",
            session_id,
            restaurants=restaurants,
            selected_restaurant=selected
        )
        
        if result2.get('booking_id'):
            print("✅ First booking succeeded")
            
            # Try second booking
            print("\n[ATTEMPT 2] Second booking (should be blocked)")
            result3 = workflow.invoke(
                f"Book {selected['name']} for 3 people next week",
                "limit_user",
                session_id,
                restaurants=restaurants,
                selected_restaurant=selected
            )
            
            if "log out" in result3.get('final_response', '').lower():
                print("✅ Second booking blocked correctly")
                return True
            else:
                print("❌ Second booking not blocked")
                return False
    
    return False


if __name__ == "__main__":
    print("\n" + "=" * 80)
    print("COMPREHENSIVE END-TO-END TESTS")
    print("=" * 80)
    
    test1 = test_complete_flow()
    test2 = test_date_normalization()
    test3 = test_session_limit()
    
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    print(f"Complete Booking Flow: {'✅ PASSED' if test1 else '❌ FAILED'}")
    print(f"Date Normalization: {'✅ PASSED' if test2 else '❌ FAILED'}")
    print(f"Session Booking Limit: {'✅ PASSED' if test3 else '❌ FAILED'}")
    print(f"\nOverall: {'✅ ALL TESTS PASSED' if all([test1, test2, test3]) else '❌ SOME TESTS FAILED'}")
