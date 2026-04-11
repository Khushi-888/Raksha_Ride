# 🚀 Start RakshaRide with New Registration System

## Step-by-Step Guide to Run the Site

---

## ✅ Step 1: Stop Any Running Server

If the server is already running, stop it first:

**Option A: Close the terminal window**
- Find the terminal/command prompt running `python app_enhanced.py`
- Close it

**Option B: Press Ctrl+C**
- In the terminal running the server
- Press `Ctrl + C` to stop

---

## ✅ Step 2: Verify Files Are in Place

Check that these new files exist:

```bash
# Check new templates
dir templates\driver_register_new.html
dir templates\owner_confirm.html
dir templates\driver_upload_docs.html
```

**Expected output:**
```
✅ driver_register_new.html exists
✅ owner_confirm.html exists
✅ driver_upload_docs.html exists
```

---

## ✅ Step 3: Start the Server

Open a new terminal/command prompt and run:

```bash
python app_enhanced.py
```

**Expected output:**
```
[OK] Enhanced database initialized successfully!
======================================================================
  🚗 RakshaRide Enhanced + AI Verification Engine
======================================================================

  📡 Server: http://localhost:5000
  📧 Email: riksharide2026@gmail.com

  ✨ Features:
     • QR Code Scanning
     • Ride Management
     • Payment Integration
     • History Tracking
     • Profile Management
     • Owner/Rent Driver Registration

======================================================================

 * Running on http://127.0.0.1:5000
 * Running on http://192.168.1.7:5000
```

**✅ If you see this, the server is running!**

---

## ✅ Step 4: Open the Website

Open your browser and go to:

```
http://localhost:5000
```

**You should see the RakshaRide homepage**

---

## ✅ Step 5: Test New Driver Registration

### Test Owner Driver Registration:

1. **Click "Enroll as Driver"** button on homepage
   - Or go directly to: `http://localhost:5000/register/driver/new`

2. **Step 1 - Choose Type:**
   - Click "Owner Driver" (🏠 icon)
   - Click "Continue →"

3. **Step 2 - Fill Details:**
   ```
   Full Name: Test Owner
   Age: 30
   Mobile: 9876543210
   Email: testowner@gmail.com
   Vehicle Number: DL01AB1234
   Vehicle Type: Car
   RC Number: RC123456789
   License No.: DL-1234-5678901
   Aadhaar: 1234 5678 9012
   Password: test123
   ```
   - Click "Continue →"

4. **Step 3 - Upload Documents:**
   - Upload Aadhaar Front (any image)
   - Upload Aadhaar Back (any image)
   - Upload Driving License (any image)
   - Upload RC Book (any image)
   - Upload Selfie (any image)
   - Click "📤 Submit Registration"

5. **Step 4 - Success:**
   - You'll see "✅ Registration Submitted!"
   - Check email: testowner@gmail.com for confirmation

---

### Test Rent Driver Registration:

1. **First, create an owner account** (follow steps above)

2. **Start new registration:**
   - Go to: `http://localhost:5000/register/driver/new`
   - Click "Rent Driver" (🔑 icon)
   - Click "Continue →"

3. **Step 2 - Fill Details:**
   ```
   Full Name: Test Rent Driver
   Age: 28
   Mobile: 9876543211
   Email: testrent@gmail.com
   Vehicle Number: DL01AB1234 (same as owner)
   Vehicle Type: Car
   RC Number: RC123456789 (same as owner)
   License No.: DL-9876-5432109
   Aadhaar: 9876 5432 1098
   Password: rent123
   ```
   - Click "Continue →"

4. **Step 3 - Enter Owner Credentials:**
   ```
   Owner's Email: testowner@gmail.com
   Owner's Password: test123
   ```
   - Click "🔍 Verify Owner & Send Request"

5. **Step 4 - Request Sent:**
   - You'll see "📨 Request Sent to Owner!"
   - Owner will receive email with confirmation link

6. **Owner Confirms:**
   - Check owner's email: testowner@gmail.com
   - Click the confirmation link in email
   - Review rent driver details
   - Click "✅ Confirm & Proceed to Document Upload"

7. **Upload Documents:**
   - Document upload page opens automatically
   - Upload all 5 documents
   - Click "📤 Submit Documents for Verification"

8. **Both Get Notified:**
   - Rent driver gets email: "Documents submitted"
   - Owner gets email: "Rent driver submitted documents"
   - After admin verification, both get login credentials

---

## ✅ Step 6: Verify Database

Check that data is saved:

```bash
python check_db.py
```

**Look for:**
```
--- DRIVERS DATA ---
(1, 'Test Owner', 30, '9876543210', 'testowner@gmail.com', ...)
(2, 'Test Rent Driver', 28, '9876543211', 'testrent@gmail.com', ...)

--- DRIVER DOCUMENTS ---
Documents uploaded for driver_id: 1, 2

--- RENTER REQUESTS ---
Request from driver 2 to owner 1: APPROVED
```

---

## 🐛 Troubleshooting

### Issue: Server won't start

**Error:** `Address already in use`

**Solution:**
```bash
# Find and kill the process using port 5000
netstat -ano | findstr :5000
taskkill /PID <PID_NUMBER> /F

# Then start again
python app_enhanced.py
```

---

### Issue: Page not found (404)

**Error:** `404 Not Found` when accessing `/register/driver/new`

**Solution:**
1. Make sure server is running
2. Check terminal for errors
3. Verify files exist:
   ```bash
   dir templates\driver_register_new.html
   ```
4. Restart server:
   ```bash
   # Press Ctrl+C to stop
   python app_enhanced.py
   ```

---

### Issue: Email not sending

**Error:** Owner doesn't receive confirmation email

**Solution:**
1. Check Gmail credentials in `app_enhanced.py` (lines 25-28)
2. Test email system:
   ```bash
   python test_email_quick.py
   ```
3. Check spam folder
4. For testing, you can skip email and directly access:
   ```
   http://localhost:5000/owner/confirm?token=test_123
   ```

---

### Issue: Documents not uploading

**Error:** "Please upload all required documents"

**Solution:**
1. Make sure you select actual image files
2. Check browser console (F12) for errors
3. Try smaller image files (< 5MB each)
4. Supported formats: JPG, PNG, PDF

---

### Issue: Owner verification fails

**Error:** "Owner credentials are incorrect"

**Solution:**
1. Make sure owner account exists first
2. Use exact email and password from owner registration
3. Check database:
   ```bash
   python check_db.py
   ```
4. Look for owner's email in drivers table

---

## 📊 Quick Test Checklist

- [ ] Server starts without errors
- [ ] Homepage loads at http://localhost:5000
- [ ] "Enroll as Driver" button works
- [ ] New registration page loads
- [ ] Can select Owner/Rent type
- [ ] Can fill all form fields
- [ ] Can upload documents (Owner)
- [ ] Can verify owner credentials (Rent)
- [ ] Success page shows after submission
- [ ] Data appears in database

---

## 🎯 URLs to Test

```
Homepage:
http://localhost:5000

New Driver Registration:
http://localhost:5000/register/driver/new

Owner Confirmation (with token):
http://localhost:5000/owner/confirm?token=<TOKEN>

Document Upload (with token):
http://localhost:5000/driver/upload_documents?token=<TOKEN>

Passenger Dashboard:
http://localhost:5000/dashboard/passenger

Driver Dashboard:
http://localhost:5000/dashboard/driver
```

---

## 📧 Email Templates

### Owner Registration Email:
```
Subject: RakshaRide — Registration Received

Hello Test Owner,

Your driver registration has been received successfully.

Details:
  Name          : Test Owner
  Vehicle No.   : DL01AB1234
  RC Number     : RC123456789
  License No.   : DL-1234-5678901
  Unique ID     : DRV-XXXXX

Our team will verify your documents within 24-48 hours.
Once verified, your User ID and Password will be sent to this email.

Thank you,
RakshaRide Team
```

### Rent Driver Request Email (to Owner):
```
Subject: RakshaRide — Rent Driver Request from Test Rent Driver

Hello Test Owner,

A driver wants to register using your vehicle on RakshaRide.

Driver Details:
  Name          : Test Rent Driver
  Mobile        : 9876543211
  Email         : testrent@gmail.com
  Vehicle No.   : DL01AB1234
  RC Number     : RC123456789
  License No.   : DL-9876-5432109
  Aadhaar       : XXXX XXXX 1098

To CONFIRM this request, click the link below:
http://localhost:5000/owner/confirm?token=<TOKEN>

If you did not expect this request, please ignore this email.

Thank you,
RakshaRide Team
```

---

## ✅ Success Indicators

**You'll know it's working when:**

1. ✅ Server starts without errors
2. ✅ New registration page loads
3. ✅ Can complete owner registration
4. ✅ Owner receives confirmation email
5. ✅ Can complete rent driver registration
6. ✅ Owner receives request email with link
7. ✅ Owner can confirm via email link
8. ✅ Document upload page opens
9. ✅ Both parties receive notification emails
10. ✅ Data appears in database

---

## 🎉 You're All Set!

Your RakshaRide system now has:
- ✅ Owner driver registration
- ✅ Rent driver registration
- ✅ Owner verification flow
- ✅ Document upload system
- ✅ Email notifications
- ✅ Database storage
- ✅ View-only access for rent drivers

**Start the server and test it!**

```bash
python app_enhanced.py
```

Then open: http://localhost:5000

---

Made with ❤️ for women's safety
