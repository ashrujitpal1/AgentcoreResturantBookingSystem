"""
Test Intent Classifier with conversation context
"""
import os
import sys
from dotenv import load_dotenv

# Load environment
load_dotenv()

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.agents.intent_classifier import IntentClassifierAgent

def test_intent_classification():
    """Test intent classifier with conversation history"""
    
    # Initialize agent
    classifier = IntentClassifierAgent()
    
    # Test 1: Simple booking confirmation with context
    print("\n" + "="*80)
    print("TEST 1: Booking confirmation with full conversation history")
    print("="*80)
    
    conversation_history = """USER: Find an Indian restaurant in New York
ASSISTANT: Found 1 restaurant:

**Spice Symphony** - Indian cuisine
   Rating: 4.8/5
   Location: New York
   ID: rest_006

Would you like to book a table at Spice Symphony?"""
    
    context = {
        "conversation_history": conversation_history
    }
    
    user_message = "Yes for two"
    correlation_id = "test_001"
    
    print(f"\nUser message: {user_message}")
    print(f"\nConversation history:\n{conversation_history}")
    print("\n" + "-"*80)
    
    result = classifier.process(user_message, correlation_id, context)
    
    print(f"\n✅ RESULT:")
    print(f"   Intent: {result.get('intent')}")
    print(f"   Confidence: {result.get('confidence')}")
    print(f"   Entities: {result.get('extracted_entities')}")
    print(f"   Model: {result.get('model')}")
    
    # Test 2: Simple "yes"
    print("\n" + "="*80)
    print("TEST 2: Simple 'yes' confirmation")
    print("="*80)
    
    user_message = "yes"
    correlation_id = "test_002"
    
    print(f"\nUser message: {user_message}")
    print(f"\nConversation history:\n{conversation_history}")
    print("\n" + "-"*80)
    
    result = classifier.process(user_message, correlation_id, context)
    
    print(f"\n✅ RESULT:")
    print(f"   Intent: {result.get('intent')}")
    print(f"   Confidence: {result.get('confidence')}")
    print(f"   Entities: {result.get('extracted_entities')}")
    print(f"   Model: {result.get('model')}")
    
    # Test 3: Without context (should be search)
    print("\n" + "="*80)
    print("TEST 3: 'yes' without context (should default to search)")
    print("="*80)
    
    user_message = "yes"
    correlation_id = "test_003"
    
    print(f"\nUser message: {user_message}")
    print(f"\nConversation history: None")
    print("\n" + "-"*80)
    
    result = classifier.process(user_message, correlation_id, context=None)
    
    print(f"\n✅ RESULT:")
    print(f"   Intent: {result.get('intent')}")
    print(f"   Confidence: {result.get('confidence')}")
    print(f"   Entities: {result.get('extracted_entities')}")
    print(f"   Model: {result.get('model')}")

if __name__ == "__main__":
    test_intent_classification()
