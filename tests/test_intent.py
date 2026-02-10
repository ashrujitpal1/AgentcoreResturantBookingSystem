"""Test intent classification directly"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.agents import IntentClassifierAgent
from dotenv import load_dotenv
load_dotenv()

agent = IntentClassifierAgent()

tests = [
    "Find Indian restaurant in New York",
    "Book a table for 4 people",
    "Book Sakura Omakase for 3 people tomorrow at 7pm",
    "Reserve a table at Spice Symphony",
    "yes",
    "sure, for two people"
]

for query in tests:
    result = agent.process(query, "test_123")
    print(f"\nQuery: {query}")
    print(f"Intent: {result['intent']} (confidence: {result.get('confidence', 0)})")
