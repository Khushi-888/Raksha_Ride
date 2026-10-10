"""
Comprehensive end-to-end user journey test for RakshaRide.
Tests Passenger auth & lifecycle, Driver auth & lifecycle, Admin flow, and Ride lifecycle.
"""
import app_enhanced
import time
import sqlite3
from auth_utils import generate_token

app = app_enhanced.app
client = app.test_client()

ts = int(time.time())
p_email = f"pax_{ts}@test.com"
p_mobile = f"95{ts % 100000000:08d}"

print("=== 1. PASSENGER FLOW ===")
# Register
r1 = client.post('/api/register_passenger', json={
    'name': 'Priya Sharma',
    'email': p_email,
    'mobile': p_mobile,
    'password': 'SecurePassword123!'
})
assert r1.status_code == 200 and r1.json.get('success'), f"Register failed: {r1.json}"
print("[PASS] Passenger registered")

# Login Step 1
r2 = client.post('/api/login_passenger', json={
    'credential': p_email,
    'password': 'SecurePassword123!'
})
assert r2.status_code == 200 and r2.json.get('requires_otp'), f"Login step 1 failed: {r2.json}"
print("[PASS] Passenger login step 1 requested OTP")

# Get OTP
conn = sqlite3.connect('database_enhanced.db')
c = conn.cursor()
c.execute("SELECT otp FROM otp_verification WHERE email = ?", (p_email,))
otp = c.fetchone()[0]
conn.close()

# Verify OTP
r3 = client.post('/api/verify_login_otp_passenger', json={'email': p_email, 'otp': otp})
assert r3.status_code == 200 and r3.json.get('token'), f"OTP verify failed: {r3.json}"
p_token = r3.json['token']
p_headers = {'Authorization': f'Bearer {p_token}'}
p_id = r3.json['user']['id']
print(f"[PASS] Passenger verified with ID {p_id}")

# Session check
r4 = client.get('/api/session_check', headers=p_headers)
assert r4.json.get('logged_in') and r4.json.get('user_type') == 'passenger', f"Session check failed: {r4.json}"
print("[PASS] Passenger session confirmed")

# /api/auth/me
r5 = client.get('/api/auth/me', headers=p_headers)
assert r5.json.get('user', {}).get('role') == 'passenger', f"Auth me failed: {r5.json}"
print("[PASS] Passenger /api/auth/me profile returned")

print("\n=== 2. DRIVER FLOW ===")
d_email = f"driver_{ts}@test.com"
d_mobile = f"85{ts % 100000000:08d}"

# Register Driver
r_drv = client.post('/api/register_driver_v2', data={
    'name': 'Rajesh Kumar',
    'email': d_email,
    'mobile': d_mobile,
    'age': 35,
    'gender': 'Male',
    'role': 'OWNER',
    'vehicle_number': f"RJ14MN{ts % 10000:04d}",
    'vehicle_type': 'Auto',
    'address': 'Jaipur Central',
    'rc_number': f"RC_{ts}",
    'license_number': f"DL_{ts}",
    'aadhaar_number': '112233445566'
})
assert r_drv.json.get('success'), f"Driver register failed: {r_drv.json}"
driver_id = r_drv.json['driver_id']
print(f"[PASS] Driver registered with ID {driver_id}")

# Admin final verification
with client.session_transaction() as sess:
    sess['is_admin'] = True
r_app = client.post('/api/admin/final_verification', json={'driver_id': driver_id})
assert r_app.json.get('success'), f"Admin approval failed: {r_app.json}"
print("[PASS] Driver approved and unique ID generated")

# Set driver password for direct login test
conn = sqlite3.connect('database_enhanced.db')
c = conn.cursor()
c.execute("SELECT unique_id FROM drivers WHERE id = ?", (driver_id,))
drv_uid = c.fetchone()[0]
from app_enhanced import hash_password
known_pw = "DriverSecret123!"
c.execute("UPDATE drivers SET password = ?, first_login = 0 WHERE id = ?", (hash_password(known_pw), driver_id))
conn.commit()
conn.close()

# Driver Login
r_dlog = client.post('/api/login_driver', json={'credential': drv_uid, 'password': known_pw})
assert r_dlog.json.get('success') and r_dlog.json.get('token'), f"Driver login failed: {r_dlog.json}"
d_token = r_dlog.json['token']
d_headers = {'Authorization': f'Bearer {d_token}'}
print(f"[PASS] Driver logged in successfully with {drv_uid}")

# Driver Profile
r_dprof = client.get('/api/driver_profile', headers=d_headers)
assert r_dprof.json.get('success'), f"Driver profile failed: {r_dprof.json}"
print("[PASS] Driver profile returned")

print("\n=== 3. RIDE LIFECYCLE ===")
# Passenger Starts Ride with Driver
r_start = client.post('/api/start_ride', headers=p_headers, json={
    'driver_id': driver_id,
    'pickup_location': 'MI Road, Jaipur',
    'dropoff_location': 'Railway Station, Jaipur'
})
assert r_start.json.get('success'), f"Start ride failed: {r_start.json}"
ride_id = r_start.json.get('ride_id')
print(f"[PASS] Passenger started ride with ID {ride_id}")

# Complete ride
r_comp = client.post('/api/complete_ride', headers=d_headers, json={'ride_id': ride_id, 'distance_km': 6.0})
assert r_comp.json.get('success'), f"Complete ride failed: {r_comp.json}"
print("[PASS] Driver completed ride")

# Submit rating
r_rate = client.post('/api/submit_rating', headers=p_headers, json={
    'ride_id': ride_id,
    'driver_id': driver_id,
    'rating': 5,
    'feedback': 'Excellent and safe ride!'
})
assert r_rate.json.get('success'), f"Rating failed: {r_rate.json}"
print("[PASS] Passenger submitted 5-star rating")

print("\n=== 4. ROLE ISOLATION ===")
r_blk1 = client.get('/api/driver_profile', headers=p_headers)
assert r_blk1.status_code == 401, f"Passenger was not blocked from driver profile!"
r_blk2 = client.post('/api/update_emergency_contact', headers=d_headers, json={'emergency_name': 'Hacker'})
assert r_blk2.status_code == 401, f"Driver was not blocked from passenger emergency contact!"
print("[PASS] Two-way role boundaries strictly enforced (401)")

print("\n=======================================================")
print("ALL FULL SYSTEM FLOWS VERIFIED 100% WORKING PROPERLY!")
print("=======================================================")
