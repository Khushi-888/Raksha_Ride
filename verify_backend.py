import requests
import json
import time

BASE_URL = "http://localhost:8001"

def test_backend():
    print("🚀 Starting Backend Verification...")

    # 1. Register a Driver
    print("\n[1/3] Registering Driver...")
    driver_data = {
        "name": "Production Driver",
        "age": 35,
        "mobile": "9998887776",
        "email": "prod.driver@riksha.in",
        "vehicle_number": "MH-12-RR-9999",
        "rc_number": "RC99999",
        "pick_location": "Pune",
        "password": "production_pass"
    }
    res = requests.post(f"{BASE_URL}/api/register/driver", json=driver_data)
    if res.status_code == 201:
        print("✅ Driver Registered:", res.json())
    else:
        print("❌ Registration Failed:", res.text)
        return

    # 2. Login
    print("\n[2/3] Logging in...")
    login_data = {
        "credential": "prod.driver@riksha.in",
        "password": "production_pass",
        "role": "driver"
    }
    res = requests.post(f"{BASE_URL}/api/login", json=login_data)
    if res.status_code == 200:
        token = res.json()["access_token"]
        print("✅ Login Successful, Token acquired.")
    else:
        print("❌ Login Failed:", res.text)
        return

    # 3. Update Location & Check Nearby
    print("\n[3/3] Testing Nearby Drivers...")
    # Update location (Pune Center approx)
    headers = {"Authorization": f"Bearer {token}"}
    lat, lng = 18.5204, 73.8567
    requests.post(f"{BASE_URL}/api/location/update", params={"lat": lat, "lng": lng}, headers=headers)
    print(f"📍 Location updated to {lat}, {lng}")

    # Search nearby (radius 10km)
    res = requests.get(f"{BASE_URL}/api/nearby-drivers", params={"lat": 18.5205, "lng": 73.8568, "radius": 10000})
    if res.status_code == 200:
        nearby = res.json()
        print(f"✅ Found {len(nearby)} nearby drivers.")
        for d in nearby:
            print(f"   - {d['name']} ({d['distance_meters']}m away)")
    else:
        print("❌ Nearby Search Failed:", res.text)

if __name__ == "__main__":
    # Note: Ensure the server is running (uvicorn main:app) before running this.
    try:
        test_backend()
    except Exception as e:
        print(f"❗ Error: {e}")
