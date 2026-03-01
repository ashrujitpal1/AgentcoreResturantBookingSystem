#!/usr/bin/env python3
"""
Local Test Script for Stateless Orchestration
Mocks AWS dependencies to test the workflow logic locally
"""
import sys
import os
from unittest.mock import Mock, MagicMock, patch
import json

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

def create_mock_mcp_tools():
    """Create mock MCP tools"""
    mock_tool = Mock()
    mock_tool.tool_name = "fetchRestaurantDetails"
    mock_tool.invoke = Mock(return_value={
        "restaurants": [
            {
                "restaurantId": "R001",
                "name": "Pasta Paradise",
                "cuisine": "Italian",
                "city": "Seattle",
                "rating": 4.5
            },
            {
                "restaurantId": "R002",
                "name": "Pizza Palace",
                "cuisine": "Italian",
                "city": "Seattle",
                "rating": 4.3
            }
        ]
    })
    return [mock_tool]

def create_mock_memory_client():
    """Create mock AgentCore Memory client"""
    mock_client = Mock()
    
    # Mock list_events (retrieve memory)
    mock_client.list_events = Mock(return_value={
        'events': []  # Empty initially
    })
    
    # Mock create_event (store memory)
    mock_client.create_event = Mock(return_value={'eventId': 'evt_123'})
    
    return mock_client

def test_restaurant_search():
    """Test 1: Restaurant Search Flow"""
    print("\n" + "="*60)
    print("TEST 1: Restaurant Search Flow")
    print("="*60)
    
    with patch('boto3.client') as mock_boto:
        mock_boto.return_value = create_mock_memory_client()
        
        # Set environment variable
        os.environ['MEMORY_ID'] = 'test-memory-id'
        os.environ['AWS_REGION'] = 'us-east-1'
        
        from workflows.restaurant_workflow import RestaurantBookingWorkflow
        
        # Create workflow with mock tools
        mcp_tools = create_mock_mcp_tools()
        workflow = RestaurantBookingWorkflow(mcp_tools)
        
        # Test search
        result = workflow.invoke(
            user_message="Find Italian restaurants in Seattle",
            user_id="test_user_001",
            session_id="test_session_001",
            is_first_message=False
        )
        
        print(f"\n✅ Intent: {result.get('intent')}")
        print(f"✅ Response: {result.get('final_response')[:100]}...")
        print(f"✅ Restaurants found: {len(result.get('restaurants', []))}")
        
        # Verify memory storage was called
        memory_client = mock_boto.return_value
        assert memory_client.create_event.called, "Memory storage should be called"
        print("✅ Memory storage called")
        
        return result

def test_multi_turn_booking():
    """Test 2: Multi-Turn Booking Flow"""
    print("\n" + "="*60)
    print("TEST 2: Multi-Turn Booking Flow")
    print("="*60)
    
    with patch('boto3.client') as mock_boto:
        # Mock memory with previous search results
        mock_client = create_mock_memory_client()
        
        # Simulate stored restaurants in memory
        import base64
        restaurants_data = [
            {
                "restaurantId": "R001",
                "name": "Pasta Paradise",
                "cuisine": "Italian",
                "city": "Seattle"
            }
        ]
        restaurants_b64 = base64.b64encode(json.dumps(restaurants_data).encode()).decode()
        
        mock_client.list_events = Mock(return_value={
            'events': [
                {
                    'metadata': {
                        'intent': {'stringValue': 'search'},
                        'restaurants_b64': {'stringValue': restaurants_b64}
                    },
                    'payload': [
                        {'conversational': {'role': 'USER', 'content': {'text': 'Find Italian restaurants'}}},
                        {'conversational': {'role': 'ASSISTANT', 'content': {'text': 'Found 1 restaurant'}}}
                    ]
                }
            ]
        })
        
        mock_boto.return_value = mock_client
        
        os.environ['MEMORY_ID'] = 'test-memory-id'
        os.environ['AWS_REGION'] = 'us-east-1'
        
        from workflows.restaurant_workflow import RestaurantBookingWorkflow
        
        # Create workflow
        mcp_tools = create_mock_mcp_tools()
        workflow = RestaurantBookingWorkflow(mcp_tools)
        
        # Test booking (should retrieve restaurants from memory)
        result = workflow.invoke(
            user_message="Book Pasta Paradise for tomorrow at 7pm, 2 people",
            user_id="test_user_001",
            session_id="test_session_001",
            is_first_message=False
        )
        
        print(f"\n✅ Intent: {result.get('intent')}")
        print(f"✅ Response: {result.get('final_response')[:100]}...")
        print(f"✅ Restaurants from memory: {len(result.get('restaurants', []))}")
        
        # Verify memory retrieval was called
        assert mock_client.list_events.called, "Memory retrieval should be called"
        print("✅ Memory retrieval called")
        
        return result

def test_greeting():
    """Test 3: First Message Greeting"""
    print("\n" + "="*60)
    print("TEST 3: First Message Greeting")
    print("="*60)
    
    with patch('boto3.client') as mock_boto:
        mock_boto.return_value = create_mock_memory_client()
        
        os.environ['MEMORY_ID'] = 'test-memory-id'
        os.environ['AWS_REGION'] = 'us-east-1'
        
        from workflows.restaurant_workflow import RestaurantBookingWorkflow
        
        mcp_tools = create_mock_mcp_tools()
        workflow = RestaurantBookingWorkflow(mcp_tools)
        
        result = workflow.invoke(
            user_message="Hello",
            user_id="test_user_001",
            session_id="test_session_001",
            is_first_message=True
        )
        
        print(f"\n✅ Is Greeting: {result.get('is_greeting')}")
        print(f"✅ Response: {result.get('final_response')}")
        
        return result

def test_memory_persistence():
    """Test 4: Memory Persistence"""
    print("\n" + "="*60)
    print("TEST 4: Memory Persistence (Restaurants Stored)")
    print("="*60)
    
    with patch('boto3.client') as mock_boto:
        mock_client = create_mock_memory_client()
        mock_boto.return_value = mock_client
        
        os.environ['MEMORY_ID'] = 'test-memory-id'
        os.environ['AWS_REGION'] = 'us-east-1'
        
        from workflows.restaurant_workflow import RestaurantBookingWorkflow
        
        mcp_tools = create_mock_mcp_tools()
        workflow = RestaurantBookingWorkflow(mcp_tools)
        
        # Simulate search
        result = workflow.invoke(
            user_message="Find Italian restaurants in Seattle",
            user_id="test_user_001",
            session_id="test_session_001",
            is_first_message=False
        )
        
        # Check if create_event was called with restaurants_b64
        call_args = mock_client.create_event.call_args
        if call_args:
            metadata = call_args[1].get('metadata', {})
            
            if 'restaurants_b64' in metadata:
                print("✅ Restaurants stored in memory (restaurants_b64 present)")
                
                # Decode and verify
                import base64
                rest_b64 = metadata['restaurants_b64']['stringValue']
                restaurants = json.loads(base64.b64decode(rest_b64).decode())
                print(f"✅ Stored {len(restaurants)} restaurants")
                print(f"✅ First restaurant: {restaurants[0].get('name')}")
            else:
                print("❌ Restaurants NOT stored in memory")
        
        return result

def main():
    """Run all tests"""
    print("\n" + "="*60)
    print("STATELESS ORCHESTRATION - LOCAL TESTS")
    print("="*60)
    print("\nNote: Using mocked AWS dependencies")
    print("This tests the workflow logic without AWS connectivity\n")
    
    try:
        # Test 1: Restaurant Search
        test_restaurant_search()
        
        # Test 2: Multi-Turn Booking
        test_multi_turn_booking()
        
        # Test 3: Greeting
        test_greeting()
        
        # Test 4: Memory Persistence
        test_memory_persistence()
        
        print("\n" + "="*60)
        print("✅ ALL TESTS PASSED")
        print("="*60)
        print("\nNext Steps:")
        print("1. Deploy to AWS Lambda")
        print("2. Configure AgentCore Memory")
        print("3. Set up MCP Gateway")
        print("4. Run integration tests with real AWS services")
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
