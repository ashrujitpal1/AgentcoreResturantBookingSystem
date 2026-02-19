#!/usr/bin/env python3
"""Display summary statistics for 7-day forecast"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from app import generate_7day_forecast, CURRENT_DATE, CITIES
from collections import Counter

def analyze_forecast():
    forecast = generate_7day_forecast()
    
    print("=" * 80)
    print("📊 7-DAY WEATHER FORECAST SUMMARY")
    print("=" * 80)
    print(f"\n📅 Period: {CURRENT_DATE.strftime('%Y-%m-%d')} to 2026-02-16")
    print(f"🏙️  Cities: {len(CITIES)}")
    print(f"📆 Days: 7")
    print(f"⏰ Time Slots: 4 per day (Morning, Afternoon, Evening, Night)")
    print(f"📈 Total Entries: {len(CITIES) * 7 * 4}")
    
    # Analyze conditions
    all_conditions = []
    all_temps = []
    
    for city, days in forecast.items():
        for day in days:
            for slot in day['slots']:
                all_conditions.append(slot['condition'])
                all_temps.append(slot['temperature'])
    
    condition_counts = Counter(all_conditions)
    
    print(f"\n🌤️  Weather Conditions Distribution:")
    for condition, count in condition_counts.most_common():
        percentage = (count / len(all_conditions)) * 100
        print(f"   {condition:15} : {count:3} ({percentage:5.1f}%)")
    
    print(f"\n🌡️  Temperature Statistics:")
    print(f"   Min: {min(all_temps)}°F")
    print(f"   Max: {max(all_temps)}°F")
    print(f"   Avg: {sum(all_temps) / len(all_temps):.1f}°F")
    
    print(f"\n🏙️  Cities Covered:")
    for i, city in enumerate(CITIES, 1):
        print(f"   {i}. {city}")
    
    print("\n" + "=" * 80)

if __name__ == '__main__':
    analyze_forecast()
