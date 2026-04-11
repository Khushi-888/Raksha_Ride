# 🚗 RakshaRide Enhanced - Complete User Guide

## 🎉 System Overview

RakshaRide is now a complete ride-sharing platform with QR code scanning, ride management, payment integration, and history tracking!

---

## 🚀 Quick Start

### Step 1: Install Dependencies
```bash
pip install -r requirements_enhanced.txt
```

### Step 2: Start the Server
**Option A: Double-click the batch file**
```
START_ENHANCED_SYSTEM.bat
```

**Option B: Run manually**
```bash
python app_enhanced.py
```

### Step 3: Open in Browser
```
http://localhost:5000
```

---

## 👤 For Passengers

### Registration
1. Click "Register" on homepage
2. Select "Passenger" tab
3. Fill in your details:
   - Name
   - Phone number
   - Email
   - Password (6+ characters)
4. Click "Send OTP"
5. Check console or email for OTP code
6. Enter OTP and click "Register"

### Login
1. Enter email or phone
2. Enter password
3. Click "Login as Passenger"

### Scanning Driver QR Code
1. Go to "Scan QR" tab
2. Click "Start Scanner"
3. Allow camera access
4. Point camera at driver's QR code
5. System automatically scans and verifies driver

### Verifying Driver Details
After scanning, you'll see:
- Driver name
- Mobile number
- Vehicle number
- Vehicle type
- Rating (⭐ out of 5)
- Total rides completed

### Starting a Ride
1. Review driver details
2. (Optional) Enter pickup location
3. (Optional) Enter dropoff location
4. Click "Start Ride"
5. Ride begins!

### During the Ride
- You'll see active ride information
- Driver details displayed
- Start time shown
- Wait for driver to complete the ride

### After Ride Completion
- Driver completes the ride
- System calculates fare automatically
- Payment QR code generated
- Scan QR to pay (or pay cash)

### Viewing Ride History
1. Go to "Ride History" tab
2. See all your past rides:
   - Driver name and vehicle
   - Date and time
   - Duration and distance
   - Fare amount
   - Payment status
   - Pickup/dropoff locations

### Viewing Profile
1. Go to "Profile" tab
2. See your information:
   - Personal details
   - Total rides taken
   - Total amount spent
   - Member since date

---

## 🚗 For Drivers

### Registration
1. Click "Register" on homepage
2. Select "Driver" tab
3. Fill in your details:
   - Name
   - Age (18-70)
   - Mobile number
   - Email
   - Vehicle type (Car/Auto/Bike)
   - Vehicle number
   - RC number
   - Password (6+ characters)
4. Click "Send OTP"
5. Check console or email for OTP code
6. Enter OTP and click "Register"
7. System generates your unique QR code

### Login
1. Enter email
2. Enter password
3. Click "Login as Driver"

### Your QR Code
1. Go to "My QR Code" tab
2. Your unique QR code is displayed
3. Show this to passengers
4. They scan it to start a ride

### When Passenger Scans Your QR
- System verifies your identity
- Passenger sees your details
- They can start the ride
- You'll see active ride notification

### During Active Ride
You'll see:
- Passenger name and contact
- Pickup location
- Dropoff location
- Start time
- Distance input field

### Completing a Ride
1. Enter distance traveled (in KM)
   - Default: 5 km if not entered
2. Click "Complete Ride"
3. System calculates fare:
   - Base fare: ₹50
   - Per KM: ₹15
   - Per minute: ₹2
4. Payment QR code generated
5. Show QR to passenger for payment

### Fare Calculation Example
```
Distance: 5 km
Duration: 20 minutes
Fare = ₹50 + (5 × ₹15) + (20 × ₹2)
Fare = ₹50 + ₹75 + ₹40
Fare = ₹165
```

### Viewing Ride History
1. Go to "Ride History" tab
2. See all your completed rides:
   - Passenger name and contact
   - Date and time
   - Duration and distance
   - Earnings
   - Payment status
   - Pickup/dropoff locations

### Viewing Profile
1. Go to "Profile" tab
2. See your information:
   - Personal details
   - Vehicle information
   - Rating (⭐ out of 5)
   - Total rides completed
   - Total earnings
   - Average per ride
   - Member since date

---

## 💰 Payment System

### How It Works
1. Driver completes ride
2. System calculates fare
3. Payment QR code generated
4. Passenger scans QR code
5. Payment processed
6. Both histories updated

### Payment Methods
- QR Code (primary)
- Cash (manual confirmation)
- UPI (future enhancement)

---

## 📱 Features Summary

### ✅ Passenger Features
- QR code scanner with camera
- Driver verification before ride
- Start ride with locations
- Active ride tracking
- Complete ride history
- Payment QR scanning
- Profile with statistics

### ✅ Driver Features
- Unique QR code generation
- Active ride management
- Complete ride with distance
- Automatic fare calculation
- Payment QR for receiving
- Complete ride history
- Profile with earnings

### ✅ System Features
- Secure authentication
- OTP verification
- Session management
- Real-time ride status
- Automatic fare calculation
- Payment tracking
- History for both parties
- Profile statistics

---

## 🔧 Technical Details

### Database Tables
1. **passengers** - Passenger accounts
2. **drivers** - Driver accounts
3. **otp_verification** - OTP codes
4. **rides** - All ride records
5. **payments** - Payment transactions

### API Endpoints (20+)
- Authentication (7 endpoints)
- QR Code (2 endpoints)
- Ride Management (3 endpoints)
- History (3 endpoints)
- Payment (1 endpoint)
- Profile (2 endpoints)

### Security Features
- Password hashing (SHA256)
- Session management
- OTP verification
- QR code validation
- Transaction tracking

---

## 🐛 Troubleshooting

### Camera Not Working
- Allow camera permissions in browser
- Use HTTPS for production
- Check browser compatibility

### OTP Not Received
- Check console for OTP code
- OTP displayed in browser alert
- Gmail setup optional (system works without it)

### QR Code Not Scanning
- Ensure good lighting
- Hold camera steady
- QR code should be clear and visible
- Try refreshing the page

### Ride Not Starting
- Verify driver is available
- Check if you have active ride
- Ensure QR code is valid

### Payment Issues
- Verify ride is completed
- Check payment QR code
- Confirm transaction ID

---

## 📊 System Status

### ✅ Fully Implemented
- Registration & Login
- OTP Verification
- QR Code Generation
- QR Code Scanning
- Ride Management
- Fare Calculation
- Payment QR
- History Tracking
- Profile Management

### 🔄 Optional Enhancements
- Gmail SMTP (works without it)
- Real-time GPS tracking
- Rating system
- Push notifications
- Advanced analytics

---

## 💡 Tips for Best Experience

### For Passengers
1. Always verify driver details before starting ride
2. Enter pickup/dropoff locations for better tracking
3. Keep payment ready after ride
4. Check ride history regularly

### For Drivers
1. Keep QR code visible and clear
2. Enter accurate distance for fair pricing
3. Complete rides promptly
4. Track your earnings in profile

---

## 🎯 Next Steps

### Immediate Use
1. Register as passenger or driver
2. Test QR code scanning
3. Complete a test ride
4. Check history and profile

### Future Enhancements
- Real-time location tracking
- In-app chat
- Rating and reviews
- Multiple payment methods
- Advanced analytics dashboard

---

## 📞 Support

### Common Issues
- OTP: Check console output
- Camera: Allow browser permissions
- Login: Verify credentials
- QR: Ensure good lighting

### System Requirements
- Python 3.7+
- Modern web browser
- Camera access (for scanning)
- Internet connection

---

## 🎉 Success!

Your RakshaRide Enhanced system is now fully operational with:
- ✅ Complete passenger dashboard
- ✅ Complete driver dashboard
- ✅ QR code system
- ✅ Ride management
- ✅ Payment integration
- ✅ History tracking
- ✅ Profile management

**Start using the system now!**

Run: `python app_enhanced.py`
Open: `http://localhost:5000`

---

Made with ❤️ for women's safety
