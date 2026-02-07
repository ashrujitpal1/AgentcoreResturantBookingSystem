#!/usr/bin/env python3
"""Comprehensive test for LLM-based restaurant matching with realistic scenarios"""

import os
import sys
from dotenv import load_dotenv

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))
load_dotenv()

from src.core import AmazonNovaProvider

def test_comprehensive_matching():
    """Test various realistic booking conversation patterns"""
    
    restaurants = [
        {"restaurantId": "rest_001", "name": "Dragon Pearl", "city": "San Francisco", "cuisine": "Chinese"},
        {"restaurantId": "rest_002", "name": "Golden Dragon", "city": "San Francisco", "cuisine": "Chinese"},
        {"restaurantId": "rest_003", "name": "Sakura Omakase", "city": "San Francisco", "cuisine": "Japanese"},
        {"restaurantId": "rest_004", "name": "The French Laundry", "city": "San Francisco", "cuisine": "French"},
    ]
    
    test_cases = [
        # Explicit restaurant name mentions
        {"conv": "User: Chinese food in SF\nBot: Found Dragon Pearl, Golden Dragon", 
         "msg": "yes, at Golden Dragon", "expected": "rest_002", "desc": "Explicit name after 'at'"},
        
        {"conv": "User: Show Chinese places\nBot: Dragon Pearl and Golden Dragon available", 
         "msg": "Dragon Pearl please", "expected": "rest_001", "desc": "Name with 'please'"},
        
        {"conv": "User: Chinese restaurants\nBot: **Dragon Pearl** (4.5★) and **Golden Dragon** (4.2★)", 
         "msg": "I'll take Dragon Pearl", "expected": "rest_001", "desc": "Name with markdown formatting"},
        
        {"conv": "User: Where can I eat Chinese?\nBot: Try Dragon Pearl or Golden Dragon", 
         "msg": "Let's go with the Golden Dragon", "expected": "rest_002", "desc": "Name with 'the' article"},
        
        # Confirmation without explicit name
        {"conv": "User: Chinese food\nBot: Dragon Pearl is highly rated", 
         "msg": "yes", "expected": "rest_001", "desc": "Simple 'yes' - single restaurant context"},
        
        {"conv": "User: Book Dragon Pearl\nBot: Dragon Pearl available for booking", 
         "msg": "book it", "expected": "rest_001", "desc": "'book it' - restaurant in user's original message"},
        
        {"conv": "User: I want Dragon Pearl\nBot: Great choice! Dragon Pearl is available", 
         "msg": "yes for 2 people", "expected": "rest_001", "desc": "'yes for X people' - restaurant mentioned earlier"},
        
        {"conv": "User: Show me Dragon Pearl\nBot: Dragon Pearl: Chinese, 4.5★, $$$", 
         "msg": "perfect, book a table", "expected": "rest_001", "desc": "'book a table' - implicit confirmation"},
        
        # Partial name matches
        {"conv": "User: Chinese places\nBot: Dragon Pearl and Golden Dragon", 
         "msg": "the dragon pearl one", "expected": "rest_001", "desc": "Partial match with 'the...one'"},
        
        {"conv": "User: Chinese food\nBot: Found Dragon Pearl, Golden Dragon", 
         "msg": "golden one please", "expected": "rest_002", "desc": "Partial name 'golden'"},
        
        # Ambiguous cases (should default to first)
        {"conv": "User: Chinese restaurants\nBot: Dragon Pearl, Golden Dragon, Sakura Omakase", 
         "msg": "yes", "expected": "rest_001", "desc": "Ambiguous 'yes' - multiple options"},
        
        {"conv": "User: Show restaurants\nBot: Dragon Pearl, Golden Dragon, Sakura Omakase", 
         "msg": "book for 4", "expected": "rest_001", "desc": "No restaurant mentioned - default to first"},
        
        # Conversational confirmations
        {"conv": "User: Chinese in SF\nBot: Dragon Pearl is excellent", 
         "msg": "sounds good", "expected": "rest_001", "desc": "'sounds good' - implicit confirmation"},
        
        {"conv": "User: Where to eat?\nBot: I recommend Golden Dragon", 
         "msg": "ok let's do it", "expected": "rest_002", "desc": "'let's do it' - casual confirmation"},
        
        {"conv": "User: Chinese food\nBot: Dragon Pearl has great reviews", 
         "msg": "that works", "expected": "rest_001", "desc": "'that works' - agreement"},
        
        # With additional details
        {"conv": "User: Chinese restaurants\nBot: Dragon Pearl and Golden Dragon available", 
         "msg": "Golden Dragon for tomorrow at 7pm", "expected": "rest_002", "desc": "Name with booking details"},
        
        {"conv": "User: Show Chinese\nBot: Dragon Pearl (4.5★) and Golden Dragon (4.2★)", 
         "msg": "Dragon Pearl, table for 2", "expected": "rest_001", "desc": "Name with party size"},
        
        # Edge cases
        {"conv": "User: I love dragons\nBot: Found Dragon Pearl and Golden Dragon", 
         "msg": "the pearl one", "expected": "rest_001", "desc": "Partial identifier 'pearl'"},
        
        {"conv": "User: Chinese\nBot: Dragon Pearl, Golden Dragon, Sakura Omakase", 
         "msg": "not the Japanese one", "expected": "rest_001", "desc": "Negative selection (should pick first Chinese)"},
        
        {"conv": "User: Fancy dinner\nBot: The French Laundry is available", 
         "msg": "yes please", "expected": "rest_004", "desc": "Confirmation for single high-end restaurant"},
    ]
    
    bedrock = AmazonNovaProvider("amazon.nova-lite-v1:0", region=os.getenv('AWS_REGION', 'us-east-1'))
    
    passed = 0
    failed = 0
    
    for i, test in enumerate(test_cases, 1):
        restaurant_list = "\n".join([f"{r['name']} (ID: {r['restaurantId']}, {r['cuisine']})" for r in restaurants])
        
        match_prompt = f"""Which restaurant ID?

Conversation:
{test['conv']}

User: {test['msg']}

Restaurants:
{restaurant_list}

Return ONLY the restaurant ID (e.g., rest_001). No explanation.

If user names a restaurant → return its ID
If user says "yes"/"ok"/"book it" → return last mentioned restaurant ID
If unclear → return FIRST restaurant ID

ID:"""
        
        try:
            response = bedrock.invoke(
                messages=[{"role": "user", "content": [{"text": match_prompt}]}],
                temperature=0.0,
                max_tokens=50
            )
            
            matched_id = response["content"].strip()
            matched_restaurant = next((r for r in restaurants if r["restaurantId"] == matched_id), None)
            
            if matched_id == test['expected']:
                passed += 1
                status = "✅ PASS"
            else:
                failed += 1
                status = "❌ FAIL"
            
            print(f"{status} | Test {i:2d} | {test['desc'][:40]:40s} | Expected: {test['expected']} | Got: {matched_id}")
            
            if matched_id != test['expected']:
                print(f"         | Message: '{test['msg']}'")
                if matched_restaurant:
                    print(f"         | Matched: {matched_restaurant['name']}")
                
        except Exception as e:
            failed += 1
            print(f"❌ ERROR | Test {i:2d} | {test['desc'][:40]:40s} | {str(e)[:50]}")
    
    print(f"\n{'='*80}")
    print(f"Results: {passed} passed, {failed} failed out of {len(test_cases)} tests")
    print(f"Success Rate: {passed/len(test_cases)*100:.1f}%")
    print(f"{'='*80}")

if __name__ == "__main__":
    print("Comprehensive Restaurant Matching Test")
    print("="*80)
    test_comprehensive_matching()
