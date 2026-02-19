#!/usr/bin/env python3
"""Export 7-day forecast to JSON file"""

import sys
import os
import json
sys.path.insert(0, os.path.dirname(__file__))

from app import generate_7day_forecast, CURRENT_DATE

def export_forecast():
    forecast_data = {
        "current_date": CURRENT_DATE.strftime('%Y-%m-%d %H:%M:%S'),
        "forecast_days": 7,
        "time_slots_per_day": 4,
        "time_slots": ["Morning", "Afternoon", "Evening", "Night"],
        "forecast": generate_7day_forecast()
    }
    
    output_file = "forecast_7days.json"
    with open(output_file, 'w') as f:
        json.dump(forecast_data, f, indent=2)
    
    print(f"✅ Forecast exported to {output_file}")
    
    # Print summary
    total_entries = 0
    for city, days in forecast_data["forecast"].items():
        total_entries += len(days) * 4
    
    print(f"📊 Summary:")
    print(f"   Cities: 8")
    print(f"   Days: 7")
    print(f"   Time Slots per Day: 4")
    print(f"   Total Weather Entries: {total_entries}")

if __name__ == '__main__':
    export_forecast()
