# 🚗 RakshaRide - Complete System Flow

## Visual Guide: How Everything Works Together

---

## 📧 Email OTP Flow (CONFIRMED WORKING ✅)

```
┌─────────────────────────────────────────────────────────────┐
│                    USER REGISTRATION                         │
└─────────────────────────────────────────────────────────────┘

1. User enters email: khushisaharan42@gmail.com
                ↓
2. Clicks "Send OTP"
                ↓
3. Backend generates: 123456
                ↓
4. Backend saves to database:
   ┌──────────────────────────────────────┐
   │ otp_verification table               │
   │ email: khushisaharan42@gmail.com     │
   │ otp: 123456                          │
   │ expiry: 2026-03-07 12:08:17          │
   └──────────────────────────────────────┘
                ↓
5. Backend sends email via Gmail SMTP ✅
   ┌──────────────────────────────────────┐
   │ From: riksharide2026@gmail.com       │
   │ To: khushisaharan42@gmail.com        │
   │ Subject: RakshaRide - Your OTP Code  │
   │                                      │
   │ Your OTP: 123456                     │
   │ Valid for 5 minutes                  │
   └──────────────────────────────────────┘
                ↓
6. User receives email in inbox ✅
                ↓
7. User enters OTP: 123456
                ↓
8. Backend verifies OTP
                ↓
9. Backend creates account & saves:
   ┌──────────────────────────────────────┐
   │ passengers/drivers table             │
   │ name: Rajni Devi                     │
   │ email: khushisaharan42@gmail.com     │
   │ password: [hashed]                   │
   │ created_at: 2026-03-07 07:52:13      │
   └──────────────────────────────────────┘
                ↓
10. Account created! ✅
```

---

## 🚗 Complete Ride Flow (DATABASE AUTO-SAVE ✅)

```
┌─────────────────────────────────────────────────────────────┐
│                    RIDE LIFECYCLE                            │
└─────────────────────────────────────────────────────────────┘

STEP 1: DRIVER REGISTRATION
────────────────────────────
Driver registers → QR code generated → Saved to database

┌──────────────────────────────────────┐
│ drivers table                        │
│ id: 1                                │
│ name: khushi                         │
│ vehicle: DL4362732                   │
│ qr_code: {"driver_id": 1, ...}       │
│ is_available: 1                      │
└──────────────────────────────────────┘


STEP 2: PASSENGER SCANS QR
───────────────────────────
Passenger opens camera → Scans driver QR → Driver verified

Backend checks:
┌──────────────────────────────────────┐
│ SELECT * FROM drivers WHERE id = 1   │
│ Result: ✅ Driver found              │
│         ✅ Available                 │
│         ✅ Rating: 5.0               │
└──────────────────────────────────────┘


STEP 3: START RIDE
──────────────────
Passenger clicks "Start Ride" → Ride created → Saved to database

┌──────────────────────────────────────┐
│ rides table                          │
│ id: 1                                │
│ passenger_id: 1                      │
│ driver_id: 1                         │
│ passenger_name: Rajni Devi           │
│ driver_name: khushi                  │
│ driver_vehicle: DL4362732            │
│ start_time: 2026-03-07 12:00:00      │
│ status: active                       │
└──────────────────────────────────────┘

Backend also updates:
┌──────────────────────────────────────┐
│ UPDATE drivers                       │
│ SET is_available = 0                 │
│ WHERE id = 1                         │
└──────────────────────────────────────┘


STEP 4: RIDE IN PROGRESS
─────────────────────────
Driver drives → Location tracked → Route recorded

┌──────────────────────────────────────┐
│ rides table (updating)               │
│ route_coordinates: [lat,lng,...]     │
│ distance_km: 5.2                     │
└──────────────────────────────────────┘


STEP 5: COMPLETE RIDE
─────────────────────
Driver/Passenger clicks "Complete" → Fare calculated → Saved

Backend calculates:
Fare = ₹50 (base) + (5.2 km × ₹15) + (20 min × ₹2)
     = ₹50 + ₹78 + ₹40
     = ₹168

Backend updates:
┌──────────────────────────────────────┐
│ rides table                          │
│ end_time: 2026-03-07 12:20:00        │
│ duration_minutes: 20                 │
│ distance_km: 5.2                     │
│ fare: 168.0                          │
│ status: completed                    │
└──────────────────────────────────────┘

┌──────────────────────────────────────┐
│ passengers table                     │
│ total_rides: 1                       │
│ total_spent: 168.0                   │
└──────────────────────────────────────┘

┌──────────────────────────────────────┐
│ drivers table                        │
│ total_rides: 1                       │
│ total_earned: 168.0                  │
│ is_available: 1                      │
└──────────────────────────────────────┘


STEP 6: PAYMENT
───────────────
Payment QR generated → Passenger pays → Transaction recorded

┌──────────────────────────────────────┐
│ payments table                       │
│ id: 1                                │
│ ride_id: 1                           │
│ passenger_id: 1                      │
│ driver_id: 1                         │
│ amount: 168.0                        │
│ payment_qr: [QR code image]          │
│ status: pending                      │
└──────────────────────────────────────┘

After payment:
┌──────────────────────────────────────┐
│ payments table                       │
│ status: completed                    │
│ transaction_id: TXN123ABC            │
│ paid_at: 2026-03-07 12:25:00         │
└──────────────────────────────────────┘

┌──────────────────────────────────────┐
│ rides table                          │
│ payment_status: completed            │
└──────────────────────────────────────┘
```

---

## 📊 Database Relationships

```
┌─────────────────┐
│   passengers    │
│─────────────────│
│ id (PK)         │◄────┐
│ name            │     │
│ email           │     │
│ phone           │     │
│ total_rides     │     │
│ total_spent     │     │
└─────────────────┘     │
                        │
                        │ passenger_id (FK)
                        │
┌─────────────────┐     │     ┌─────────────────┐
│    drivers      │     │     │     rides       │
│─────────────────│     │     │─────────────────│
│ id (PK)         │◄────┼─────┤ id (PK)         │
│ name            │     │     │ passenger_id    │
│ vehicle_number  │     └─────┤ driver_id       │
│ qr_code         │           │ start_time      │
│ is_available    │           │ end_time        │
│ total_rides     │           │ fare            │
│ total_earned    │           │ status          │
└─────────────────┘           └─────────────────┘
                                      │
                                      │ ride_id (FK)
                                      │
                              ┌───────▼─────────┐
                              │    payments     │
                              │─────────────────│
                              │ id (PK)         │
                              │ ride_id         │
                              │ amount          │
                              │ payment_qr      │
                              │ status          │
                              │ transaction_id  │
                              └─────────────────┘
```

---

## 🔄 Auto-Save Triggers

```
┌─────────────────────────────────────────────────────────────┐
│              WHEN DATA IS AUTOMATICALLY SAVED                │
└─────────────────────────────────────────────────────────────┘

EVENT: User clicks "Send OTP"
TRIGGER: send_otp() function
ACTION: INSERT INTO otp_verification
RESULT: ✅ OTP saved to database

EVENT: User clicks "Create Account" (Passenger)
TRIGGER: register_passenger() function
ACTION: INSERT INTO passengers
RESULT: ✅ Passenger saved to database

EVENT: User clicks "Create Account" (Driver)
TRIGGER: register_driver() function
ACTION: INSERT INTO drivers + QR code generation
RESULT: ✅ Driver saved with QR code

EVENT: Passenger clicks "Start Ride"
TRIGGER: start_ride() function
ACTION: INSERT INTO rides + UPDATE drivers availability
RESULT: ✅ Ride started and saved

EVENT: User clicks "Complete Ride"
TRIGGER: complete_ride() function
ACTION: UPDATE rides + UPDATE passengers stats + UPDATE drivers stats + INSERT INTO payments
RESULT: ✅ Ride completed, all stats updated

EVENT: Passenger clicks "Pay Now"
TRIGGER: process_payment() function
ACTION: UPDATE payments + UPDATE rides payment_status
RESULT: ✅ Payment recorded

EVENT: Driver updates location
TRIGGER: update_driver_location() function
ACTION: UPDATE drivers SET latitude, longitude
RESULT: ✅ Location saved

EVENT: Driver updates UPI ID
TRIGGER: update_upi_id() function
ACTION: UPDATE drivers SET upi_id
RESULT: ✅ UPI ID saved
```

---

## 🎯 Real-World Example

```
┌─────────────────────────────────────────────────────────────┐
│                    COMPLETE USER JOURNEY                     │
└─────────────────────────────────────────────────────────────┘

DAY 1: REGISTRATION
───────────────────
09:00 AM - Rajni Devi visits website
09:01 AM - Clicks "Join as Passenger"
09:02 AM - Enters: Rajni Devi, +916283798319, khushisaharan42@gmail.com
09:03 AM - Clicks "Send OTP"
09:03 AM - ✅ Email sent to khushisaharan42@gmail.com
09:04 AM - Checks email, sees OTP: 847291
09:05 AM - Enters OTP, clicks "Create Account"
09:05 AM - ✅ Account created! Saved to database
09:06 AM - Redirected to dashboard

DATABASE STATE:
┌──────────────────────────────────────┐
│ passengers table                     │
│ id: 1                                │
│ name: Rajni Devi                     │
│ email: khushisaharan42@gmail.com     │
│ total_rides: 0                       │
│ total_spent: 0.0                     │
└──────────────────────────────────────┘


DAY 2: FIRST RIDE
─────────────────
10:00 AM - Rajni needs a ride
10:01 AM - Opens RakshaRide app
10:02 AM - Scans driver khushi's QR code
10:03 AM - Sees: khushi, DL4362732, Rating: 5.0
10:04 AM - Clicks "Start Ride"
10:04 AM - ✅ Ride started! Saved to database

DATABASE STATE:
┌──────────────────────────────────────┐
│ rides table                          │
│ id: 1                                │
│ passenger_id: 1                      │
│ driver_id: 1                         │
│ passenger_name: Rajni Devi           │
│ driver_name: khushi                  │
│ start_time: 2026-03-08 10:04:00      │
│ status: active                       │
└──────────────────────────────────────┘

10:25 AM - Reaches destination
10:26 AM - Clicks "Complete Ride"
10:26 AM - ✅ Fare calculated: ₹168
10:26 AM - ✅ All data updated

DATABASE STATE:
┌──────────────────────────────────────┐
│ rides table                          │
│ end_time: 2026-03-08 10:25:00        │
│ duration_minutes: 21                 │
│ distance_km: 5.2                     │
│ fare: 168.0                          │
│ status: completed                    │
└──────────────────────────────────────┘

┌──────────────────────────────────────┐
│ passengers table                     │
│ total_rides: 1                       │
│ total_spent: 168.0                   │
└──────────────────────────────────────┘

┌──────────────────────────────────────┐
│ drivers table                        │
│ total_rides: 1                       │
│ total_earned: 168.0                  │
└──────────────────────────────────────┘

┌──────────────────────────────────────┐
│ payments table                       │
│ ride_id: 1                           │
│ amount: 168.0                        │
│ status: pending                      │
└──────────────────────────────────────┘

10:27 AM - Scans payment QR
10:28 AM - Pays via UPI
10:28 AM - ✅ Payment completed

DATABASE STATE:
┌──────────────────────────────────────┐
│ payments table                       │
│ status: completed                    │
│ transaction_id: TXN8A3F2B1C          │
│ paid_at: 2026-03-08 10:28:00         │
└──────────────────────────────────────┘
```

---

## ✅ Confirmation: Everything Auto-Saves

```
USER ACTION              →  DATABASE OPERATION           →  RESULT
─────────────────────────────────────────────────────────────────────
Register                 →  INSERT INTO passengers       →  ✅ Saved
Send OTP                 →  INSERT INTO otp_verification →  ✅ Saved
Verify OTP               →  DELETE FROM otp_verification →  ✅ Cleaned
Login                    →  SELECT + Session created     →  ✅ Logged in
Start Ride               →  INSERT INTO rides            →  ✅ Saved
Update Location          →  UPDATE drivers               →  ✅ Saved
Complete Ride            →  UPDATE rides + passengers    →  ✅ Saved
Generate Payment         →  INSERT INTO payments         →  ✅ Saved
Process Payment          →  UPDATE payments              →  ✅ Saved
View History             →  SELECT FROM rides            →  ✅ Retrieved
```

---

## 🎉 Summary

**Your system automatically saves:**
- ✅ Every user registration
- ✅ Every OTP generated
- ✅ Every ride started
- ✅ Every ride completed
- ✅ Every payment made
- ✅ Every location update
- ✅ Every statistic change

**No manual intervention needed!**

**Email OTP:**
- ✅ Sends to actual user email
- ✅ Professional branded format
- ✅ Tested and confirmed working

**Database:**
- ✅ All tables created
- ✅ All relationships working
- ✅ All data persistent
- ✅ Auto-saves on every action

---

Made with ❤️ for women's safety
