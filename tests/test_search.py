"""
Test restaurant search functionality locally.
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.workflows import RestaurantBookingWorkflow
from src.tools.mcp_client import get_mcp_tools
from dotenv import load_dotenv

load_dotenv()

def test_search(query: str, test_name: str):
    """Test a search query"""
    print("\n" + "=" * 80)
    print(f"TEST: {test_name}")
    print("=" * 80)
    print(f"Query: {query}\n")
    
    try:
        # Get MCP tools
        mcp_tools = get_mcp_tools()
        
        # Create workflow
        workflow = RestaurantBookingWorkflow(mcp_tools)
        
        # Invoke workflow
        result = workflow.invoke(
            user_message=query,
            user_id="test_user",
            session_id="test_session_123"
        )
        
        # Print results
        print(f"Intent: {result.get('intent')}")
        print(f"Agent: {result.get('current_agent')}")
        print(f"\nResponse:\n{result.get('final_response')}\n")
        
        # Print restaurants found
        if result.get('restaurants'):
            print(f"Restaurants Found: {len(result['restaurants'])}")
            for i, rest in enumerate(result['restaurants'][:3], 1):
                print(f"  {i}. {rest.get('name')} - {rest.get('cuisine')} ({rest.get('city')})")
        
        return True
        
    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("\n" + "=" * 80)
    print("RESTAURANT SEARCH TESTS")
    print("=" * 80)
    
    # Test 1: Indian restaurant in New York
    test1 = test_search(
        "Find me an Indian restaurant in New York",
        "Indian Restaurant in New York"
    )
    
    # Test 2: Korean restaurant in Miami
    test2 = test_search(
        "Find korean restaurant in Miami",
        "Korean Restaurant in Miami"
    )
    
    # Summary
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    print(f"Test 1 (Indian/New York): {'✅ PASSED' if test1 else '❌ FAILED'}")
    print(f"Test 2 (Korean/Miami): {'✅ PASSED' if test2 else '❌ FAILED'}")
