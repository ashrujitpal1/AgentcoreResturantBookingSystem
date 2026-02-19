# Updated /forecast Endpoint

## 🔄 Changes Made

The `/forecast` endpoint now accepts **city** and **date** as input parameters and returns a 7-day forecast starting from the specified date.

## 📋 API Specification

### Endpoint
```
GET /forecast?city={city_name}&date={start_date}
```

### Parameters
- **city** (required): City name (e.g., "Miami", "New York", "San Francisco")
- **date** (required): Start date in YYYY-MM-DD format (e.g., "2026-02-10")

### Response
```json
{
  "city": "Miami",
  "start_date": "2026-02-10",
  "end_date": "2026-02-16",
  "forecast_days": 7,
  "time_slots_per_day": 4,
  "forecast": [
    {
      "date": "2026-02-10",
      "slots": [
        {
          "city": "Miami",
          "date": "2026-02-10",
          "time_slot": "Morning",
          "temperature": 65,
          "condition": "Partly Cloudy",
          "humidity": 35,
          "wind_speed": 20
        },
        ... (3 more time slots for this day)
      ]
    },
    ... (6 more days)
  ]
}
```

## 🧪 Test Examples

### Example 1: Miami from Feb 10
```bash
curl "http://localhost:8080/forecast?city=Miami&date=2026-02-10"
```

### Example 2: Boston from Feb 15
```bash
curl "http://localhost:8080/forecast?city=Boston&date=2026-02-15"
```

### Example 3: San Francisco from March 1
```bash
curl "http://localhost:8080/forecast?city=San%20Francisco&date=2026-03-01"
```

### Example 4: New York from Feb 20
```bash
curl "http://localhost:8080/forecast?city=New%20York&date=2026-02-20"
```

## ✅ Features

- ✓ Returns exactly 7 days starting from input date
- ✓ Includes the input date as Day 1
- ✓ 4 time slots per day (Morning, Afternoon, Evening, Night)
- ✓ Validates city name
- ✓ Validates date format
- ✓ Returns start_date and end_date in response

## 🔧 Testing

### Restart the service first:
```bash
# Stop current service (Ctrl+C)
# Start updated service
python3 app.py
```

### Run tests:
```bash
python3 test_forecast_updated.py
```

## 📊 Summary

| Input | Output |
|-------|--------|
| City: Miami, Date: 2026-02-10 | 7 days: Feb 10-16 |
| City: Boston, Date: 2026-02-15 | 7 days: Feb 15-21 |
| City: San Francisco, Date: 2026-03-01 | 7 days: Mar 1-7 |

**Note:** Please restart the Flask service to apply the changes!
