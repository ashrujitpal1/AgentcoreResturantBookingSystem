"""
Test LangGraph workflow with Strands agents.
Demonstrates intent routing, handoff pattern, and SAGA compensation.
"""
import sys
sys.path.append('/Users/USER/Work/AI/AgentCore/AgentcoreResturantBookingSystem')

from src.workflows import RestaurantBookingWorkflow


def create_mock_tools():
    """Create mock MCP tools for testing"""
    
    def mock_fetch_restaurants(**kwargs):
        return {
            "restaurants": [
                {
                    "id": "rest_001",
                    "name": "Bella Italia",
                    "cuisine": "Italian",
                    "city": "Boston",
                    "rating": 4.5,
                    "priceRange": "$$"
                },
                {
                    "id": "rest_002",
                    "name": "Pasta Paradise",
                    "cuisine": "Italian",
                    "city": "Boston",
                    "rating": 4.3,
                    "priceRange": "$$$"
                }
            ]
        }
    
    def mock_search_user(**kwargs):
        return {"found": False, "user": None}
    
    def mock_register_user(**kwargs):
        return {"userId": "user_123"}
    
    def mock_token_calculation(**kwargs):
        return {"tokenAmount": 50.0}
    
    def mock_book_table(**kwargs):
        return {"bookingId": "booking_456"}
    
    def mock_payment(**kwargs):
        return {"paymentId": "payment_789"}
    
    return {
        "fetchRestaurantDetails": mock_fetch_restaurants,
        "searchUserDetails": mock_search_user,
        "registerUser": mock_register_user,
        "tokenAmountCalculation": mock_token_calculation,
        "bookATable": mock_book_table,
        "paymentAPI": mock_payment
    }


def test_search_workflow():
    """Test restaurant search workflow"""
    print("=" * 80)
    print("TEST 1: Restaurant Search Workflow")
    print("=" * 80)
    
    mcp_tools = create_mock_tools()
    workflow = RestaurantBookingWorkflow(mcp_tools)
    
    result = workflow.invoke(
        user_message="Find Italian restaurants in Boston",
        user_id="user_001",
        session_id="session_" + "x" * 25  # Min 33 chars
    )
    
    print(f"\n✅ Intent: {result['intent']}")
    print(f"✅ Confidence: {result['confidence']}")
    print(f"✅ Current Agent: {result['current_agent']}")
    print(f"✅ Restaurants Found: {len(result.get('restaurants', []))}")
    print(f"\n📝 Response:\n{result['final_response']}")


def test_booking_workflow():
    """Test booking workflow with SAGA pattern"""
    print("\n" + "=" * 80)
    print("TEST 2: Booking Workflow (SAGA Pattern)")
    print("=" * 80)
    
    mcp_tools = create_mock_tools()
    workflow = RestaurantBookingWorkflow(mcp_tools)
    
    result = workflow.invoke(
        user_message="Book a table for 4 at Bella Italia tomorrow at 7pm",
        user_id="user_001",
        session_id="session_" + "x" * 25
    )
    
    print(f"\n✅ Intent: {result['intent']}")
    print(f"✅ Current Agent: {result['current_agent']}")
    print(f"✅ Booking ID: {result.get('booking_id', 'N/A')}")
    print(f"✅ Token Amount: ${result.get('token_amount', 0)}")
    print(f"\n📝 Response:\n{result['final_response']}")
    
    if result.get('compensation_stack'):
        print(f"\n🔄 SAGA Steps:")
        for step in result['compensation_stack']:
            print(f"   {step}")


def test_handoff_pattern():
    """Test handoff from search to booking"""
    print("\n" + "=" * 80)
    print("TEST 3: Handoff Pattern (Search → Booking)")
    print("=" * 80)
    
    mcp_tools = create_mock_tools()
    workflow = RestaurantBookingWorkflow(mcp_tools)
    
    # First: Search
    result1 = workflow.invoke(
        user_message="Show me Italian restaurants",
        user_id="user_001",
        session_id="session_" + "x" * 25
    )
    
    print(f"\n📍 Step 1: Search")
    print(f"   Agent: {result1['current_agent']}")
    print(f"   Next Agent: {result1.get('next_agent', 'None')}")
    
    # Second: Book (with handoff trigger)
    result2 = workflow.invoke(
        user_message="Book the first one for 2 people tomorrow",
        user_id="user_001",
        session_id="session_" + "x" * 25
    )
    
    print(f"\n📍 Step 2: Booking")
    print(f"   Agent: {result2['current_agent']}")
    print(f"   Success: {result2.get('booking_id') is not None}")


if __name__ == "__main__":
    print("\n" + "=" * 80)
    print("LANGGRAPH WORKFLOW TESTS")
    print("=" * 80)
    
    try:
        test_search_workflow()
        test_booking_workflow()
        test_handoff_pattern()
        
        print("\n" + "=" * 80)
        print("✅ All workflow tests completed")
        print("=" * 80)
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
