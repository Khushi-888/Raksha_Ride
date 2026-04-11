# 🔑 Generate New Gmail App Password

## ❌ Current Issue

The App Password `evsz tunv eoqi lawu` is currently working.

Error: `Username and Password not accepted`

---

## ✅ Solution: Generate Fresh App Password

Follow these exact steps:

### Step 1: Enable 2-Step Verification (If Not Already)

1. Go to: https://myaccount.google.com/security
2. Sign in to: **riksharide2026@gmail.com**
3. Scroll to "How you sign in to Google"
4. Click "2-Step Verification"
5. If not enabled, click "Get Started" and follow prompts
6. You'll need your phone for verification

### Step 2: Delete Old App Passwords

1. Go to: https://myaccount.google.com/apppasswords
2. Sign in if needed
3. Look for any existing passwords
4. Delete them (click X or trash icon)

### Step 3: Generate NEW App Password

1. Still on: https://myaccount.google.com/apppasswords
2. Click "Select app" → Choose **"Mail"**
3. Click "Select device" → Choose **"Other (Custom name)"**
4. Type: **"RakshaRide"**
5. Click **"Generate"**
6. Google shows 16-character password like: `abcd efgh ijkl mnop`
7. **COPY IT IMMEDIATELY** (you won't see it again!)

### Step 4: Update Code

Open `app_enhanced.py` and find line ~26:

```python
GMAIL_APP_PASSWORD = "uhnzgwqdjeamzigr"  # OLD PASSWORD
```

Replace with YOUR NEW password:

```python
GMAIL_APP_PASSWORD = "abcd efgh ijkl mnop"  # NEW PASSWORD (use yours!)
```

**IMPORTANT:** 
- Copy EXACTLY as shown (with spaces)
- All 16 characters
- No extra spaces at start/end

### Step 5: Test It

```bash
python test_email_quick.py
```

Expected output:
```
✅ SUCCESS! Email Sent!
📬 Check your inbox: khushisaiharan42@gmail.com
```

---

## 🔍 Troubleshooting

### "App passwords" not showing?

**Solution:**
- Make sure 2-Step Verification is FULLY enabled
- Wait 5-10 minutes after enabling
- Sign out and back in
- Try direct link: https://myaccount.google.com/apppasswords

### Still getting error?

**Check:**
1. ✅ 2-Step Verification is enabled
2. ✅ Generated NEW App Password (not old one)
3. ✅ Copied ALL 16 characters
4. ✅ Included spaces as shown
5. ✅ No typos in email address

### Alternative: Use Different Email

If Gmail is too complicated, you can use:

**Outlook/Hotmail:**
```python
GMAIL_EMAIL = "your-email@outlook.com"
GMAIL_APP_PASSWORD = "your-password"
SMTP_SERVER = "smtp-mail.outlook.com"
SMTP_PORT = 587
```

---

## 📝 Quick Checklist

Before testing:
- [ ] 2-Step Verification enabled
- [ ] Old App Passwords deleted
- [ ] NEW App Password generated
- [ ] Password copied correctly (16 chars with spaces)
- [ ] Code updated in `app_enhanced.py`
- [ ] File saved

---

## 🎯 After Fixing

Once email works, OTP will be sent to user's actual email address!

**User Experience:**
1. User enters email during registration
2. Clicks "Send OTP"
3. **Email arrives in their inbox** ✅
4. User checks email
5. Enters OTP
6. Account created!

No need to check console - OTP goes directly to email!

---

## 💡 Pro Tip

Test with your own email first:
1. Register with your personal email
2. Check if OTP arrives
3. Verify it works
4. Then use for production

---

Made with ❤️ for women's safety
