# 🛡️ RakshaRide — Safe Verified Ride Sharing

A full-stack ride-sharing platform built with Flask + SQLite.

## Features
- Driver/Passenger registration with OTP email verification
- Document upload & verification system
- QR code per driver for passenger scanning
- Real-time GPS tracking
- SOS emergency alert system
- JWT authentication
- Admin panel

## Run Locally

```bash
pip install -r requirements.txt
python app_enhanced.py
```

Open: http://localhost:5000

## Deploy on Render

1. Push this repo to GitHub
2. Go to [render.com](https://render.com) → New Web Service
3. Connect your GitHub repo
4. Render auto-detects `Procfile` and deploys

## Environment Variables (set in Render dashboard)

| Variable | Value |
|---|---|
| `SECRET_KEY` | any random string |
| `GMAIL_EMAIL` | your gmail |
| `GMAIL_APP_PASSWORD` | gmail app password |
| `FLASK_ENV` | production |
