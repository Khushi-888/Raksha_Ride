# 🛡️ RakshaRide — Safe Verified Ride Sharing

Live at: **https://raksharide.onrender.com**

---

## 1. Introduction
**RakshaRide** is a safety-centric, full-stack ride-hailing application designed to provide transparency and security in the unorganized transportation sector (Rickshaws/Taxis). The system utilizes dynamic QR code generation, real-time database synchronization, and SerpApi integrations to ensure that every journey is verified, tracked, and securely recorded for both passengers and drivers.

---

## 2. 🎯 Advanced Features & Objectives

### 1️⃣ Real-Time ID Verification (QR-Based)
The primary objective is to eliminate "shadow" drivers.
- Drivers register with their License (DL) and Registration Certificate (RC) numbers.
- Accounts are verified via Email OTP.
- The system generates a unique QR code for verified drivers. Before a ride, passengers scan this QR to instantly verify the driver's identity, vehicle details, and ratings.

### 2️⃣ GPS Cloud Sync & Tracking
Tracks driver and ride location continuously.
- Saves start and end locations using coordinates.
- All data is backed up to the database for cloud sync, keeping a permanent history of the route.
- Integrated with **SerpApi Address Autocomplete & Geocoding** for precise pickup/dropoff places.

### 3️⃣ Dynamic Fare Engine & Route Intelligence
To prevent overcharging, the system calculates fares automatically based on distance and time.
- Formula: `Fare = ₹50 (base) + (distance × ₹15/km) + (time × ₹2/min)`
- Integrated with **SerpApi Route & Transparent Fair Pricing** for driving distance and duration estimates.

### 4️⃣ Direct Payment QR
Generates a payment QR code at the end of the ride containing a direct UPI link.
- Works with any UPI app (GPay, PhonePe, Paytm).
- Payment transactions are tracked and stored in the database.

### 5️⃣ SOS & Safety Integrations
- **SerpApi Nearest Police & Hospital Lookup** for the SOS emergency alert system.
- **SerpApi Pre-Ride Safety Intelligence** (real-time road alerts & local news).
- **SerpApi Admin Driver/Vehicle Sanity Check** (soft background screening).

---

## 3. 📱 User Features

### 🧍 For Passengers
- 📷 Scan driver QR code using HTML5 Camera to verify driver details (name, vehicle, rating).
- 🚗 Start ride with specified pickup/dropoff locations.
- 📊 View complete ride and payment history.
- 🚨 Access to SOS emergency features.

### 🚕 For Drivers (Owner/Rent Flow)
- 🔲 Display unique QR code for passenger scanning.
- 🚗 Manage active rides and update statuses (Available/Busy).
- ✅ Complete rides with automatic fare calculation.
- 💳 Generate dynamic UPI Payment QR for fare collection.
- 📊 Track total rides and earnings.

---

## 4. 🔄 Complete Ride Flow

1. **Identity Verification:** Users register via Email OTP. Verified drivers get a unique QR code.
2. **Scan & Verify:** Passenger opens the app, clicks "Start Scanner," and scans the driver's QR code. The system verifies the driver.
3. **Start Ride:** Passenger reviews details and starts the ride. The driver is marked as busy, and GPS start locations are logged.
4. **Complete Ride:** Driver completes the ride. The system calculates the fare automatically based on distance and time.
5. **Payment:** A Payment QR is generated. The passenger scans it to pay via UPI.
6. **Log:** The ride is saved in both users' histories with full route coordinates and payment status.

---

## 5. 🗄️ Database Design

The system uses an SQLite relational database (`database_enhanced.db`) with 5 core tables:
1. **`passengers`**: Accounts, profiles, and statistics for riders.
2. **`drivers`**: Driver credentials (DL, RC), vehicle info, ratings, and generated QR codes.
3. **`rides`**: The "Common Ride Table" linking driver and passenger. Stores GPS coordinates, calculated fares, and ride statuses.
4. **`payments`**: Payment QR data, UPI IDs, amounts, and transaction statuses.
5. **`otp_verification`**: Temporary storage for Email OTP authentication.

---

## 6. 🚀 Quick Start / Run Locally

### 1. Install Dependencies
```bash
pip install -r requirements_enhanced.txt
```

### 2. Start the Server
**Option A (Windows):** Double-click `START_ENHANCED_SYSTEM.bat`
**Option B (Command Line):**
```bash
python app_enhanced.py
```

### 3. Open Browser
Navigate to: `http://localhost:5000`

---

## 7. 🔑 Admin Panel & Environment Variables

### Admin Panel
- **URL:** `http://localhost:5000/admin`
- **Username:** `admin`
- **Password:** `admin@RakshaRide2024`

### Environment Variables (`.env`)
| Variable | Description |
|---|---|
| `SECRET_KEY` | Flask session secret key |
| `GMAIL_EMAIL` | Email used for sending OTPs |
| `GMAIL_APP_PASSWORD` | App password for SMTP authentication |
| `FLASK_ENV` | `production` or `development` |
| `APP_URL` | e.g., `https://raksharide.onrender.com` |
| `SERPAPI_KEY` | API key from serpapi.com |

---

## 8. 📋 API Endpoints

### Core Application APIs
- **Auth:** `/api/send_otp`, `/api/verify_otp`, `/api/register_passenger`, `/api/register_driver`
- **Driver:** `/api/get_driver_qr`, `/api/update_driver_location`, `/api/get_nearby_drivers`
- **Rides:** `/api/scan_driver_qr`, `/api/start_ride`, `/api/complete_ride`
- **Payment:** `/api/process_payment`

### SerpApi Powered Endpoints
- `GET /api/geocode`: Address autocomplete & geocoding.
- `GET /api/nearby_safety`: Pre-ride local route safety news.
- `GET /api/route`: Road distance, duration & fare routing.
- `GET /api/nearby_emergency`: Nearest police stations & hospitals for SOS.
- `GET /api/admin/driver_sanity_check`: Soft background screening.

---

## 9. 🔧 Technical Stack
- **Backend:** Python, Flask, Waitress
- **Database:** SQLite
- **Frontend:** HTML5, Vanilla CSS (Glassmorphism), JavaScript
- **Scanning:** HTML5 Camera API, jsQR library
- **APIs:** SerpApi for intelligent location/safety routing
- **Deployment:** Render (via `Procfile`)

---

*Made with ❤️ for women's safety & verified urban transportation.*
