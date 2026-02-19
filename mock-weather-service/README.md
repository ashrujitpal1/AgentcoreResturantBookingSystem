# Mock Weather Service

Minimal Flask service that returns mock weather data for specific cities and dates.

## Supported Cities
- Austin, Boston, Chicago, Los Angeles, Miami, New York, San Francisco, Seattle

## API Endpoints

### Health Check
```bash
GET /health
```

### Get Weather (Single Time Slot)
```bash
GET /weather?city=Boston&date=2024-01-15&time_slot=Morning
```

**Response:**
```json
{
  "city": "Boston",
  "date": "2024-01-15",
  "time_slot": "Morning",
  "temperature": 72,
  "condition": "Sunny",
  "humidity": 65,
  "wind_speed": 12
}
```

### Get 7-Day Forecast (All Cities, All Time Slots)
```bash
GET /forecast
```

**Response:**
```json
{
  "current_date": "2026-02-10 06:00:00",
  "forecast_days": 7,
  "time_slots_per_day": 4,
  "forecast": {
    "Austin": [
      {
        "date": "2026-02-10",
        "slots": [
          {"city": "Austin", "date": "2026-02-10", "time_slot": "Morning", "temperature": 95, "condition": "Stormy", "humidity": 64, "wind_speed": 11},
          {"city": "Austin", "date": "2026-02-10", "time_slot": "Afternoon", "temperature": 56, "condition": "Rainy", "humidity": 46, "wind_speed": 7},
          {"city": "Austin", "date": "2026-02-10", "time_slot": "Evening", "temperature": 92, "condition": "Stormy", "humidity": 74, "wind_speed": 22},
          {"city": "Austin", "date": "2026-02-10", "time_slot": "Night", "temperature": 54, "condition": "Foggy", "humidity": 74, "wind_speed": 9}
        ]
      }
    ]
  }
}
```

**Time Slots:** Morning, Afternoon, Evening, Night

## Local Testing

```bash
# Install dependencies
pip install -r requirements.txt

# Run service
python app.py

# Test single weather query
curl "http://localhost:8080/weather?city=Boston&date=2024-01-15&time_slot=Morning"

# Test 7-day forecast (all cities, all time slots)
curl "http://localhost:8080/forecast"

# Generate formatted forecast display
python generate_forecast.py
```

## EC2 Deployment

### 1. Launch EC2 Instance
- AMI: Amazon Linux 2023
- Instance Type: t2.micro
- Security Group: Allow inbound TCP 8080

### 2. Setup on EC2
```bash
# SSH into EC2
ssh -i your-key.pem ec2-user@<EC2_PUBLIC_IP>

# Install Python
sudo yum update -y
sudo yum install python3 python3-pip -y

# Upload service files
# (Use scp or git clone)

# Install dependencies
cd mock-weather-service
pip3 install -r requirements.txt

# Run with gunicorn
gunicorn -w 2 -b 0.0.0.0:8080 app:app
```

### 3. Run as systemd service (optional)
```bash
sudo tee /etc/systemd/system/weather-mock.service > /dev/null <<EOF
[Unit]
Description=Mock Weather Service
After=network.target

[Service]
User=ec2-user
WorkingDirectory=/home/ec2-user/mock-weather-service
ExecStart=/usr/local/bin/gunicorn -w 2 -b 0.0.0.0:8080 app:app
Restart=always

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable weather-mock
sudo systemctl start weather-mock
```

## Usage Examples

```bash
# Get weather for specific time slot
curl "http://<EC2_IP>:8080/weather?city=New%20York&date=2026-02-10&time_slot=Morning"

# Get 7-day forecast for all cities
curl "http://<EC2_IP>:8080/forecast"

# Get weather for San Francisco evening
curl "http://<EC2_IP>:8080/weather?city=San%20Francisco&date=2026-02-15&time_slot=Evening"

# Health check
curl "http://<EC2_IP>:8080/health"
```
