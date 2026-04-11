# 🏗️ RakshaRide Enhanced - System Architecture

## 📊 High-Level Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    RakshaRide Enhanced                       │
│              Complete Ride Sharing Platform                  │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
        ┌─────────────────────────────────────────┐
        │         Frontend (HTML/JS/CSS)          │
        ├─────────────────────────────────────────┤
        │  • index_enhanced.html (Landing)        │
        │  • dashboard_passenger.html             │
        │  • dashboard_driver.html                │
        │  • QR Scanner (HTML5 Camera)            │
        │  • jsQR Library                         │
        └─────────────────────────────────────────┘
                              │
                              ▼ HTTP/JSON
        ┌─────────────────────────────────────────┐
        │      Backend (Flask - Python)           │
        ├─────────────────────────────────────────┤
        │  • app_enhanced.py (1153 lines)         │
        │  • 20+ API Endpoints                    │
        │  • Session Management                   │
        │  • QR Code Generation                   │
        │  • Fare Calculation                     │
        └─────────────────────────────────────────┘
                              │
                              ▼ SQL
        ┌─────────────────────────────────────────┐
        │      Database (SQLite)                  │
        ├─────────────────────────────────────────┤
        │  • passengers                           │
        │  • drivers                              │
        │  • otp_verification                     │
        │  • rides                                │
        │  • payments                             │
        └─────────────────────────────────────────┘
```

---

## 🔄 Complete Ride Flow

```
PASSENGER SIDE                    SYSTEM                    DRIVER SIDE

┌──────────────┐                                          ┌──────────────┐
│ Open App     │                                          │ Open App     │
└──────┬───────┘                                          └──────┬───────┘
       │                                                          │
       ▼                                                          ▼
┌──────────────┐                                          ┌──────────────┐
│ Click "Scan  │                                          │ Show QR Code │
│ QR Code"     │                                          │              │
└──────┬───────┘                                          └──────────────┘
       │                                                          ▲
       ▼                                                          │
┌──────────────┐                                                 │
│ Camera Opens │                                                 │
└──────┬───────┘                                                 │
       │                                                          │
       ▼                                                          │
┌──────────────┐         ┌──────────────┐                       │
│ Scan Driver  │────────▶│ Verify QR    │                       │
│ QR Code      │         │ Data         │                       │
└──────────────┘         └──────┬───────┘                       │
                                │                                │
                                ▼                                │
                         ┌──────────────┐                       │
                         │ Get Driver   │──────────────────────┘
                         │ Details      │
                         └──────┬───────┘
                                │
       ┌────────────────────────┘
       │
       ▼
┌──────────────┐
│ Verify       │
│ Driver Info  │
│ • Name       │
│ • Vehicle    │
│ • Rating     │
└──────┬───────┘
       │
       ▼
┌──────────────┐         ┌──────────────┐         ┌──────────────┐
│ Click "Start │────────▶│ Create Ride  │────────▶│ Notification │
│ Ride"        │         │ Record       │         │ "Ride Active"│
└──────────────┘         └──────┬───────┘         └──────────────┘
                                │
                                ▼
                         ┌──────────────┐
                         │ Mark Driver  │
                         │ as Busy      │
                         └──────┬───────┘
                                │
       ┌────────────────────────┴────────────────────────┐
       │                                                  │
       ▼                                                  ▼
┌──────────────┐                                  ┌──────────────┐
│ See Active   │                                  │ See Active   │
│ Ride Info    │                                  │ Ride Info    │
└──────────────┘                                  └──────┬───────┘
                                                         │
                                                         ▼
                                                  ┌──────────────┐
                                                  │ Enter        │
                                                  │ Distance     │
                                                  └──────┬───────┘
                                                         │
                                                         ▼
                                                  ┌──────────────┐
                         ┌──────────────┐        │ Click        │
                         │ Calculate    │◀───────│ "Complete    │
                         │ Fare         │        │ Ride"        │
                         │ Base + Dist  │        └──────────────┘
                         │ + Time       │
                         └──────┬───────┘
                                │
                                ▼
                         ┌──────────────┐
                         │ Generate     │
                         │ Payment QR   │
                         └──────┬───────┘
                                │
       ┌────────────────────────┴────────────────────────┐
       │                                                  │
       ▼                                                  ▼
┌──────────────┐                                  ┌──────────────┐
│ See Payment  │                                  │ Show Payment │
│ QR Code      │                                  │ QR to        │
│              │                                  │ Passenger    │
└──────┬───────┘                                  └──────────────┘
       │
       ▼
┌──────────────┐         ┌──────────────┐
│ Scan Payment │────────▶│ Process      │
│ QR & Pay     │         │ Payment      │
└──────────────┘         └──────┬───────┘
                                │
                                ▼
                         ┌──────────────┐
                         │ Save to      │
                         │ History      │
                         └──────┬───────┘
                                │
       ┌────────────────────────┴────────────────────────┐
       │                                                  │
       ▼                                                  ▼
┌──────────────┐                                  ┌──────────────┐
│ View in      │                                  │ View in      │
│ History Tab  │                                  │ History Tab  │
│ • Driver     │                                  │ • Passenger  │
│ • Fare       │                                  │ • Earnings   │
│ • Date/Time  │                                  │ • Date/Time  │
└──────────────┘                                  └──────────────┘
```

---

## 🗄️ Database Schema

```
┌─────────────────────────────────────────────────────────────┐
│                        PASSENGERS                            │
├─────────────────────────────────────────────────────────────┤
│ id (PK)                                                      │
│ name                                                         │
│ phone (UNIQUE)                                               │
│ email (UNIQUE)                                               │
│ password (HASHED)                                            │
│ profile_image                                                │
│ total_rides                                                  │
│ total_spent                                                  │
│ created_at                                                   │
└─────────────────────────────────────────────────────────────┘
                              │
                              │ 1:N
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                           RIDES                              │
├─────────────────────────────────────────────────────────────┤
│ id (PK)                                                      │
│ passenger_id (FK) ──────────────────────────────────────────┘
│ driver_id (FK) ──────────────────────────────────────────┐
│ passenger_name                                            │
│ passenger_phone                                           │
│ driver_name                                               │
│ driver_mobile                                             │
│ driver_vehicle                                            │
│ pickup_location                                           │
│ dropoff_location                                          │
│ start_time                                                │
│ end_time                                                  │
│ duration_minutes                                          │
│ distance_km                                               │
│ fare                                                      │
│ status (pending/active/completed)                        │
│ payment_status (pending/completed)                       │
│ created_at                                                │
└───────────────────────────────────────────────────────────┘
                              │
                              │ 1:1
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                         PAYMENTS                             │
├─────────────────────────────────────────────────────────────┤
│ id (PK)                                                      │
│ ride_id (FK) ────────────────────────────────────────────────┘
│ passenger_id (FK)                                            │
│ driver_id (FK)                                               │
│ amount                                                       │
│ payment_method                                               │
│ payment_qr                                                   │
│ upi_id                                                       │
│ status (pending/completed)                                   │
│ transaction_id                                               │
│ paid_at                                                      │
│ created_at                                                   │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                          DRIVERS                             │
├─────────────────────────────────────────────────────────────┤
│ id (PK)                                                      │
│ name                                                         │
│ age                                                          │
│ mobile (UNIQUE)                                              │
│ email (UNIQUE)                                               │
│ vehicle_number                                               │
│ vehicle_type                                                 │
│ rc_number                                                    │
│ password (HASHED)                                            │
│ qr_code (JSON)                                               │
│ profile_image                                                │
│ is_available                                                 │
│ rating                                                       │
│ total_rides                                                  │
│ total_earned                                                 │
│ created_at                                                   │
└─────────────────────────────────────────────────────────────┘
                              │
                              │ 1:N
                              └──────────────────────────────────┐
                                                                 │
┌─────────────────────────────────────────────────────────────┐
│                     OTP_VERIFICATION                         │
├─────────────────────────────────────────────────────────────┤
│ id (PK)                                                      │
│ email                                                        │
│ otp                                                          │
│ expiry_time                                                  │
│ attempts                                                     │
│ created_at                                                   │
└─────────────────────────────────────────────────────────────┘
```

---

## 🔌 API Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      API ENDPOINTS                           │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                    AUTHENTICATION                            │
├─────────────────────────────────────────────────────────────┤
│ POST /api/send_otp                                           │
│ POST /api/verify_otp                                         │
│ POST /api/register_passenger                                 │
│ POST /api/register_driver                                    │
│ POST /api/login_passenger                                    │
│ POST /api/login_driver                                       │
│ POST /api/logout                                             │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                      QR CODE                                 │
├─────────────────────────────────────────────────────────────┤
│ GET  /api/get_driver_qr                                      │
│ POST /api/scan_driver_qr                                     │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                   RIDE MANAGEMENT                            │
├─────────────────────────────────────────────────────────────┤
│ POST /api/start_ride                                         │
│ POST /api/complete_ride                                      │
│ GET  /api/get_active_ride                                    │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                       HISTORY                                │
├─────────────────────────────────────────────────────────────┤
│ GET /api/get_passenger_history                               │
│ GET /api/get_driver_history                                  │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                       PAYMENT                                │
├─────────────────────────────────────────────────────────────┤
│ POST /api/process_payment                                    │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                       PROFILE                                │
├─────────────────────────────────────────────────────────────┤
│ GET /api/get_profile                                         │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                        PAGES                                 │
├─────────────────────────────────────────────────────────────┤
│ GET /                                                        │
│ GET /dashboard/passenger                                     │
│ GET /dashboard/driver                                        │
└─────────────────────────────────────────────────────────────┘
```

---

## 🔐 Security Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    SECURITY LAYERS                           │
└─────────────────────────────────────────────────────────────┘

Layer 1: Authentication
├── Password Hashing (SHA256)
├── OTP Verification (6-digit, 5-min expiry)
└── Session Management (Flask sessions)

Layer 2: Authorization
├── Session Validation
├── User Type Checking (passenger/driver)
└── Route Protection

Layer 3: Data Validation
├── Email Format Validation
├── Phone Number Validation
├── Age Validation (18-70)
└── Input Sanitization

Layer 4: QR Code Security
├── Timestamp Validation
├── Driver ID Verification
├── Data Integrity Check
└── JSON Schema Validation

Layer 5: Payment Security
├── Transaction ID Generation
├── Payment Status Tracking
├── Ride-Payment Linking
└── Duplicate Prevention
```

---

## 💰 Fare Calculation Logic

```
┌─────────────────────────────────────────────────────────────┐
│                  FARE CALCULATION                            │
└─────────────────────────────────────────────────────────────┘

Input:
├── Start Time (from ride record)
├── End Time (current time)
└── Distance (entered by driver)

Calculation:
├── Duration = End Time - Start Time
├── Duration (minutes) = Duration / 60
├── Base Fare = ₹50
├── Distance Charge = Distance × ₹15/km
├── Time Charge = Duration × ₹2/min
└── Total Fare = Base + Distance + Time

Example:
├── Distance: 5 km
├── Duration: 20 minutes
├── Base: ₹50
├── Distance: 5 × ₹15 = ₹75
├── Time: 20 × ₹2 = ₹40
└── Total: ₹50 + ₹75 + ₹40 = ₹165
```

---

## 📱 Frontend Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    FRONTEND STRUCTURE                        │
└─────────────────────────────────────────────────────────────┘

index_enhanced.html
├── Login Forms
│   ├── Passenger Login
│   └── Driver Login
└── Registration Forms
    ├── Passenger Registration
    │   ├── OTP Verification
    │   └── Form Validation
    └── Driver Registration
        ├── OTP Verification
        ├── Vehicle Details
        └── QR Code Generation

dashboard_passenger.html
├── Header (User Info, Stats, Logout)
├── Tabs (Scan QR, History, Profile)
├── Scan QR Section
│   ├── Camera Access
│   ├── QR Scanner (jsQR)
│   ├── Driver Verification Card
│   └── Start Ride Form
├── History Section
│   └── Ride List (with details)
└── Profile Section
    └── Statistics & Info

dashboard_driver.html
├── Header (User Info, Stats, Logout)
├── Tabs (My QR, History, Profile)
├── QR Code Section
│   ├── QR Display
│   ├── Active Ride Management
│   └── Complete Ride Form
├── History Section
│   └── Ride List (with earnings)
└── Profile Section
    └── Performance & Earnings
```

---

## 🔄 State Management

```
┌─────────────────────────────────────────────────────────────┐
│                     STATE FLOW                               │
└─────────────────────────────────────────────────────────────┘

User States:
├── Not Logged In
│   └── Can: Register, Login
├── Logged In (Passenger)
│   ├── No Active Ride
│   │   └── Can: Scan QR, View History, View Profile
│   └── Has Active Ride
│       └── Can: View Ride Details, Wait for Completion
└── Logged In (Driver)
    ├── Available
    │   └── Can: Show QR, View History, View Profile
    └── Busy (Active Ride)
        └── Can: View Ride Details, Complete Ride

Ride States:
├── pending (created, not started)
├── active (in progress)
└── completed (finished)

Payment States:
├── pending (not paid)
└── completed (paid)

Driver Availability:
├── available (can accept rides)
└── busy (has active ride)
```

---

## 🎨 UI Component Hierarchy

```
┌─────────────────────────────────────────────────────────────┐
│                   UI COMPONENTS                              │
└─────────────────────────────────────────────────────────────┘

Common Components:
├── Header
│   ├── Logo
│   ├── User Info
│   └── Logout Button
├── Tabs
│   └── Tab Buttons
├── Message Box
│   ├── Success
│   ├── Error
│   └── Info
└── Forms
    ├── Input Fields
    ├── Buttons
    └── Validation

Passenger Components:
├── QR Scanner
│   ├── Video Element
│   ├── Canvas (hidden)
│   └── Scanner Controls
├── Driver Card
│   ├── Driver Info Grid
│   └── Action Buttons
├── Active Ride Display
│   └── Ride Details
└── History List
    └── Ride Items

Driver Components:
├── QR Display
│   ├── QR Image
│   └── Instructions
├── Active Ride Manager
│   ├── Passenger Info
│   ├── Distance Input
│   └── Complete Button
├── Payment QR Display
│   └── QR Image
└── History List
    └── Ride Items with Earnings
```

---

## 🚀 Deployment Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                  DEPLOYMENT OPTIONS                          │
└─────────────────────────────────────────────────────────────┘

Development (Current):
├── Flask Development Server
├── SQLite Database
├── Local File System
└── Port: 5000

Production (Recommended):
├── WSGI Server (Gunicorn/uWSGI)
├── PostgreSQL/MySQL Database
├── Nginx Reverse Proxy
├── SSL/TLS Certificate
├── Cloud Storage (for QR codes)
└── Domain with HTTPS

Scaling Options:
├── Load Balancer
├── Multiple App Instances
├── Redis for Sessions
├── CDN for Static Files
└── Database Replication
```

---

Made with ❤️ for women's safety
