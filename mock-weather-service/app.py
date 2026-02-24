from flask import Flask, jsonify, request
import random
from datetime import datetime, timedelta

app = Flask(__name__)

CITIES = ["Austin", "Boston", "Chicago", "Los Angeles", "Miami", "New York", "San Francisco", "Seattle"]
CONDITIONS = ["Sunny", "Cloudy", "Rainy", "Partly Cloudy", "Stormy", "Foggy"]
TIME_SLOTS = ["Morning", "Afternoon", "Evening", "Night"]

CURRENT_DATE = datetime(2026, 2, 10, 6, 0, 0)

def generate_weather(city, date, time_slot):
    """Generate deterministic mock weather based on city, date, and time slot"""
    seed = hash(f"{city}{date}{time_slot}") % 10000
    random.seed(seed)
    
    return {
        "city": city,
        "date": date,
        "time_slot": time_slot,
        "temperature": random.randint(50, 95),
        "condition": random.choice(CONDITIONS),
        "humidity": random.randint(30, 90),
        "wind_speed": random.randint(5, 25)
    }

def generate_7day_forecast():
    """Generate 7-day forecast for all cities with 4 time slots per day"""
    forecast = {}
    
    for city in CITIES:
        forecast[city] = []
        for day in range(7):
            date = (CURRENT_DATE + timedelta(days=day)).strftime('%Y-%m-%d')
            day_forecast = {"date": date, "slots": []}
            
            for slot in TIME_SLOTS:
                weather = generate_weather(city, date, slot)
                day_forecast["slots"].append(weather)
            
            forecast[city].append(day_forecast)
    
    return forecast

@app.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "healthy"}), 200

@app.route('/weather', methods=['GET'])
def get_weather():
    city = request.args.get('city')
    date = request.args.get('date')
    time_slot = request.args.get('time_slot')
    
    if not city or not date:
        return jsonify({"error": "Missing city or date parameter"}), 400
    
    if city not in CITIES:
        return jsonify({"error": f"City not supported. Available: {', '.join(CITIES)}"}), 400
    
    try:
        datetime.strptime(date, '%Y-%m-%d')
    except ValueError:
        return jsonify({"error": "Invalid date format. Use YYYY-MM-DD"}), 400
    
    if time_slot and time_slot not in TIME_SLOTS:
        return jsonify({"error": f"Invalid time_slot. Available: {', '.join(TIME_SLOTS)}"}), 400
    
    weather = generate_weather(city, date, time_slot or "Morning")
    return jsonify(weather), 200

@app.route('/forecast', methods=['GET'])
def get_forecast():
    """Get 7-day forecast starting from specified date for a specific city"""
    city = request.args.get('city')
    start_date = request.args.get('date')
    
    if not city:
        return jsonify({
            "error": "Missing city parameter",
            "available_cities": CITIES
        }), 400
    
    if not start_date:
        return jsonify({"error": "Missing date parameter. Use format: YYYY-MM-DD"}), 400
    
    if city not in CITIES:
        return jsonify({
            "error": f"City '{city}' not supported",
            "available_cities": CITIES
        }), 400
    
    try:
        base_date = datetime.strptime(start_date, '%Y-%m-%d')
    except ValueError:
        return jsonify({"error": "Invalid date format. Use YYYY-MM-DD"}), 400
    
    forecast = []
    for day in range(7):
        date = (base_date + timedelta(days=day)).strftime('%Y-%m-%d')
        day_forecast = {"date": date, "slots": []}
        
        for slot in TIME_SLOTS:
            weather = generate_weather(city, date, slot)
            day_forecast["slots"].append(weather)
        
        forecast.append(day_forecast)
    
    return jsonify({
        "city": city,
        "start_date": start_date,
        "end_date": (base_date + timedelta(days=6)).strftime('%Y-%m-%d'),
        "forecast_days": 7,
        "time_slots_per_day": 4,
        "forecast": forecast
    }), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
