#!/usr/bin/env python3
"""Generate and display 7-day weather forecast for all cities"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from app import generate_7day_forecast, CURRENT_DATE, CITIES

def display_forecast():
    print(f"📅 Current Date: {CURRENT_DATE.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🌍 Cities: {len(CITIES)}")
    print(f"📆 Forecast Days: 7")
    print(f"⏰ Time Slots per Day: 4 (Morning, Afternoon, Evening, Night)\n")
    print("=" * 80)
    
    forecast = generate_7day_forecast()
    
    for city in CITIES:
        print(f"\n🏙️  {city.upper()}")
        print("-" * 80)
        
        for day_data in forecast[city]:
            print(f"\n  📅 {day_data['date']}")
            for slot_data in day_data['slots']:
                print(f"    {slot_data['time_slot']:10} | {slot_data['temperature']:2}°F | "
                      f"{slot_data['condition']:15} | Humidity: {slot_data['humidity']:2}% | "
                      f"Wind: {slot_data['wind_speed']:2} mph")

if __name__ == '__main__':
    display_forecast()
