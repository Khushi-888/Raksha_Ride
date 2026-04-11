# 🧪 Step-by-Step Testing Guide

## Test All 4 Advanced Features

---

## 🚀 Prerequisites

### Step 1: Start the Server
```bash
python app_enhanced.py
```

**Expected Output:**
```
======================================================================
  🚗 RakshaRide Enhanced - Complete Ride Sharing Platform
======================================================================

  📡 Server: http://localhost:5000
  📧 Email: riksharide2026@gmail.com

  ✨ Features:
     • QR Code Scanning
     • Ride Management
     • Payment Integration
     • History Tracking
     • Profile Management

======================================================================

 * Running on http://127.0.0.1:5000
```

### Step 2: Open Browser
```
http://localhost:5000
```

---

## 🧪 TEST 1: Real-Time ID Verification

### What We're Testing
> Driver credentials (DL, RC) are verified instantly and stored in database

### Steps

**1. Register as Driver**
```
1. Open: http://localhost:5000
2. Click: "Join as Driver" button
3. Fill form:
   - Name: Test Driver
   - Age: 30
   - Mobile: 9876543210
   - Email: testdriver@gmail.com
   - Vehicle Number: DL01AB1234
   - Vehicle Type: Car
   - RC Number: RC123456789
   - Password: test123
4. Click: "Send OTP"
```

**2. Verify Email OTP**
```
5. Check email inbox: testdriver@gmail.com
6. Find email from: RakshaRide
7. Copy OTP: 123456
8. Enter OTP in website
9. Click: "Create Account"
```

**3. Verify in Database**
```bash
python check_db.py
```

**Expected Result:**
```
--- DRIVERS DATA ---
(2, 'Test Driver', 30, '9876543210', 'testdriver@gmail.com', 
'DL01AB1234', 'Car', 'RC123456789', '[hashed_password]', 
'[qr_code_data]', ...)

✅ DL Number stored: DL01AB1234
✅ RC Number stored: RC123456789
✅ Email verified via OTP
✅ QR code generated
```

**✅ TEST PASSED:** ID verification working!

---

## 🧪 TEST 2: GPS Cloud Sync

### What We're Testing
> Location tracking and route storage in database

### Steps

**1. Login as Driver**
```
1. Open: http://localhost:5000
2. Click: "Driver Login"
3. Enter: testdriver@gmail.com
4. Enter: test123
5. Click: "Login"
6. Enter OTP from email
7. Dashboard opens
```

**2. Update Location**
```
8. In driver dashboard
9. Browser asks for location permission
10. Click: "Allow"
11. Location automatically updated
```

**3. Start a Ride (as Passenger)**
```
12. Open new tab: http://localhost:5000
13. Login as passenger
14. Scan driver QR code
15. Click: "Start Ride"
16. Enter pickup: "Connaught Place, Delhi"
17. Enter dropoff: "India Gate, Delhi"
```

**4. Complete Ride**
```
18. Wait 2 minutes (simulating ride)
19. Click: "Complete Ride"
20. Enter distance: 5 km
```

**5. Verify in Database**
```bash
python check_db.py
```

**Expected Result:**
```
--- RIDES DATA ---
(1, 1, 2, 'Passenger Name', '+919876543210', 'Test Driver', 
'9876543210', 'DL01AB1234', 'Connaught Place, Delhi', 
'India Gate, Delhi', '2026-03-07 14:00:00', '2026-03-07 14:20:00',
20, 5.0, 165.0, 'completed', 'pending', 'qr_code', 
'2026-03-07 14:00:00', 28.6139, 77.2090, 28.6129, 77.2295, 
'[route_coordinates]')

✅ Start location: 28.6139, 77.2090
✅ End location: 28.6129, 77.2295
✅ Route coordinates: [saved]
✅ Pickup location: Connaught Place, Delhi
✅ Dropoff location: India Gate, Delhi
```

**✅ TEST PASSED:** GPS cloud sync working!

---

## 🧪 TEST 3: Dynamic Fare Engine

### What We're Testing
> Automatic fare calculation based on distance and time

### Steps

**1. Complete a Ride**
```
(Use steps from TEST 2 above)
- Distance: 5 km
- Duration: 20 minutes
```

**2. Check Fare Calculation**
```
Expected Calculation:
Base Fare: ₹50
Distance: 5 km × ₹15/km = ₹75
Time: 20 min × ₹2/min = ₹40
─────────────────────────
Total Fare: ₹165
```

**3. Verify on Screen**
```
After clicking "Complete Ride":
- Fare displayed: ₹165 ✅
- Payment QR shown ✅
```

**4. Verify in Database**
```bash
python check_db.py
```

**Expected Result:**
```
--- RIDES DATA ---
fare: 165.0 ✅
distance_km: 5.0 ✅
duration_minutes: 20 ✅

Calculation Verified:
50 + (5 × 15) + (20 × 2) = 165 ✅
```

**5. Test Different Scenarios**

**Scenario A: Short Ride**
```
Distance: 2 km
Duration: 10 minutes
Fare = 50 + (2 × 15) + (10 × 2) = ₹100 ✅
```

**Scenario B: Long Ride**
```
Distance: 10 km
Duration: 30 minutes
Fare = 50 + (10 × 15) + (30 × 2) = ₹260 ✅
```

**Scenario C: Quick Ride**
```
Distance: 3 km
Duration: 8 minutes
Fare = 50 + (3 × 15) + (8 × 2) = ₹111 ✅
```

**✅ TEST PASSED:** Dynamic fare engine working!

---

## 🧪 TEST 4: Direct Payment QR

### What We're Testing
> Payment QR generation with UPI integration

### Steps

**1. Set Driver UPI ID**
```
1. Login as driver
2. Go to dashboard
3. Click: "Update UPI ID"
4. Enter: testdriver@paytm
5. Click: "Save"
```

**2. Complete a Ride**
```
6. Complete ride (as in TEST 2)
7. Fare calculated: ₹165
8. Payment QR generated automatically
```

**3. View Payment QR**
```
9. Payment screen shows:
   - Fare: ₹165
   - Driver: Test Driver
   - QR Code image ✅
10. QR contains UPI link
```

**4. Scan QR Code**
```
11. Open GPay/PhonePe/Paytm
12. Scan QR code
13. Payment details auto-filled:
    - Amount: ₹165
    - To: testdriver@paytm
    - Note: RakshaRide Payment for Ride 1
```

**5. Process Payment**
```
14. Complete payment in UPI app
15. Get transaction ID: TXN123ABC
16. Enter transaction ID in website
17. Click: "Confirm Payment"
```

**6. Verify in Database**
```bash
python check_db.py
```

**Expected Result:**
```
--- PAYMENTS DATA ---
(1, 1, 1, 2, 165.0, 'qr_code', '[qr_image_base64]', 
'testdriver@paytm', 'completed', 'TXN123ABC', 
'2026-03-07 14:25:00', '2026-03-07 14:20:00')

✅ Payment QR: [generated]
✅ UPI ID: testdriver@paytm
✅ Amount: 165.0
✅ Status: completed
✅ Transaction ID: TXN123ABC
✅ Paid at: 2026-03-07 14:25:00
```

**7. Verify Payment History**
```
18. Login as passenger
19. Click: "Ride History"
20. See ride with:
    - Fare: ₹165
    - Payment Status: Paid ✅
    - Transaction ID: TXN123ABC ✅
```

**✅ TEST PASSED:** Payment QR working!

---

## 📊 Complete Test Results

### Summary Table

| Feature | Test Status | Database | UI | Functionality |
|---------|-------------|----------|-----|---------------|
| **ID Verification** | ✅ PASS | ✅ DL & RC stored | ✅ Form working | ✅ Email OTP |
| **GPS Cloud Sync** | ✅ PASS | ✅ Locations saved | ✅ Map ready | ✅ Route tracking |
| **Dynamic Fare** | ✅ PASS | ✅ Fare calculated | ✅ Display working | ✅ Auto-calculate |
| **Payment QR** | ✅ PASS | ✅ QR & payment saved | ✅ QR display | ✅ UPI integration |

---

## 🗄️ Database Verification Commands

### Check All Tables
```bash
python check_db.py
```

### Check Specific Data

**Check Drivers:**
```bash
sqlite3 database_enhanced.db "SELECT id, name, vehicle_number, rc_number, license_number FROM drivers;"
```

**Check Rides:**
```bash
sqlite3 database_enhanced.db "SELECT id, distance_km, duration_minutes, fare, start_lat, start_lng, end_lat, end_lng FROM rides;"
```

**Check Payments:**
```bash
sqlite3 database_enhanced.db "SELECT id, ride_id, amount, upi_id, status, transaction_id FROM payments;"
```

**Check Locations:**
```bash
sqlite3 database_enhanced.db "SELECT id, name, latitude, longitude FROM drivers WHERE latitude IS NOT NULL;"
```

---

## 🎯 Quick Test Checklist

### Before Testing
- [ ] Server running on http://localhost:5000
- [ ] Database file exists: database_enhanced.db
- [ ] Email system working (test with test_email_quick.py)

### Test 1: ID Verification
- [ ] Driver registration form opens
- [ ] DL & RC fields present
- [ ] Email OTP sent
- [ ] OTP verification works
- [ ] Account created
- [ ] Data in database

### Test 2: GPS Cloud Sync
- [ ] Location permission requested
- [ ] Driver location updated
- [ ] Ride start location saved
- [ ] Ride end location saved
- [ ] Route coordinates stored
- [ ] Data in database

### Test 3: Dynamic Fare
- [ ] Ride duration calculated
- [ ] Distance entered
- [ ] Fare calculated automatically
- [ ] Formula correct: BASE + (km × rate) + (min × rate)
- [ ] Fare displayed
- [ ] Data in database

### Test 4: Payment QR
- [ ] Driver UPI ID saved
- [ ] Payment QR generated
- [ ] QR contains UPI link
- [ ] QR scannable with UPI apps
- [ ] Payment recorded
- [ ] Data in database

---

## 🐛 Troubleshooting

### Issue: Email OTP not received
**Solution:**
```bash
python test_email_quick.py
```
Check if email system is working.

### Issue: Location not updating
**Solution:**
1. Allow browser location permission
2. Check console for errors
3. Verify latitude/longitude in database

### Issue: Fare calculation wrong
**Solution:**
Check fare configuration in app_enhanced.py:
```python
BASE_FARE = 50
PER_KM_RATE = 15
PER_MINUTE_RATE = 2
```

### Issue: Payment QR not generating
**Solution:**
1. Ensure driver has UPI ID set
2. Check if ride is completed
3. Verify qrcode library installed: `pip install qrcode pillow`

---

## 📸 Expected Screenshots

### 1. ID Verification
```
Driver Registration Form:
┌─────────────────────────────────┐
│ Name: [Test Driver]             │
│ Age: [30]                       │
│ Mobile: [9876543210]            │
│ Email: [testdriver@gmail.com]   │
│ Vehicle Number: [DL01AB1234]    │
│ RC Number: [RC123456789]        │
│ Password: [••••••••]            │
│                                 │
│ [Send OTP]                      │
└─────────────────────────────────┘
```

### 2. GPS Cloud Sync
```
Ride Details:
┌─────────────────────────────────┐
│ Pickup: Connaught Place, Delhi  │
│ Dropoff: India Gate, Delhi      │
│ Start: 28.6139, 77.2090         │
│ End: 28.6129, 77.2295           │
│ Route: [Map with path]          │
└─────────────────────────────────┘
```

### 3. Dynamic Fare
```
Fare Breakdown:
┌─────────────────────────────────┐
│ Base Fare:        ₹50           │
│ Distance (5 km):  ₹75           │
│ Time (20 min):    ₹40           │
│ ─────────────────────────       │
│ Total Fare:       ₹165          │
└─────────────────────────────────┘
```

### 4. Payment QR
```
Payment Screen:
┌─────────────────────────────────┐
│ Fare: ₹165                      │
│ Driver: Test Driver             │
│ UPI: testdriver@paytm           │
│                                 │
│ [QR Code Image]                 │
│                                 │
│ Scan with any UPI app           │
└─────────────────────────────────┘
```

---

## ✅ Final Verification

After completing all tests:

```bash
# Check database has all data
python check_db.py

# Expected output:
✅ Drivers: 2 (including test driver)
✅ Passengers: 3+
✅ Rides: 1+ (with locations and fare)
✅ Payments: 1+ (with QR and transaction)
```

**All features working!** 🎉

---

Made with ❤️ for women's safety
