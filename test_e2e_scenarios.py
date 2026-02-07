#!/usr/bin/env python3
"""
End-to-end test scenarios for restaurant booking workflow.
Tests complete flows: search → incremental info → booking confirmation.
"""

import os
import sys
import uuid
from dotenv import load_dotenv

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))
load_dotenv()

from src.workflows import RestaurantBookingWorkflow
from src.tools.mcp_client import get_mcp_tools

def run_scenario(scenario_name: str, conversation_turns: list):
    """Run a complete booking scenario with multiple conversation turns"""
    print(f"\n{'='*80}")
    print(f"SCENARIO: {scenario_name}")
    print(f"{'='*80}\n")
    
    workflow = RestaurantBookingWorkflow(get_mcp_tools())
    user_id = f"test_user_{uuid.uuid4().hex[:8]}"
    session_id = f"req_{uuid.uuid4()}"
    
    restaurants = []
    selected_restaurant = None
    
    for i, turn in enumerate(conversation_turns, 1):
        user_message = turn['user']
        expected_keywords = turn.get('expect', [])
        
        print(f"Turn {i}:")
        print(f"  User: {user_message}")
        
        try:
            result = workflow.invoke(
                user_message=user_message,
                user_id=user_id,
                session_id=session_id,
                restaurants=restaurants,
                selected_restaurant=selected_restaurant
            )
            
            response = result.get('final_response', '')
            print(f"  Bot: {response[:150]}{'...' if len(response) > 150 else ''}")
            
            # Update state ONLY from workflow results
            if result.get('restaurants'):
                restaurants = result['restaurants']
                print(f"  → Restaurants in state: {len(restaurants)}")
                if len(restaurants) == 1:
                    selected_restaurant = restaurants[0]
                    print(f"  → Auto-selected: {selected_restaurant.get('name')}")
            
            if result.get('booking_id'):
                print(f"  ✅ Booking confirmed: {result['booking_id']}")
            
            # Validate expectations
            if expected_keywords:
                for keyword in expected_keywords:
                    if keyword.lower() in response.lower():
                        print(f"  ✓ Contains '{keyword}'")
                    else:
                        print(f"  ✗ Missing '{keyword}'")
            
            print()
            
        except Exception as e:
            print(f"  ❌ ERROR: {e}\n")
            break
    
    print(f"{'='*80}\n")

# Test Scenarios
scenarios = [
    {
        "name": "Scenario 1: Direct booking with all info upfront",
        "turns": [
            {
                "user": "Italian restaurant in New York",
                "expect": ["La Bella Vita", "Italian"]
            },
            {
                "user": "Yes, book it for John Smith, phone 5551234567, tomorrow at 7 PM, 2 guests",
                "expect": ["booking", "confirmed"]
            }
        ]
    },
    
    {
        "name": "Scenario 2: Incremental information - name first",
        "turns": [
            {
                "user": "Find Chinese restaurants in San Francisco",
                "expect": ["Chinese", "San Francisco"]
            },
            {
                "user": "yes",
                "expect": ["name", "phone", "date", "time", "guests"]
            },
            {
                "user": "My name is Alice Johnson",
                "expect": ["phone", "date", "time", "guests"]
            },
            {
                "user": "Phone is 5559876543",
                "expect": ["date", "time", "guests"]
            },
            {
                "user": "Tomorrow at 8 PM for 4 people",
                "expect": ["booking", "confirmed"]
            }
        ]
    },
    
    {
        "name": "Scenario 3: Incremental information - date/time first",
        "turns": [
            {
                "user": "Japanese food in New York",
                "expect": ["Japanese", "New York"]
            },
            {
                "user": "book it",
                "expect": ["name", "phone", "date", "time", "guests"]
            },
            {
                "user": "Tomorrow at 6:30 PM",
                "expect": ["name", "phone", "guests"]
            },
            {
                "user": "Bob Wilson, 5552223333",
                "expect": ["guests"]
            },
            {
                "user": "2 guests",
                "expect": ["booking", "confirmed"]
            }
        ]
    },
    
    {
        "name": "Scenario 4: Multiple restaurants - explicit selection",
        "turns": [
            {
                "user": "Chinese restaurants in San Francisco",
                "expect": ["Chinese", "San Francisco"]
            },
            {
                "user": "I want Golden Dragon",
                "expect": ["name", "phone", "date", "time", "guests"]
            },
            {
                "user": "Carol Davis, 5554445555, today at 7 PM, 3 people",
                "expect": ["booking", "confirmed"]
            }
        ]
    },
    
    {
        "name": "Scenario 5: Conversational booking confirmation",
        "turns": [
            {
                "user": "Show me French restaurants in New York",
                "expect": ["French", "New York"]
            },
            {
                "user": "sounds good",
                "expect": ["name", "phone", "date", "time", "guests"]
            },
            {
                "user": "David Lee",
                "expect": ["phone", "date", "time", "guests"]
            },
            {
                "user": "5556667777",
                "expect": ["date", "time", "guests"]
            },
            {
                "user": "tomorrow 8pm",
                "expect": ["guests"]
            },
            {
                "user": "for 2",
                "expect": ["booking", "confirmed"]
            }
        ]
    },
    
    {
        "name": "Scenario 6: All info in one message after search",
        "turns": [
            {
                "user": "Italian in New York",
                "expect": ["Italian", "New York"]
            },
            {
                "user": "Book for Emma Stone, 5558889999, tomorrow 7:30 PM, 4 guests",
                "expect": ["booking", "confirmed"]
            }
        ]
    },
    
    {
        "name": "Scenario 7: Partial info then complete",
        "turns": [
            {
                "user": "Korean BBQ in Los Angeles",
                "expect": ["Korean", "Los Angeles"]
            },
            {
                "user": "yes for tomorrow",
                "expect": ["name", "phone", "time", "guests"]
            },
            {
                "user": "Frank Miller, 5551112222, 7 PM, 6 people",
                "expect": ["booking", "confirmed"]
            }
        ]
    },
    
    {
        "name": "Scenario 8: Restaurant name in booking request",
        "turns": [
            {
                "user": "Chinese food in San Francisco",
                "expect": ["Chinese", "San Francisco"]
            },
            {
                "user": "Dragon Pearl - book for Grace Chen, 5553334444, tomorrow 6 PM, 2 guests",
                "expect": ["booking", "confirmed"]
            }
        ]
    }
]

if __name__ == "__main__":
    print("\n" + "="*80)
    print("END-TO-END RESTAURANT BOOKING TEST SCENARIOS")
    print("="*80)
    
    # Run only first 3 scenarios for quick validation
    for scenario in scenarios[:3]:
        run_scenario(scenario['name'], scenario['turns'])
    
    print("\n" + "="*80)
    print(f"COMPLETED {min(3, len(scenarios))} SCENARIOS")
    print("="*80 + "\n")
