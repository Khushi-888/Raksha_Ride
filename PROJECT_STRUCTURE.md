# RakshaRide — Professional Project Structure

## 📁 Folder Organization

```
RakshaRide/
│
├── 📂 frontend/                 ← All UI (HTML, CSS, JS)
│   ├── templates/               ← Jinja2 HTML templates
│   └── static/                  ← CSS, JS, images
│
├── 📂 backend/                  ← Server & API
│   ├── app_enhanced.py          ← Main Flask application
│   ├── auth_utils.py            ← JWT authentication
│   ├── wsgi.py                  ← Production server entry
│   └── requirements.txt         ← Python dependencies
│
└── 📂 database/                 ← Data layer
    └── database_enhanced.db     ← SQLite (auto-created on startup)
```

---

## 🌐 Frontend (`templates/` + `static/`)

### Key Pages
| File | Purpose |
|---|---|
| `templates/index.html` | Landing page — Driver/Passenger boxes |
| `templates/dashboard_driver_new.html` | Driver dashboard (GPS, QR, docs, payment) |
| `templates/dashboard_passenger_new.html` | Passenger dashboard (scan, track, SOS) |
| `templates/login_govt.html` | Login page (driver + passenger) |
| `templates/register_govt.html` | Passenger registration |
| `templates/driver_register_new.html` | Driver registration (Owner + Rent) |
| `templates/driver_upload_docs.html` | Document upload after registration |
| `templates/owner_confirm.html` | Owner approves rent driver |
| `templates/admin_dashboard.html` | Admin panel (drivers, passengers, rides, SOS) |
| `templates/db_viewer.html` | Live database viewer (admin only) |

### CSS Files
| File | Purpose |
|---|---|
| `static/css/raksharide.css` | Main design system (colors, components, responsive) |
| `static/css/theme.css` | Dark/light theme variables |
| `static/css/main.css` | Additional styles |

### JS Files
| File | Purpose |
|---|---|
| `static/js/auth.js` | JWT token storage + `authFetch()` wrapper |

---

## ⚙️ Backend (`app_enhanced.py` + `auth_utils.py`)

### Main App: `app_enhanced.py`
Single Flask file with all routes organized by section:

| Section | Routes | Purpose |
|---|---|---|
| Auth | `/api/send_otp`, `/api/verify_otp`, `/api/login_driver`, `/api/login_passenger` | OTP + password login |
| Registration | `/api/register_driver_v2`, `/api/register_passenger` | User registration |
| Driver | `/api/driver_profile`, `/api/toggle_availability`, `/api/update_driver_profile` | Driver management |
| Passenger | `/api/passenger_profile`, `/api/update_passenger_profile` | Passenger management |
| Rides | `/api/start_ride`, `/api/complete_ride`, `/api/get_active_ride` | Ride lifecycle |
| GPS | `/api/update_location`, `/api/get_driver_location`, `/api/nearby_drivers` | Real-time tracking |
| Geofencing | `/api/set_geofence`, `/api/check_geofence`, `/api/clear_geofence` | Zone alerts |
| Payment | `/api/get_payment_qr`, `/api/update_payment_qr`, `/api/confirm_payment`, `/api/driver_confirm_payment` | Payment flow |
| SOS | `/api/sos_alert`, `/api/update_emergency_contact` | Emergency system |
| Documents | `/api/get_driver_documents`, `/api/owner/upload_doc`, `/api/owner/delete_doc` | Document management |
| Admin | `/api/admin/login`, `/api/admin/pending_drivers`, `/api/admin/approve_driver` | Admin operations |
| Password | `/api/forgot_password_otp`, `/api/reset_password` | Password recovery |

### Auth Utils: `auth_utils.py`
- `generate_token(user_id, user_type, name)` — creates JWT
- `get_current_user()` — reads JWT from header OR Flask session
- `require_auth(user_type)` — route decorator

---

## 🗄️ Database (`database_enhanced.db`)

### Tables
| Table | Purpose |
|---|---|
| `drivers` | Driver accounts, vehicle info, GPS, QR code |
| `passengers` | Passenger accounts, emergency contacts |
| `rides` | All ride records with fare, distance, status |
| `driver_documents` | Uploaded docs (base64 stored) |
| `live_locations` | Real-time GPS (Kalman filtered) |
| `otp_verification` | OTP codes with expiry |
| `renter_requests` | Owner-renter approval flow |
| `payments` | Payment records |
| `sos_alerts` | SOS alert history with GPS |
| `admins` | Admin accounts |
| `ratings` | Driver ratings |

---

## 🚀 Deployment

**Live URL:** https://raksharide.onrender.com  
**GitHub:** https://github.com/Khushi-888/Raksha_Ride  
**Platform:** Render (free tier)  
**Server:** Gunicorn + Flask  
**DB:** SQLite (set `DB_PATH=/var/data/database_enhanced.db` + Render Disk for persistence)

### Environment Variables (set in Render)
```
BREVO_API_KEY=your_brevo_key        # Email sending
GMAIL_EMAIL=riksharide2026@gmail.com
GMAIL_APP_PASSWORD=your_app_password
SECRET_KEY=your_secret_key
ADMIN_PASSWORD=RakshaAdmin@2024#Secure!
DB_PATH=/var/data/database_enhanced.db  # Persistent disk
```

---

## 🔑 Admin Access
- URL: https://raksharide.onrender.com/admin
- Username: `admin`
- Password: `RakshaAdmin@2024#Secure!`
