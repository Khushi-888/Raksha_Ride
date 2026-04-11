# 🚀 RakshaRide Enhanced - Quick Reference Card

## ⚡ Quick Start (30 seconds)

```bash
# 1. Install
pip install -r requirements_enhanced.txt

# 2. Run
python app_enhanced.py

# 3. Open
http://localhost:5000
```

---

## 📱 Key Features

| Feature | Passenger | Driver |
|---------|-----------|--------|
| QR Code | Scan ✅ | Display ✅ |
| Ride Start | Yes ✅ | Notified ✅ |
| Ride Complete | Notified ✅ | Yes ✅ |
| Payment | Scan QR ✅ | Show QR ✅ |
| History | View ✅ | View ✅ |
| Profile | Stats ✅ | Earnings ✅ |

---

## 🔑 Important URLs

| Page | URL |
|------|-----|
| Homepage | `http://localhost:5000` |
| Passenger Dashboard | `http://localhost:5000/dashboard/passenger` |
| Driver Dashboard | `http://localhost:5000/dashboard/driver` |

---

## 💰 Fare Formula

```
Fare = ₹50 + (Distance × ₹15) + (Minutes × ₹2)
```

**Example:** 5km, 20min = ₹165

---

## 🔄 Ride Flow (Simple)

```
1. Passenger scans Driver QR
2. Passenger starts ride
3. Driver completes ride
4. System calculates fare
5. Passenger pays via QR
6. Saved in history
```

---

## 📊 API Quick Reference

### Authentication
```
POST /api/send_otp
POST /api/verify_otp
POST /api/register_passenger
POST /api/register_driver
POST /api/login_passenger
POST /api/login_driver
POST /api/logout
```

### Ride Management
```
GET  /api/get_driver_qr
POST /api/scan_driver_qr
POST /api/start_ride
POST /api/complete_ride
GET  /api/get_active_ride
```

### History & Profile
```
GET /api/get_passenger_history
GET /api/get_driver_history
GET /api/get_profile
POST /api/process_payment
```

---

## 🗄️ Database Tables

| Table | Purpose |
|-------|---------|
| passengers | Passenger accounts |
| drivers | Driver accounts + QR |
| rides | All ride records |
| payments | Payment transactions |
| otp_verification | OTP codes |

---

## 🎯 Common Tasks

### Register New User
1. Click "Register"
2. Choose Passenger/Driver
3. Fill form
4. Click "Send OTP"
5. Check console for OTP
6. Enter OTP
7. Click "Register"

### Start a Ride
1. Login as passenger
2. Click "Start Scanner"
3. Scan driver QR
4. Verify details
5. Click "Start Ride"

### Complete a Ride
1. Driver sees active ride
2. Enter distance (km)
3. Click "Complete Ride"
4. Show payment QR

### View History
1. Go to "History" tab
2. See all past rides
3. Check payment status

---

## 🐛 Quick Fixes

| Problem | Solution |
|---------|----------|
| Camera not working | Allow permissions |
| OTP not received | Check console |
| QR not scanning | Better lighting |
| Login failed | Check credentials |

---

## 📁 File Structure

```
raksharide/
├── app_enhanced.py              # Backend
├── requirements_enhanced.txt    # Dependencies
├── templates/
│   ├── index_enhanced.html      # Landing
│   ├── dashboard_passenger.html # Passenger
│   └── dashboard_driver.html    # Driver
├── database_enhanced.db         # Database
└── START_ENHANCED_SYSTEM.bat    # Quick start
```

---

## 🔐 Security Features

- ✅ Password hashing (SHA256)
- ✅ OTP verification (6-digit)
- ✅ Session management
- ✅ QR validation
- ✅ Transaction tracking

---

## 💡 Pro Tips

### For Passengers
- Always verify driver before ride
- Enter locations for better tracking
- Keep payment ready

### For Drivers
- Keep QR code visible
- Enter accurate distance
- Complete rides promptly

---

## 📊 System Stats

| Metric | Value |
|--------|-------|
| Total Files | 8 |
| Lines of Code | 2500+ |
| API Endpoints | 20+ |
| Database Tables | 5 |
| Features | 15+ |

---

## 🎉 Status

**Backend:** ✅ 100% Complete  
**Frontend:** ✅ 100% Complete  
**Documentation:** ✅ 100% Complete  

---

## 📞 Quick Help

### OTP Issues
```
Check console output:
python app_enhanced.py

OTP will be printed there
```

### Camera Issues
```
Browser settings → Allow camera
Use Chrome/Firefox/Edge
```

### Database Reset
```
Delete: database_enhanced.db
Run: python app_enhanced.py
(Creates fresh database)
```

---

## 🚀 Next Steps

1. ✅ Run system
2. ✅ Register users
3. ✅ Test QR scanning
4. ✅ Complete test ride
5. ✅ Check history

---

## 📖 Full Documentation

- **README_ENHANCED.md** - Overview
- **COMPLETE_USER_GUIDE.md** - Detailed guide
- **SYSTEM_COMPLETE_SUMMARY.md** - Summary
- **SYSTEM_ARCHITECTURE.md** - Architecture

---

## ⚡ One-Line Commands

```bash
# Install
pip install -r requirements_enhanced.txt

# Run
python app_enhanced.py

# Test
python test_enhanced_system.py
```

---

Made with ❤️ for women's safety
