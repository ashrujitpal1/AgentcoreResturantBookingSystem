#!/usr/bin/env python3
"""Test the getCurrentDateTime tool."""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.orchestrator import handler

class MockContext:
    aws_request_id = "test_datetime_123"

def test_current_datetime():
    """Test getCurrentDateTime tool."""
    print("\n" + "="*80)
    print("TESTING getCurrentDateTime TOOL")
    print("="*80)
    
    event = {
        "inputText": "What's the current date and time?",
        "userId": "user_001",
        "sessionId": "session_datetime_test"
    }
    
    result = handler(event, MockContext())
    
    print(f"\n✅ Response: {result.get('response')}")
    print(f"✅ Metadata: {result.get('metadata')}")

if __name__ == "__main__":
    test_current_datetime()
