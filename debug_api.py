import requests
import json

def test_api():
    url = "http://localhost:8001/api/register/passenger"
    payload = {
        "name": "Success User 2",
        "mobile": "9800000001",
        "password": "successpassword456"
    }
    headers = {
        "Content-Type": "application/json"
    }
    
    try:
        print(f"Sending POST to {url}...")
        response = requests.post(url, json=payload, headers=headers)
        print(f"Status Code: {response.status_code}")
        print(f"Response Headers: {response.headers}")
        print(f"Response Body: {response.text}")
    except Exception as e:
        print(f"Error connecting to API: {e}")

if __name__ == "__main__":
    test_api()
