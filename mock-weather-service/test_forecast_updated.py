#!/usr/bin/env python3
"""Test updated /forecast endpoint with city and date inputs"""

import requests
import sys

BASE_URL = "http://localhost:8080"

def test_forecast(city, date):
    print(f"\n🔍 Testing: {city} starting from {date}")
    print("-" * 70)
    
    try:
        response = requests.get(f"{BASE_URL}/forecast", params={"city": city, "date": date})
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Success!")
            print(f"   City:       {data['city']}")
            print(f"   Start Date: {data['start_date']}")
            print(f"   End Date:   {data['end_date']}")
            print(f"   Days:       {data['forecast_days']}")
            print(f"\n   Forecast Dates:")
            for day in data['forecast']:
                print(f"      • {day['date']}")
            print(f"\n   Day 1 ({data['forecast'][0]['date']}) Weather:")
            for slot in data['forecast'][0]['slots']:
                print(f"      {slot['time_slot']:10} - {slot['temperature']}°F, {slot['condition']}")
        else:
            print(f"❌ Error: {response.json()}")
            
    except requests.exceptions.ConnectionError:
        print("❌ Error: Service not running. Restart with: python3 app.py")
        sys.exit(1)

if __name__ == '__main__':
    print("=" * 70)
    print("🌤️  TESTING UPDATED /forecast ENDPOINT")
    print("=" * 70)
    
    test_forecast("Miami", "2026-02-10")
    test_forecast("Boston", "2026-02-15")
    test_forecast("San Francisco", "2026-03-01")
    test_forecast("New York", "2026-02-20")
    
    print("\n" + "=" * 70)
    print("✅ All tests completed!")
    print("=" * 70)
