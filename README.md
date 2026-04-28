# 🛡️ RakshaRide — Safe Ride Sharing Platform

A complete ride-sharing safety platform built with Flask + SQLite, deployed on Render.

## 🌐 Live Site
**https://raksharide.onrender.com**

## 📁 Project Structure

```
RakshaRide/
├── frontend/
│   ├── templates/          ← HTML pages (Jinja2)
│   └── static/             ← CSS, JS, images
├── backend/
│   ├── app_enhanced.py     ← Flask app (all routes)
│   ├── auth_utils.py       ← JWT authentication
│   ├── wsgi.py             ← Production entry point
│   └── requirements.txt    ← Dependencies
└── database/
    └── database_enhanced.db ← SQLite (auto-created)
```

> Note: Flask requires `templates/` and `static/` at root level for deployment.
> See `PROJECT_STRUCTURE.md` for full documentation.

## ✨ Features

### For Passengers
- Register with OTP email verification
- Scan driver QR code to connect
- Live GPS tracking on OpenStreetMap
- Set pickup & dropoff locations
- Geofencing alerts (arrival notifications)
- SOS emergency alert with GPS location
- Payment via driver's QR code

### For Drivers
- Register as Owner or Rent driver
- Upload documents (Aadhaar, License, RC)
- Unique QR code generated automatically
- Live GPS tracking with Kalman filter
- Payment QR upload
- Ride history & earnings

### For Admin
- Driver verification panel
- View all passengers, rides, SOS alerts
- Approve/reject driver documents
- Live database viewer

## 🔧 Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python Flask |
| Database | SQLite (WAL mode) |
| Frontend | HTML + CSS + Vanilla JS |
| Maps | Leaflet.js + OpenStreetMap |
| Email | Brevo API (HTTP) |
| Auth | JWT + Flask Sessions |
| GPS | Kalman Filter + Haversine |
| Hosting | Render (free tier) |

## 🚀 Run Locally

```bash
pip install -r requirements.txt
python app_enhanced.py
```

Open: http://localhost:5000

## 🔑 Admin Login
- URL: `/admin`
- Username: `admin`
- Password: `RakshaAdmin@2024#Secure!`

## 📧 Environment Variables

```env
BREVO_API_KEY=your_key
GMAIL_EMAIL=your@gmail.com
GMAIL_APP_PASSWORD=your_app_password
SECRET_KEY=your_secret
ADMIN_PASSWORD=your_admin_password
DB_PATH=/var/data/database_enhanced.db
```

## 📖 Full Documentation
See [PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md)
