#!/usr/bin/env python3
"""Test mock weather service with city, date, and time slot"""

import requests
import sys

BASE_URL = "http://localhost:8080"

def test_weather(city, date, time_slot):
    """Test weather endpoint with given parameters"""
    print(f"\n🔍 Testing: {city} on {date} at {time_slot}")
    print("-" * 60)
    
    try:
        response = requests.get(
            f"{BASE_URL}/weather",
            params={"city": city, "date": date, "time_slot": time_slot}
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Success!")
            print(f"   City:        {data['city']}")
            print(f"   Date:        {data['date']}")
            print(f"   Time Slot:   {data['time_slot']}")
            print(f"   Temperature: {data['temperature']}°F")
            print(f"   Condition:   {data['condition']}")
            print(f"   Humidity:    {data['humidity']}%")
            print(f"   Wind Speed:  {data['wind_speed']} mph")
        else:
            print(f"❌ Error: {response.json()}")
            
    except requests.exceptions.ConnectionError:
        print("❌ Error: Service not running. Start with: python3 app.py")
        sys.exit(1)

if __name__ == '__main__':
    # Test cases
    print("=" * 60)
    print("🌤️  MOCK WEATHER SERVICE - TEST")
    print("=" * 60)
    
    test_weather("Miami", "2026-02-10", "Morning")
    test_weather("New York", "2026-02-12", "Evening")
    test_weather("San Francisco", "2026-02-15", "Afternoon")
    test_weather("Boston", "2026-02-14", "Night")
    
    print("\n" + "=" * 60)
    print("✅ All tests completed!")
    print("=" * 60)
