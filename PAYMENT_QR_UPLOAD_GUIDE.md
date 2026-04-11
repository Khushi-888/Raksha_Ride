# 💳 Payment QR Upload Feature - Complete Guide

## ✅ NEW FEATURE IMPLEMENTED!

Drivers can now upload their own UPI payment QR code, and passengers will see that actual QR when paying after rides.

---

## 🎯 How It Works

### For Drivers:

**Step 1: Upload Payment QR**
1. Login as Driver
2. Click "💳 Payment QR" tab in dashboard
3. Click "📁 Choose Image"
4. Select your UPI payment QR screenshot
5. Preview appears
6. Click "💾 Save to Account"
7. ✅ Payment QR saved to database!

**Step 2: QR Status**
- If uploaded: Shows "✅ Active Payment QR" with your QR image
- If not uploaded: Shows "⚠️ No Payment QR Uploaded" warning

### For Passengers:

**Step 1: Complete Ride**
1. During active ride
2. Click "✅ Finish Ride & Pay" button
3. Enter distance traveled (e.g., 5 km)
4. Fare calculated automatically

**Step 2: Payment Modal**
- Modal appears with:
  - Ride summary (distance, duration, fare)
  - Driver's uploaded payment QR image ✅
  - "Scan to Pay" instructions

**Step 3: Pay**
1. Scan QR with any UPI app (GPay, PhonePe, Paytm)
2. Payment details auto-filled
3. Complete payment
4. Click "✅ Payment Done"

---

## 🗄️ Database Schema

### Drivers Table (Updated)
```sql
ALTER TABLE drivers ADD COLUMN payment_qr_image TEXT;
```

**Field:**
- `payment_qr_image` - Stores base64 encoded image data (data URI format)

**Example Data:**
```
payment_qr_image: "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAA..."
```

---

## 🔌 API Endpoints

### 1. Upload Payment QR (Driver Only)
```
POST /api/upload_payment_qr
```

**Request:**
```json
{
  "qr_image": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAA..."
}
```

**Response:**
```json
{
  "success": true,
  "message": "Payment QR saved successfully!"
}
```

**Authentication:** Requires driver session

---

### 2. Get Own Payment QR (Driver Only)
```
GET /api/get_payment_qr
```

**Response:**
```json
{
  "success": true,
  "payment_qr_image": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAA...",
  "upi_id": "driver@paytm",
  "driver_name": "Rajesh Kumar"
}
```

**Authentication:** Requires driver session

---

### 3. Get Driver Payment QR (Public - For Passengers)
```
GET /api/get_driver_payment_qr?driver_id=2
```

**Response:**
```json
{
  "success": true,
  "payment_qr_image": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAA...",
  "upi_id": "driver@paytm",
  "driver_name": "Rajesh Kumar"
}
```

**Authentication:** None required (public endpoint for payment)

---

## 📱 Complete User Flow

### Driver Flow:

```
┌─────────────────────────────────────────────────────────────┐
│                    DRIVER UPLOADS PAYMENT QR                 │
└─────────────────────────────────────────────────────────────┘

1. Driver logs in
         ↓
2. Goes to "💳 Payment QR" tab
         ↓
3. Sees current status:
   - ✅ Active QR (if uploaded)
   - ⚠️ No QR (if not uploaded)
         ↓
4. Clicks "📁 Choose Image"
         ↓
5. Selects UPI QR screenshot from phone/computer
         ↓
6. Preview appears
         ↓
7. Clicks "💾 Save to Account"
         ↓
8. API Call: POST /api/upload_payment_qr
         ↓
9. Database Updated:
   ┌──────────────────────────────────────┐
   │ drivers table                        │
   │ id: 2                                │
   │ payment_qr_image: [base64 data]     │ ✅ SAVED
   └──────────────────────────────────────┘
         ↓
10. Success message: "✅ Payment QR saved successfully!"
         ↓
11. QR now shows as "Active"
```

### Passenger Flow:

```
┌─────────────────────────────────────────────────────────────┐
│                PASSENGER COMPLETES RIDE & PAYS               │
└─────────────────────────────────────────────────────────────┘

1. Passenger in active ride
         ↓
2. Clicks "✅ Finish Ride & Pay"
         ↓
3. Enters distance: 5 km
         ↓
4. API Call: POST /api/complete_ride
         ↓
5. Fare calculated: ₹168
         ↓
6. API Call: GET /api/get_driver_payment_qr?driver_id=2
         ↓
7. Driver's payment QR retrieved from database
         ↓
8. Payment Modal Opens:
   ┌──────────────────────────────────────┐
   │ 💳 Payment                           │
   │                                      │
   │ Distance: 5 km                       │
   │ Duration: 20 min                     │
   │ Total Fare: ₹168                     │
   │                                      │
   │ Scan to Pay:                         │
   │ [Driver's Uploaded QR Image] ✅      │
   │                                      │
   │ [✅ Payment Done]                    │
   └──────────────────────────────────────┘
         ↓
9. Passenger scans QR with GPay/PhonePe
         ↓
10. Payment completed
         ↓
11. Clicks "✅ Payment Done"
         ↓
12. Modal closes
         ↓
13. Ride completed! ✅
```

---

## 🎨 UI Features

### Driver Dashboard - Payment QR Tab

**Active QR Display:**
```
┌─────────────────────────────────────────┐
│ ✅ Active Payment QR                    │
│                                         │
│ [QR Code Image]                         │
│                                         │
│ Passengers will see this QR when       │
│ paying you after rides.                 │
└─────────────────────────────────────────┘
```

**Upload Section:**
```
┌─────────────────────────────────────────┐
│ 📤 Upload New Payment QR                │
│                                         │
│ [📁 Choose Image]                       │
│                                         │
│ Preview:                                │
│ [Selected Image]                        │
│                                         │
│ [💾 Save to Account] [❌ Cancel]        │
└─────────────────────────────────────────┘
```

**Instructions:**
```
┌─────────────────────────────────────────┐
│ 📱 How to Get Your UPI Payment QR       │
│                                         │
│ 1. Open your UPI app                    │
│ 2. Go to "Receive Money"                │
│ 3. Take screenshot of QR                │
│ 4. Upload it here                       │
│ 5. Passengers will see this QR          │
└─────────────────────────────────────────┘
```

### Passenger Dashboard - Payment Modal

```
┌─────────────────────────────────────────┐
│ 💳 Payment                              │
│                                         │
│ ┌─────────────────────────────────────┐ │
│ │ Distance: 5 km                      │ │
│ │ Duration: 20 min                    │ │
│ │ ─────────────────────────────────── │ │
│ │ Total Fare: ₹168                    │ │
│ └─────────────────────────────────────┘ │
│                                         │
│ Scan to Pay                             │
│                                         │
│ [Driver's Uploaded QR Image]            │
│                                         │
│ Scan this QR code with any UPI app      │
│                                         │
│ [✅ Payment Done]                       │
└─────────────────────────────────────────┘
```

---

## 🧪 Testing Guide

### Test 1: Driver Uploads Payment QR

**Steps:**
1. Start server: `python app_enhanced.py`
2. Open: http://localhost:5000
3. Login as driver
4. Click "💳 Payment QR" tab
5. Click "📁 Choose Image"
6. Select any QR code image
7. Preview appears
8. Click "💾 Save to Account"

**Expected Result:**
```
✅ Payment QR saved successfully!
✅ Active Payment QR section shows your image
```

**Verify in Database:**
```bash
python check_db.py
```

Look for `payment_qr_image` field in drivers table with base64 data.

---

### Test 2: Passenger Sees Driver's QR

**Steps:**
1. Login as passenger
2. Scan driver QR and start ride
3. Click "✅ Finish Ride & Pay"
4. Enter distance: 5
5. Payment modal opens

**Expected Result:**
```
✅ Modal shows:
   - Fare: ₹168
   - Driver's uploaded QR image
   - "Scan to Pay" text
```

**If Driver Hasn't Uploaded QR:**
```
⚠️ Modal shows:
   - Fare: ₹168
   - Warning: "Driver hasn't uploaded payment QR yet"
   - "Please pay via cash or ask driver for UPI ID"
```

---

### Test 3: Complete Payment Flow

**Steps:**
1. Complete Test 1 (driver uploads QR)
2. Complete Test 2 (passenger starts ride)
3. Passenger clicks "Finish Ride & Pay"
4. Payment modal shows driver's QR
5. Scan QR with real UPI app (GPay/PhonePe)
6. Payment details auto-filled
7. Complete payment
8. Click "✅ Payment Done"

**Expected Result:**
```
✅ Payment modal closes
✅ Ride marked as completed
✅ Passenger dashboard refreshes
```

---

## 🔧 Technical Implementation

### Frontend (Driver Dashboard)

**File:** `templates/dashboard_driver_beautiful.html`

**Key Functions:**
```javascript
// Load current payment QR
async function loadPaymentQR()

// Preview selected image
function previewPaymentQR(event)

// Upload to server
async function uploadPaymentQR()

// Cancel upload
function cancelUpload()
```

**File Upload:**
```javascript
<input type="file" id="payment-qr-input" accept="image/*" onchange="previewPaymentQR(event)">
```

**Image Preview:**
```javascript
const reader = new FileReader();
reader.onload = function(e) {
    document.getElementById('preview-image').src = e.target.result;
};
reader.readAsDataURL(file);
```

---

### Frontend (Passenger Dashboard)

**File:** `templates/dashboard_passenger_beautiful.html`

**Key Functions:**
```javascript
// Finish ride and show payment
async function finishRide(rideId)

// Cancel ride
async function cancelRide(rideId)

// Show payment modal with driver's QR
async function showPaymentModal(ride)

// Close payment modal
function closePaymentModal()
```

**Payment Modal:**
```javascript
// Fetch driver's payment QR
const response = await fetch(`/api/get_driver_payment_qr?driver_id=${driver_id}`);

// Display in modal
modal.innerHTML = `
    <img src="${data.payment_qr_image}">
    <p>Scan to pay ₹${fare}</p>
`;
```

---

### Backend (Flask APIs)

**File:** `app_enhanced.py`

**Upload Payment QR:**
```python
@app.route('/api/upload_payment_qr', methods=['POST'])
def upload_payment_qr():
    qr_image = data.get('qr_image')  # base64 data URI
    driver_id = session['user_id']
    
    c.execute('UPDATE drivers SET payment_qr_image = ? WHERE id = ?', 
              (qr_image, driver_id))
    
    return jsonify({"success": True})
```

**Get Payment QR (Driver):**
```python
@app.route('/api/get_payment_qr', methods=['GET'])
def get_payment_qr():
    driver_id = session['user_id']
    
    c.execute('SELECT payment_qr_image FROM drivers WHERE id = ?', 
              (driver_id,))
    
    return jsonify({"payment_qr_image": result[0]})
```

**Get Payment QR (Public):**
```python
@app.route('/api/get_driver_payment_qr', methods=['GET'])
def get_driver_payment_qr():
    driver_id = request.args.get('driver_id')
    
    c.execute('SELECT payment_qr_image FROM drivers WHERE id = ?', 
              (driver_id,))
    
    return jsonify({"payment_qr_image": result[0]})
```

---

## ✅ Feature Checklist

### Driver Side
- [x] Payment QR tab in dashboard
- [x] Upload QR image functionality
- [x] Image preview before upload
- [x] Save to database
- [x] Display current active QR
- [x] Status indicators (Active/Not Uploaded)
- [x] Instructions for getting UPI QR

### Passenger Side
- [x] "Finish Ride & Pay" button
- [x] "Cancel Ride" button
- [x] Distance input prompt
- [x] Fare calculation
- [x] Payment modal
- [x] Driver's QR display in modal
- [x] Fallback message if no QR
- [x] "Payment Done" button

### Backend
- [x] Database field: payment_qr_image
- [x] API: Upload payment QR
- [x] API: Get own payment QR
- [x] API: Get driver payment QR (public)
- [x] Base64 image storage
- [x] Session authentication
- [x] Error handling

---

## 🎉 Summary

**New Feature Complete!**

✅ Drivers can upload their UPI payment QR
✅ QR saved to database as base64 image
✅ Passengers see driver's actual QR when paying
✅ Payment modal with fare breakdown
✅ Finish ride and cancel ride options
✅ Complete payment flow working

**Benefits:**
- No manual UPI ID entry needed
- Passengers scan actual driver's QR
- Faster payment process
- Professional payment experience
- All data tracked in database

**Ready to use!** 🚀

---

Made with ❤️ for women's safety
