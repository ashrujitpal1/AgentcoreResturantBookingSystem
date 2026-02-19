#!/usr/bin/env python3
"""Direct test of weather generation with city, date, and time slot"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from app import generate_weather, CITIES, TIME_SLOTS

def test_weather_direct(city, date, time_slot):
    """Test weather generation directly"""
    print(f"\n🔍 Testing: {city} on {date} at {time_slot}")
    print("-" * 60)
    
    if city not in CITIES:
        print(f"❌ Error: City '{city}' not supported")
        print(f"   Available: {', '.join(CITIES)}")
        return
    
    if time_slot not in TIME_SLOTS:
        print(f"❌ Error: Time slot '{time_slot}' not valid")
        print(f"   Available: {', '.join(TIME_SLOTS)}")
        return
    
    weather = generate_weather(city, date, time_slot)
    
    print(f"✅ Success!")
    print(f"   City:        {weather['city']}")
    print(f"   Date:        {weather['date']}")
    print(f"   Time Slot:   {weather['time_slot']}")
    print(f"   Temperature: {weather['temperature']}°F")
    print(f"   Condition:   {weather['condition']}")
    print(f"   Humidity:    {weather['humidity']}%")
    print(f"   Wind Speed:  {weather['wind_speed']} mph")

if __name__ == '__main__':
    print("=" * 60)
    print("🌤️  MOCK WEATHER SERVICE - DIRECT TEST")
    print("=" * 60)
    
    # Test with different cities, dates, and time slots
    test_weather_direct("Miami", "2026-02-10", "Morning")
    test_weather_direct("New York", "2026-02-12", "Evening")
    test_weather_direct("San Francisco", "2026-02-15", "Afternoon")
    test_weather_direct("Boston", "2026-02-14", "Night")
    test_weather_direct("Chicago", "2026-02-11", "Morning")
    test_weather_direct("Los Angeles", "2026-02-13", "Afternoon")
    
    print("\n" + "=" * 60)
    print("✅ All tests completed!")
    print("=" * 60)
