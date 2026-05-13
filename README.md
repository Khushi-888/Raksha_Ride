# 🛡️ RakshaRide — Safe Verified Ride Sharing

Live at: **https://raksharide.onrender.com**

## Features
- Driver/Passenger registration with OTP email verification
- Owner/Rent driver flow with document upload
- QR code per driver for passenger scanning
- Real-time GPS tracking
- SOS emergency alert system
- JWT authentication
- Admin panel with DB viewer (manual refresh, edit/delete)

## Run Locally

```bash
pip install -r requirements.txt
python app_enhanced.py
```

Open: http://localhost:5000

## Admin Panel
- URL: http://localhost:5000/admin
- Username: `admin`
- Password: `admin@RakshaRide2024`

## Deploy on Render
Render auto-detects `Procfile` and deploys automatically on push to GitHub.

## Environment Variables (Render)
| Variable | Value |
|---|---|
| `SECRET_KEY` | any random string |
| `GMAIL_EMAIL` | riksharide2026@gmail.com |
| `GMAIL_APP_PASSWORD` | evsztunveoqilawu |
| `FLASK_ENV` | production |
| `APP_URL` | https://raksharide.onrender.com |
