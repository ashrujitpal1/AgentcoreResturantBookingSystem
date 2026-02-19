import requests
import sys

BASE_URL = "http://localhost:8080"

def test_health():
    response = requests.get(f"{BASE_URL}/health")
    assert response.status_code == 200
    print("✓ Health check passed")

def test_weather():
    cities = ["Austin", "Boston", "Chicago", "Los Angeles", "Miami", "New York", "San Francisco", "Seattle"]
    
    for city in cities:
        response = requests.get(f"{BASE_URL}/weather", params={"city": city, "date": "2024-01-15"})
        assert response.status_code == 200
        data = response.json()
        assert data["city"] == city
        assert data["date"] == "2024-01-15"
        print(f"✓ {city}: {data['temperature']}°F, {data['condition']}")

def test_invalid_city():
    response = requests.get(f"{BASE_URL}/weather", params={"city": "Paris", "date": "2024-01-15"})
    assert response.status_code == 400
    print("✓ Invalid city rejected")

def test_invalid_date():
    response = requests.get(f"{BASE_URL}/weather", params={"city": "Boston", "date": "invalid"})
    assert response.status_code == 400
    print("✓ Invalid date rejected")

if __name__ == '__main__':
    try:
        test_health()
        test_weather()
        test_invalid_city()
        test_invalid_date()
        print("\n✅ All tests passed!")
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        sys.exit(1)
