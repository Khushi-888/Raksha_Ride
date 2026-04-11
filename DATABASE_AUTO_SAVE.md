# ✅ Database Auto-Save Confirmation

## 🎯 Yes! All Data is Automatically Saved

Your RakshaRide system **automatically saves all data** to the database when users interact with the website.

---

## 📊 What Gets Saved Automatically

### 1. Passenger Registration
**When:** User completes registration
**Saved to:** `passengers` table
**Data:**
- ✅ Name
- ✅ Phone number
- ✅ Email address
- ✅ Password (hashed with SHA256)
- ✅ Registration timestamp
- ✅ Total rides (starts at 0)
- ✅ Total spent (starts at 0)

### 2. Driver Registration
**When:** Driver completes registration
**Saved to:** `drivers` table
**Data:**
- ✅ Name
- ✅ Age
- ✅ Mobile number
- ✅ Email address
- ✅ Vehicle type (Car/Auto/Bike)
- ✅ Vehicle number
- ✅ RC number
- ✅ Password (hashed)
- ✅ QR code data (JSON)
- ✅ Rating (default 5.0)
- ✅ Total rides (starts at 0)
- ✅ Total earned (starts at 0)
- ✅ Availability status
- ✅ Registration timestamp

### 3. OTP Verification
**When:** OTP is generated
**Saved to:** `otp_verification` table
**Data:**
- ✅ Email address
- ✅ OTP code (6 digits)
- ✅ Expiry time (5 minutes)
- ✅ Attempts counter
- ✅ Creation timestamp

### 4. Rides
**When:** Ride starts/completes
**Saved to:** `rides` table
**Data:**
- ✅ Passenger ID
- ✅ Driver ID
- ✅ Passenger name & phone
- ✅ Driver name, mobile & vehicle
- ✅ Pickup location
- ✅ Dropoff location
- ✅ Start time
- ✅ End time
- ✅ Duration (minutes)
- ✅ Distance (km)
- ✅ Fare (₹)
- ✅ Status (pending/active/completed)
- ✅ Payment status

### 5. Payments
**When:** Ride completes
**Saved to:** `payments` table
**Data:**
- ✅ Ride ID
- ✅ Passenger ID
- ✅ Driver ID
- ✅ Amount (fare)
- ✅ Payment method
- ✅ Payment QR code
- ✅ Status (pending/completed)
- ✅ Transaction ID
- ✅ Payment timestamp

---

## 🔄 Automatic Updates

### User Statistics
**Automatically updated when:**
- Ride completes → `total_rides` increments
- Payment made → `total_spent` (passenger) / `total_earned` (driver) updates
- Driver availability → `is_available` changes

### Ride Status
**Automatically updated when:**
- Ride starts → Status: `active`
- Ride completes → Status: `completed`
- Payment made → Payment status: `completed`

---

## 💾 Database File

**Location:** `database_enhanced.db` (SQLite)

**Created automatically when:**
- First time running `python app_enhanced.py`
- Database initialization runs

**Tables created:**
1. `passengers` - All passenger accounts
2. `drivers` - All driver accounts
3. `otp_verification` - OTP codes
4. `rides` - All ride records
5. `payments` - All payment transactions

---

## 🔍 View Your Data

### Method 1: SQLite Browser
```bash
# Install SQLite browser
# Then open: database_enhanced.db
```

### Method 2: Command Line
```bash
sqlite3 database_enhanced.db

# View passengers
SELECT * FROM passengers;

# View drivers
SELECT * FROM drivers;

# View rides
SELECT * FROM rides;

# View payments
SELECT * FROM payments;

# Exit
.quit
```

### Method 3: Python Script
```python
import sqlite3

conn = sqlite3.connect('database_enhanced.db')
c = conn.cursor()

# Get all passengers
c.execute("SELECT * FROM passengers")
print(c.fetchall())

# Get all drivers
c.execute("SELECT * FROM drivers")
print(c.fetchall())

conn.close()
```

---

## ✅ Data Flow Example

### Registration Flow
```
1. User fills form
   ↓
2. Clicks "Send OTP"
   ↓
3. OTP saved to database
   ↓
4. User enters OTP
   ↓
5. System verifies OTP
   ↓
6. User data saved to database
   ↓
7. Account created!
```

### Ride Flow
```
1. Passenger scans QR
   ↓
2. Driver verified from database
   ↓
3. Ride starts
   ↓
4. Ride record saved to database
   ↓
5. Driver completes ride
   ↓
6. Fare calculated
   ↓
7. Payment record created
   ↓
8. All data saved to database
   ↓
9. Statistics updated
```

---

## 🎯 Confirmation

**Every action saves data:**
- ✅ Register → Database
- ✅ Login → Session + Database check
- ✅ Start ride → Database
- ✅ Complete ride → Database
- ✅ Make payment → Database
- ✅ View history → From database

**Nothing is lost!** All data persists in `database_enhanced.db`

---

## 📊 Database Schema

### Passengers Table
```sql
CREATE TABLE passengers (
    id INTEGER PRIMARY KEY,
    name TEXT,
    phone TEXT UNIQUE,
    email TEXT UNIQUE,
    password TEXT,
    total_rides INTEGER DEFAULT 0,
    total_spent REAL DEFAULT 0,
    created_at TIMESTAMP
)
```

### Drivers Table
```sql
CREATE TABLE drivers (
    id INTEGER PRIMARY KEY,
    name TEXT,
    age INTEGER,
    mobile TEXT UNIQUE,
    email TEXT UNIQUE,
    vehicle_number TEXT,
    vehicle_type TEXT,
    rc_number TEXT,
    password TEXT,
    qr_code TEXT,
    rating REAL DEFAULT 5.0,
    total_rides INTEGER DEFAULT 0,
    total_earned REAL DEFAULT 0,
    is_available BOOLEAN DEFAULT 1,
    created_at TIMESTAMP
)
```

### Rides Table
```sql
CREATE TABLE rides (
    id INTEGER PRIMARY KEY,
    passenger_id INTEGER,
    driver_id INTEGER,
    passenger_name TEXT,
    driver_name TEXT,
    pickup_location TEXT,
    dropoff_location TEXT,
    start_time TIMESTAMP,
    end_time TIMESTAMP,
    duration_minutes INTEGER,
    distance_km REAL,
    fare REAL,
    status TEXT,
    payment_status TEXT,
    created_at TIMESTAMP
)
```

---

## 🎉 Summary

**Your RakshaRide system:**
- ✅ Automatically saves all user data
- ✅ Stores in SQLite database
- ✅ Persists across server restarts
- ✅ Updates statistics automatically
- ✅ Tracks complete ride history
- ✅ Records all payments
- ✅ Never loses data

**Everything is saved automatically - no manual intervention needed!**

---

Made with ❤️ for women's safety
