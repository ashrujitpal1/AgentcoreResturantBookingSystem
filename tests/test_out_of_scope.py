#!/usr/bin/env python3
"""Test out-of-scope request handling."""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.orchestrator import handler

class MockContext:
    aws_request_id = "test_scope_123"

def test_out_of_scope():
    """Test out-of-scope requests."""
    print("\n" + "="*80)
    print("TESTING OUT-OF-SCOPE REQUEST HANDLING")
    print("="*80)
    
    test_cases = [
        "What's the weather today?",
        "Tell me a joke",
        "What time is it?",
        "Who won the game yesterday?",
        "What's 2+2?"
    ]
    
    for query in test_cases:
        print(f"\n📝 Query: {query}")
        event = {
            "inputText": query,
            "userId": "user_001",
            "sessionId": f"session_scope_test_{hash(query)}"
        }
        
        result = handler(event, MockContext())
        print(f"✅ Response: {result.get('response')}")
        print("-" * 80)

if __name__ == "__main__":
    test_out_of_scope()
