# 🚀 Quick Start Guide - RakshaRide Enhanced

## ✅ System is Ready!

All files are complete and working. Follow these simple steps:

---

## Step 1: Install Dependencies

Open terminal/command prompt and run:

```bash
pip install -r requirements_enhanced.txt
```

This installs:
- Flask (web framework)
- qrcode (QR code generation)
- Pillow (image processing)
- flask-cors (API support)

---

## Step 2: Start the Server

**Option A: Double-click the batch file**
```
START_ENHANCED_SYSTEM.bat
```

**Option B: Run command**
```bash
python app_enhanced.py
```

You should see:
```
============================================================
  🚗 RakshaRide Enhanced - Complete Ride Sharing Platform
============================================================

  📡 Server: http://localhost:5000
  📧 Email: riksharide2026@gmail.com

  ✨ Features:
     • QR Code Scanning
     • Ride Management
     • Payment Integration
     • History Tracking
     • Profile Management

============================================================

 * Running on http://127.0.0.1:5000
```

---

## Step 3: Open in Browser

Open your web browser and go to:
```
http://localhost:5000
```

You'll see a beautiful dark-themed landing page!

---

## Step 4: Test the System

### Register as Passenger
1. Click "Join Now" button
2. Select "👤 Passenger"
3. Fill in details:
   - Name: Test User
   - Phone: 9999999999
   - Email: test@example.com
   - Password: test123
4. Click "Send OTP"
5. Check console for OTP (also shown in alert)
6. Enter OTP
7. Click "Create Account"

### Register as Driver
1. Click "Join Now" button
2. Select "🚗 Driver Partner"
3. Fill in details:
   - Name: Test Driver
   - Age: 30
   - Mobile: 8888888888
   - Email: driver@example.com
   - Vehicle Type: Car
   - Vehicle Number: DL01AB1234
   - RC Number: RC123456
   - Password: test123
4. Click "Send OTP"
5. Check console for OTP
6. Enter OTP
7. Click "Create Account"

### Login
1. Click "Sign In" button
2. Select role (Passenger or Driver)
3. Enter credentials
4. Click "Sign In"
5. You'll be redirected to dashboard

---

## 🎨 What You'll See

### Landing Page
- Modern dark theme with glassmorphism
- Professional navigation bar
- Elegant form design
- Smooth animations
- Role selector with icons
- Beautiful gradient buttons

### Passenger Dashboard
- QR code scanner
- Driver verification
- Ride management
- History tracking
- Profile statistics

### Driver Dashboard
- QR code display
- Ride completion
- Payment QR generation
- Earnings tracking
- Performance stats

---

## 🐛 Troubleshooting

### Server Won't Start
```bash
# Check if port 5000 is already in use
# On Windows:
netstat -ano | findstr :5000

# Kill the process if needed
taskkill /PID <process_id> /F

# Try again
python app_enhanced.py
```

### Module Not Found Error
```bash
# Reinstall dependencies
pip install -r requirements_enhanced.txt
```

### OTP Not Showing
- Check the console/terminal where server is running
- OTP is printed there
- Also shown in browser alert popup

### Camera Not Working (for QR scanning)
- Allow camera permissions in browser
- Use modern browser (Chrome, Firefox, Edge)
- HTTPS required for production (works on localhost)

---

## 📊 System Features

✅ Registration with OTP verification
✅ Login system (passenger & driver)
✅ QR code generation for drivers
✅ QR code scanning for passengers
✅ Driver verification before ride
✅ Ride start/complete management
✅ Automatic fare calculation
✅ Payment QR generation
✅ Complete ride history
✅ Profile with statistics
✅ Beautiful modern UI

---

## 💡 Quick Tips

1. **OTP Location**: Always check the console where `python app_enhanced.py` is running
2. **Multiple Users**: Open different browsers (Chrome, Firefox) to test passenger and driver simultaneously
3. **Database Reset**: Delete `database_enhanced.db` file to start fresh
4. **Port Change**: Edit `app_enhanced.py` line at bottom to change port from 5000

---

## 🎯 Next Steps

1. ✅ Start server
2. ✅ Register passenger and driver
3. ✅ Login to both accounts
4. ✅ Test QR code scanning
5. ✅ Complete a test ride
6. ✅ Check history on both sides

---

## 📞 Need Help?

Check these files:
- **COMPLETE_USER_GUIDE.md** - Detailed instructions
- **SYSTEM_COMPLETE_SUMMARY.md** - System overview
- **QUICK_REFERENCE.md** - Quick reference card

---

## ✅ Verification Checklist

Before using, verify:
- [ ] Python 3.7+ installed
- [ ] Dependencies installed (`pip install -r requirements_enhanced.txt`)
- [ ] Port 5000 available
- [ ] Modern web browser available
- [ ] Camera access (for QR scanning)

---

**Everything is ready! Start the server and enjoy your complete ride-sharing platform!**

Made with ❤️ for women's safety
