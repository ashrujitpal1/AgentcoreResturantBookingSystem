# Mock Weather Service - Quick Reference

## 📁 Location
`mock-weather-service/`

## 🌍 Supported Cities
Austin, Boston, Chicago, Los Angeles, Miami, New York, San Francisco, Seattle

## ⏰ Time Slots
Morning, Afternoon, Evening, Night

## 📅 Forecast Period
- **Start Date:** 2026-02-10 06:00:00
- **Duration:** 7 days
- **Total Entries:** 224 (8 cities × 7 days × 4 time slots)

## 🚀 Quick Start

### Local Testing
```bash
cd mock-weather-service
pip3 install -r requirements.txt
python3 app.py
```

### Test Request
```bash
# Single weather query
curl "http://localhost:8080/weather?city=Boston&date=2026-02-10&time_slot=Morning"

# 7-day forecast (all cities, all time slots)
curl "http://localhost:8080/forecast"

# Generate formatted display
python3 generate_forecast.py

# Export to JSON
python3 export_forecast.py
```

### Expected Response (Single Query)
```json
{
  "city": "Boston",
  "date": "2026-02-10",
  "time_slot": "Morning",
  "temperature": 62,
  "condition": "Foggy",
  "humidity": 61,
  "wind_speed": 15
}
```

### Expected Response (7-Day Forecast)
```json
{
  "current_date": "2026-02-10 06:00:00",
  "forecast_days": 7,
  "time_slots_per_day": 4,
  "forecast": {
    "Austin": [...],
    "Boston": [...],
    ...
  }
}
```

## ☁️ EC2 Deployment

### 1. Upload to EC2
```bash
scp -i your-key.pem -r mock-weather-service ec2-user@<EC2_IP>:~
```

### 2. Deploy
```bash
ssh -i your-key.pem ec2-user@<EC2_IP>
cd mock-weather-service
./deploy_ec2.sh
```

### 3. Security Group
Allow inbound: TCP port 8080 from your IP or 0.0.0.0/0

### 4. Test
```bash
curl "http://<EC2_PUBLIC_IP>:8080/health"
curl "http://<EC2_PUBLIC_IP>:8080/weather?city=Miami&date=2024-07-04"
```

## 📝 API Endpoints

| Endpoint | Method | Parameters | Description |
|----------|--------|------------|-------------|
| `/health` | GET | - | Health check |
| `/weather` | GET | `city`, `date`, `time_slot` | Get weather for specific slot |
| `/forecast` | GET | - | Get 7-day forecast (all cities, all slots) |

## 🔧 Service Management (EC2)
```bash
sudo systemctl status weather-mock   # Check status
sudo systemctl restart weather-mock  # Restart
sudo systemctl stop weather-mock     # Stop
sudo journalctl -u weather-mock -f   # View logs
```
