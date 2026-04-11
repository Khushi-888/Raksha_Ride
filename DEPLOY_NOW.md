# 🚀 Deploy RakshaRide to Render — Complete Guide

## Files Ready for Deployment
- ✅ `requirements.txt` — Python packages
- ✅ `Procfile` — Gunicorn start command
- ✅ `runtime.txt` — Python 3.11
- ✅ `render.yaml` — Render config
- ✅ `.gitignore` — Excludes DB, uploads, keys
- ✅ `README.md` — Project docs

---

## Step 1: Install Git (if not installed)
Download from: https://git-scm.com/download/win

---

## Step 2: Create GitHub Repository

1. Go to https://github.com → Sign in
2. Click **+** → **New repository**
3. Name: `raksharide`
4. Set to **Public**
5. Click **Create repository**

---

## Step 3: Push Code to GitHub

Open **Command Prompt** in your project folder:

```cmd
git init
git add .
git commit -m "RakshaRide deploy"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/raksharide.git
git push -u origin main
```

Replace `YOUR_USERNAME` with your GitHub username.

---

## Step 4: Deploy on Render

1. Go to https://render.com → **Sign up with GitHub**
2. Click **New +** → **Web Service**
3. Click **Connect** next to your `raksharide` repo
4. Fill in settings:
   - **Name:** raksharide
   - **Region:** Oregon (US West)
   - **Branch:** main
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `gunicorn app_enhanced:app --bind 0.0.0.0:$PORT --workers 1 --timeout 120`
5. Scroll to **Environment Variables** → Add:
   | Key | Value |
   |-----|-------|
   | `FLASK_ENV` | `production` |
   | `SECRET_KEY` | `raksharide-secret-2024-xyz` |
   | `GMAIL_EMAIL` | `riksharide2026@gmail.com` |
   | `GMAIL_APP_PASSWORD` | `evsztunveoqilawu` |
6. Click **Create Web Service**
7. Wait 3-5 minutes for build to complete

---

## Step 5: Your Site is Live!

URL: `https://raksharide.onrender.com`

---

## ⚠️ Important Notes

### Database
Render free tier has **ephemeral storage** — database resets on redeploy.
For permanent data, use **Render Disk** ($7/month) or migrate to PostgreSQL.

### GPS & QR
Both work automatically on HTTPS (Render provides free SSL).

### Free Tier Sleep
App sleeps after 15 min inactivity. First request takes ~30 seconds.
To keep it awake: use https://uptimerobot.com (free ping every 5 min).

---

## Troubleshooting

**Build fails?**
Check Render logs. Common fix: ensure `requirements.txt` has all packages.

**App crashes on start?**
Check that `Procfile` says exactly:
```
web: gunicorn app_enhanced:app --bind 0.0.0.0:$PORT --workers 1 --timeout 120
```

**Database errors?**
The DB initializes automatically on first start. Check Render logs for `[OK] Enhanced database initialized`.
