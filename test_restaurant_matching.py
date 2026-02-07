#!/usr/bin/env python3
"""Test LLM-based restaurant matching logic"""

import os
import sys
from dotenv import load_dotenv

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

load_dotenv()

from src.core import AmazonNovaProvider
import boto3

def test_restaurant_matching():
    """Test LLM matching restaurant names from conversation"""
    
    # Mock restaurant list (from Lambda)
    restaurants = [
        {"restaurantId": "rest_001", "name": "Dragon Pearl", "city": "San Francisco", "cuisine": "Chinese"},
        {"restaurantId": "rest_002", "name": "Golden Dragon", "city": "San Francisco", "cuisine": "Chinese"},
        {"restaurantId": "rest_003", "name": "Sakura Omakase", "city": "San Francisco", "cuisine": "Japanese"},
    ]
    
    # Test scenarios
    test_cases = [
        {
            "conversation": "User: I want Chinese food in San Francisco\nAssistant: I found Dragon Pearl, Golden Dragon, and Sakura Omakase",
            "user_message": "yes, at Golden Dragon",
            "expected": "rest_002"
        },
        {
            "conversation": "User: Chinese restaurants in SF\nAssistant: Found **Dragon Pearl** and **Golden Dragon**",
            "user_message": "Dragon Pearl - Book a table",
            "expected": "rest_001"
        },
        {
            "conversation": "User: Show me Chinese places\nAssistant: Here are some options: Dragon Pearl, Golden Dragon",
            "user_message": "yes for two people",
            "expected": None  # Ambiguous - should default to first
        },
        {
            "conversation": "User: I want to eat at Dragon Pearl\nAssistant: Dragon Pearl is available",
            "user_message": "book it",
            "expected": "rest_001"
        }
    ]
    
    # Get LLM provider
    bedrock = AmazonNovaProvider("amazon.nova-lite-v1:0", region=os.getenv('AWS_REGION', 'us-east-1'))
    
    for i, test in enumerate(test_cases, 1):
        print(f"\n{'='*60}")
        print(f"Test Case {i}")
        print(f"{'='*60}")
        print(f"Conversation: {test['conversation'][:80]}...")
        print(f"User Message: {test['user_message']}")
        print(f"Expected: {test['expected']}")
        
        # Build restaurant list
        restaurant_list = "\n".join([
            f"{r['name']} (ID: {r['restaurantId']}, {r['cuisine']})" 
            for r in restaurants
        ])
        
        # LLM matching prompt
        match_prompt = f"""Extract the restaurant ID from this conversation.

Conversation:
{test['conversation']}

User: {test['user_message']}

Restaurants:
{restaurant_list}

Rules:
- If user explicitly names a restaurant, return its ID
- If user says "yes"/"book it" without naming, check conversation for last mentioned restaurant
- If ambiguous, return the FIRST restaurant ID
- Return ONLY the ID (e.g., rest_001), nothing else"""
        
        try:
            response = bedrock.invoke(
                messages=[{"role": "user", "content": [{"text": match_prompt}]}],
                temperature=0.0,
                max_tokens=50
            )
            
            matched_id = response["content"].strip()
            print(f"LLM Response: {matched_id}")
            
            # Find matched restaurant
            matched_restaurant = None
            for r in restaurants:
                if r["restaurantId"] == matched_id:
                    matched_restaurant = r
                    break
            
            if matched_restaurant:
                print(f"✅ Matched: {matched_restaurant['name']} ({matched_restaurant['restaurantId']})")
            else:
                print(f"⚠️  No match or ambiguous: {matched_id}")
            
            # Verify expectation
            if test['expected']:
                if matched_id == test['expected']:
                    print(f"✅ PASS - Correct match")
                else:
                    print(f"❌ FAIL - Expected {test['expected']}, got {matched_id}")
            else:
                print(f"ℹ️  Ambiguous case - LLM returned: {matched_id}")
                
        except Exception as e:
            print(f"❌ ERROR: {e}")

if __name__ == "__main__":
    print("Testing LLM-based Restaurant Matching")
    print("="*60)
    test_restaurant_matching()
