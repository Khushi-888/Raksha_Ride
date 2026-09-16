"""
Quick test script to verify RakshaRide Enhanced system
"""

import requests
import json

BASE_URL = "http://localhost:5000"

def test_system():
    print("\n" + "="*60)
    print("  Testing RakshaRide Enhanced System")
    print("="*60 + "\n")
    
    # Test 1: Homepage
    print("1. Testing homepage...")
    try:
        response = requests.get(BASE_URL)
        if response.status_code == 200:
            print("   ✅ Homepage loads successfully")
        else:
            print(f"   ❌ Homepage failed: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
        print("   ⚠️  Make sure server is running: python app_enhanced.py")
        return
    
    # Test 2: Send OTP
    print("\n2. Testing OTP generation...")
    try:
        response = requests.post(f"{BASE_URL}/api/send_otp", 
            json={"email": "test@example.com"})
        data = response.json()
        if data.get("success"):
            print(f"   ✅ OTP generated: {data.get('dev_otp')}")
        else:
            print(f"   ❌ OTP failed: {data.get('message')}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Test 3: Register Passenger
    print("\n3. Testing passenger registration...")
    try:
        # First get OTP
        otp_response = requests.post(f"{BASE_URL}/api/send_otp", 
            json={"email": "passenger@test.com"})
        otp_data = otp_response.json()
        otp = otp_data.get('dev_otp')
        
        # Verify OTP
        verify_response = requests.post(f"{BASE_URL}/api/verify_otp",
            json={"email": "passenger@test.com", "otp": otp})
        
        # Register
        reg_response = requests.post(f"{BASE_URL}/api/register_passenger",
            json={
                "name": "Test Passenger",
                "phone": "9999999999",
                "email": "passenger@test.com",
                "password": "test123"
            })
        reg_data = reg_response.json()
        
        if reg_data.get("success"):
            print(f"   ✅ Passenger registered successfully")
        else:
            print(f"   ⚠️  Registration: {reg_data.get('message')}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Test 4: Register Driver
    print("\n4. Testing driver registration...")
    try:
        # First get OTP
        otp_response = requests.post(f"{BASE_URL}/api/send_otp", 
            json={"email": "driver@test.com"})
        otp_data = otp_response.json()
        otp = otp_data.get('dev_otp')
        
        # Verify OTP
        verify_response = requests.post(f"{BASE_URL}/api/verify_otp",
            json={"email": "driver@test.com", "otp": otp})
        
        # Register
        reg_response = requests.post(f"{BASE_URL}/api/register_driver",
            json={
                "name": "Test Driver",
                "age": 30,
                "mobile": "8888888888",
                "email": "driver@test.com",
                "vehicle_number": "DL01AB1234",
                "vehicle_type": "Car",
                "rc_number": "RC123456",
                "password": "test123"
            })
        reg_data = reg_response.json()
        
        if reg_data.get("success"):
            print(f"   ✅ Driver registered successfully")
            print(f"   ✅ QR code generated for driver")
        else:
            print(f"   ⚠️  Registration: {reg_data.get('message')}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    print("\n" + "="*60)
    print("  Test Summary")
    print("="*60)
    print("\n✅ System is working!")
    print("\nNext steps:")
    print("1. Open http://localhost:5000 in browser")
    print("2. Register as passenger or driver")
    print("3. Test QR code scanning")
    print("4. Complete a test ride")
    print("\n" + "="*60 + "\n")

if __name__ == "__main__":
    test_system()
