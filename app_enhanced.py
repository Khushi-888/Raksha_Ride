"""
RakshaRide Enhanced - Complete Ride Sharing Platform
Includes: QR Code System, Ride Management, Payment Integration, History Tracking
"""

from flask import Flask, render_template, request, jsonify, session
from flask_cors import CORS
import sqlite3
import uuid
import hashlib
import hmac
import secrets
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
import re
import json
import qrcode
import io
import base64
import threading
import math
import os
from PIL import Image
from auth_utils import generate_token, get_current_user, require_auth

# ── DUAL AUTH HELPERS ─────────────────────────────────────────────────────────
def _driver_id():
    """Return driver user_id from session OR JWT token. None if not authenticated."""
    if session.get('user_type') == 'driver' and session.get('user_id'):
        return session['user_id']
    u = get_current_user()
    if u and u.get('user_type') == 'driver':
        return u['user_id']
    return None

def _passenger_id():
    """Return passenger user_id from session OR JWT token. None if not authenticated."""
    if session.get('user_type') == 'passenger' and session.get('user_id'):
        return session['user_id']
    u = get_current_user()
    if u and u.get('user_type') == 'passenger':
        return u['user_id']
    return None

def _require_driver():
    """Returns (driver_id, None) or (None, error_response)."""
    did = _driver_id()
    if not did:
        return None, (jsonify({"success": False, "message": "Driver authentication required", "code": "AUTH_REQUIRED"}), 401)
    return did, None

def _require_passenger():
    """Returns (passenger_id, None) or (None, error_response)."""
    pid = _passenger_id()
    if not pid:
        return None, (jsonify({"success": False, "message": "Passenger authentication required", "code": "AUTH_REQUIRED"}), 401)
    return pid, None


# Optional imports with fallbacks
try:
    from security_enhancements import (
        encrypt_document, decrypt_document,
        sign_qr_payload, verify_qr_payload,
        generate_unique_id, mask_aadhaar
    )
except ImportError:
    def encrypt_document(data): return data
    def decrypt_document(data): return data
    def sign_qr_payload(driver_id, name, vehicle, mobile):
        return json.dumps({"driver_id": driver_id, "name": name, "vehicle": vehicle, "mobile": mobile})
    def verify_qr_payload(payload): return json.loads(payload) if payload else None
    def generate_unique_id(prefix='DRV'):
        import secrets as s
        return f"{prefix}-{s.token_hex(4).upper()}"
    def mask_aadhaar(num): return "XXXX-XXXX-" + str(num)[-4:] if num else ""

try:
    from ai_verification import (
        extract_document_text, compute_face_similarity,
        generate_liveness_challenge, verify_liveness_token,
        run_verification_pipeline
    )
except ImportError:
    def extract_document_text(data): return {}
    def compute_face_similarity(a, b): return 0.0
    def generate_liveness_challenge(): return {"challenge": "blink"}
    def verify_liveness_token(token): return True
    def run_verification_pipeline(data): return {"status": "pending"}

try:
    from flask_mail import Mail, Message
    mail_available = True
except ImportError:
    mail_available = False

try:
    from werkzeug.utils import secure_filename
except ImportError:
    def secure_filename(f): return f

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'raksha-ride-enhanced-secret-key-2024')
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['SESSION_COOKIE_SECURE'] = os.environ.get('FLASK_ENV') == 'production'
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=24)
# Performance: compress responses
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 31536000  # 1 year cache for static files
CORS(app, supports_credentials=True, origins="*")

# Base URL
BASE_URL = os.environ.get('APP_URL', 'http://localhost:5000')

# ── RATE LIMITER (in-memory, prevents OTP spam) ───────────────────────────────
from time import time as _time
_rate_cache = {}

def rate_limit(key, limit=3, window=60):
    """
    Returns True if request is allowed, False if rate limit exceeded.
    limit: max requests per window (default 3 per 60 seconds)
    """
    now = _time()
    if key not in _rate_cache:
        _rate_cache[key] = []
    # Remove expired timestamps
    _rate_cache[key] = [t for t in _rate_cache[key] if now - t < window]
    if len(_rate_cache[key]) >= limit:
        return False
    _rate_cache[key].append(now)
    return True

# Gmail Configuration — reads from env vars in production
GMAIL_EMAIL = os.environ.get('GMAIL_EMAIL', 'riksharide2026@gmail.com')
GMAIL_APP_PASSWORD = os.environ.get('GMAIL_APP_PASSWORD', 'lpuqabvhriyqajqg')
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587

app.config['MAIL_SERVER'] = SMTP_SERVER
app.config['MAIL_PORT'] = SMTP_PORT
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = GMAIL_EMAIL
# Cleanup the app password for Flask-Mail
app.config['MAIL_PASSWORD'] = GMAIL_APP_PASSWORD.replace(' ', '').replace('-', '')
app.config['MAIL_DEFAULT_SENDER'] = GMAIL_EMAIL # Simplified for Flask-Mail

mail = Mail(app)

def _smtp_send(to_email, subject, html_body, plain_body=None):
    """
    Send email via HTTP API (Brevo) — works on Render free tier.
    SMTP is blocked on Render, so we use Brevo's REST API instead.
    Falls back to Gmail SMTP if Brevo key not set (for local dev).
    """
    import urllib.request
    import urllib.error

    gmail_email = os.environ.get('GMAIL_EMAIL', 'riksharide2026@gmail.com')
    brevo_key   = os.environ.get('BREVO_API_KEY', '')

    # ── Brevo HTTP API (works on Render — uses HTTPS port 443) ───────────────
    if brevo_key:
        try:
            payload = json.dumps({
                "sender": {"name": "RakshaRide", "email": gmail_email},
                "to": [{"email": to_email}],
                "subject": subject,
                "htmlContent": html_body,
                "textContent": plain_body or ""
            }).encode('utf-8')

            req = urllib.request.Request(
                "https://api.brevo.com/v3/smtp/email",
                data=payload,
                headers={
                    "accept": "application/json",
                    "api-key": brevo_key,
                    "content-type": "application/json"
                },
                method="POST"
            )
            with urllib.request.urlopen(req, timeout=15) as resp:
                result = json.loads(resp.read().decode())
                print(f"[EMAIL OK via Brevo] {to_email} — messageId: {result.get('messageId','?')}")
                return True
        except urllib.error.HTTPError as e:
            body = e.read().decode()
            print(f"[EMAIL Brevo HTTP Error] {e.code}: {body}")
        except Exception as e:
            print(f"[EMAIL Brevo FAIL] {type(e).__name__}: {e}")

    # ── Gmail SMTP fallback (works locally, blocked on Render free tier) ──────
    gmail_pw = os.environ.get('GMAIL_APP_PASSWORD', 'lpuqabvhriyqajqg').replace(' ', '').replace('-', '')
    from email.mime.multipart import MIMEMultipart as _MM
    from email.mime.text import MIMEText as _MT
    import smtplib as _smtp

    def _build_msg():
        msg = _MM('alternative')
        msg['From'] = f"RakshaRide <{gmail_email}>"
        msg['To'] = to_email
        msg['Subject'] = subject
        msg.attach(_MT(plain_body or "View in HTML client.", 'plain'))
        msg.attach(_MT(html_body, 'html'))
        return msg

    for port, use_ssl in [(587, False), (465, True)]:
        try:
            msg = _build_msg()
            if use_ssl:
                import ssl as _ssl
                ctx = _ssl.create_default_context()
                with _smtp.SMTP_SSL("smtp.gmail.com", port, context=ctx, timeout=20) as s:
                    s.login(gmail_email, gmail_pw)
                    s.sendmail(gmail_email, to_email, msg.as_string())
            else:
                s = _smtp.SMTP("smtp.gmail.com", port, timeout=20)
                s.ehlo(); s.starttls(); s.ehlo()
                s.login(gmail_email, gmail_pw)
                s.sendmail(gmail_email, to_email, msg.as_string())
                s.quit()
            print(f"[EMAIL OK via Gmail {port}] {to_email}")
            return True
        except Exception as e:
            print(f"[EMAIL Gmail {port} FAIL] {type(e).__name__}: {e}")

    print(f"[EMAIL ALL FAILED] {to_email} — Set BREVO_API_KEY in Render env vars")
    return False



def send_email_async(to_email, subject, html_body, plain_body=None):
    """Send email in background thread — uses direct SMTP, never blocks."""
    import threading as _t
    def _send():
        _smtp_send(to_email, subject, html_body, plain_body)
    _t.Thread(target=_send, daemon=True).start()


# â”€â”€ UPLOAD CONFIGURATION â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
UPLOAD_BASE = "static/uploads"
PROFILE_DIR = os.path.join(UPLOAD_BASE, "profile")
DOC_DIR = os.path.join(UPLOAD_BASE, "documents")
QR_DIR = os.path.join(UPLOAD_BASE, "qr")

for d in [PROFILE_DIR, DOC_DIR, QR_DIR]:
    os.makedirs(d, exist_ok=True)

def save_uploaded_file(file, target_dir, prefix=""):
    """
    Save uploaded file. On Render (read-only FS), stores as base64 data URI.
    Locally, saves to disk and returns path.
    Always reads bytes FIRST before attempting disk save.
    """
    if not file or not getattr(file, 'filename', None) or file.filename == '':
        return None
    try:
        # Read all bytes first — stream can only be read once
        file.seek(0)
        data = file.read()
        if not data:
            return None

        ext = file.filename.rsplit('.', 1)[-1].lower() if '.' in file.filename else 'jpg'
        mime = {'jpg': 'image/jpeg', 'jpeg': 'image/jpeg', 'png': 'image/png',
                'pdf': 'application/pdf', 'gif': 'image/gif'}.get(ext, 'image/jpeg')

        # Try disk save first (works locally, fails on Render read-only FS)
        try:
            os.makedirs(target_dir, exist_ok=True)
            filename = secure_filename(file.filename)
            unique_name = f"{prefix}_{uuid.uuid4().hex[:8]}_{filename}"
            file_path = os.path.join(target_dir, unique_name)
            with open(file_path, 'wb') as f:
                f.write(data)
            return file_path.replace("\\", "/")
        except (OSError, PermissionError):
            pass

        # Render fallback — store as base64 data URI in DB
        b64 = base64.b64encode(data).decode()
        return f"data:{mime};base64,{b64}"

    except Exception as e:
        print(f"[WARN] save_uploaded_file failed: {e}")
        return None


# â”€â”€ CORE UTILITY FUNCTIONS â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

def calculate_fare(duration_mins, distance_km):
    """Alias — kept for backward compat. See full version below."""
    BASE_FARE = 25.0
    per_km    = 12.0
    per_min   = 1.0
    return round(BASE_FARE + (distance_km * per_km) + (duration_mins * per_min), 2)

def generate_payment_qr_code(ride_id, amount, driver_name, upi_id):
    """Generates a UPI payment URL for scanning"""
    # Standard UPI Deep Link format: upi://pay?pa=address&pn=name&am=amount&cu=INR
    pa = upi_id or "raksharide.merchant@upi"
    upi_url = f"upi://pay?pa={pa}&pn={driver_name}&am={amount}&cu=INR&tn=Ride_{ride_id}"
    
    qr = qrcode.QRCode(box_size=10, border=4)
    qr.add_data(upi_url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    
    buffered = io.BytesIO()
    img.save(buffered, format="PNG")
    return f"data:image/png;base64,{base64.b64encode(buffered.getvalue()).decode()}"

def _send_credentials_email(email, name, user_id, password):
    """Sends officially generated credentials to the verified driver"""
    subject = "RakshaRide - Your Verified Driver Credentials"
    body = f"""
    <h2>Verification Complete!</h2>
    <p>Dear {name},</p>
    <p>We are pleased to inform you that your RakshaRide driver profile has been verified and activated.</p>
    <div style="padding: 20px; background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 10px;">
        <p><strong>Official Driver ID:</strong> {user_id}</p>
        <p><strong>Temporary Password:</strong> {password}</p>
    </div>
    <p><strong>Note:</strong> You will be required to change this password upon your first login.</p>
    <p>Safe journeys!</p>
    <a href="/login/driver" style="display:inline-block; padding:10px 20px; background:#003366; color:white; text-decoration:none; border-radius:5px;">Login to Portal</a>
    """
    send_email_async(email, subject, body)

def _send_owner_creds_notification(email, owner_name, renter_name, renter_id):
    """Notifies owner that their renter is now verified and active"""
    subject = "RakshaRide - Renter Verification Complete"
    body = f"""
    <h2>Partner Verification Finalized</h2>
    <p>Dear {owner_name},</p>
    <p>The renter associated with your vehicle, <strong>{renter_name}</strong>, has completed their document verification.</p>
    <p>They have been issued Driver ID: <strong>{renter_id}</strong> and can now start accept rides using your vehicle within the RakshaRide trust network.</p>
    """
    send_email_async(email, subject, body)

def sign_qr_payload(id, name, vehicle, mobile):
    """Signs driver payload using HMAC to prevent QR tampering"""
    secret_key = "raksha_secret_dev"  # Should be in app.config
    payload = f"{id}|{name}|{vehicle}|{mobile}"
    signature = hmac.new(secret_key.encode(), payload.encode(), hashlib.sha256).hexdigest()
    return {
        "id": id,
        "name": name,
        "vehicle": vehicle,
        "mobile": mobile,
        "signature": signature
    }

# -- DATABASE HELPER ----------------------------------------------------------
DB_PATH = 'database_enhanced.db'
import threading
_db_local = threading.local()

def get_db_conn():
    """Return a fast, optimized SQLite connection."""
    conn = sqlite3.connect(DB_PATH, timeout=30, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    # Performance PRAGMAs — set once per connection
    conn.execute('PRAGMA journal_mode=WAL;')
    conn.execute('PRAGMA synchronous=NORMAL;')
    conn.execute('PRAGMA cache_size=-32000;')   # 32 MB page cache
    conn.execute('PRAGMA temp_store=MEMORY;')
    conn.execute('PRAGMA mmap_size=268435456;') # 256 MB memory-mapped I/O
    conn.execute('PRAGMA busy_timeout=10000;')
    return conn
# Database initialization
def init_db():
    conn = get_db_conn()
    c = conn.cursor()
    
    # Passengers table
    c.execute('''CREATE TABLE IF NOT EXISTS passengers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        phone TEXT NOT NULL UNIQUE,
        email TEXT NOT NULL UNIQUE,
        password TEXT NOT NULL,
        profile_image TEXT,
        total_rides INTEGER DEFAULT 0,
        total_spent REAL DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    
    # Drivers table
    c.execute('''CREATE TABLE IF NOT EXISTS drivers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        age INTEGER NOT NULL,
        mobile TEXT NOT NULL UNIQUE,
        email TEXT NOT NULL UNIQUE,
        vehicle_number TEXT NOT NULL,
        vehicle_type TEXT DEFAULT 'Car',
        rc_number TEXT NOT NULL,
        password TEXT NOT NULL,
        address TEXT,
        qr_code TEXT,
        unique_id TEXT UNIQUE,
        profile_image TEXT,
        upi_id TEXT,
        latitude REAL,
        longitude REAL,
        is_available BOOLEAN DEFAULT 1,
        rating REAL DEFAULT 5.0,
        total_rides INTEGER DEFAULT 0,
        total_earned REAL DEFAULT 0,
        role TEXT DEFAULT 'OWNER',
        owner_id INTEGER,
        verification_status TEXT DEFAULT 'pending',
        license_number TEXT,
        payment_qr_image TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    
    # OTP verification table
    c.execute('''CREATE TABLE IF NOT EXISTS otp_verification (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT NOT NULL,
        otp TEXT NOT NULL,
        expiry_time TIMESTAMP NOT NULL,
        attempts INTEGER DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    
    # Rides table
    c.execute('''CREATE TABLE IF NOT EXISTS rides (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        passenger_id INTEGER NOT NULL,
        driver_id INTEGER NOT NULL,
        passenger_name TEXT NOT NULL,
        passenger_phone TEXT NOT NULL,
        driver_name TEXT NOT NULL,
        driver_mobile TEXT NOT NULL,
        driver_vehicle TEXT NOT NULL,
        pickup_location TEXT DEFAULT 'Not specified',
        dropoff_location TEXT DEFAULT 'Not specified',
        start_lat REAL,
        start_lng REAL,
        end_lat REAL,
        end_lng REAL,
        route_coordinates TEXT,
        start_time TIMESTAMP,
        end_time TIMESTAMP,
        duration_minutes INTEGER,
        distance_km REAL DEFAULT 0,
        fare REAL,
        status TEXT DEFAULT 'pending',
        payment_status TEXT DEFAULT 'pending',
        payment_method TEXT DEFAULT 'qr_code',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (passenger_id) REFERENCES passengers(id),
        FOREIGN KEY (driver_id) REFERENCES drivers(id)
    )''')
    
    # Payments table
    c.execute('''CREATE TABLE IF NOT EXISTS payments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        ride_id INTEGER NOT NULL,
        passenger_id INTEGER NOT NULL,
        driver_id INTEGER NOT NULL,
        amount REAL NOT NULL,
        payment_method TEXT DEFAULT 'qr_code',
        payment_qr TEXT,
        upi_id TEXT,
        status TEXT DEFAULT 'pending',
        transaction_id TEXT,
        paid_at TIMESTAMP,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (ride_id) REFERENCES rides(id),
        FOREIGN KEY (passenger_id) REFERENCES passengers(id),
        FOREIGN KEY (driver_id) REFERENCES drivers(id)
    )''')
    
    # â”€â”€ Runtime migrations (safe to run every startup) â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    migrations = [
        ('drivers', 'payment_qr_image',    'TEXT'),
        ('drivers', 'unique_id',            'TEXT'),
        ('drivers', 'verification_status',  'TEXT DEFAULT "pending"'),
        ('drivers', 'aadhaar_number',       'TEXT'),
        ('drivers', 'aadhaar_doc',          'TEXT'),
        ('drivers', 'rc_doc',               'TEXT'),
        ('drivers', 'admin_notes',          'TEXT'),
        ('drivers', 'role',                 'TEXT DEFAULT "OWNER"'),
        ('drivers', 'owner_id',             'INTEGER'),
        ('drivers', 'ai_face_score',        'REAL'),
        ('drivers', 'ai_ocr_data',          'TEXT'),
        ('drivers', 'live_selfie',          'TEXT'),
        ('drivers', 'license_number',       'TEXT'),
        ('drivers', 'gender',               'TEXT DEFAULT "Any"'),
        ('passengers', 'unique_id',         'TEXT'),
        ('passengers', 'aadhaar_number',    'TEXT'),
        ('passengers', 'aadhaar_doc',       'TEXT'),
        ('passengers', 'emergency_mobile',  'TEXT'),
        ('passengers', 'emergency_email',   'TEXT'),
        ('passengers', 'emergency_name',    'TEXT'),
        ('rides', 'share_token',            'TEXT'),
        ('rides', 'share_token_active',     'INTEGER DEFAULT 0'),
        ('drivers', 'first_login',          'INTEGER DEFAULT 0'),
    ]
    for table, col, coltype in migrations:
        try:
            c.execute(f'ALTER TABLE {table} ADD COLUMN {col} {coltype}')
            conn.commit()
        except Exception:
            pass  # Column already exists

    # â”€â”€ Documents table (Owner-Renter document vault) â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    c.execute('''CREATE TABLE IF NOT EXISTS driver_documents (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        driver_id INTEGER NOT NULL,
        uploaded_by INTEGER NOT NULL,
        doc_type TEXT NOT NULL,
        file_data TEXT,
        ocr_extracted TEXT,
        ai_status TEXT DEFAULT 'PENDING',
        ai_score REAL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (driver_id) REFERENCES drivers(id),
        FOREIGN KEY (uploaded_by) REFERENCES drivers(id)
    )''')

    # â”€â”€ Owner-Renter link requests â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    c.execute('''CREATE TABLE IF NOT EXISTS renter_requests (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        renter_id INTEGER NOT NULL,
        owner_email TEXT NOT NULL,
        owner_id INTEGER,
        approval_token TEXT UNIQUE,
        status TEXT DEFAULT 'PENDING',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (renter_id) REFERENCES drivers(id)
    )''')

    # â”€â”€ Ratings & Reviews table â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    c.execute('''CREATE TABLE IF NOT EXISTS ratings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        driver_id INTEGER NOT NULL,
        passenger_id INTEGER NOT NULL,
        ride_id INTEGER,
        rating INTEGER CHECK(rating BETWEEN 1 AND 5),
        comment TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (driver_id) REFERENCES drivers(id),
        FOREIGN KEY (passenger_id) REFERENCES passengers(id),
        FOREIGN KEY (ride_id) REFERENCES rides(id)
    )''')

    # â”€â”€ Admins table â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    c.execute('''CREATE TABLE IF NOT EXISTS admins (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL UNIQUE,
        password TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')

    # â”€â”€ Seed default admin if none exists â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    c.execute('SELECT COUNT(*) FROM admins')
    if c.fetchone()[0] == 0:
        import hashlib as _hl, os as _os
        admin_pw_raw = _os.environ.get('ADMIN_PASSWORD', 'RakshaAdmin@2024#Secure!')
        default_pw = _hl.sha256(admin_pw_raw.encode()).hexdigest()
        c.execute("INSERT INTO admins (username, password) VALUES (?, ?)", ('admin', default_pw))
        print("[OK] Admin created — use ADMIN_PASSWORD env var to set password")

    # ── Performance indexes (safe to run every startup) ──────────────────────
    # ── live_locations table (upsert GPS — one row per user) ─────────────────
    c.execute("""CREATE TABLE IF NOT EXISTS live_locations (
        user_id INTEGER PRIMARY KEY,
        role TEXT NOT NULL DEFAULT 'driver',
        latitude REAL,
        longitude REAL,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )""")
    conn.commit()
    indexes = [
        "CREATE INDEX IF NOT EXISTS idx_drivers_email ON drivers(email)",
        "CREATE INDEX IF NOT EXISTS idx_drivers_mobile ON drivers(mobile)",
        "CREATE INDEX IF NOT EXISTS idx_drivers_available ON drivers(is_available)",
        "CREATE INDEX IF NOT EXISTS idx_drivers_status ON drivers(verification_status)",
        "CREATE INDEX IF NOT EXISTS idx_passengers_email ON passengers(email)",
        "CREATE INDEX IF NOT EXISTS idx_passengers_phone ON passengers(phone)",
        "CREATE INDEX IF NOT EXISTS idx_rides_passenger ON rides(passenger_id)",
        "CREATE INDEX IF NOT EXISTS idx_rides_driver ON rides(driver_id)",
        "CREATE INDEX IF NOT EXISTS idx_rides_status ON rides(status)",
        "CREATE INDEX IF NOT EXISTS idx_otp_email ON otp_verification(email)",
        "CREATE INDEX IF NOT EXISTS idx_docs_driver ON driver_documents(driver_id)",
        "CREATE INDEX IF NOT EXISTS idx_renter_token ON renter_requests(approval_token)",
    ]
    for idx in indexes:
        try:
            c.execute(idx)
        except Exception:
            pass
    conn.commit()
    conn.close()
    print("[OK] Enhanced database initialized successfully!")

# Initialize database on startup
init_db()

# Helper functions
def hash_password(password):
    """Hash password using SHA256"""
    return hashlib.sha256(password.encode()).hexdigest()

def generate_otp():
    """Generate 6-digit OTP"""
    return ''.join([str(secrets.randbelow(10)) for _ in range(6)])

def generate_driver_qr_code(driver_id, driver_name, vehicle_number, mobile):
    """Generate QR code — fully in-memory, no filesystem writes (works on Render)"""
    try:
        # QR payload with driver info
        qr_data = sign_qr_payload(driver_id, driver_name, vehicle_number, mobile)
        qr_data['driver_id'] = str(driver_id)
        qr_json = json.dumps(qr_data)

        # Generate QR code entirely in memory
        qr = qrcode.QRCode(version=1, box_size=8, border=3)
        qr.add_data(qr_json)
        qr.make(fit=True)
        img = qr.make_image(fill_color="#1565C0", back_color="white")

        buffered = io.BytesIO()
        img.save(buffered, format="PNG")
        img_str = base64.b64encode(buffered.getvalue()).decode()
        b64_data_uri = f"data:image/png;base64,{img_str}"

        # Store base64 in DB (no file path needed)
        return b64_data_uri, b64_data_uri

    except Exception as e:
        print(f"[WARN] QR Gen Error: {e}")
        return None, None

def generate_payment_qr_code(ride_id, amount, driver_name, upi_id=None):
    """Generate payment QR code"""
    try:
        # Create payment data
        if upi_id:
            # UPI payment string format
            payment_data = f"upi://pay?pa={upi_id}&pn={driver_name}&am={amount}&cu=INR&tn=RakshaRide Payment for Ride {ride_id}"
        else:
            # Generic payment data
            payment_data = {
                'type': 'payment',
                'ride_id': ride_id,
                'amount': amount,
                'driver': driver_name,
                'timestamp': datetime.now().isoformat()
            }
            payment_data = json.dumps(payment_data)
        
        # Generate QR code
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(payment_data)
        qr.make(fit=True)
        
        # Create image
        img = qr.make_image(fill_color="black", back_color="white")
        
        # Convert to base64
        buffered = io.BytesIO()
        img.save(buffered, format="PNG")
        img_str = base64.b64encode(buffered.getvalue()).decode()
        
        return f"data:image/png;base64,{img_str}"
        
    except Exception as e:
        print(f"Error generating payment QR: {str(e)}")
        return None

def calculate_fare(duration_minutes, distance_km=0):
    """Calculate ride fare — distance-based pricing (₹25 base + ₹12/km + ₹1/min)"""
    BASE_FARE      = 25.0
    PER_KM_RATE    = 12.0
    PER_MINUTE_RATE = 1.0
    fare = BASE_FARE + (distance_km * PER_KM_RATE) + (duration_minutes * PER_MINUTE_RATE)
    return round(fare, 2)

def send_email_otp(to_email, otp):
    """Send OTP via direct SMTP — works on Render."""
    subject = "RakshaRide — Your Verification Code"
    html_body = (
        "<div style='font-family:Arial,sans-serif;max-width:500px;margin:0 auto'>"
        "<div style='background:linear-gradient(135deg,#FFC107,#1565C0);padding:20px;border-radius:12px 12px 0 0;text-align:center'>"
        "<h1 style='color:white;margin:0'>RakshaRide</h1>"
        "<p style='color:rgba(255,255,255,0.9);margin:5px 0 0'>Verification Code</p>"
        "</div>"
        "<div style='background:#fff;border:1px solid #e0e0e0;padding:30px;border-radius:0 0 12px 12px'>"
        "<p style='color:#333;font-size:16px'>Your one-time verification code is:</p>"
        "<div style='background:#f5f5f5;border:2px dashed #FFC107;border-radius:10px;padding:20px;text-align:center;margin:20px 0'>"
        f"<span style='font-size:36px;font-weight:900;letter-spacing:10px;color:#1565C0'>{otp}</span>"
        "</div>"
        "<p style='color:#666;font-size:14px'>Valid for <strong>5 minutes</strong> only.</p>"
        "<p style='color:#666;font-size:14px'>Never share this code with anyone.</p>"
        "</div></div>"
    )
    plain = f"Your RakshaRide OTP is: {otp}\nValid for 5 minutes. Do not share."
    ok = _smtp_send(to_email, subject, html_body, plain)
    if ok:
        return True, "OTP sent successfully"
    else:
        print(f"[OTP FALLBACK] Email failed. OTP for {to_email}: {otp}")
        return False, f"Email failed. Dev OTP: {otp}"


def _deliver_email(msg):
    """Internal helper to deliver SMTP message with robust error handling"""
    try:
        # Clean the app password (remove spaces and dashes)
        clean_pw = GMAIL_APP_PASSWORD.replace(' ', '').replace('-', '')
        
        # Connect to Gmail SMTP server
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT, timeout=30)
        server.set_debuglevel(1) # Diagnostics enabled
        server.starttls()
        
        # Login with credentials
        server.login(GMAIL_EMAIL, clean_pw)
        
        # Send email
        server.send_message(msg)
        server.quit()
        
        print(f"âœ… Email delivered successfully to {msg['To']}")
        return True
    except Exception as e:
        print(f"âŒ SMTP Critical Failure: {str(e)}")
        # Log to a file if needed
        return False

def send_owner_approval_email(owner_email, renter_name, vehicle_details, token):
    """Send approval request to owner — uses Brevo via send_email_async (non-blocking)."""
    approval_url = f"{BASE_URL}/owner_confirm?token={token}"
    subject = "RakshaRide — Driver Authorization Request"
    html = (
        "<div style='font-family:Arial,sans-serif;max-width:600px;margin:0 auto'>"
        "<div style='background:linear-gradient(135deg,#1565C0,#FFC107);padding:24px;border-radius:12px 12px 0 0;text-align:center'>"
        "<h1 style='color:white;margin:0'>RakshaRide</h1>"
        "<p style='color:rgba(255,255,255,0.9);margin:6px 0 0'>Vehicle Owner Action Required</p>"
        "</div>"
        "<div style='background:#fff;border:1px solid #e0e0e0;padding:28px;border-radius:0 0 12px 12px'>"
        "<h2 style='color:#1565C0'>Driver Authorization Request</h2>"
        "<p>Dear Vehicle Owner,</p>"
        f"<p>Driver <strong>{renter_name}</strong> wants to operate your vehicle <strong>{vehicle_details}</strong> on RakshaRide.</p>"
        "<div style='background:#f5f5f5;border-radius:10px;padding:16px;margin:20px 0'>"
        f"<p style='margin:0'><strong>Driver:</strong> {renter_name}</p>"
        f"<p style='margin:8px 0 0'><strong>Vehicle:</strong> {vehicle_details}</p>"
        "</div>"
        "<div style='text-align:center;margin:24px 0'>"
        f"<a href='{approval_url}' style='background:#1565C0;color:white;padding:14px 32px;"
        "text-decoration:none;border-radius:8px;font-weight:bold;font-size:16px;display:inline-block'>"
        "Review &amp; Approve Request</a>"
        "</div>"
        "<p style='color:#666;font-size:13px'>If you did not expect this, please ignore this email.</p>"
        "</div></div>"
    )
    plain = f"Driver {renter_name} wants to use your vehicle ({vehicle_details}). Approve: {approval_url}"
    send_email_async(owner_email, subject, html, plain)
    print(f"[OWNER EMAIL] Queued for {owner_email}")
    return True


def is_valid_email(email):
    """Validate email format"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

# Routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/scanner')
def scanner_view():
    return render_template('scanner.html')

@app.route('/verify_driver/<unique_id>')
def verify_driver_details(unique_id):
    """View to show driver details after scanning QR"""
    try:
        conn = get_db_conn()
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        c.execute("SELECT name, vehicle_number, vehicle_type, rating, total_rides, is_available, verification_status FROM drivers WHERE unique_id = ?", (unique_id,))
        driver = c.fetchone()
        conn.close()
        
        if not driver:
            return "Driver not found", 404
            
        # Ensure passenger is logged in
        if 'user_id' not in session or session.get('user_type') != 'passenger':
            return render_template('passenger_otp_login.html', unique_id=unique_id, driver=driver)
            
        return render_template('verify_driver.html', driver=driver)
    except Exception as e:
        return str(e), 500

@app.route('/api/passenger_scan_otp_request', methods=['POST'])
def passenger_scan_otp_request():
    """Send OTP to passenger email after scanning driver ID"""
    try:
        data = request.get_json()
        email = data.get('email', '').strip()
        
        if not email:
            return jsonify({"success": False, "message": "Email is required"}), 400
            
        # Generate and save OTP
        otp_code = f"{secrets.randbelow(899999) + 100000}"
        expiry = datetime.now() + timedelta(minutes=10)
        
        conn = get_db_conn()
        c = conn.cursor()
        c.execute("DELETE FROM otp_verification WHERE email = ?", (email,))
        c.execute("INSERT INTO otp_verification (email, otp, expiry_time) VALUES (?, ?, ?)",
                  (email, otp_code, expiry))
        conn.commit()
        conn.close()
        
        # Send Email
        send_email_async(
            email,
            "RakshaRide - Passenger Verification Code",
            f"<h3>Identity Verification</h3><p>Your secure OTP for starting your RakshaRide journey is: <b>{otp_code}</b>. It expires in 10 minutes.</p>"
        )
        
        return jsonify({"success": True, "message": "OTP sent successfully!"})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

@app.route('/api/passenger_scan_otp_verify', methods=['POST'])
def passenger_scan_otp_verify():
    """Verify passenger OTP and log in"""
    try:
        data = request.get_json()
        email = data.get('email', '').strip()
        otp = data.get('otp', '').strip()
        
        if not email or not otp:
            return jsonify({"success": False, "message": "Email and OTP required"}), 400
            
        conn = get_db_conn()
        c = conn.cursor()
        c.execute("SELECT otp, expiry_time FROM otp_verification WHERE email = ?", (email,))
        res = c.fetchone()
        
        if not res or res[0] != otp:
             conn.close()
             return jsonify({"success": False, "message": "Invalid or expired OTP"}), 400
             
        # Check if passenger exists, if not create a temporary entry
        c.execute("SELECT id, name FROM passengers WHERE email = ?", (email,))
        p = c.fetchone()
        
        if not p:
            # Create a simple profile if not exists
            name = email.split('@')[0].capitalize()
            unique_id = generate_unique_id('PSR')
            c.execute("INSERT INTO passengers (name, email, phone, password, unique_id) VALUES (?, ?, ?, ?, ?)",
                      (name, email, 'Not set', 'TEMP_OTP', unique_id))
            conn.commit()
            p_id = c.lastrowid
        else:
            p_id, name = p
            
        session['user_id'] = p_id
        session['user_name'] = name
        session['user_type'] = 'passenger'
        session.permanent = True
        
        token = generate_token(p_id, 'passenger', name)
        
        conn.commit()
        conn.close()
        
        return jsonify({
            "success": True,
            "message": "Verified successfully!",
            "name": name,
            "token": token,
            "user_id": p_id,
            "user_type": "passenger"
        })
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

@app.route('/dashboard/passenger')
def passenger_dashboard():
    pid = _passenger_id()
    if not pid:
        token_param = request.args.get('token', '')
        if token_param:
            from auth_utils import decode_token
            payload = decode_token(token_param)
            if payload and payload.get('user_type') == 'passenger':
                session['user_id'] = payload['user_id']
                session['user_type'] = 'passenger'
                session['name'] = payload.get('name', '')
                session.permanent = True
                pid = payload['user_id']
    if not pid:
        return render_template('login_govt.html', type='passenger')
    return render_template('dashboard_passenger_new.html')

@app.route('/dashboard/driver')
def driver_dashboard():
    # Accept session OR JWT (token passed as query param for redirect after login)
    did = _driver_id()
    if not did:
        # Check if token passed in query string (from redirect after login)
        token_param = request.args.get('token', '')
        if token_param:
            from auth_utils import decode_token
            payload = decode_token(token_param)
            if payload and payload.get('user_type') == 'driver':
                session['user_id'] = payload['user_id']
                session['user_type'] = 'driver'
                session['name'] = payload.get('name', '')
                session.permanent = True
                did = payload['user_id']
    if not did:
        return render_template('login_govt.html', type='driver')
    return render_template('dashboard_driver_new.html')

@app.route('/login/passenger')
def login_passenger_page():
    return render_template('login_govt.html', type='passenger')

@app.route('/login/driver')
def login_driver_page():
    return render_template('login_govt.html', type='driver')

@app.route('/register/passenger')
def register_passenger_page():
    return render_template('register_govt.html', type='passenger')

@app.route('/register_driver_new')
def register_driver_new():
    return render_template('driver_register_new.html')

# Continue in next part...

# ============================================================================
# Authentication APIs (Same as before, enhanced)
# ============================================================================

@app.route('/api/send_otp', methods=['POST'])
def send_otp():
    """Send OTP — saves to DB immediately, sends email in background (non-blocking)."""
    try:
        data = request.get_json() or {}
        email = data.get('email', '').strip()

        if not email or not is_valid_email(email):
            return jsonify({"success": False, "message": "Invalid email address"}), 400

        # Rate limit: max 3 per 60s per email
        if not rate_limit(f"otp_{email}", limit=3, window=60):
            return jsonify({"success": False, "message": "Too many requests. Wait 60 seconds."}), 429

        # Check already registered
        conn = get_db_conn()
        c = conn.cursor()
        c.execute("SELECT id FROM passengers WHERE email = ?", (email,))
        if c.fetchone():
            conn.close()
            return jsonify({"success": False, "message": "Email already registered. Please login."}), 400
        c.execute("SELECT id FROM drivers WHERE email = ?", (email,))
        if c.fetchone():
            conn.close()
            return jsonify({"success": False, "message": "Email already registered as driver. Please login."}), 400

        # Generate OTP and save to DB immediately
        otp = generate_otp()
        expiry_time = datetime.now() + timedelta(minutes=5)
        c.execute("DELETE FROM otp_verification WHERE email = ?", (email,))
        c.execute("INSERT INTO otp_verification (email, otp, expiry_time, attempts) VALUES (?, ?, ?, 0)",
                  (email, otp, expiry_time))
        conn.commit()
        conn.close()

        # Also store in session as backup (survives DB resets on Render)
        session[f'otp_{email}'] = {'otp': otp, 'expiry': expiry_time.isoformat()}
        session.permanent = True

        # Send email in background thread — response returns immediately
        html = (
            "<div style='font-family:Arial;padding:20px;max-width:500px'>"
            "<h2 style='color:#1565C0'>RakshaRide OTP</h2>"
            "<p>Your verification code is:</p>"
            "<div style='font-size:36px;font-weight:900;letter-spacing:10px;color:#FFC107;"
            "padding:20px;background:#f5f5f5;border-radius:10px;text-align:center'>"
            + otp +
            "</div>"
            "<p style='color:#666;margin-top:16px'>Valid for <strong>5 minutes</strong>. Do not share.</p>"
            "</div>"
        )
        send_email_async(email, "RakshaRide — Your OTP", html, f"Your OTP: {otp} (valid 5 min)")

        print(f"[OTP] Generated for {email}: {otp}")
        return jsonify({
            "success": True,
            "message": f"Verification code sent to {email}. Check your inbox and spam folder.",
            "email_sent": True
        })

    except Exception as e:
        print(f"[send_otp ERROR] {e}")
        return jsonify({"success": False, "message": "Server error. Please try again."}), 500


@app.route('/api/verify_otp', methods=['POST'])
def verify_otp():
    """Verify OTP"""
    try:
        data = request.get_json()
        email = data.get('email', '').strip()
        otp = data.get('otp', '').strip()
        
        if not email or not otp:
            return jsonify({"success": False, "message": "Email and OTP required"}), 400

        # Rate limit: max 5 verify attempts per email per 60 seconds
        if not rate_limit(f"verify_{email}", limit=5, window=60):
            return jsonify({"success": False, "message": "Too many verification attempts. Please wait."}), 429
        
        conn = get_db_conn()
        c = conn.cursor()
        
        c.execute("""SELECT otp, expiry_time, attempts 
                     FROM otp_verification WHERE email = ?""", (email,))
        result = c.fetchone()
        
        if not result:
            # Fallback: check session-stored OTP (handles Render DB resets)
            session_otp_data = session.get(f'otp_{email}')
            if session_otp_data:
                stored_otp = session_otp_data.get('otp')
                expiry_str = session_otp_data.get('expiry')
                try:
                    expiry_time = datetime.fromisoformat(expiry_str)
                except Exception:
                    conn.close()
                    return jsonify({"success": False, "message": "OTP expired. Please request a new one."}), 400
                if datetime.now() > expiry_time:
                    session.pop(f'otp_{email}', None)
                    conn.close()
                    return jsonify({"success": False, "message": "OTP expired. Please request a new one."}), 400
                if otp != stored_otp:
                    conn.close()
                    return jsonify({"success": False, "message": "Invalid OTP. Please check and try again."}), 400
                # Valid — clear session OTP
                session.pop(f'otp_{email}', None)
                conn.close()
                return jsonify({"success": True, "message": "OTP verified successfully"})
            conn.close()
            return jsonify({"success": False, "message": "OTP not found or expired. Please request a new OTP."}), 404
        
        stored_otp, expiry_time_str, attempts = result
        
        try:
            expiry_time = datetime.fromisoformat(expiry_time_str.replace(' ', 'T'))
        except:
            expiry_time = datetime.strptime(expiry_time_str, '%Y-%m-%d %H:%M:%S.%f')
        
        if datetime.now() > expiry_time:
            c.execute("DELETE FROM otp_verification WHERE email = ?", (email,))
            conn.commit()
            conn.close()
            return jsonify({"success": False, "message": "OTP expired"}), 400
        
        if attempts >= 3:
            c.execute("DELETE FROM otp_verification WHERE email = ?", (email,))
            conn.commit()
            conn.close()
            return jsonify({"success": False, "message": "Too many attempts"}), 400
        
        if otp != stored_otp:
            c.execute("UPDATE otp_verification SET attempts = attempts + 1 WHERE email = ?", (email,))
            conn.commit()
            remaining = 3 - (attempts + 1)
            conn.close()
            return jsonify({"success": False, "message": f"Invalid OTP. {remaining} attempts remaining"}), 400
        
        c.execute("DELETE FROM otp_verification WHERE email = ?", (email,))
        conn.commit()
        conn.close()
        
        return jsonify({"success": True, "message": "OTP verified successfully"})
        
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

@app.route('/api/register_passenger', methods=['POST'])
def register_passenger():
    """Register new passenger with unique ID"""
    try:
        data = request.get_json()
        name = data.get('name', '').strip()
        phone = (data.get('phone') or data.get('mobile') or '').strip()
        email = data.get('email', '').strip()
        password = data.get('password', '').strip()
        aadhaar_number = data.get('aadhaar_number', '').strip()
        aadhaar_doc = data.get('aadhaar_doc', '')

        if not all([name, phone, email, password]):
            return jsonify({"success": False, "message": "All fields required (name, mobile, email, password)"}), 400

        if not is_valid_email(email):
            return jsonify({"success": False, "message": "Invalid email"}), 400

        if len(password) < 6:
            return jsonify({"success": False, "message": "Password must be 6+ characters"}), 400

        hashed_password = hash_password(password)
        unique_id = generate_unique_id('PSR')
        enc_aadhaar = encrypt_document(aadhaar_doc) if aadhaar_doc else None

        conn = get_db_conn()
        c = conn.cursor()
        try:
            c.execute("SELECT id FROM passengers WHERE email = ?", (email,))
            if c.fetchone():
                conn.close()
                return jsonify({"success": False, "message": "Email is already registered"}), 400

            c.execute("SELECT id FROM passengers WHERE phone = ?", (phone,))
            if c.fetchone():
                conn.close()
                return jsonify({"success": False, "message": "Mobile number is already registered"}), 400

            c.execute("""INSERT INTO passengers
                         (name, phone, email, password, unique_id, aadhaar_number, aadhaar_doc)
                         VALUES (?, ?, ?, ?, ?, ?, ?)""",
                      (name, phone, email, hashed_password, unique_id, aadhaar_number, enc_aadhaar))
            conn.commit()
            passenger_id = c.lastrowid
            conn.close()

            return jsonify({
                "success": True,
                "message": "Account created successfully!",
                "user_id": passenger_id,
                "unique_id": unique_id
            })
        except sqlite3.IntegrityError:
            conn.close()
            return jsonify({"success": False, "message": "Identity collision. Please verify your details."}), 400

    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

@app.route('/api/register_driver', methods=['POST'])
def register_driver():
    """Register new driver with unique ID and document storage"""
    try:
        data = request.get_json()
        name = data.get('name', '').strip()
        age = data.get('age')
        mobile = data.get('mobile', '').strip()
        email = data.get('email', '').strip()
        vehicle_number = data.get('vehicle_number', '').strip()
        vehicle_type = data.get('vehicle_type', 'Car').strip()
        rc_number = data.get('rc_number', '').strip()
        password = data.get('password', '').strip()
        aadhaar_number = data.get('aadhaar_number', '').strip()
        aadhaar_doc = data.get('aadhaar_doc', '')   # base64 data URI
        rc_doc = data.get('rc_doc', '')             # base64 data URI

        if not all([name, age, mobile, email, vehicle_number, rc_number, password]):
            return jsonify({"success": False, "message": "All fields required"}), 400

        if not is_valid_email(email):
            return jsonify({"success": False, "message": "Invalid email"}), 400

        if len(password) < 6:
            return jsonify({"success": False, "message": "Password must be 6+ characters"}), 400

        try:
            age = int(age)
            if age < 18 or age > 70:
                return jsonify({"success": False, "message": "Age must be 18-70"}), 400
        except ValueError:
            return jsonify({"success": False, "message": "Invalid age"}), 400

        hashed_password = hash_password(password)
        unique_id = generate_unique_id('DRV')

        # Encrypt documents before storage
        enc_aadhaar = encrypt_document(aadhaar_doc) if aadhaar_doc else None
        enc_rc = encrypt_document(rc_doc) if rc_doc else None

        # Placeholder QR (driver_id unknown yet)
        qr_image, qr_data = generate_driver_qr_code(0, name, vehicle_number, mobile)

        conn = get_db_conn()
        c = conn.cursor()
        try:
            for col, val, msg in [
                ('email',          email,          'Email is already registered'),
                ('mobile',         mobile,         'Mobile number is already registered'),
                ('vehicle_number', vehicle_number, 'Vehicle number already registered'),
                ('rc_number',      rc_number,      'RC number already registered'),
            ]:
                c.execute(f"SELECT id FROM drivers WHERE {col} = ?", (val,))
                if c.fetchone():
                    conn.close()
                    return jsonify({"success": False, "message": msg}), 400

            c.execute("""INSERT INTO drivers
                         (name, age, mobile, email, vehicle_number, vehicle_type, rc_number,
                          password, qr_code, unique_id, verification_status,
                          aadhaar_number, aadhaar_doc, rc_doc)
                         VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'pending', ?, ?, ?)""",
                      (name, age, mobile, email, vehicle_number, vehicle_type, rc_number,
                       hashed_password, qr_data, unique_id, aadhaar_number, enc_aadhaar, enc_rc))
            conn.commit()
            driver_id = c.lastrowid

            # Regenerate QR with real driver_id (HMAC-signed)
            qr_image, qr_data = generate_driver_qr_code(driver_id, name, vehicle_number, mobile)
            c.execute("UPDATE drivers SET qr_code = ? WHERE id = ?", (qr_data, driver_id))
            conn.commit()
            conn.close()

            return jsonify({
                "success": True,
                "message": "Driver enrolled! Account pending admin verification. You will be notified by email.",
                "user_id": driver_id,
                "unique_id": unique_id
            })
        except sqlite3.IntegrityError:
            conn.close()
            return jsonify({"success": False, "message": "Enrollment collision. One or more fields already exist."}), 400

    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

# ============================================================================
# NEW OWNER/RENTER REGISTRATION SYSTEM
# ============================================================================

@app.route('/register/driver/new')
def driver_register_new_page():
    """New multi-step driver registration page"""
    return render_template('driver_register_new.html')

@app.route('/owner/approve/<token>')
def owner_approve_view(token):
    """Secure link for owner to review and approve renter"""
    return render_template('owner_confirm.html', token=token)

@app.route('/owner_confirm')
def owner_confirm_view():
    """Alternative route — supports ?token= query param from email links"""
    token = request.args.get('token', '')
    return render_template('owner_confirm.html', token=token)

@app.route('/upload_docs')
def upload_docs_page():
    """Document upload page - accessed via token for owners"""
    token = request.args.get('token')
    driver_id = request.args.get('driver_id') # For self-uploading owners
    return render_template('driver_upload_docs.html', token=token, driver_id=driver_id)

@app.route('/api/register_driver_v2', methods=['POST'])
def register_driver_v2():
    """Unified registration for OWNER and RENT drivers using form-data"""
    try:
        # 1. Debug prints as requested
        print("--- INCOMING FORM DATA ---")
        print(request.form)
        print("--- INCOMING FILES ---")
        print(request.files)

        # 2. Extract and Step 1: Trim all text inputs
        role = request.form.get('role', 'OWNER').strip().upper()
        name = request.form.get('name', '').strip()
        age_raw = request.form.get('age', '').strip()
        mobile = request.form.get('mobile', '').strip()
        email = request.form.get('email', '').strip()
        vehicle_number = request.form.get('vehicle_number', '').strip()
        vehicle_type = request.form.get('vehicle_type', 'Car').strip()
        rc_number = request.form.get('rc_number', '').strip()
        license_number = request.form.get('license_number', '').strip()
        aadhaar_number = request.form.get('aadhaar_number', '').strip()
        address = request.form.get('address', '').strip()
        gender = request.form.get('gender', 'Any').strip()

        # 3. Individual Field Validation (No more 'if not all')
        if not name: return jsonify({"success": False, "message": "Full Name is required"}), 400
        if not age_raw: return jsonify({"success": False, "message": "Age is required"}), 400
        if not address: return jsonify({"success": False, "message": "Full Address is required"}), 400
        if not mobile: return jsonify({"success": False, "message": "Mobile Number is required"}), 400
        if not email: return jsonify({"success": False, "message": "Email Address is required"}), 400
        if not vehicle_number: return jsonify({"success": False, "message": "Vehicle Number is required"}), 400
        if not rc_number: return jsonify({"success": False, "message": "RC Number is required"}), 400
        if not license_number: return jsonify({"success": False, "message": "License Number is required"}), 400
        if not aadhaar_number: return jsonify({"success": False, "message": "Aadhaar Number is required"}), 400

        # Handle Role-specific owner_email
        owner_email = ""
        if role == 'RENT':
            owner_email = request.form.get('owner_email', '').strip()
            if not owner_email:
                return jsonify({"success": False, "message": "Owner Email is required for Renter registration"}), 400

        # File Handling Example (as per request)
        # Note: In Step 1, files might be optional or handled in Step 2, but I'll add the check as requested.
        # Registration form might have a single 'aadhar' file input.
        if request.files and 'aadhar' in request.files:
            aadhar_file = request.files.get('aadhar')
            if not aadhar_file or aadhar_file.filename == "":
                 return jsonify({"success": False, "message": "Aadhaar file is missing or empty"}), 400

        # Validate Age
        try:
            age = int(age_raw)
            if age < 18 or age > 70:
                return jsonify({"success": False, "message": "Age must be between 18 and 70"}), 400
        except ValueError:
            return jsonify({"success": False, "message": "Invalid Age format"}), 400

        if not is_valid_email(email):
            return jsonify({"success": False, "message": "Invalid Email format"}), 400

        # 4. Check for duplicates (using the requested error message)
        conn = get_db_conn()
        c = conn.cursor()

        existing_driver_id = None
        c.execute("SELECT id FROM drivers WHERE email = ?", (email,))
        em_res = c.fetchone()
        
        c.execute("SELECT id FROM drivers WHERE mobile = ?", (mobile,))
        mob_res = c.fetchone()

        if em_res or mob_res:
            if role == 'RENT':
                # No "email already exists error" for renter. Reuse existing profile!
                existing_driver_id = em_res[0] if em_res else mob_res[0]
            else:
                conn.close()
                return jsonify({"success": False, "message": "Email or Mobile already registered"}), 400

        # 5. Database Insertion
        # Status logic
        verification_status = 'pending'
        owner_id = None
        approval_token = uuid.uuid4().hex

        if role == 'RENT':
            c.execute("SELECT id FROM drivers WHERE email = ? AND role = 'OWNER'", (owner_email,))
            owner_res = c.fetchone()
            if owner_res:
                owner_id = owner_res[0]
            else:
                placeholder_pw_owner = hash_password(secrets.token_urlsafe(12))
                c.execute("""INSERT INTO drivers 
                             (name, age, mobile, email, vehicle_number, vehicle_type, rc_number, password, unique_id, verification_status, role) 
                             VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'inactive', 'OWNER')""",
                          ("Pending Owner", 0, secrets.token_hex(6), owner_email, vehicle_number, vehicle_type, "PENDING", placeholder_pw_owner, "PENDING_OWNER"))
                owner_id = c.lastrowid

        # Credentials are NOT generated here for RENTERS (only after approval)
        placeholder_pw = hash_password(secrets.token_urlsafe(12))
        unique_id = "PENDING_" + secrets.token_hex(4).upper()

        if not existing_driver_id:
            c.execute("""INSERT INTO drivers
                         (name, age, mobile, email, vehicle_number, vehicle_type, rc_number,
                          password, unique_id, verification_status, role, owner_id, license_number, aadhaar_number, address, gender)
                         VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                      (name, age, mobile, email, vehicle_number, vehicle_type, rc_number,
                       placeholder_pw, unique_id, verification_status, role, owner_id, license_number, aadhaar_number, address, gender))
            conn.commit()
            driver_id = c.lastrowid
        else:
            driver_id = existing_driver_id

        if role == 'RENT':
            c.execute("INSERT INTO renter_requests (renter_id, owner_email, owner_id, approval_token, status) VALUES (?, ?, ?, ?, 'PENDING')",
                      (driver_id, owner_email, owner_id, approval_token))
            conn.commit()
            
            # Send email to owner — non-blocking, failure won't crash registration
            try:
                send_owner_approval_email(owner_email, name, f"{vehicle_type} - {vehicle_number}", approval_token)
            except Exception as email_err:
                print(f"[WARN] Owner email failed (non-fatal): {email_err}")

        # Finalize QR — wrap in try/except so QR failure doesn't break registration
        try:
            qr_image, qr_data = generate_driver_qr_code(driver_id, name, vehicle_number, mobile)
            if qr_data:
                c.execute("UPDATE drivers SET qr_code = ? WHERE id = ?", (qr_data, driver_id))
                conn.commit()
        except Exception as qr_err:
            print(f"[WARN] QR generation failed (non-fatal): {qr_err}")
        conn.close()

        # Success Response
        if role == 'OWNER':
            msg = "Registration successful! Proceed to upload documents."
            redirect_url = f"/upload_docs?driver_id={driver_id}"
            # Store in session as backup for upload step
            session['pending_driver_id'] = driver_id
        else:
            msg = f"Registration submitted! An approval link has been sent to the vehicle owner at {owner_email}."
            redirect_url = "/register/driver/new?status=pending_owner"

        return jsonify({
            "success": True,
            "message": msg,
            "driver_id": driver_id,
            "unique_id": unique_id,
            "redirect_url": redirect_url
        })

    except Exception as e:
        print(f"Registration Final Error: {str(e)}")
        return jsonify({"success": False, "message": f"Server Error: {str(e)}"}), 500

@app.route('/api/owner_confirm_load', methods=['GET'])
def owner_confirm_load():
    """Load rent driver details for owner confirmation"""
    try:
        token = request.args.get('token', '')
        
        if not token:
            return jsonify({"success": False, "message": "Invalid token"}), 400

        conn = get_db_conn()
        c = conn.cursor()

        c.execute("SELECT renter_id, owner_id, status FROM renter_requests WHERE approval_token = ?", (token,))
        result = c.fetchone()

        if not result or result[2] != 'PENDING':
            conn.close()
            return jsonify({"success": False, "message": "Invalid or already processed token"}), 400

        renter_id, owner_id, req_status = result

        c.execute("""SELECT name, email, mobile, age, vehicle_number, vehicle_type, 
                     license_number, created_at FROM drivers WHERE id = ?""", (renter_id,))
        driver_result = c.fetchone()
        conn.close()

        if not driver_result:
            return jsonify({"success": False, "message": "Driver not found"}), 400

        return jsonify({
            "success": True,
            "driver": {
                "name": driver_result[0],
                "email": driver_result[1],
                "mobile": driver_result[2],
                "age": driver_result[3],
                "vehicle_number": driver_result[4],
                "vehicle_type": driver_result[5],
                "license_number": driver_result[6],
                "created_at": driver_result[7]
            }
        })

    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

@app.route('/api/owner_confirm_action', methods=['POST'])
def owner_confirm_action():
    """Owner approves or rejects rent driver request"""
    try:
        data = request.get_json()
        token = data.get('token', '')
        action = data.get('action', '')

        if not token or action not in ['APPROVE', 'REJECT']:
            return jsonify({"success": False, "message": "Invalid request"}), 400

        conn = get_db_conn()
        c = conn.cursor()

        c.execute("SELECT renter_id, owner_id, owner_email, status FROM renter_requests WHERE approval_token = ?", (token,))
        result = c.fetchone()

        if not result or result[3] != 'PENDING':
            conn.close()
            return jsonify({"success": False, "message": "Invalid or already processed token"}), 400

        renter_id, owner_id, owner_email, status = result

        if action == 'APPROVE':
            c.execute("UPDATE renter_requests SET status = 'APPROVED' WHERE approval_token = ?", (token,))
            c.execute("UPDATE drivers SET verification_status = 'approved_by_owner' WHERE id = ?", (renter_id,))
            conn.commit()

            c.execute("SELECT name, email FROM drivers WHERE id = ?", (renter_id,))
            renter_name, renter_email = c.fetchone()
            conn.close()

            send_email_async(
                renter_email,
                "RakshaRide - Owner Approved Your Request",
                f"""<h2>Great News!</h2>
                <p>Dear {renter_name},</p>
                <p>The vehicle owner has approved your registration request.</p>
                <p>The owner will now upload the required documents.</p>"""
            )

            return jsonify({
                "success": True,
                "message": "Request approved! Please upload vehicle documents for verification.",
                "redirect_url": f"/upload_docs?token={token}"
            })

        else:
            c.execute("UPDATE renter_requests SET status = 'REJECTED' WHERE approval_token = ?", (token,))
            c.execute("DELETE FROM drivers WHERE id = ?", (renter_id,))
            conn.commit()
            conn.close()

            return jsonify({
                "success": True,
                "message": "Request rejected."
            })

    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

@app.route('/api/upload_driver_docs', methods=['POST'])
def upload_driver_docs():
    """Upload documents and trigger final verification / credential generation"""
    try:
        # Always read from form first (multipart), fall back to JSON
        if request.content_type and 'multipart' in request.content_type:
            token = request.form.get('token', '').strip()
            driver_id = request.form.get('driver_id', '').strip()
        elif request.is_json:
            data = request.get_json() or {}
            token = str(data.get('token') or '').strip()
            driver_id = str(data.get('driver_id') or '').strip()
        else:
            # Fallback: try both
            token = (request.form.get('token') or '').strip()
            driver_id = (request.form.get('driver_id') or '').strip()

        # Normalise — treat "None"/"null"/"undefined" as empty
        if token in ('None', 'null', 'undefined', ''):
            token = ''
        if driver_id in ('None', 'null', 'undefined', ''):
            driver_id = ''

        # Last resort: check Flask session (set during registration)
        if not driver_id and not token:
            driver_id = str(session.get('pending_driver_id', ''))

        print(f"[UPLOAD] driver_id={driver_id!r} token={'none' if not token else token[:8]+'...'}")

        conn = get_db_conn()
        conn.row_factory = sqlite3.Row
        c = conn.cursor()

        # Resolve driver_id from token (rent driver flow via owner approval link)
        if token:
            c.execute("SELECT renter_id, owner_id FROM renter_requests WHERE approval_token = ?", (token,))
            req = c.fetchone()
            if not req:
                conn.close()
                return jsonify({"success": False, "message": "Invalid or expired approval link. Please ask the owner to resend the confirmation email."}), 400
            driver_id = str(req['renter_id'])
            uploader_id = req['owner_id'] or driver_id
        else:
            # Owner uploading their own documents directly
            if not driver_id:
                conn.close()
                return jsonify({"success": False, "message": "Missing driver ID. Please go back and register again."}), 400
            uploader_id = driver_id

        # ── Profile Image ─────────────────────────────────────────────────────
        if 'profile_image' in request.files and request.files['profile_image'].filename:
            profile_data = save_uploaded_file(request.files['profile_image'], PROFILE_DIR, f"p_{driver_id}")
            if profile_data:
                # Store in drivers table
                c.execute("UPDATE drivers SET profile_image = ? WHERE id = ?", (profile_data, driver_id))
                # Also store in driver_documents as 'photo' so dashboard can show it
                c.execute("DELETE FROM driver_documents WHERE driver_id = ? AND doc_type = 'photo'", (driver_id,))
                c.execute("""INSERT INTO driver_documents (driver_id, uploaded_by, doc_type, file_data, ai_status)
                             VALUES (?, ?, 'photo', ?, 'PENDING')""", (driver_id, uploader_id, profile_data))

        # ── Document Uploads ──────────────────────────────────────────────────
        doc_map = {
            'aadhar_doc':  'aadhaar',
            'license_doc': 'license',
            'rc_doc':      'rc',
        }
        for file_key, doc_type in doc_map.items():
            if file_key in request.files and request.files[file_key].filename:
                doc_data = save_uploaded_file(request.files[file_key], DOC_DIR, f"d_{driver_id}_{doc_type}")
                if doc_data:
                    c.execute("DELETE FROM driver_documents WHERE driver_id = ? AND doc_type = ?", (driver_id, doc_type))
                    c.execute("""INSERT INTO driver_documents (driver_id, uploaded_by, doc_type, file_data, ai_status)
                                 VALUES (?, ?, ?, ?, 'PENDING')""", (driver_id, uploader_id, doc_type, doc_data))
                    print(f"[UPLOAD] Saved {doc_type} for driver {driver_id} ({len(doc_data)} chars)")

        # ── JSON Base64 legacy path ───────────────────────────────────────────
        if request.is_json:
            json_data = request.get_json() or {}
            for doc_type, base64_data in (json_data.get('documents') or {}).items():
                if base64_data:
                    enc = encrypt_document(base64_data)
                    c.execute("DELETE FROM driver_documents WHERE driver_id = ? AND doc_type = ?", (driver_id, doc_type))
                    c.execute("""INSERT INTO driver_documents (driver_id, uploaded_by, doc_type, file_data, ai_status)
                                 VALUES (?, ?, ?, ?, 'PENDING')""", (driver_id, uploader_id, doc_type, enc))

        # ── Status & Credentials ──────────────────────────────────────────────
        c.execute("SELECT * FROM drivers WHERE id = ?", (driver_id,))
        driver = c.fetchone()
        if not driver:
            conn.close()
            return jsonify({"success": False, "message": "Driver record not found after upload"}), 404

        # Mark verified
        c.execute("UPDATE drivers SET verification_status = 'verified' WHERE id = ?", (driver_id,))
        if token and driver['owner_id']:
            c.execute("UPDATE drivers SET verification_status = 'verified' WHERE id = ?", (driver['owner_id'],))

        # Generate credentials
        raw_password = secrets.token_urlsafe(10)
        hashed_pw = hash_password(raw_password)
        new_unique_id = f"DRV{int(driver_id):04d}"

        # Generate QR — generate_driver_qr_code returns (b64_png, b64_png)
        try:
            qr_image_b64, _ = generate_driver_qr_code(
                driver_id, driver['name'], driver['vehicle_number'], driver['mobile'])
            qr_to_store = qr_image_b64  # Store the base64 PNG directly
        except Exception as qr_err:
            print(f"[WARN] QR generation failed: {qr_err}")
            qr_to_store = None  # Will be regenerated on next login

        c.execute("""UPDATE drivers
                     SET unique_id = ?, password = ?, qr_code = ?, first_login = 1
                     WHERE id = ?""",
                  (new_unique_id, hashed_pw, qr_to_store, driver_id))

        conn.commit()
        conn.close()

        # Send credentials email (non-blocking — failure won't break response)
        try:
            _send_credentials_email(driver['email'], driver['name'], new_unique_id, raw_password)
        except Exception as email_err:
            print(f"[WARN] Credentials email failed (non-fatal): {email_err}")

        print(f"[UPLOAD] ✅ Driver {driver_id} verified. ID={new_unique_id}")
        return jsonify({
            "success": True,
            "message": "Documents uploaded and credentials generated!",
            "unique_id": new_unique_id,
            "temp_password": raw_password
        })
    except Exception as e:
        print(f"Docs Upload Error: {e}")
        return jsonify({"success": False, "message": str(e)}), 500

@app.route('/driver/<int:driver_id>')
def driver_public_profile(driver_id):
    """Public driver profile accessible via QR scan"""
    try:
        conn = get_db_conn()
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        c.execute("SELECT * FROM drivers WHERE id = ?", (driver_id,))
        driver = c.fetchone()
        conn.close()
        
        if not driver: return "Driver not found", 404
            
        return render_template('driver_profile_public.html', driver=driver)
    except Exception as e:
        return str(e), 500

@app.route('/api/get_driver_docs', methods=['GET'])
def get_driver_docs():
    """Fetch documents for dashboard display"""
    try:
        if 'user_id' not in session or session.get('user_type') != 'driver':
            return jsonify({"success": False, "message": "Unauthorized"}), 401
        
        driver_id = session['user_id']
        conn = get_db_conn()
        c = conn.cursor()
        
        c.execute("SELECT doc_type, ai_status, file_data FROM driver_documents WHERE driver_id = ?", (driver_id,))
        docs = []
        for r in c.fetchall():
            doc_type, status, data = r
            # If data is a path, we serve it via static
            if data and (data.startswith('static/') or data.startswith('uploads/')):
                # Convert to absolute or standard relative for frontend
                web_path = f"/{data}" if not data.startswith('/') else data
                docs.append({"type": doc_type, "status": status, "path": web_path})
            else:
                # Legacy Base64
                docs.append({"type": doc_type, "status": status, "data": data})
                
        conn.close()
        return jsonify({"success": True, "documents": docs})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

@app.route('/api/login_passenger', methods=['POST'])
def login_passenger():
    """Passenger login — non-blocking OTP send."""
    try:
        data = request.get_json() or {}
        credential = (data.get('credential') or data.get('email') or '').strip()
        password   = (data.get('password') or '').strip()

        if not credential or not password:
            return jsonify({"success": False, "message": "Email and password required"}), 400

        hashed_password = hash_password(password)
        conn = get_db_conn()
        c = conn.cursor()
        c.execute("""SELECT id, name, email, phone FROM passengers
                     WHERE (email = ? OR phone = ?) AND password = ?""",
                  (credential, credential, hashed_password))
        result = c.fetchone()

        if not result:
            conn.close()
            return jsonify({"success": False, "message": "Invalid email/phone or password"}), 401

        user_id, name, email, phone = result

        otp = generate_otp()
        expiry_time = datetime.now() + timedelta(minutes=5)
        c.execute("DELETE FROM otp_verification WHERE email = ?", (email,))
        c.execute("INSERT INTO otp_verification (email, otp, expiry_time, attempts) VALUES (?, ?, ?, 0)",
                  (email, otp, expiry_time))
        conn.commit()
        conn.close()

        # Session backup for Render DB resets
        session[f'otp_{email}'] = {'otp': otp, 'expiry': expiry_time.isoformat()}
        session.permanent = True

        html = (
            "<div style='font-family:Arial;padding:20px'>"
            "<h2 style='color:#1565C0'>RakshaRide Login OTP</h2>"
            "<p>Your login verification code:</p>"
            "<div style='font-size:36px;font-weight:900;letter-spacing:10px;color:#FFC107;"
            "padding:20px;background:#f5f5f5;border-radius:10px;text-align:center'>"
            + otp +
            "</div>"
            "<p style='color:#666;margin-top:16px'>Valid for <strong>5 minutes</strong>.</p>"
            "</div>"
        )
        send_email_async(email, "RakshaRide Login OTP", html, f"Login OTP: {otp}")
        print(f"[LOGIN OTP] {email}: {otp}")

        return jsonify({
            "success": True,
            "requires_otp": True,
            "email": email,
            "message": f"Verification code sent to {email}. Check your inbox.",
            "email_sent": True
        })

    except Exception as e:
        print(f"[login_passenger ERROR] {e}")
        return jsonify({"success": False, "message": "An internal error occurred. Please try again."}), 500


@app.route('/api/verify_login_otp_passenger', methods=['POST'])
def verify_login_otp_passenger():
    """Passenger login Step 2: Verify OTP -> Grant Session"""
    try:
        data = request.get_json()
        email = data.get('email', '').strip()
        otp = data.get('otp', '').strip()
        
        if not email or not otp:
            return jsonify({"success": False, "message": "Email and OTP required"}), 400
        
        # Call common verification
        # But here we also need to set the session for the actual user
        
        conn = get_db_conn()
        c = conn.cursor()
        
        c.execute("SELECT otp, expiry_time FROM otp_verification WHERE email = ?", (email,))
        result = c.fetchone()
        
        if not result or result[0] != otp:
            conn.close()
            return jsonify({"success": False, "message": "Invalid or expired OTP"}), 400
            
        # Clear OTP
        c.execute("DELETE FROM otp_verification WHERE email = ?", (email,))
        
        # Get User Info
        c.execute("SELECT id, name, email, phone, total_rides, total_spent FROM passengers WHERE email = ?", (email,))
        user_info = c.fetchone()
        conn.commit()
        conn.close()
        
        if user_info:
            session['user_id'] = user_info[0]
            session['user_name'] = user_info[1]
            session['user_type'] = 'passenger'
            session.permanent = True
            token = generate_token(user_info[0], 'passenger', user_info[1])
            return jsonify({
                "success": True, 
                "message": "Login successful!",
                "token": token,
                "user": {
                    "id": user_info[0],
                    "name": user_info[1],
                    "email": user_info[2],
                    "phone": user_info[3],
                    "type": "passenger",
                    "total_rides": user_info[4],
                    "total_spent": user_info[5]
                }
            })
        
        return jsonify({"success": False, "message": "User not found after OTP"}), 404
        
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

@app.route('/api/login_driver', methods=['POST'])
def login_driver():
    """Driver login with User ID (DRVxxxx) or Email, handles first-time password change"""
    try:
        data = request.get_json()
        credential = data.get('credential', '').strip()
        password = data.get('password', '').strip()
        
        if not credential or not password:
            return jsonify({"success": False, "message": "Credentials required"}), 400
            
        conn = get_db_conn()
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        
        # Accept email OR unique_id (DRVxxxx)
        c.execute("SELECT * FROM drivers WHERE unique_id = ? OR email = ?", (credential, credential))
        driver = c.fetchone()
        
        if not driver:
            conn.close()
            return jsonify({"success": False, "message": "Invalid User ID or password"}), 401
            
        if driver['password'] != hash_password(password):
            conn.close()
            return jsonify({"success": False, "message": "Invalid User ID or password"}), 401
            
        if driver['verification_status'] not in ['approved', 'verified']:
            conn.close()
            return jsonify({"success": False, "message": "Account under review. Credentials available after approval/verification."}), 403
            
        # Check if first login
        requires_password_change = bool(driver['first_login'])
        
        # Set session
        session['user_id'] = driver['id']
        session['user_type'] = 'driver'
        session['name'] = driver['name']
        session['unique_id'] = driver['unique_id']
        session.permanent = True

        # Generate JWT token so authFetch works on Render (session cookies unreliable cross-origin)
        token = generate_token(driver['id'], 'driver', driver['name'])
        
        conn.close()
        
        return jsonify({
            "success": True,
            "message": "Login successful",
            "token": token,
            "user_type": "driver",
            "driver_id": driver['id'],
            "unique_id": driver['unique_id'],
            "redirect_url": "/change_password" if requires_password_change else "/dashboard/driver"
        })
        
    except Exception as e:
        print(f"Login error: {str(e)}")
        return jsonify({"success": False, "message": str(e)}), 500

@app.route('/change_password')
def change_password_page():
    if 'user_id' not in session:
        return render_template('login_govt.html')
    return render_template('change_password.html')

@app.route('/api/update_password', methods=['POST'])
def update_password():
    """First-time password change for approved drivers"""
    try:
        if 'user_id' not in session:
            return jsonify({"success": False, "message": "Unauthorized"}), 401
            
        data = request.get_json()
        new_password = data.get('new_password', '').strip()
        confirm_password = data.get('confirm_password', '').strip()
        
        if len(new_password) < 6:
            return jsonify({"success": False, "message": "New password must be 6+ characters"}), 400
            
        if new_password != confirm_password:
            return jsonify({"success": False, "message": "Passwords do not match"}), 400
            
        conn = get_db_conn()
        c = conn.cursor()
        c.execute("UPDATE drivers SET password = ?, first_login = 0 WHERE id = ?",
                  (hash_password(new_password), session['user_id']))
        conn.commit()
        conn.close()
        
        return jsonify({"success": True, "message": "Password updated successfully!", "redirect": "/dashboard/driver"})
        
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

@app.route('/api/get_driver_overview')
def get_driver_overview():
    """Returns summarized stats for the driver intelligence dashboard"""
    try:
        if 'user_id' not in session or session['user_type'] != 'driver':
            return jsonify({"success": False, "message": "Unauthorized"}), 401
            
        driver_id = session['user_id']
        conn = get_db_conn()
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        
        # Total rides and earnings
        c.execute("SELECT COUNT(*) as count, SUM(fare) as earnings, SUM(distance_km) as distance FROM rides WHERE driver_id = ? AND status = 'completed'", (driver_id,))
        stats = c.fetchone()
        
        # Unique passengers
        c.execute("SELECT COUNT(DISTINCT passenger_id) as passengers FROM rides WHERE driver_id = ?", (driver_id,))
        passengers = c.fetchone()
        
        # Mock earnings history for chart (last 7 days)
        # In a real app, this would be grouped by date from the DB
        earnings_history = [
            {"date": (datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d'), "amount": 0}
            for i in range(6, -1, -1)
        ]
        
        c.execute("""
            SELECT strftime('%Y-%m-%d', start_time) as date, SUM(fare) as daily_total 
            FROM rides 
            WHERE driver_id = ? AND status = 'completed' AND start_time >= date('now', '-7 days')
            GROUP BY date
        """, (driver_id,))
        
        db_history = {row['date']: row['daily_total'] for row in c.fetchall()}
        for day in earnings_history:
            if day['date'] in db_history:
                day['amount'] = db_history[day['date']]
                
        conn.close()
        
        return jsonify({
            "success": True,
            "total_rides": stats['count'] or 0,
            "total_earned": stats['earnings'] or 0,
            "total_distance": stats['distance'] or 0,
            "total_passengers": passengers['passengers'] or 0,
            "earnings_history": earnings_history
        })
        
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

@app.route('/api/get_driver_ratings')
def get_driver_ratings():
    """Fetched ratings and reviews for the Trust Score section"""
    try:
        if 'user_id' not in session or session['user_type'] != 'driver':
            return jsonify({"success": False, "message": "Unauthorized"}), 401
            
        driver_id = session['user_id']
        conn = get_db_conn()
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        
        c.execute("SELECT * FROM ratings WHERE driver_id = ? ORDER BY created_at DESC", (driver_id,))
        reviews = [dict(row) for row in c.fetchall()]
        
        c.execute("SELECT AVG(rating) as avg FROM ratings WHERE driver_id = ?", (driver_id,))
        avg = c.fetchone()['avg'] or 5.0
        
        conn.close()
        
        return jsonify({
            "success": True,
            "average": avg,
            "reviews": reviews
        })
        
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

@app.route('/api/submit_rating', methods=['POST'])
def submit_rating():
    """Allows passengers to rate drivers after a ride"""
    try:
        if 'user_id' not in session or session['user_type'] != 'passenger':
            return jsonify({"success": False, "message": "Only passengers can submit ratings"}), 401
            
        data = request.get_json()
        driver_id = data.get('driver_id')
        rating = data.get('rating')
        comment = data.get('comment', '')
        ride_id = data.get('ride_id')
        
        if not driver_id or not rating:
            return jsonify({"success": False, "message": "Missing rating details"}), 400
            
        conn = get_db_conn()
        c = conn.cursor()
        c.execute("INSERT INTO ratings (driver_id, passenger_id, ride_id, rating, comment) VALUES (?, ?, ?, ?, ?)",
                  (driver_id, session['user_id'], ride_id, rating, comment))
        
        # Update driver average rating Cache
        c.execute("UPDATE drivers SET rating = (SELECT AVG(rating) FROM ratings WHERE driver_id = ?) WHERE id = ?",
                  (driver_id, driver_id))
                  
        conn.commit()
        conn.close()
        
        return jsonify({"success": True, "message": "Feedback submitted! Thank you."})
        
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

@app.route('/api/get_driver_profile_for_passenger')
def get_driver_profile_for_passenger():
    """Public driver profile view for scanner activation"""
    try:
        unique_id = request.args.get('unique_id')
        if not unique_id:
            return jsonify({"success": False, "message": "Invalid QR Payload"}), 400
            
        conn = get_db_conn()
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        
        c.execute("SELECT id, name, vehicle_type, vehicle_number, rating, verification_status, profile_image FROM drivers WHERE unique_id = ?", (unique_id,))
        driver = c.fetchone()
        
        if not driver:
            conn.close()
            return jsonify({"success": False, "message": "Driver not found"}), 404
            
        if driver['verification_status'] != 'verified':
            conn.close()
            return jsonify({"success": False, "message": "Driver not verified by RakshaRide"}), 403
            
        res = dict(driver)
        conn.close()
        
        return jsonify({"success": True, "profile": res})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

@app.route('/api/verify_login_otp_driver', methods=['POST'])
def verify_login_otp_driver():
    """Driver login Step 2: Verify OTP -> Grant Session"""
    try:
        data = request.get_json()
        email = data.get('email', '').strip()
        otp = data.get('otp', '').strip()
        
        if not email or not otp:
            return jsonify({"success": False, "message": "Email and OTP required"}), 400
        
        conn = get_db_conn()
        c = conn.cursor()
        
        c.execute("SELECT otp, expiry_time FROM otp_verification WHERE email = ?", (email,))
        result = c.fetchone()
        
        if not result or result[0] != otp:
            conn.close()
            return jsonify({"success": False, "message": "Invalid or expired OTP"}), 400
            
        # Clear OTP
        c.execute("DELETE FROM otp_verification WHERE email = ?", (email,))
        
        # Get User Info
        c.execute("""SELECT id, name, email, mobile, vehicle_number, vehicle_type, rating, total_rides, total_earned 
                     FROM drivers WHERE email = ?""", (email,))
        user_info = c.fetchone()
        conn.commit()
        conn.close()
        
        if user_info:
            session['user_id'] = user_info[0]
            session['user_name'] = user_info[1]
            session['user_type'] = 'driver'
            session.permanent = True
            token = generate_token(user_info[0], 'driver', user_info[1])
            return jsonify({
                "success": True, 
                "message": "Login successful!",
                "token": token,
                "user": {
                    "id": user_info[0],
                    "name": user_info[1],
                    "email": user_info[2],
                    "mobile": user_info[3],
                    "vehicle_number": user_info[4],
                    "vehicle_type": user_info[5],
                    "type": "driver",
                    "rating": user_info[6],
                    "total_rides": user_info[7],
                    "total_earned": user_info[8]
                }
            })
        
        return jsonify({"success": False, "message": "Driver not found after OTP"}), 404
        
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

# Continue with ride management APIs in next part...

# ============================================================================
# QR Code & Driver APIs
# ============================================================================

@app.route('/api/get_driver_qr', methods=['GET'])
def get_driver_qr():
    """Get driver's QR code"""
    try:
        if 'user_id' not in session or session.get('user_type') != 'driver':
            return jsonify({"success": False, "message": "Unauthorized"}), 401
        
        driver_id = session['user_id']
        
        conn = get_db_conn()
        c = conn.cursor()
        c.execute("SELECT name, vehicle_number, mobile, qr_code FROM drivers WHERE id = ?", (driver_id,))
        result = c.fetchone()
        conn.close()
        
        if not result:
            return jsonify({"success": False, "message": "Driver not found"}), 404
        
        name, vehicle_number, mobile, qr_data = result
        
        # Generate QR image
        qr_image, _ = generate_driver_qr_code(driver_id, name, vehicle_number, mobile)
        
        return jsonify({
            "success": True,
            "qr_image": qr_image,
            "qr_data": qr_data,
            "driver": {
                "id": driver_id,
                "name": name,
                "vehicle": vehicle_number,
                "mobile": mobile
            }
        })
        
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

@app.route('/api/scan_driver_qr', methods=['POST'])
def scan_driver_qr():
    """Scan driver QR â€” verify HMAC signature and expiry"""
    try:
        if 'user_id' not in session or session.get('user_type') != 'passenger':
            return jsonify({"success": False, "message": "Unauthorized"}), 401

        data = request.get_json()
        qr_data_str = data.get('qr_data', '')
        if not qr_data_str:
            return jsonify({"success": False, "message": "QR data required"}), 400

        # Verify HMAC + expiry
        is_valid, err_msg, qr_data = verify_qr_payload(qr_data_str)
        if not is_valid:
            return jsonify({"success": False, "message": err_msg}), 400

        if qr_data.get('type') != 'driver':
            return jsonify({"success": False, "message": "Not a driver QR code"}), 400

        driver_id = qr_data.get('driver_id')

        conn = get_db_conn()
        c = conn.cursor()
        c.execute("""SELECT id, name, mobile, vehicle_number, vehicle_type, rating,
                            total_rides, is_available, verification_status
                     FROM drivers WHERE id = ?""", (driver_id,))
        result = c.fetchone()
        conn.close()

        if not result:
            return jsonify({"success": False, "message": "Driver not found"}), 404

        did, name, mobile, vehicle_number, vehicle_type, rating, total_rides, is_available, vstatus = result

        if vstatus not in ['approved', 'verified']:
            return jsonify({"success": False, "message": "Driver not yet verified by admin"}), 403

        if not is_available:
            return jsonify({"success": False, "message": "Driver is currently not available"}), 400

        return jsonify({
            "success": True,
            "message": "âœ… Driver identity verified (HMAC OK)",
            "driver": {
                "id": did, "name": name, "mobile": mobile,
                "vehicle_number": vehicle_number, "vehicle_type": vehicle_type,
                "rating": rating, "total_rides": total_rides,
                "is_available": bool(is_available)
            }
        })

    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

@app.route('/api/get_nearby_drivers', methods=['GET'])
def get_nearby_drivers():
    """Get list of available drivers (nearby)"""
    try:
        conn = get_db_conn()
        c = conn.cursor()
        c.execute("""SELECT id, name, vehicle_type, vehicle_number, rating, total_rides, latitude, longitude
                     FROM drivers WHERE is_available = 1""")
        results = c.fetchall()
        conn.close()
        
        drivers = []
        for r in results:
            drivers.append({
                "id": r[0],
                "name": r[1],
                "vehicle_type": r[2],
                "vehicle_number": r[3],
                "rating": r[4],
                "total_rides": r[5],
                "latitude": r[6],
                "longitude": r[7]
            })
        
        return jsonify({"success": True, "drivers": drivers})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

@app.route('/api/update_driver_location', methods=['POST'])
def update_driver_location():
    """Update driver's current location"""
    try:
        if 'user_id' not in session or session.get('user_type') != 'driver':
            return jsonify({"success": False, "message": "Unauthorized"}), 401
        
        data = request.get_json()
        driver_id = session['user_id']
        lat = data.get('latitude')
        lng = data.get('longitude')
        
        conn = get_db_conn()
        c = conn.cursor()
        c.execute("UPDATE drivers SET latitude = ?, longitude = ? WHERE id = ?", (lat, lng, driver_id))
        conn.commit()
        conn.close()
        
        return jsonify({"success": True, "message": "Location updated"})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

@app.route('/api/update_upi_id', methods=['POST'])
def update_upi_id():
    """Update driver's UPI ID for payments"""
    try:
        if 'user_id' not in session or session.get('user_type') != 'driver':
            return jsonify({"success": False, "message": "Unauthorized"}), 401
        
        data = request.get_json()
        driver_id = session['user_id']
        upi_id = data.get('upi_id')
        
        conn = get_db_conn()
        c = conn.cursor()
        c.execute("UPDATE drivers SET upi_id = ? WHERE id = ?", (upi_id, driver_id))
        conn.commit()
        conn.close()
        
        return jsonify({"success": True, "message": "UPI ID updated successfully!"})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

@app.route('/api/start_ride', methods=['POST'])
def start_ride():
    """Start a new ride — supports both session and JWT auth"""
    try:
        pid, err = _require_passenger()
        if err: return err
        passenger_id = pid

        data = request.get_json()
        driver_id = data.get('driver_id')
        pickup_location = data.get('pickup_location', 'Current Location')
        dropoff_location = data.get('dropoff_location', 'Destination')
        start_lat = data.get('latitude') or data.get('lat')
        start_lng = data.get('longitude') or data.get('lng')

        if not driver_id:
            return jsonify({"success": False, "message": "Driver ID required"}), 400

        conn = get_db_conn()
        c = conn.cursor()

        c.execute("SELECT name, phone FROM passengers WHERE id = ?", (passenger_id,))
        passenger_result = c.fetchone()
        if not passenger_result:
            conn.close()
            return jsonify({"success": False, "message": "Passenger not found"}), 404

        c.execute("SELECT name, mobile, vehicle_number, vehicle_type, is_available, unique_id FROM drivers WHERE id = ?", (driver_id,))
        driver_result = c.fetchone()
        if not driver_result:
            conn.close()
            return jsonify({"success": False, "message": "Driver not found"}), 404

        passenger_name, passenger_phone = passenger_result
        driver_name, driver_mobile, driver_vehicle, vehicle_type, is_available, driver_uid = driver_result

        if not is_available:
            conn.close()
            return jsonify({"success": False, "message": "Driver is currently busy. Please try another driver."}), 400

        # Check if passenger already has active ride
        c.execute("SELECT id FROM rides WHERE passenger_id = ? AND status = 'active'", (passenger_id,))
        existing = c.fetchone()
        if existing:
            conn.close()
            return jsonify({
                "success": True,
                "message": "Resuming existing ride",
                "ride": {"id": existing[0], "status": "active",
                         "driver_name": driver_name, "driver_vehicle": driver_vehicle}
            })

        start_time = datetime.now()
        c.execute("""INSERT INTO rides
                     (passenger_id, driver_id, passenger_name, passenger_phone,
                      driver_name, driver_mobile, driver_vehicle,
                      pickup_location, dropoff_location,
                      start_lat, start_lng, start_time, status)
                     VALUES (?,?,?,?,?,?,?,?,?,?,?,?,'active')""",
                  (passenger_id, driver_id, passenger_name, passenger_phone,
                   driver_name, driver_mobile, driver_vehicle,
                   pickup_location, dropoff_location,
                   start_lat, start_lng, start_time))
        ride_id = c.lastrowid
        c.execute("UPDATE drivers SET is_available = 0 WHERE id = ?", (driver_id,))
        conn.commit()
        conn.close()

        return jsonify({
            "success": True,
            "message": "Ride started successfully!",
            "ride_id": ride_id,
            "ride": {
                "id": ride_id,
                "passenger_name": passenger_name,
                "driver_name": driver_name,
                "driver_mobile": driver_mobile,
                "driver_vehicle": driver_vehicle,
                "vehicle_type": vehicle_type,
                "pickup_location": pickup_location,
                "start_time": start_time.isoformat(),
                "status": "active"
            }
        })
        
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

@app.route('/api/toggle_availability', methods=['POST'])
def toggle_availability():
    """Toggle driver's availability status"""
    try:
        if 'user_id' not in session or session.get('user_type') != 'driver':
            return jsonify({"success": False, "message": "Unauthorized"}), 401
        
        driver_id = session['user_id']
        
        conn = get_db_conn()
        c = conn.cursor()
        c.execute("UPDATE drivers SET is_available = 1 - is_available WHERE id = ?", (driver_id,))
        c.execute("SELECT is_available FROM drivers WHERE id = ?", (driver_id,))
        is_available = c.fetchone()[0]
        conn.commit()
        conn.close()
        
        return jsonify({"success": True, "is_available": bool(is_available)})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

@app.route('/api/complete_ride', methods=['POST'])
def complete_ride():
    """Complete a ride — supports JWT + session auth"""
    try:
        current_user = get_current_user()
        if not current_user:
            return jsonify({"success": False, "message": "Not authenticated"}), 401
        data = request.get_json()
        ride_id = data.get('ride_id')
        distance_km = data.get('distance_km', 5.0)  # Default 5km if not provided
        
        if not ride_id:
            return jsonify({"success": False, "message": "Ride ID required"}), 400
        
        conn = get_db_conn()
        c = conn.cursor()
        
        # Get ride details
        c.execute("""SELECT passenger_id, driver_id, start_time, status 
                     FROM rides WHERE id = ?""", (ride_id,))
        result = c.fetchone()
        
        if not result:
            conn.close()
            return jsonify({"success": False, "message": "Ride not found"}), 404
        
        passenger_id, driver_id, start_time_str, status = result
        
        if status != 'active':
            conn.close()
            return jsonify({"success": False, "message": "Ride is not active"}), 400
        
        # Calculate duration and fare
        start_time = datetime.fromisoformat(start_time_str.replace(' ', 'T'))
        end_time = datetime.now()
        duration = end_time - start_time
        duration_minutes = int(duration.total_seconds() / 60)
        
        fare = calculate_fare(duration_minutes, distance_km)
        
        route_coordinates = data.get('route_coordinates', '[]')
        
        # Update ride
        end_lat = data.get('latitude')
        end_lng = data.get('longitude')
        
        c.execute("""UPDATE rides SET end_time = ?, duration_minutes = ?, distance_km = ?, 
                     fare = ?, route_coordinates = ?, end_lat = ?, end_lng = ?, status = 'completed' WHERE id = ?""",
                   (end_time, duration_minutes, distance_km, fare, route_coordinates, end_lat, end_lng, ride_id))
        
        # Update driver availability and stats
        c.execute("""UPDATE drivers SET is_available = 1, total_rides = total_rides + 1, 
                     total_earned = total_earned + ? WHERE id = ?""", (fare, driver_id))
        
        # Update passenger stats
        c.execute("""UPDATE passengers SET total_rides = total_rides + 1, 
                     total_spent = total_spent + ? WHERE id = ?""", (fare, passenger_id))
        
        # Create payment record
        c.execute("""INSERT INTO payments (ride_id, passenger_id, driver_id, amount, status) 
                     VALUES (?, ?, ?, ?, 'pending')""", (ride_id, passenger_id, driver_id, fare))
        payment_id = c.lastrowid
        
        # Get driver name and UPI ID for payment QR
        c.execute("SELECT name, upi_id FROM drivers WHERE id = ?", (driver_id,))
        drv_result = c.fetchone()
        driver_name = drv_result[0]
        upi_id = drv_result[1]
        
        # Generate payment QR
        payment_qr = generate_payment_qr_code(ride_id, fare, driver_name, upi_id)
        c.execute("UPDATE payments SET payment_qr = ? WHERE id = ?", (payment_qr, payment_id))
        
        conn.commit()
        conn.close()
        
        print(f"\n{'='*60}")
        print(f"âœ… RIDE COMPLETED")
        print(f"Ride ID: {ride_id}")
        print(f"Duration: {duration_minutes} minutes")
        print(f"Distance: {distance_km} km")
        print(f"Fare: â‚¹{fare}")
        print(f"{'='*60}\n")
        
        return jsonify({
            "success": True,
            "message": "Ride completed successfully!",
            "ride": {
                "id": ride_id,
                "duration_minutes": duration_minutes,
                "distance_km": distance_km,
                "fare": fare,
                "payment_qr": payment_qr,
                "payment_id": payment_id
            }
        })
        
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

# Continue with history and payment APIs in next part...

# ============================================================================
# History & Profile APIs
# ============================================================================

@app.route('/api/get_passenger_history', methods=['GET'])
def get_passenger_history():
    """Get passenger ride history"""
    try:
        if 'user_id' not in session or session.get('user_type') != 'passenger':
            return jsonify({"success": False, "message": "Unauthorized"}), 401
        
        passenger_id = session['user_id']
        
        conn = get_db_conn()
        c = conn.cursor()
        
        c.execute("""SELECT r.id, r.driver_name, r.driver_mobile, r.driver_vehicle, 
                     r.pickup_location, r.dropoff_location, r.start_time, r.end_time, 
                     r.duration_minutes, r.distance_km, r.fare, r.status, r.payment_status,
                     p.status as payment_status_detail, p.paid_at
                     FROM rides r
                     LEFT JOIN payments p ON r.id = p.ride_id
                     WHERE r.passenger_id = ?
                     ORDER BY r.created_at DESC""", (passenger_id,))
        
        rides = []
        for row in c.fetchall():
            rides.append({
                "id": row[0],
                "driver_name": row[1],
                "driver_mobile": row[2],
                "driver_vehicle": row[3],
                "pickup_location": row[4],
                "dropoff_location": row[5],
                "start_time": row[6],
                "end_time": row[7],
                "duration_minutes": row[8],
                "distance_km": row[9],
                "fare": row[10],
                "status": row[11],
                "payment_status": row[12],
                "paid_at": row[14]
            })
        
        conn.close()
        
        return jsonify({
            "success": True,
            "rides": rides,
            "total_rides": len(rides)
        })
        
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

@app.route('/api/get_driver_history', methods=['GET'])
def get_driver_history():
    """Get driver ride history"""
    try:
        if 'user_id' not in session or session.get('user_type') != 'driver':
            return jsonify({"success": False, "message": "Unauthorized"}), 401
        
        driver_id = session['user_id']
        
        conn = get_db_conn()
        c = conn.cursor()
        
        c.execute("""SELECT r.id, r.passenger_name, r.passenger_phone, 
                     r.pickup_location, r.dropoff_location, r.start_time, r.end_time, 
                     r.duration_minutes, r.distance_km, r.fare, r.status, r.payment_status,
                     p.status as payment_status_detail, p.paid_at
                     FROM rides r
                     LEFT JOIN payments p ON r.id = p.ride_id
                     WHERE r.driver_id = ?
                     ORDER BY r.created_at DESC""", (driver_id,))
        
        rides = []
        for row in c.fetchall():
            rides.append({
                "id": row[0],
                "passenger_name": row[1],
                "passenger_phone": row[2],
                "pickup_location": row[3],
                "dropoff_location": row[4],
                "start_time": row[5],
                "end_time": row[6],
                "duration_minutes": row[7],
                "distance_km": row[8],
                "fare": row[9],
                "status": row[10],
                "payment_status": row[11],
                "paid_at": row[13]
            })
        
        conn.close()
        
        return jsonify({
            "success": True,
            "rides": rides,
            "total_rides": len(rides)
        })
        
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

@app.route('/api/get_active_ride', methods=['GET'])
def get_active_ride():
    """Get user's active ride — supports JWT + session auth"""
    try:
        current_user = get_current_user()
        if not current_user:
            return jsonify({"success": False, "message": "Not authenticated"}), 401

        user_id = current_user['user_id']
        user_type = current_user.get('user_type', '')

        conn = get_db_conn()
        c = conn.cursor()

        if user_type == 'passenger':
            c.execute("""SELECT r.id, r.driver_name, r.driver_mobile, r.driver_vehicle,
                         r.pickup_location, r.start_time, d.latitude, d.longitude, r.driver_id
                         FROM rides r
                         LEFT JOIN drivers d ON r.driver_id = d.id
                         WHERE r.passenger_id = ? AND r.status = 'active'
                         ORDER BY r.start_time DESC LIMIT 1""", (user_id,))
        else:
            c.execute("""SELECT r.id, r.passenger_name, r.passenger_phone, r.driver_vehicle,
                         r.pickup_location, r.start_time, d.latitude, d.longitude, r.passenger_id
                         FROM rides r
                         LEFT JOIN drivers d ON r.driver_id = d.id
                         WHERE r.driver_id = ? AND r.status = 'active'
                         ORDER BY r.start_time DESC LIMIT 1""", (user_id,))

        result = c.fetchone()
        conn.close()

        if not result:
            return jsonify({"success": True, "ride": None, "active_ride": None})

        ride = {
            "id": result[0],
            "driver_name": result[1] if user_type == 'passenger' else None,
            "passenger_name": result[1] if user_type == 'driver' else None,
            "other_party_name": result[1],
            "other_party_contact": result[2],
            "driver_vehicle": result[3],
            "pickup_location": result[4],
            "start_time": result[5],
            "driver_lat": result[6],
            "driver_lng": result[7],
            "status": "active"
        }
        return jsonify({"success": True, "ride": ride, "active_ride": ride})

    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

@app.route('/api/process_payment', methods=['POST'])
def process_payment():
    """Process payment for a ride"""
    try:
        if 'user_id' not in session or session.get('user_type') != 'passenger':
            return jsonify({"success": False, "message": "Unauthorized"}), 401
        
        data = request.get_json()
        payment_id = data.get('payment_id')
        transaction_id = data.get('transaction_id', f"TXN{secrets.token_hex(8).upper()}")
        
        if not payment_id:
            return jsonify({"success": False, "message": "Payment ID required"}), 400
        
        conn = get_db_conn()
        c = conn.cursor()
        
        # Update payment status
        paid_at = datetime.now()
        c.execute("""UPDATE payments SET status = 'completed', transaction_id = ?, paid_at = ? 
                     WHERE id = ?""", (transaction_id, paid_at, payment_id))
        
        # Update ride payment status
        c.execute("UPDATE rides SET payment_status = 'completed' WHERE id = (SELECT ride_id FROM payments WHERE id = ?)", 
                  (payment_id,))
        
        conn.commit()
        conn.close()
        
        return jsonify({
            "success": True,
            "message": "Payment processed successfully!",
            "transaction_id": transaction_id,
            "paid_at": paid_at.isoformat()
        })
        
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

@app.route('/api/get_profile', methods=['GET'])
def get_profile():
    """Get user profile"""
    try:
        if 'user_id' not in session:
            return jsonify({"success": False, "message": "Unauthorized"}), 401
        
        user_id = session['user_id']
        user_type = session['user_type']
        
        conn = get_db_conn()
        c = conn.cursor()
        
        if user_type == 'passenger':
            c.execute("""SELECT name, phone, email, total_rides, total_spent, created_at 
                         FROM passengers WHERE id = ?""", (user_id,))
            result = c.fetchone()
            
            if result:
                profile = {
                    "type": "passenger",
                    "name": result[0],
                    "phone": result[1],
                    "email": result[2],
                    "total_rides": result[3],
                    "total_spent": result[4],
                    "member_since": result[5]
                }
        else:
            c.execute("""SELECT name, mobile, email, vehicle_number, vehicle_type, rc_number, 
                         rating, total_rides, total_earned, is_available, created_at,
                         role, owner_id, verification_status, license_number, address, unique_id,
                         profile_image, qr_code
                         FROM drivers WHERE id = ?""", (user_id,))
            result = c.fetchone()
            
            if result:
                profile = {
                    "type": "driver",
                    "name": result[0],
                    "mobile": result[1],
                    "email": result[2],
                    "vehicle_number": result[3],
                    "vehicle_type": result[4],
                    "rc_number": result[5],
                    "rating": result[6],
                    "total_rides": result[7],
                    "total_earned": result[8],
                    "is_available": bool(result[9]),
                    "member_since": result[10],
                    "role": result[11],
                    "owner_id": result[12],
                    "verification_status": result[13],
                    "license_number": result[14],
                    "address": result[15],
                    "unique_id": result[16],
                    "profile_image": result[17],
                    "qr_code": result[18]
                }
                
                # If no QR path in DB, generate one (fallback)
                if not profile["qr_code"]:
                    _, qr_path = generate_driver_qr_code(user_id, result[0], result[3], result[1])
                    if qr_path:
                        c.execute("UPDATE drivers SET qr_code = ? WHERE id = ?", (qr_path, user_id))
                        conn.commit()
                        profile["qr_code"] = qr_path

                return jsonify({
                    "success": True, 
                    "profile": profile
                })
        
        conn.close()
        
        if not result:
            return jsonify({"success": False, "message": "Profile not found"}), 404
        
        return jsonify({
            "success": True,
            "profile": profile
        })
        
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

@app.route('/api/get_driver_payment_qr', methods=['GET'])
def get_driver_payment_qr():
    """Get any driver's payment QR image by driver_id (public, for passenger payment)"""
    try:
        driver_id = request.args.get('driver_id')
        if not driver_id:
            return jsonify({"success": False, "message": "driver_id required"}), 400

        conn = get_db_conn()
        c = conn.cursor()
        c.execute('SELECT payment_qr_image, upi_id, name FROM drivers WHERE id = ?', (driver_id,))
        result = c.fetchone()
        conn.close()

        if not result:
            return jsonify({"success": False, "message": "Driver not found"}), 404

        payment_qr_image, upi_id, name = result
        return jsonify({
            "success": True,
            "payment_qr_image": payment_qr_image,
            "upi_id": upi_id,
            "driver_name": name
        })
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500


@app.route('/api/upload_payment_qr', methods=['POST'])
def upload_payment_qr():
    """Upload / update driver's custom payment QR image"""
    try:
        if 'user_id' not in session or session.get('user_type') != 'driver':
            return jsonify({"success": False, "message": "Unauthorized"}), 401

        data = request.get_json()
        qr_image = data.get('qr_image', '').strip()  # base64 data URI

        if not qr_image:
            return jsonify({"success": False, "message": "QR image data required"}), 400

        # Basic validation: must be a data URI
        if not qr_image.startswith('data:image/'):
            return jsonify({"success": False, "message": "Invalid image format. Must be a valid image."}), 400

        driver_id = session['user_id']

        conn = get_db_conn()
        c = conn.cursor()
        c.execute('UPDATE drivers SET payment_qr_image = ? WHERE id = ?', (qr_image, driver_id))
        conn.commit()
        conn.close()

        return jsonify({"success": True, "message": "Payment QR saved successfully!"})

    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500


@app.route('/api/get_payment_qr', methods=['GET'])
def get_payment_qr():
    """Get driver's saved payment QR image"""
    try:
        if 'user_id' not in session or session.get('user_type') != 'driver':
            return jsonify({"success": False, "message": "Unauthorized"}), 401

        driver_id = session['user_id']

        conn = get_db_conn()
        c = conn.cursor()
        c.execute('SELECT payment_qr_image, upi_id, name FROM drivers WHERE id = ?', (driver_id,))
        result = c.fetchone()
        conn.close()

        if not result:
            return jsonify({"success": False, "message": "Driver not found"}), 404

        payment_qr_image, upi_id, name = result

        return jsonify({
            "success": True,
            "payment_qr_image": payment_qr_image,
            "upi_id": upi_id,
            "driver_name": name
        })

    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500


@app.route('/api/logout', methods=['POST'])
def logout():
    """Logout user"""
    session.clear()
    return jsonify({"success": True, "message": "Logged out successfully"})


# ============================================================================
# Admin Routes
# ============================================================================

@app.route('/admin')
def admin_login_page():
    if session.get('is_admin'):
        return admin_dashboard_page()
    return render_template('admin_login.html')

@app.route('/admin/dashboard')
def admin_dashboard_page():
    if not session.get('is_admin'):
        return render_template('admin_login.html')
    return render_template('admin_dashboard.html')

@app.route('/api/admin/login', methods=['POST'])
def admin_login():
    """Admin login"""
    try:
        data = request.get_json()
        username = data.get('username', '').strip()
        password = data.get('password', '').strip()
        hashed = hash_password(password)

        conn = get_db_conn()
        c = conn.cursor()
        c.execute('SELECT id, username FROM admins WHERE username = ? AND password = ?',
                  (username, hashed))
        result = c.fetchone()
        conn.close()

        if not result:
            return jsonify({"success": False, "message": "Invalid admin credentials"}), 401

        session['is_admin'] = True
        session['admin_id'] = result[0]
        session['admin_name'] = result[1]
        return jsonify({"success": True, "message": "Admin login successful"})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

@app.route('/api/admin/logout', methods=['POST'])
def admin_logout():
    session.pop('is_admin', None)
    session.pop('admin_id', None)
    session.pop('admin_name', None)
    return jsonify({"success": True})

@app.route('/api/admin/pending_drivers', methods=['GET'])
def admin_pending_drivers():
    """List drivers pending verification"""
    if not session.get('is_admin'):
        return jsonify({"success": False, "message": "Unauthorized"}), 401
    try:
        conn = get_db_conn()
        c = conn.cursor()
        c.execute("""SELECT id, name, age, mobile, email, vehicle_number, vehicle_type,
                            rc_number, unique_id, aadhaar_number, verification_status,
                            admin_notes, created_at
                     FROM drivers
                     ORDER BY CASE verification_status
                         WHEN 'pending' THEN 0 WHEN 'approved' THEN 1 ELSE 2 END,
                         created_at DESC""")
        rows = c.fetchall()
        conn.close()
        drivers = []
        for r in rows:
            drivers.append({
                "id": r[0], "name": r[1], "age": r[2], "mobile": r[3],
                "email": r[4], "vehicle_number": r[5], "vehicle_type": r[6],
                "rc_number": r[7], "unique_id": r[8],
                "aadhaar_masked": mask_aadhaar(r[9] or ''),
                "verification_status": r[10], "admin_notes": r[11],
                "registered_at": r[12]
            })
        return jsonify({"success": True, "drivers": drivers})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

@app.route('/api/admin/view_doc', methods=['GET'])
def admin_view_doc():
    """Decrypt and return a driver document for admin review"""
    if not session.get('is_admin'):
        return jsonify({"success": False, "message": "Unauthorized"}), 401
    try:
        driver_id = request.args.get('driver_id')
        doc_type = request.args.get('doc_type', 'aadhaar')  # 'aadhaar' or 'rc'
        conn = get_db_conn()
        c = conn.cursor()
        col = 'aadhaar_doc' if doc_type == 'aadhaar' else 'rc_doc'
        c.execute(f'SELECT {col}, name FROM drivers WHERE id = ?', (driver_id,))
        row = c.fetchone()
        conn.close()
        if not row or not row[0]:
            return jsonify({"success": False, "message": "Document not found"}), 404
        decrypted = decrypt_document(row[0])
        return jsonify({"success": True, "doc": decrypted, "driver_name": row[1], "doc_type": doc_type})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

@app.route('/api/admin/approve_driver', methods=['POST'])
def admin_approve_driver():
    """Approve a driver â€” also regenerates their QR"""
    if not session.get('is_admin'):
        return jsonify({"success": False, "message": "Unauthorized"}), 401
    try:
        data = request.get_json()
        driver_id = data.get('driver_id')
        notes = data.get('notes', '')
        conn = get_db_conn()
        c = conn.cursor()
        c.execute("UPDATE drivers SET verification_status = 'approved', admin_notes = ? WHERE id = ?",
                  (notes, driver_id))
        # Regenerate fresh HMAC QR on approval
        c.execute('SELECT name, vehicle_number, mobile FROM drivers WHERE id = ?', (driver_id,))
        row = c.fetchone()
        if row:
            _, qr_data = generate_driver_qr_code(driver_id, row[0], row[1], row[2])
            c.execute('UPDATE drivers SET qr_code = ? WHERE id = ?', (qr_data, driver_id))
        conn.commit()
        # Notify driver by email
        c.execute('SELECT email, name FROM drivers WHERE id = ?', (driver_id,))
        drv = c.fetchone()
        conn.close()
        if drv:
            send_email_otp.__wrapped__ if hasattr(send_email_otp, '__wrapped__') else None
            try:
                _send_approval_email(drv[0], drv[1], approved=True, notes=notes)
            except Exception:
                pass
        return jsonify({"success": True, "message": "Driver approved and QR regenerated!"})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

@app.route('/api/admin/final_verification', methods=['POST'])
def admin_final_verification():
    """Final step: Generate secure credentials and notify OWNER & RENTER"""
    if not session.get('is_admin'):
        return jsonify({"success": False, "message": "Unauthorized"}), 401
    
    try:
        data = request.get_json()
        driver_id = data.get('driver_id')
        
        if not driver_id:
            return jsonify({"success": False, "message": "Driver ID required"}), 400

        conn = get_db_conn()
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        
        c.execute("SELECT * FROM drivers WHERE id = ?", (driver_id,))
        driver = c.fetchone()
        
        if not driver:
            conn.close()
            return jsonify({"success": False, "message": "Driver not found"}), 404
        
        # 1. Generate Credentials (DRVxxxx + Random Password)
        new_unique_id = f"DRV{driver['id']:04d}"
        raw_password = secrets.token_urlsafe(10)
        hashed_pw = hash_password(raw_password)
        
        # 2. Update Driver status and credentials
        c.execute("""
            UPDATE drivers 
            SET verification_status = 'approved',
                unique_id = ?,
                password = ?,
                first_login = 1
            WHERE id = ?
        """, (new_unique_id, hashed_pw, driver_id))
        
        # 3. Notify driver
        _send_credentials_email(driver['email'], driver['name'], new_unique_id, raw_password)
        
        # 4. If renter, notify owner as well
        if driver['role'] == 'RENT' and driver['owner_id']:
            c.execute("SELECT email, name FROM drivers WHERE id = ?", (driver['owner_id'],))
            owner = c.fetchone()
            if owner:
                _send_owner_creds_notification(owner['email'], owner['name'], driver['name'], new_unique_id)
        
        conn.commit()
        conn.close()
        
        return jsonify({"success": True, "message": f"Account approved. Credentials sent to {driver['email']}."})
        
    except Exception as e:
        print(f"Admin Final Verification Error: {str(e)}")
        return jsonify({"success": False, "message": str(e)}), 500

def _send_credentials_email(email, name, unique_id, password):
    """Send driver login credentials via Brevo (non-blocking)."""
    subject = "RakshaRide — Your Account is Approved!"
    html = (
        "<div style='font-family:Arial,sans-serif;max-width:600px;margin:0 auto'>"
        "<div style='background:linear-gradient(135deg,#2E7D32,#FFC107);padding:24px;border-radius:12px 12px 0 0;text-align:center'>"
        "<h1 style='color:white;margin:0'>RakshaRide</h1>"
        "<p style='color:rgba(255,255,255,0.9);margin:6px 0 0'>Account Approved!</p>"
        "</div>"
        "<div style='background:#fff;border:1px solid #e0e0e0;padding:28px;border-radius:0 0 12px 12px'>"
        f"<h2 style='color:#2E7D32'>Welcome, {name}!</h2>"
        "<p>Your RakshaRide driver account has been verified and approved.</p>"
        "<div style='background:#f5f5f5;border-radius:10px;padding:20px;margin:20px 0'>"
        "<h3 style='margin:0 0 12px;color:#1565C0'>Your Login Credentials</h3>"
        f"<p style='margin:6px 0'><strong>User ID:</strong> <code style='background:#e3f2fd;padding:4px 8px;border-radius:4px'>{unique_id}</code></p>"
        f"<p style='margin:6px 0'><strong>Password:</strong> <code style='background:#e3f2fd;padding:4px 8px;border-radius:4px'>{password}</code></p>"
        "</div>"
        f"<div style='text-align:center;margin:24px 0'>"
        f"<a href='{BASE_URL}/login/driver' style='background:#1565C0;color:white;padding:14px 32px;"
        "text-decoration:none;border-radius:8px;font-weight:bold;font-size:16px;display:inline-block'>"
        "Login to Dashboard</a>"
        "</div>"
        "<p style='color:#C62828;font-size:13px'><strong>Important:</strong> Change your password after first login.</p>"
        "</div></div>"
    )
    plain = f"Your RakshaRide credentials — User ID: {unique_id} | Password: {password} | Login: {BASE_URL}/login/driver"
    send_email_async(email, subject, html, plain)
    print(f"[CREDENTIALS EMAIL] Queued for {email}")
    return True


def _send_owner_creds_notification(owner_email, owner_name, renter_name, unique_id):
    """Notify owner that their renter is verified — uses Brevo."""
    subject = f"RakshaRide — Renter {renter_name} Account Activated"
    html = (
        "<div style='font-family:Arial,sans-serif;max-width:600px;margin:0 auto'>"
        "<div style='background:linear-gradient(135deg,#1565C0,#FFC107);padding:24px;border-radius:12px 12px 0 0;text-align:center'>"
        "<h1 style='color:white;margin:0'>RakshaRide</h1>"
        "</div>"
        "<div style='background:#fff;border:1px solid #e0e0e0;padding:28px;border-radius:0 0 12px 12px'>"
        f"<h2 style='color:#1565C0'>Renter Account Activated</h2>"
        f"<p>Dear {owner_name},</p>"
        f"<p>Your renter <strong>{renter_name}</strong> has been verified and is now active on RakshaRide.</p>"
        "<div style='background:#f5f5f5;border-radius:10px;padding:16px;margin:20px 0'>"
        f"<p style='margin:0'><strong>Renter:</strong> {renter_name}</p>"
        f"<p style='margin:8px 0 0'><strong>Renter ID:</strong> {unique_id}</p>"
        "</div>"
        "<p>They are now authorized to provide rides using your vehicle.</p>"
        "</div></div>"
    )
    plain = f"Your renter {renter_name} (ID: {unique_id}) is now verified on RakshaRide."
    send_email_async(owner_email, subject, html, plain)
    print(f"[OWNER CREDS EMAIL] Queued for {owner_email}")


def _deliver_email(msg):
    """Internal helper to deliver SMTP message"""
    try:
        clean_pw = GMAIL_APP_PASSWORD.replace(' ', '').replace('-', '')
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT, timeout=15)
        server.starttls()
        server.login(GMAIL_EMAIL, clean_pw)
        server.send_message(msg)
        server.quit()
    except Exception as e:
        print(f"Email delivery error: {str(e)}")

@app.route('/api/admin/reject_driver', methods=['POST'])
def admin_reject_driver():
    """Reject a driver"""
    if not session.get('is_admin'):
        return jsonify({"success": False, "message": "Unauthorized"}), 401
    try:
        data = request.get_json()
        driver_id = data.get('driver_id')
        notes = data.get('notes', 'Documents could not be verified.')
        conn = get_db_conn()
        c = conn.cursor()
        c.execute("UPDATE drivers SET verification_status = 'rejected', admin_notes = ? WHERE id = ?",
                  (notes, driver_id))
        conn.commit()
        c.execute('SELECT email, name FROM drivers WHERE id = ?', (driver_id,))
        drv = c.fetchone()
        conn.close()
        if drv:
            try:
                _send_approval_email(drv[0], drv[1], approved=False, notes=notes)
            except Exception:
                pass
        return jsonify({"success": True, "message": "Driver rejected."})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

def _send_approval_email(to_email: str, name: str, approved: bool, notes: str = ''):
    """Send driver approval/rejection email"""
    status = 'APPROVED âœ…' if approved else 'REJECTED âŒ'
    action = ('You can now log in to the RakshaRide driver app.'
              if approved else
              f'Reason: {notes}\n\nPlease re-register with correct documents or contact support.')
    body = f"""Dear {name},

Your RakshaRide driver account verification status: {status}

{action}

Thank you,
RakshaRide Admin Team
"""
    msg = MIMEMultipart()
    msg['From'] = f'RakshaRide Admin <{GMAIL_EMAIL}>'
    msg['To'] = to_email
    msg['Subject'] = f'RakshaRide Account Verification â€” {status}'
    msg.attach(MIMEText(body, 'plain'))
    clean_pw = GMAIL_APP_PASSWORD.replace(' ', '').replace('-', '')
    server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT, timeout=15)
    server.starttls()
    server.login(GMAIL_EMAIL, clean_pw)
    server.send_message(msg)
    server.quit()

# ============================================================================
# AI Verification & Owner-Renter APIs
# ============================================================================

@app.route('/api/ai/ocr_extract', methods=['POST'])
def ai_ocr_extract():
    """Run OCR on an uploaded document and return extracted fields."""
    try:
        data = request.get_json()
        image_uri = data.get('image', '')
        result = extract_document_text(image_uri)
        return jsonify({"success": True, "ocr": result})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500


@app.route('/api/ai/face_match', methods=['POST'])
def ai_face_match():
    """Compare ID photo vs live selfie and return similarity score."""
    try:
        data = request.get_json()
        id_photo = data.get('id_photo', '')
        selfie   = data.get('selfie', '')
        result = compute_face_similarity(id_photo, selfie)
        return jsonify({"success": True, "face_match": result})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500


@app.route('/api/ai/liveness_challenge', methods=['POST'])
def ai_liveness_challenge():
    """Issue a liveness challenge for anti-spoofing."""
    try:
        session_id = session.get('user_id', secrets.token_hex(8))
        challenge = generate_liveness_challenge(str(session_id))
        return jsonify({"success": True, "challenge": challenge})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500


@app.route('/api/ai/liveness_verify', methods=['POST'])
def ai_liveness_verify():
    """Verify returned liveness token after user completes gesture."""
    try:
        data = request.get_json()
        token     = data.get('token', '')
        completed = data.get('completed_challenge', '')
        ok, msg = verify_liveness_token(token, completed)
        return jsonify({"success": ok, "message": msg})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500


@app.route('/api/ai/full_pipeline', methods=['POST'])
def ai_full_pipeline():
    """
    Complete AI verification pipeline:
      - OCR from Aadhaar/RC image
      - Face match (ID photo vs selfie)
      - Decision: VERIFIED / FLAGGED / REJECTED
      Stores result on the driver record.
    """
    try:
        if 'user_id' not in session or session.get('user_type') != 'driver':
            return jsonify({"success": False, "message": "Unauthorized"}), 401

        data     = request.get_json()
        id_photo = data.get('id_photo', '')   # Aadhaar image
        selfie   = data.get('selfie', '')     # Live selfie
        doc_type = data.get('doc_type', 'AADHAAR').upper()

        # Run in sequence (parallel via threading if needed)
        ocr_result  = extract_document_text(id_photo)
        face_result = compute_face_similarity(id_photo, selfie)
        pipeline    = run_verification_pipeline(ocr_result, face_result)

        driver_id = session['user_id']

        # Save score & selfie to driver record
        enc_selfie = encrypt_document(selfie) if selfie else None
        ocr_json   = json.dumps(ocr_result)

        new_status = pipeline['status'].lower()  # verified / flagged / rejected
        conn = get_db_conn()
        c = conn.cursor()
        c.execute("""
            UPDATE drivers
            SET ai_face_score = ?, ai_ocr_data = ?, live_selfie = ?,
                verification_status = ?
            WHERE id = ?""",
            (pipeline['score'], ocr_json, enc_selfie, new_status, driver_id))

        # Store in driver_documents vault
        enc_doc = encrypt_document(id_photo) if id_photo else None
        c.execute("""
            INSERT INTO driver_documents
              (driver_id, uploaded_by, doc_type, file_data, ocr_extracted,
               ai_status, ai_score)
            VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (driver_id, driver_id, doc_type, enc_doc,
             ocr_result.get('raw_text', ''),
             pipeline['status'], pipeline['score']))

        conn.commit()

        # If auto-verified, send welcome email in background
        if pipeline['status'] == 'VERIFIED':
            c.execute('SELECT email, name, unique_id FROM drivers WHERE id = ?', (driver_id,))
            drv = c.fetchone()
            conn.close()
            if drv:
                threading.Thread(
                    target=_send_welcome_email,
                    args=(drv[0], drv[1], drv[2]),
                    daemon=True
                ).start()
        else:
            conn.close()

        return jsonify({
            "success": True,
            "pipeline": pipeline
        })
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500


def _send_welcome_email(to_email: str, name: str, unique_id: str):
    """Send auto-verified welcome email to driver."""
    try:
        body = f"""Welcome to RakshaRide, {name}!

Your AI verification is complete. You are APPROVED to drive.

Your Driver ID: {unique_id}

You can now log in using your email or Driver ID.

Ride Safe,
RakshaRide Team
"""
        msg = MIMEMultipart()
        msg['From'] = f'RakshaRide <{GMAIL_EMAIL}>'
        msg['To'] = to_email
        msg['Subject'] = f'Welcome to RakshaRide! Your ID: {unique_id}'
        msg.attach(MIMEText(body, 'plain'))
        clean_pw = GMAIL_APP_PASSWORD.replace(' ', '').replace('-', '')
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT, timeout=15)
        server.starttls()
        server.login(GMAIL_EMAIL, clean_pw)
        server.send_message(msg)
        server.quit()
    except Exception as e:
        print(f"[WARN] Welcome email failed: {e}")


# â”€â”€ Owner-Renter Flow â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

@app.route('/api/driver/send_renter_request', methods=['POST'])
def send_renter_request():
    """
    Renter submits their owner's email.
    Creates a pending link request; owner gets a notification.
    """
    try:
        if 'user_id' not in session or session.get('user_type') != 'driver':
            return jsonify({"success": False, "message": "Unauthorized"}), 401

        data        = request.get_json()
        owner_email = data.get('owner_email', '').strip()
        renter_id   = session['user_id']

        if not owner_email:
            return jsonify({"success": False, "message": "Owner email required"}), 400

        conn = get_db_conn()
        c = conn.cursor()

        # Find owner
        c.execute("SELECT id, name FROM drivers WHERE email = ? AND role = 'OWNER'", (owner_email,))
        owner = c.fetchone()

        c.execute("""
            INSERT INTO renter_requests (renter_id, owner_email, owner_id, status)
            VALUES (?, ?, ?, 'PENDING')""",
            (renter_id, owner_email, owner[0] if owner else None))
        conn.commit()

        # Get renter name
        c.execute('SELECT name FROM drivers WHERE id = ?', (renter_id,))
        renter_name = c.fetchone()[0]
        conn.close()

        # Notify owner
        if owner:
            threading.Thread(
                target=_send_renter_notification,
                args=(owner_email, owner[1], renter_name),
                daemon=True
            ).start()
            return jsonify({"success": True, "message": "Request sent to owner! Awaiting approval."})
        else:
            return jsonify({"success": True,
                            "message": "Request logged. Owner not yet registered."})

    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500


@app.route('/api/driver/approve_renter', methods=['POST'])
def approve_renter():
    """Owner approves a renter linking request."""
    try:
        if 'user_id' not in session or session.get('user_type') != 'driver':
            return jsonify({"success": False, "message": "Unauthorized"}), 401

        data       = request.get_json()
        request_id = data.get('request_id')
        owner_id   = session['user_id']

        conn = get_db_conn()
        c = conn.cursor()

        # Verify this request belongs to the owner
        c.execute("SELECT renter_id FROM renter_requests WHERE id = ? AND owner_id = ?",
                  (request_id, owner_id))
        row = c.fetchone()
        if not row:
            conn.close()
            return jsonify({"success": False, "message": "Request not found"}), 404

        renter_id = row[0]
        c.execute("UPDATE renter_requests SET status = 'APPROVED' WHERE id = ?", (request_id,))
        c.execute("UPDATE drivers SET owner_id = ?, role = 'RENTER' WHERE id = ?",
                  (owner_id, renter_id))
        conn.commit()
        conn.close()
        return jsonify({"success": True, "message": "Renter linked to your account!"})

    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500


@app.route('/api/driver/renter_requests', methods=['GET'])
def get_renter_requests():
    """Owner fetches pending renter link requests."""
    if 'user_id' not in session or session.get('user_type') != 'driver':
        return jsonify({"success": False, "message": "Unauthorized"}), 401
    try:
        owner_id = session['user_id']
        conn = get_db_conn()
        c = conn.cursor()
        c.execute("""
            SELECT rr.id, d.name, d.email, d.mobile, rr.status, rr.created_at
            FROM renter_requests rr
            JOIN drivers d ON d.id = rr.renter_id
            WHERE rr.owner_id = ?
            ORDER BY rr.created_at DESC""", (owner_id,))
        rows = c.fetchall()
        conn.close()
        return jsonify({"success": True, "requests": [
            {"id": r[0], "name": r[1], "email": r[2], "mobile": r[3],
             "status": r[4], "at": r[5]} for r in rows
        ]})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500


def _send_renter_notification(owner_email, owner_name, renter_name):
    try:
        body = f"""Dear {owner_name},

A new driver ({renter_name}) has requested to link to your vehicle on RakshaRide.

Log in to your dashboard to approve or deny this request.

RakshaRide Team
"""
        msg = MIMEMultipart()
        msg['From'] = f'RakshaRide <{GMAIL_EMAIL}>'
        msg['To'] = owner_email
        msg['Subject'] = f'RakshaRide: Renter Link Request from {renter_name}'
        msg.attach(MIMEText(body, 'plain'))
        clean_pw = GMAIL_APP_PASSWORD.replace(' ', '').replace('-', '')
        s = smtplib.SMTP(SMTP_SERVER, SMTP_PORT, timeout=15)
        s.starttls(); s.login(GMAIL_EMAIL, clean_pw)
        s.send_message(msg); s.quit()
    except Exception as e:
        print(f"[WARN] Renter notification failed: {e}")


# â”€â”€ Live Share Token (Emergency Tracking) â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

@app.route('/api/ride/generate_share_token', methods=['POST'])
def generate_share_token():
    """Passenger generates a public share link for their active ride."""
    try:
        if 'user_id' not in session or session.get('user_type') != 'passenger':
            return jsonify({"success": False, "message": "Unauthorized"}), 401

        data    = request.get_json()
        ride_id = data.get('ride_id')
        if not ride_id:
            return jsonify({"success": False, "message": "ride_id required"}), 400

        token = secrets.token_urlsafe(20)
        conn = get_db_conn()
        c = conn.cursor()
        c.execute("""
            UPDATE rides SET share_token = ?, share_token_active = 1
            WHERE id = ? AND passenger_id = ?""",
            (token, ride_id, session['user_id']))
        conn.commit()
        conn.close()

        share_url = f"{BASE_URL}/track/{token}"
        return jsonify({"success": True, "share_token": token, "share_url": share_url,
                        "message": "Share this link with anyone to let them track your ride live."})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500


@app.route('/track/<token>')
def public_ride_tracker(token):
    """Public page â€” no login required â€” shows live ride status."""
    return render_template('ride_tracker.html', share_token=token)


@app.route('/api/ride/track/<token>', methods=['GET'])
def api_ride_track(token):
    """API for public tracker page to poll ride data."""
    try:
        conn = get_db_conn()
        c = conn.cursor()
        c.execute("""
            SELECT r.id, r.driver_name, r.driver_vehicle, r.driver_mobile,
                   r.pickup_location, r.dropoff_location,
                   r.start_lat, r.start_lng, r.end_lat, r.end_lng,
                   r.status, r.start_time, r.share_token_active,
                   d.latitude, d.longitude, d.verification_status
            FROM rides r
            JOIN drivers d ON d.id = r.driver_id
            WHERE r.share_token = ? AND r.share_token_active = 1""", (token,))
        row = c.fetchone()
        conn.close()
        if not row:
            return jsonify({"success": False, "message": "Invalid or expired share link"}), 404

        return jsonify({"success": True, "ride": {
            "id": row[0], "driver_name": row[1], "driver_vehicle": row[2],
            "driver_mobile": row[3], "pickup_location": row[4],
            "dropoff_location": row[5],
            "start_lat": row[6], "start_lng": row[7],
            "end_lat": row[8], "end_lng": row[9],
            "status": row[10], "start_time": row[11],
            "driver_live_lat": row[13], "driver_live_lng": row[14],
            "driver_verified": row[15] == 'verified'
        }})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500


@app.route('/api/ride/stop_sharing', methods=['POST'])
def stop_sharing():
    """Deactivate share token."""
    try:
        if 'user_id' not in session or session.get('user_type') != 'passenger':
            return jsonify({"success": False, "message": "Unauthorized"}), 401
        data = request.get_json()
        ride_id = data.get('ride_id')
        conn = get_db_conn()
        c = conn.cursor()
        c.execute("UPDATE rides SET share_token_active = 0 WHERE id = ? AND passenger_id = ?",
                  (ride_id, session['user_id']))
        conn.commit(); conn.close()
        return jsonify({"success": True, "message": "Live sharing stopped."})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500


# â”€â”€ Document Vault (Owner-Renter restriction) â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

@app.route('/api/driver/upload_document', methods=['POST'])
def upload_driver_document():
    """
    Upload Aadhaar/RC/License to encrypted vault.
    RENTER cannot upload RC â€” only OWNER can.
    """
    try:
        if 'user_id' not in session or session.get('user_type') != 'driver':
            return jsonify({"success": False, "message": "Unauthorized"}), 401

        data     = request.get_json()
        doc_type = data.get('doc_type', '').upper()
        image    = data.get('image', '')
        uploader_id = session['user_id']

        if not doc_type or not image:
            return jsonify({"success": False, "message": "doc_type and image required"}), 400

        # Renter restriction: cannot upload RC or Insurance
        conn = get_db_conn()
        c = conn.cursor()
        c.execute('SELECT role FROM drivers WHERE id = ?', (uploader_id,))
        row = c.fetchone()
        if row and row[0] == 'RENTER' and doc_type in ('RC', 'INSURANCE'):
            conn.close()
            return jsonify({"success": False,
                            "message": "Renters cannot upload vehicle RC/Insurance. Contact your vehicle Owner."}), 403

        enc_image  = encrypt_document(image)
        ocr_result = extract_document_text(image)
        ocr_text   = ocr_result.get('raw_text', '')
        doc_number = ocr_result.get('doc_number', '')

        # Detect duplicate doc number
        if doc_number:
            c.execute("SELECT id FROM driver_documents WHERE ocr_extracted LIKE ?",
                      (f'%{doc_number}%',))
            if c.fetchone():
                conn.close()
                return jsonify({"success": False,
                                "message": f"Document number {doc_number} already registered."}), 409

        c.execute("""
            INSERT INTO driver_documents
              (driver_id, uploaded_by, doc_type, file_data, ocr_extracted, ai_status)
            VALUES (?, ?, ?, ?, ?, 'PENDING')""",
            (uploader_id, uploader_id, doc_type, enc_image, ocr_text))
        doc_id = c.lastrowid
        conn.commit(); conn.close()

        return jsonify({
            "success": True,
            "message": f"{doc_type} uploaded and queued for AI verification.",
            "doc_id": doc_id,
            "ocr": {"doc_number": doc_number, "name": ocr_result.get('name'),
                    "dob": ocr_result.get('dob')}
        })
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500


@app.route('/api/driver/my_documents', methods=['GET'])
def get_my_documents():
    """List uploaded documents for current driver (no file data, metadata only)."""
    if 'user_id' not in session or session.get('user_type') != 'driver':
        return jsonify({"success": False, "message": "Unauthorized"}), 401
    try:
        driver_id = session['user_id']
        conn = get_db_conn()
        c = conn.cursor()
        c.execute("""
            SELECT id, doc_type, ai_status, ai_score, created_at
            FROM driver_documents WHERE driver_id = ?
            ORDER BY created_at DESC""", (driver_id,))
        rows = c.fetchall()
        conn.close()
        return jsonify({"success": True, "documents": [
            {"id": r[0], "doc_type": r[1], "ai_status": r[2],
             "ai_score": r[3], "uploaded_at": r[4]} for r in rows
        ]})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500


# ============================================================================
# GPS Tracking Frontend Route
# ============================================================================

@app.route('/ride/<int:ride_id>/track')
def track_ride(ride_id):
    if session.get('user_type') != 'passenger':
        return redirect(url_for('index'))
    
    conn = get_db_conn()
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    ride = c.execute('''
        SELECT r.*, d.name as driver_name, d.vehicle_number as vehicle_details 
        FROM rides r 
        JOIN drivers d ON r.driver_id = d.id 
        WHERE r.id = ? AND r.passenger_id = ?
    ''', (ride_id, session['user_id'])).fetchone()
    conn.close()
    
    if not ride:
        return "Ride not found or unauthorized", 404
        
    return render_template('track_ride.html', ride=ride)

@app.route('/register/driver')
def register_driver_modern():
    return render_template('register_driver.html')

@app.route('/api/send_otp', methods=['POST'])
def api_send_otp_modern():
    try:
        data = request.get_json()
        email = data.get('email')
        otp = f"{secrets.randbelow(899999) + 100000}"
        expiry = datetime.now() + timedelta(minutes=10)
        conn = get_db_conn()
        c = conn.cursor()
        c.execute("DELETE FROM otp_verification WHERE email = ?", (email,))
        c.execute("INSERT INTO otp_verification (email, otp, expiry_time) VALUES (?, ?, ?)", (email, otp, expiry))
        conn.commit()
        conn.close()
        send_email_async(email, "RakshaRide Security Code", f"OTP: {otp}")
        return jsonify({"success": True})
    except Exception as e: return jsonify({"success": False, "message": str(e)})

@app.route('/api/register_driver_full', methods=['POST'])
def register_driver_full_modern():
    try:
        name = request.form.get('name')
        email = request.form.get('email')
        mobile = request.form.get('mobile')
        password = request.form.get('password')
        upi_id = request.form.get('upi_id')
        role = request.form.get('role', 'OWNER')
        
        conn = get_db_conn()
        c = conn.cursor()
        
        p_path = save_uploaded_file(request.files.get('profile_pic'), PROFILE_DIR, "p")
        pay_path = save_uploaded_file(request.files.get('payment_qr'), QR_DIR, "pay")
        
        h_pw = hash_password(password)
        u_id = f"DRV-{secrets.token_hex(3).upper()}"
        
        c.execute("INSERT INTO drivers (name, email, mobile, password, role, profile_image, payment_qr_image, upi_id, unique_id, verification_status, is_available) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'verified', 1)",
                  (name, email, mobile, h_pw, role, p_path, pay_path, upi_id, u_id))
        
        d_id = c.lastrowid
        qr_b64, qr_file = generate_driver_qr_code(d_id, name, "VERIFIED", mobile)
        c.execute("UPDATE drivers SET qr_code = ? WHERE id = ?", (qr_file, d_id))
        conn.commit()
        conn.close()
        return jsonify({"success": True, "message": "Registered!", "qr_base64": qr_b64, "unique_id": u_id})
    except Exception as e: return jsonify({"success": False, "message": str(e)})

# ============================================================================
# NEW DASHBOARD APIs
# ============================================================================

@app.route('/api/driver_profile')
def api_driver_profile():
    did, err = _require_driver()
    if err: return err
    try:
        conn = sqlite3.connect('database_enhanced.db')
        c = conn.cursor()
        c.execute("""SELECT id, name, age, mobile, email, vehicle_number, vehicle_type,
                     rc_number, license_number, aadhaar_number, role, owner_id,
                     unique_id, verification_status, rating, total_rides, total_earned,
                     is_available, qr_code, payment_qr_image, upi_id
                     FROM drivers WHERE id = ?""", (did,))
        row = c.fetchone()
        conn.close()
        if not row:
            return jsonify({"success": False, "message": "Driver not found"}), 404
        cols = ['id','name','age','mobile','email','vehicle_number','vehicle_type',
                'rc_number','license_number','aadhaar_number','role','owner_id',
                'unique_id','verification_status','rating','total_rides','total_earned',
                'is_available','qr_code','payment_qr_image','upi_id']
        driver = dict(zip(cols, row))
        # qr_code stores the base64 PNG directly (generated in-memory, no file path)
        if driver.get('qr_code'):
            qc = driver['qr_code']
            if qc.startswith('data:image/'):
                # Already a rendered PNG — use directly
                driver['qr_image'] = qc
            else:
                # Legacy: raw QR data string — regenerate PNG
                try:
                    qr = qrcode.QRCode(version=1, error_correction=qrcode.constants.ERROR_CORRECT_M, box_size=8, border=4)
                    qr.add_data(qc)
                    qr.make(fit=True)
                    img = qr.make_image(fill_color="#1565C0", back_color="white")
                    buf = io.BytesIO()
                    img.save(buf, format="PNG")
                    driver['qr_image'] = "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode()
                except Exception as qr_err:
                    print(f"[WARN] QR regen failed: {qr_err}")
                    driver['qr_image'] = None
        else:
            # No QR stored yet — generate fresh one
            try:
                qr_img, qr_data = generate_driver_qr_code(
                    driver['id'], driver['name'], driver['vehicle_number'], driver['mobile'])
                if qr_img:
                    driver['qr_image'] = qr_img
                    # Save it so we don't regenerate every time
                    conn2 = sqlite3.connect('database_enhanced.db')
                    conn2.execute("UPDATE drivers SET qr_code=? WHERE id=?", (qr_img, driver['id']))
                    conn2.commit(); conn2.close()
                else:
                    driver['qr_image'] = None
            except Exception:
                driver['qr_image'] = None
        return jsonify({"success": True, "driver": driver})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

@app.route('/api/passenger_profile')
def api_passenger_profile():
    pid, err = _require_passenger()
    if err: return err
    try:
        conn = sqlite3.connect('database_enhanced.db')
        c = conn.cursor()
        c.execute("""SELECT id, name, phone, email, total_rides, total_spent,
                     emergency_name, emergency_mobile, emergency_email
                     FROM passengers WHERE id = ?""", (pid,))
        row = c.fetchone()
        conn.close()
        if not row:
            return jsonify({"success": False, "message": "Passenger not found"}), 404
        cols = ['id','name','phone','email','total_rides','total_spent',
                'emergency_name','emergency_mobile','emergency_email']
        passenger = dict(zip(cols, row))
        return jsonify({"success": True, "passenger": passenger})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

@app.route('/api/toggle_availability', methods=['POST'])
def api_toggle_availability():
    did, err = _require_driver()
    if err: return err
    try:
        conn = sqlite3.connect('database_enhanced.db')
        c = conn.cursor()
        c.execute("SELECT is_available FROM drivers WHERE id = ?", (did,))
        row = c.fetchone()
        new_status = 0 if row and row[0] else 1
        c.execute("UPDATE drivers SET is_available = ? WHERE id = ?", (new_status, did))
        conn.commit()
        conn.close()
        return jsonify({"success": True, "is_available": bool(new_status)})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

@app.route('/api/update_driver_profile', methods=['POST'])
def api_update_driver_profile():
    did, err = _require_driver()
    if err: return err
    try:
        data = request.get_json()
        conn = sqlite3.connect('database_enhanced.db')
        c = conn.cursor()
        c.execute("UPDATE drivers SET name=?, age=?, mobile=? WHERE id=?",
                  (data.get('name'), data.get('age'), data.get('mobile'), did))
        conn.commit()
        conn.close()
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

@app.route('/api/update_passenger_profile', methods=['POST'])
def api_update_passenger_profile():
    pid, err = _require_passenger()
    if err: return err
    try:
        data = request.get_json()
        name  = (data.get('name') or '').strip()
        phone = (data.get('phone') or '').strip()
        if not name:
            return jsonify({"success": False, "message": "Name is required"}), 400
        conn = sqlite3.connect('database_enhanced.db')
        c = conn.cursor()
        c.execute("UPDATE passengers SET name=?, phone=? WHERE id=?", (name, phone, pid))
        conn.commit()
        conn.close()
        return jsonify({"success": True, "message": "Profile updated successfully!"})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

@app.route('/api/driver_ride_history')
def api_driver_ride_history():
    did, err = _require_driver()
    if err: return err
    try:
        limit = request.args.get('limit', 100, type=int)
        conn = sqlite3.connect('database_enhanced.db')
        c = conn.cursor()
        c.execute("""SELECT id, passenger_name, status, fare, distance_km,
                     duration_minutes, payment_status, created_at
                     FROM rides WHERE driver_id = ? ORDER BY created_at DESC LIMIT ?""",
                  (did, limit))
        rows = c.fetchall()
        conn.close()
        cols = ['id','passenger_name','status','fare','distance_km','duration_minutes','payment_status','created_at']
        return jsonify({"success": True, "rides": [dict(zip(cols, r)) for r in rows]})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

@app.route('/api/passenger_ride_history')
def api_passenger_ride_history():
    pid, err = _require_passenger()
    if err: return err
    try:
        limit = request.args.get('limit', 100, type=int)
        conn = sqlite3.connect('database_enhanced.db')
        c = conn.cursor()
        c.execute("""SELECT id, driver_name, status, fare, distance_km,
                     duration_minutes, payment_status, created_at
                     FROM rides WHERE passenger_id = ? ORDER BY created_at DESC LIMIT ?""",
                  (pid, limit))
        rows = c.fetchall()
        conn.close()
        cols = ['id','driver_name','status','fare','distance_km','duration_minutes','payment_status','created_at']
        return jsonify({"success": True, "rides": [dict(zip(cols, r)) for r in rows]})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

def _resolve_document_preview(file_data):
    """Resolve document file_data to a displayable data URI.
    Handles: data URI, file path, encrypted base64, raw base64."""
    if not file_data or not isinstance(file_data, str):
        return None
    # Format 1: Already a data URI
    if file_data.startswith('data:'):
        return file_data
    # Format 2: File path
    if '/' in file_data or '\\' in file_data:
        try:
            clean = file_data.replace('\\', '/').replace('\\\\', '/')
            if os.path.exists(clean):
                with open(clean, 'rb') as f:
                    data = f.read()
                ext = clean.rsplit('.', 1)[-1].lower()
                mime = {'jpg':'image/jpeg','jpeg':'image/jpeg','png':'image/png',
                        'pdf':'application/pdf','gif':'image/gif'}.get(ext,'image/jpeg')
                return f"data:{mime};base64,{base64.b64encode(data).decode()}"
        except Exception as e:
            print(f"[DOC] File read error: {e}")
        return None
    # Format 3: Encrypted base64
    try:
        decrypted = decrypt_document(file_data)
        if decrypted:
            if isinstance(decrypted, bytes):
                decrypted = decrypted.decode('utf-8', errors='ignore')
            if decrypted.startswith('data:'):
                return decrypted
            if len(decrypted) > 100:
                return 'data:image/jpeg;base64,' + decrypted
    except Exception:
        pass
    # Format 4: Raw base64
    if len(file_data) > 100:
        try:
            import base64 as _b64
            _b64.b64decode(file_data[:100])
            return 'data:image/jpeg;base64,' + file_data
        except Exception:
            pass
    return None


@app.route('/api/get_driver_documents')
@app.route('/api/get_driver_documents')
def api_get_driver_documents():
    # Accept both session auth (dashboard) and JWT token auth
    uid = None
    if 'user_id' in session and session.get('user_type') == 'driver':
        uid = session['user_id']
    else:
        current_user = get_current_user()
        if current_user and current_user.get('user_type') == 'driver':
            uid = current_user['user_id']
    if not uid:
        return jsonify({"success": False, "message": "Driver authentication required"}), 401
    try:
        conn = sqlite3.connect('database_enhanced.db')
        c = conn.cursor()
        c.execute("SELECT role, owner_id, verification_status FROM drivers WHERE id = ?", (uid,))
        row = c.fetchone()
        is_rent = row and row[0] == 'RENT'
        driver_id = uid
        if is_rent and row[1]:
            driver_id = row[1]  # Rent driver sees owner's documents
        verification_status = row[2] if row else 'pending'

        c.execute("""SELECT doc_type, file_data, ai_status, created_at
                     FROM driver_documents WHERE driver_id = ?
                     ORDER BY created_at DESC""", (driver_id,))
        rows = c.fetchall()

        # Also get profile_image from drivers table as fallback for 'photo' doc
        c.execute("SELECT profile_image FROM drivers WHERE id = ?", (driver_id,))
        drv_row = c.fetchone()
        profile_image_fallback = drv_row[0] if drv_row else None

        conn.close()

        docs = {}
        for doc_type, file_data, ai_status, created_at in rows:
            if doc_type in docs:
                continue  # Keep latest only
            preview = _resolve_document_preview(file_data)
            docs[doc_type] = {
                "uploaded": True,
                "preview": preview,
                "has_preview": preview is not None,
                "ai_status": ai_status or 'PENDING',
                "verified": ai_status == 'VERIFIED',
                "uploaded_at": created_at
            }

        # If no 'photo' doc but profile_image exists, add it
        if 'photo' not in docs and profile_image_fallback:
            preview = _resolve_document_preview(profile_image_fallback)
            if preview:
                docs['photo'] = {
                    "uploaded": True,
                    "preview": preview,
                    "has_preview": True,
                    "ai_status": "PENDING",
                    "verified": False,
                    "uploaded_at": None
                }

        return jsonify({
            "success": True,
            "documents": docs,
            "is_rent": is_rent,
            "can_upload": not is_rent,
            "driver_verified": verification_status == 'verified'
        })
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

@app.route('/api/get_document/<doc_type>')
def api_get_single_document(doc_type):
    """Serve a single document — ONLY for the owning driver (not passengers)"""
    uid = session.get('user_id') if session.get('user_type') == 'driver' else None
    if not uid:
        cu = get_current_user()
        if cu and cu.get('user_type') == 'driver':
            uid = cu['user_id']
    if not uid:
        return jsonify({"success": False, "message": "Driver authentication required"}), 401
    try:
        conn = sqlite3.connect('database_enhanced.db')
        c = conn.cursor()
        c.execute("SELECT role, owner_id FROM drivers WHERE id = ?", (uid,))
        row = c.fetchone()
        driver_id = uid
        if row and row[0] == 'RENT' and row[1]:
            driver_id = row[1]

        c.execute("SELECT file_data, ai_status FROM driver_documents WHERE driver_id = ? AND doc_type = ?",
                  (driver_id, doc_type))
        row = c.fetchone()
        conn.close()

        if not row or not row[0]:
            return jsonify({"success": False, "message": "Document not found"}), 404

        preview = _resolve_document_preview(row[0])
        if not preview:
            return jsonify({"success": False, "message": "Could not decode document"}), 500

        return jsonify({"success": True, "data": preview, "doc_type": doc_type, "ai_status": row[1] or 'PENDING'})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

@app.route('/api/get_payment_qr')
def api_get_payment_qr():
    uid = session.get('user_id') if session.get('user_type') == 'driver' else None
    if not uid:
        cu = get_current_user()
        if cu and cu.get('user_type') == 'driver':
            uid = cu['user_id']
    if not uid:
        return jsonify({"success": False}), 401
    try:
        conn = sqlite3.connect('database_enhanced.db')
        c = conn.cursor()
        c.execute("SELECT payment_qr_image, upi_id FROM drivers WHERE id = ?", (uid,))
        row = c.fetchone()
        conn.close()
        if row and row[0]:
            return jsonify({"success": True, "qr_image": row[0], "upi_id": row[1]})
        return jsonify({"success": False, "message": "No payment QR"})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

@app.route('/api/update_location', methods=['POST'])
def api_update_location():
    """Update live GPS location — upsert pattern, no DB spam."""
    current_user = get_current_user()
    if not current_user:
        return jsonify({"success": False}), 401
    try:
        data = request.get_json()
        lat  = data.get('lat') or data.get('latitude')
        lng  = data.get('lng') or data.get('longitude')
        role = data.get('type') or data.get('role', 'driver')
        uid  = current_user['user_id']

        if not lat or not lng:
            return jsonify({"success": False, "message": "lat/lng required"}), 400

        conn = sqlite3.connect('database_enhanced.db')
        c = conn.cursor()

        # Upsert into live_locations (single row per user — no duplicates)
        c.execute("""INSERT INTO live_locations (user_id, role, latitude, longitude, updated_at)
                     VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
                     ON CONFLICT(user_id) DO UPDATE SET
                         latitude=excluded.latitude,
                         longitude=excluded.longitude,
                         updated_at=CURRENT_TIMESTAMP""",
                  (uid, role, lat, lng))

        # Also update drivers table for backward compatibility
        if role == 'driver':
            c.execute("UPDATE drivers SET latitude=?, longitude=? WHERE id=?", (lat, lng, uid))

        conn.commit()
        conn.close()
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

@app.route('/api/get_driver_location')
def api_get_driver_location():
    """Get driver's live location — used by passenger every 5s."""
    current_user = get_current_user()
    if not current_user:
        return jsonify({"success": False}), 401
    try:
        # Accept driver_id directly or via ride_id
        driver_id = request.args.get('driver_id', type=int)
        ride_id   = request.args.get('ride_id')

        conn = sqlite3.connect('database_enhanced.db')
        c = conn.cursor()

        if not driver_id and ride_id:
            c.execute("SELECT driver_id FROM rides WHERE id=?", (ride_id,))
            row = c.fetchone()
            if row:
                driver_id = row[0]

        if not driver_id:
            conn.close()
            return jsonify({"success": False, "message": "driver_id required"})

        # Try live_locations first (most recent), fall back to drivers table
        c.execute("SELECT latitude, longitude, updated_at FROM live_locations WHERE user_id=? AND role='driver'",
                  (driver_id,))
        loc = c.fetchone()
        if not loc or not loc[0]:
            c.execute("SELECT latitude, longitude FROM drivers WHERE id=?", (driver_id,))
            loc = c.fetchone()
            if loc and loc[0]:
                conn.close()
                return jsonify({"success": True, "lat": loc[0], "lng": loc[1]})
            conn.close()
            return jsonify({"success": False, "message": "Location not available"})

        conn.close()
        return jsonify({"success": True, "lat": loc[0], "lng": loc[1],
                        "updated_at": loc[2] if len(loc) > 2 else None})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

@app.route('/api/lookup_driver')
def api_lookup_driver():
    driver_id = request.args.get('id', '').strip()
    try:
        conn = sqlite3.connect('database_enhanced.db')
        c = conn.cursor()
        c.execute("""SELECT id, name, vehicle_number, vehicle_type, rating, total_rides,
                     unique_id, verification_status, is_available, gender, profile_image
                     FROM drivers WHERE unique_id = ? OR CAST(id AS TEXT) = ?""",
                  (driver_id, driver_id))
        row = c.fetchone()
        if not row:
            conn.close()
            return jsonify({"success": False, "message": "Driver not found"})
        cols = ['id','name','vehicle_number','vehicle_type','rating','total_rides',
                'unique_id','verification_status','is_available','gender','profile_image']
        driver = dict(zip(cols, row))
        if not driver['is_available']:
            conn.close()
            return jsonify({"success": False, "message": "Driver is currently busy"})

        # Fetch profile photo — priority: photo doc → profile_image field → None
        driver['profile_photo'] = None

        # Try driver_documents table first (photo, selfie doc types)
        for doc_type in ('photo', 'selfie'):
            c.execute("SELECT file_data FROM driver_documents WHERE driver_id = ? AND doc_type = ? ORDER BY created_at DESC LIMIT 1",
                      (driver['id'], doc_type))
            doc_row = c.fetchone()
            if doc_row and doc_row[0]:
                fd = doc_row[0]
                # If it's already a data URI, use directly
                if fd.startswith('data:'):
                    driver['profile_photo'] = fd
                    break
                # Try decrypt
                try:
                    dec = decrypt_document(fd)
                    if dec and dec.startswith('data:'):
                        driver['profile_photo'] = dec
                        break
                except Exception:
                    pass
                # Raw base64 fallback
                if len(fd) > 100:
                    driver['profile_photo'] = 'data:image/jpeg;base64,' + fd
                    break

        # Fallback: profile_image column on drivers table
        if not driver['profile_photo'] and driver.get('profile_image'):
            pi = driver['profile_image']
            if pi.startswith('data:'):
                driver['profile_photo'] = pi
            elif os.path.exists(pi):
                try:
                    with open(pi, 'rb') as f:
                        b64 = base64.b64encode(f.read()).decode()
                    driver['profile_photo'] = f'data:image/jpeg;base64,{b64}'
                except Exception:
                    pass

        # Remove raw profile_image from response (large / path)
        driver.pop('profile_image', None)
        conn.close()
        return jsonify({"success": True, "driver": driver})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

@app.route('/api/nearby_drivers')
def api_nearby_drivers():
    try:
        lat    = request.args.get('lat', type=float)
        lng    = request.args.get('lng', type=float)
        radius = request.args.get('radius', 10, type=float)
        gender_filter = request.args.get('gender', '').strip()  # 'Male', 'Female', or ''

        conn = sqlite3.connect('database_enhanced.db')
        c = conn.cursor()
        query = """SELECT id, name, vehicle_number, vehicle_type, rating, total_rides,
                   unique_id, latitude, longitude, is_available, gender
                   FROM drivers WHERE is_available = 1 AND verification_status = 'verified'"""
        params = []
        if gender_filter and gender_filter in ('Male', 'Female'):
            query += " AND (gender = ? OR gender = 'Any' OR gender IS NULL)"
            params.append(gender_filter)
        c.execute(query, params)
        rows = c.fetchall()
        conn.close()

        cols = ['id','name','vehicle_number','vehicle_type','rating','total_rides',
                'unique_id','latitude','longitude','is_available','gender']
        drivers = []
        for row in rows:
            d = dict(zip(cols, row))
            if lat and lng and d['latitude'] and d['longitude']:
                R = 6371
                dLat = math.radians(d['latitude'] - lat)
                dLon = math.radians(d['longitude'] - lng)
                a = (math.sin(dLat/2)**2 +
                     math.cos(math.radians(lat)) * math.cos(math.radians(d['latitude'])) *
                     math.sin(dLon/2)**2)
                dist = R * 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
                if dist <= radius:
                    d['distance_km'] = round(dist, 2)
                    drivers.append(d)
            else:
                drivers.append(d)
        drivers.sort(key=lambda x: x.get('distance_km', 999))
        return jsonify({"success": True, "drivers": drivers[:20]})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

@app.route('/api/logout', methods=['POST'])
def api_logout():
    session.clear()
    return jsonify({"success": True})

# ── OWNER DOCUMENT MANAGEMENT ─────────────────────────────────────────────────
@app.route('/api/owner/upload_doc', methods=['POST'])
def api_owner_upload_doc():
    """Owner uploads/updates a document — only owner can do this."""
    current_user = get_current_user()
    if not current_user or current_user.get('user_type') != 'driver':
        return jsonify({"success": False, "message": "Driver authentication required"}), 401
    try:
        owner_id = current_user['user_id']
        # Verify this user is an OWNER
        conn = sqlite3.connect('database_enhanced.db')
        c = conn.cursor()
        c.execute("SELECT role FROM drivers WHERE id=?", (owner_id,))
        row = c.fetchone()
        if not row or row[0] != 'OWNER':
            conn.close()
            return jsonify({"success": False, "message": "Only vehicle owners can upload documents"}), 403

        data = request.get_json() or {}
        doc_type = data.get('doc_type', '').strip()
        file_data = data.get('file_data', '')

        if not doc_type or not file_data:
            conn.close()
            return jsonify({"success": False, "message": "doc_type and file_data required"}), 400

        encrypted = encrypt_document(file_data)
        # Delete old doc of same type, insert new
        c.execute("DELETE FROM driver_documents WHERE driver_id=? AND doc_type=?", (owner_id, doc_type))
        c.execute("""INSERT INTO driver_documents (driver_id, uploaded_by, doc_type, file_data, ai_status)
                     VALUES (?, ?, ?, ?, 'PENDING')""", (owner_id, owner_id, doc_type, encrypted))
        conn.commit()
        conn.close()
        return jsonify({"success": True, "message": f"{doc_type} uploaded successfully"})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

@app.route('/api/owner/delete_doc', methods=['POST'])
def api_owner_delete_doc():
    """Owner deletes a document — only owner can do this."""
    current_user = get_current_user()
    if not current_user or current_user.get('user_type') != 'driver':
        return jsonify({"success": False, "message": "Driver authentication required"}), 401
    try:
        owner_id = current_user['user_id']
        conn = sqlite3.connect('database_enhanced.db')
        c = conn.cursor()
        c.execute("SELECT role FROM drivers WHERE id=?", (owner_id,))
        row = c.fetchone()
        if not row or row[0] != 'OWNER':
            conn.close()
            return jsonify({"success": False, "message": "Only vehicle owners can delete documents"}), 403

        data = request.get_json() or {}
        doc_type = data.get('doc_type', '').strip()
        if not doc_type:
            conn.close()
            return jsonify({"success": False, "message": "doc_type required"}), 400

        c.execute("DELETE FROM driver_documents WHERE driver_id=? AND doc_type=?", (owner_id, doc_type))
        conn.commit()
        conn.close()
        return jsonify({"success": True, "message": f"{doc_type} deleted"})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

@app.route('/api/session_check')
def api_session_check():
    """Verify session/token state — used by dashboards on load"""
    user = get_current_user()
    if user:
        return jsonify({
            "logged_in": True,
            "user_id": user.get('user_id'),
            "user_type": user.get('user_type'),
            "name": user.get('name')
        })
    return jsonify({
        "logged_in": False,
        "user_id": None,
        "user_type": None,
        "name": None
    })

@app.route('/api/test_email')
def api_test_email():
    """Test email delivery — admin only. Usage: /api/test_email?to=your@email.com"""
    if not session.get('is_admin'):
        return jsonify({"error": "Login at /admin first, then visit this URL"}), 403
    to = request.args.get('to', GMAIL_EMAIL)
    ok = _smtp_send(to,
        "RakshaRide Email Test ✅",
        "<h2>Email is working!</h2><p>Your RakshaRide email system is configured correctly on Render.</p>",
        "Email test successful from RakshaRide.")
    return jsonify({
        "success": ok,
        "sent_to": to,
        "gmail_account": GMAIL_EMAIL,
        "message": "✅ Email sent! Check inbox." if ok else "❌ Email failed — check Render logs for [EMAIL lines"
    })

@app.route('/api/debug_docs')
def api_debug_docs():
    """Debug: check what documents exist for current driver"""
    current_user = get_current_user()
    if not current_user or current_user.get('user_type') != 'driver':
        return jsonify({"error": "Driver auth required"}), 401
    try:
        conn = sqlite3.connect('database_enhanced.db')
        c = conn.cursor()
        uid = current_user['user_id']
        c.execute("SELECT role, owner_id FROM drivers WHERE id=?", (uid,))
        row = c.fetchone()
        driver_id = uid
        if row and row[0] == 'RENT' and row[1]:
            driver_id = row[1]
        c.execute("""SELECT doc_type, length(file_data), ai_status, substr(file_data,1,40)
                     FROM driver_documents WHERE driver_id=?""", (driver_id,))
        docs = [{"doc_type": r[0], "data_length": r[1], "ai_status": r[2], "data_prefix": r[3]}
                for r in c.fetchall()]
        conn.close()
        return jsonify({
            "driver_id": driver_id,
            "role": row[0] if row else "OWNER",
            "documents": docs,
            "count": len(docs)
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ============================================================================
# LIVE DATABASE VIEWER
# ============================================================================

@app.route('/dbview')
def db_viewer_page():
    """Live database viewer — admin only, requires admin session"""
    if not session.get('is_admin'):
        return render_template('admin_login.html',
                               next='/dbview',
                               message='Login as admin to access the database viewer')
    return render_template('db_viewer.html')

@app.route('/api/db/tables')
def api_db_tables():
    """Get all table names and row counts"""
    try:
        conn = sqlite3.connect('database_enhanced.db')
        c = conn.cursor()
        c.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
        tables = []
        for (name,) in c.fetchall():
            if name == 'sqlite_sequence':
                continue
            c.execute(f"SELECT COUNT(*) FROM [{name}]")
            count = c.fetchone()[0]
            tables.append({"name": name, "rows": count})
        conn.close()
        return jsonify({"success": True, "tables": tables})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

@app.route('/api/db/table/<table_name>')
def api_db_table_data(table_name):
    """Get table data with pagination"""
    # Whitelist tables for security
    allowed = ['passengers','drivers','rides','payments','driver_documents',
               'renter_requests','ratings','otp_verification','admins','sos_alerts']
    if table_name not in allowed:
        return jsonify({"success": False, "message": "Table not allowed"}), 403
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        offset = (page - 1) * per_page
        conn = sqlite3.connect('database_enhanced.db')
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        # Get columns
        c.execute(f"PRAGMA table_info([{table_name}])")
        columns = [row['name'] for row in c.fetchall()]
        # Get total count
        c.execute(f"SELECT COUNT(*) FROM [{table_name}]")
        total = c.fetchone()[0]
        # Get rows — mask sensitive fields
        sensitive = {'password', 'file_data', 'aadhaar_doc', 'rc_doc', 'live_selfie',
                     'payment_qr_image', 'qr_code', 'otp'}
        c.execute(f"SELECT * FROM [{table_name}] ORDER BY rowid DESC LIMIT ? OFFSET ?",
                  (per_page, offset))
        rows = []
        for row in c.fetchall():
            row_dict = {}
            for col in columns:
                val = row[col]
                if col in sensitive and val:
                    if isinstance(val, str) and len(val) > 50:
                        row_dict[col] = f"[{len(val)} chars — hidden]"
                    else:
                        row_dict[col] = "***"
                else:
                    row_dict[col] = val
            rows.append(row_dict)
        conn.close()
        return jsonify({
            "success": True,
            "table": table_name,
            "columns": columns,
            "rows": rows,
            "total": total,
            "page": page,
            "per_page": per_page,
            "pages": (total + per_page - 1) // per_page
        })
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

@app.route('/api/db/stats')
def api_db_stats():
    """Get live database statistics"""
    try:
        conn = sqlite3.connect('database_enhanced.db')
        c = conn.cursor()
        stats = {}
        tables = ['passengers','drivers','rides','payments','driver_documents',
                  'renter_requests','ratings','sos_alerts']
        for t in tables:
            try:
                c.execute(f"SELECT COUNT(*) FROM [{t}]")
                stats[t] = c.fetchone()[0]
            except Exception:
                stats[t] = 0
        c.execute("SELECT COUNT(*) FROM rides WHERE status='active'")
        stats['active_rides'] = c.fetchone()[0]
        c.execute("SELECT COUNT(*) FROM drivers WHERE is_available=1")
        stats['available_drivers'] = c.fetchone()[0]
        c.execute("SELECT COUNT(*) FROM drivers WHERE verification_status='verified'")
        stats['verified_drivers'] = c.fetchone()[0]
        c.execute("SELECT COALESCE(SUM(fare),0) FROM rides WHERE status='completed'")
        stats['total_revenue'] = round(c.fetchone()[0], 2)
        conn.close()
        return jsonify({"success": True, "stats": stats, "timestamp": datetime.now().isoformat()})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

# ── DB ADMIN: EDIT ROW ────────────────────────────────────────────────────────
@app.route('/api/db/edit/<table_name>/<int:row_id>', methods=['POST'])
def api_db_edit_row(table_name, row_id):
    """Edit a single row — admin only"""
    if not session.get('is_admin'):
        return jsonify({"success": False, "message": "Admin access required"}), 403
    allowed = ['passengers','drivers','rides','payments','driver_documents',
               'renter_requests','ratings','otp_verification','admins','sos_alerts']
    if table_name not in allowed:
        return jsonify({"success": False, "message": "Table not allowed"}), 403
    # Never allow editing passwords directly
    protected = {'password'}
    try:
        data = request.get_json()
        updates = {k: v for k, v in data.items() if k not in protected and k != 'id'}
        if not updates:
            return jsonify({"success": False, "message": "No fields to update"}), 400
        set_clause = ', '.join([f"[{k}] = ?" for k in updates])
        values = list(updates.values()) + [row_id]
        conn = sqlite3.connect('database_enhanced.db')
        c = conn.cursor()
        c.execute(f"UPDATE [{table_name}] SET {set_clause} WHERE id = ?", values)
        conn.commit()
        rows_affected = c.rowcount
        conn.close()
        if rows_affected == 0:
            return jsonify({"success": False, "message": "Row not found"}), 404
        return jsonify({"success": True, "message": f"Row {row_id} updated in {table_name}"})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

# ── DB ADMIN: DELETE ROW ──────────────────────────────────────────────────────
@app.route('/api/db/delete/<table_name>/<int:row_id>', methods=['DELETE'])
def api_db_delete_row(table_name, row_id):
    """Delete a single row — admin only"""
    if not session.get('is_admin'):
        return jsonify({"success": False, "message": "Admin access required"}), 403
    allowed = ['passengers','drivers','rides','payments','driver_documents',
               'renter_requests','ratings','otp_verification','sos_alerts']
    # Never allow deleting admins via this endpoint
    if table_name not in allowed:
        return jsonify({"success": False, "message": "Table not allowed"}), 403
    try:
        conn = sqlite3.connect('database_enhanced.db')
        c = conn.cursor()
        c.execute(f"DELETE FROM [{table_name}] WHERE id = ?", (row_id,))
        conn.commit()
        rows_affected = c.rowcount
        conn.close()
        if rows_affected == 0:
            return jsonify({"success": False, "message": "Row not found"}), 404
        return jsonify({"success": True, "message": f"Row {row_id} deleted from {table_name}"})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

# ── DB ADMIN: VERIFY DRIVER ───────────────────────────────────────────────────
@app.route('/api/db/verify_driver/<int:driver_id>', methods=['POST'])
def api_db_verify_driver(driver_id):
    """Mark driver as verified — admin only"""
    if not session.get('is_admin'):
        return jsonify({"success": False, "message": "Admin access required"}), 403
    try:
        conn = sqlite3.connect('database_enhanced.db')
        c = conn.cursor()
        c.execute("UPDATE drivers SET verification_status='verified' WHERE id=?", (driver_id,))
        conn.commit()
        conn.close()
        return jsonify({"success": True, "message": f"Driver {driver_id} verified"})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

# ============================================================================
# SOS EMERGENCY ALERT SYSTEM
# ============================================================================

@app.route('/api/update_emergency_contact', methods=['POST'])
def api_update_emergency_contact():
    pid, err = _require_passenger()
    if err: return err
    try:
        data = request.get_json() or {}
        emergency_name   = (data.get('emergency_name') or '').strip()
        emergency_mobile = (data.get('emergency_mobile') or '').strip()
        emergency_email  = (data.get('emergency_email') or '').strip()
        if not emergency_mobile and not emergency_email:
            return jsonify({"success": False, "message": "Provide at least one emergency contact (mobile or email)"}), 400
        conn = sqlite3.connect('database_enhanced.db')
        c = conn.cursor()
        c.execute("""UPDATE passengers SET emergency_name=?, emergency_mobile=?, emergency_email=?
                     WHERE id=?""",
                  (emergency_name, emergency_mobile, emergency_email, pid))
        rows_updated = c.rowcount
        conn.commit()
        conn.close()
        if rows_updated == 0:
            return jsonify({"success": False, "message": "Passenger record not found"}), 404
        return jsonify({"success": True, "message": f"Emergency contact saved! {emergency_name or emergency_email} will be alerted in SOS."})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

@app.route('/api/sos_alert', methods=['POST'])
def api_sos_alert():
    """Send SOS emergency alert — emails emergency contact with live GPS location."""
    pid, err = _require_passenger()
    if err: return err

    try:
        data    = request.get_json() or {}
        lat     = data.get('lat')
        lng     = data.get('lng')
        ride_id = data.get('ride_id')
        uid     = pid

        conn = sqlite3.connect('database_enhanced.db')
        c = conn.cursor()

        # Get passenger + emergency contact
        c.execute("""SELECT name, phone, email, emergency_name, emergency_mobile, emergency_email
                     FROM passengers WHERE id=?""", (uid,))
        pax = c.fetchone()
        if not pax:
            conn.close()
            return jsonify({"success": False, "message": "Passenger not found"}), 404

        pax_name, pax_phone, pax_email, em_name, em_mobile, em_email = pax

        if not em_email and not em_mobile:
            conn.close()
            return jsonify({
                "success": False,
                "message": "No emergency contact set. Go to Profile → Emergency Contact and add one first."
            }), 400

        # Get driver info from active ride
        driver_name, vehicle_number = "Unknown", "Unknown"
        if ride_id:
            c.execute("SELECT driver_name, driver_vehicle FROM rides WHERE id=? AND passenger_id=?",
                      (ride_id, uid))
            ride_row = c.fetchone()
            if ride_row:
                driver_name = ride_row[0] or "Unknown"
                vehicle_number = ride_row[1] or "Unknown"

        # If no lat/lng from frontend, try last known location from DB
        if not lat or not lng:
            c.execute("SELECT latitude, longitude FROM live_locations WHERE user_id=? AND role='passenger'", (uid,))
            loc_row = c.fetchone()
            if loc_row and loc_row[0]:
                lat, lng = loc_row[0], loc_row[1]

        conn.close()

        maps_link  = f"https://maps.google.com/?q={lat},{lng}" if lat and lng else "Location unavailable"
        alert_time = datetime.now().strftime("%d %b %Y, %I:%M %p")

        # ── Build email ────────────────────────────────────────────────────────
        subject = f"🚨 SOS EMERGENCY — {pax_name} needs help NOW!"
        html_body = f"""
<div style="font-family:Arial,sans-serif;max-width:600px;margin:0 auto">
  <div style="background:#C62828;color:white;padding:28px;border-radius:12px 12px 0 0;text-align:center">
    <div style="font-size:48px;margin-bottom:8px">🚨</div>
    <h1 style="margin:0;font-size:26px;font-weight:900">EMERGENCY SOS ALERT</h1>
    <p style="margin:8px 0 0;opacity:0.9;font-size:15px">Someone needs immediate help</p>
  </div>
  <div style="background:#fff;border:2px solid #C62828;border-top:none;padding:28px;border-radius:0 0 12px 12px">
    <table style="width:100%;border-collapse:collapse;margin-bottom:20px">
      <tr style="background:#FFF8E1">
        <td style="padding:12px 16px;font-weight:bold;width:40%">👤 Passenger</td>
        <td style="padding:12px 16px">{pax_name}</td>
      </tr>
      <tr>
        <td style="padding:12px 16px;font-weight:bold">📱 Phone</td>
        <td style="padding:12px 16px">{pax_phone or 'Not provided'}</td>
      </tr>
      <tr style="background:#FFF8E1">
        <td style="padding:12px 16px;font-weight:bold">🚗 Driver</td>
        <td style="padding:12px 16px">{driver_name}</td>
      </tr>
      <tr>
        <td style="padding:12px 16px;font-weight:bold">🚘 Vehicle</td>
        <td style="padding:12px 16px">{vehicle_number}</td>
      </tr>
      <tr style="background:#FFF8E1">
        <td style="padding:12px 16px;font-weight:bold">🕐 Alert Time</td>
        <td style="padding:12px 16px">{alert_time}</td>
      </tr>
      <tr>
        <td style="padding:12px 16px;font-weight:bold">📍 Location</td>
        <td style="padding:12px 16px">{f'Lat: {lat:.5f}, Lng: {lng:.5f}' if lat else 'Not available'}</td>
      </tr>
    </table>
    <div style="text-align:center;margin-bottom:20px">
      <a href="{maps_link}" style="display:inline-block;background:#C62828;color:white;
         padding:16px 36px;border-radius:10px;text-decoration:none;font-weight:900;font-size:17px;
         letter-spacing:0.5px">
        📍 OPEN LIVE LOCATION IN GOOGLE MAPS
      </a>
    </div>
    <div style="background:#FFEBEE;border-left:4px solid #C62828;padding:14px;border-radius:6px">
      <p style="margin:0;color:#C62828;font-weight:bold">⚠️ Please contact {pax_name} immediately or call emergency services (112).</p>
    </div>
    <p style="margin-top:16px;color:#999;font-size:12px;text-align:center">
      Automated SOS from RakshaRide Safety System • {alert_time}
    </p>
  </div>
</div>"""

        sent_to = []

        # Send to emergency contact email
        if em_email:
            send_email_async(em_email, subject, html_body)
            sent_to.append(em_email)
            print(f"[SOS] Alert sent to emergency email: {em_email}")

        # Send confirmation to passenger's own email
        if pax_email:
            confirm_body = f"""
<div style="font-family:Arial,sans-serif;padding:24px;max-width:500px;margin:0 auto">
  <div style="background:#C62828;color:white;padding:20px;border-radius:10px;text-align:center;margin-bottom:20px">
    <h2 style="margin:0">🚨 Your SOS Alert Was Sent</h2>
  </div>
  <p>Your emergency alert was dispatched to: <strong>{em_name or em_email or em_mobile}</strong></p>
  <p><strong>📍 Location shared:</strong><br>
     <a href="{maps_link}" style="color:#C62828">{maps_link}</a></p>
  <p><strong>🕐 Time:</strong> {alert_time}</p>
  <p style="color:#666;font-size:13px">Stay safe. Help is on the way. Call 112 if in immediate danger.</p>
</div>"""
            send_email_async(pax_email, "✅ [SOS Sent] Your emergency alert was dispatched", confirm_body)

        # Log to DB
        try:
            conn2 = sqlite3.connect('database_enhanced.db')
            c2 = conn2.cursor()
            c2.execute("""CREATE TABLE IF NOT EXISTS sos_alerts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                passenger_id INTEGER, ride_id INTEGER,
                lat REAL, lng REAL,
                alert_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                sent_to TEXT, driver_name TEXT, vehicle_number TEXT
            )""")
            c2.execute("""INSERT INTO sos_alerts
                          (passenger_id, ride_id, lat, lng, sent_to, driver_name, vehicle_number)
                          VALUES (?,?,?,?,?,?,?)""",
                       (uid, ride_id, lat, lng, ','.join(sent_to), driver_name, vehicle_number))
            conn2.commit()
            conn2.close()
        except Exception as db_err:
            print(f"[SOS] DB log failed (non-fatal): {db_err}")

        contact_display = em_name or em_email or em_mobile or 'emergency contact'
        return jsonify({
            "success": True,
            "message": f"SOS alert sent to {contact_display}! Check your email for confirmation.",
            "sent_to": sent_to,
            "maps_link": maps_link,
            "contact": contact_display
        })

    except Exception as e:
        print(f"[SOS] Error: {e}")
        return jsonify({"success": False, "message": str(e)}), 500

# ============================================================================
# GLOBAL ERROR HANDLERS — always return JSON, never HTML error pages
# ============================================================================

@app.errorhandler(400)
def bad_request(e):
    return jsonify({"success": False, "error": "Bad request", "message": str(e)}), 400

@app.errorhandler(401)
def unauthorized(e):
    return jsonify({"success": False, "error": "Unauthorized", "message": "Login required"}), 401

@app.errorhandler(403)
def forbidden(e):
    return jsonify({"success": False, "error": "Forbidden", "message": "Admin access required"}), 403

@app.errorhandler(404)
def not_found(e):
    # Return HTML for page routes, JSON for API routes
    if request.path.startswith('/api/'):
        return jsonify({"success": False, "error": "Not found", "message": f"Route {request.path} not found"}), 404
    return render_template('index.html'), 404

@app.errorhandler(500)
def server_error(e):
    print(f"[ERROR 500] {request.path}: {e}")
    return jsonify({"success": False, "error": "Server error", "message": "An internal error occurred. Please try again."}), 500

@app.errorhandler(Exception)
def handle_exception(e):
    """Catch-all: ensures no unhandled exception returns HTML to the frontend."""
    import traceback
    print(f"[UNHANDLED] {request.path}: {traceback.format_exc()}")
    if request.path.startswith('/api/'):
        return jsonify({"success": False, "error": "Server error", "message": str(e)}), 500
    return render_template('index.html'), 500

# ============================================================================
# Missing API routes needed by dashboards
# ============================================================================

# ── FORGOT PASSWORD ───────────────────────────────────────────────────────────
@app.route('/api/forgot_password_otp', methods=['POST'])
def api_forgot_password_otp():
    """Send OTP to registered email for password reset."""
    try:
        data      = request.get_json() or {}
        email     = (data.get('email') or '').strip().lower()
        user_type = (data.get('user_type') or 'driver').strip()

        if not email or not is_valid_email(email):
            return jsonify({"success": False, "message": "Valid email required"}), 400

        if not rate_limit(f"forgot_{email}", limit=3, window=300):
            return jsonify({"success": False, "message": "Too many requests. Wait 5 minutes."}), 429

        conn = get_db_conn()
        c = conn.cursor()

        # Check email exists for the given user type
        if user_type == 'driver':
            c.execute("SELECT id, name FROM drivers WHERE email = ?", (email,))
        else:
            c.execute("SELECT id, name FROM passengers WHERE email = ?", (email,))
        row = c.fetchone()

        if not row:
            conn.close()
            # Don't reveal if email exists — generic message
            return jsonify({"success": True, "message": "If this email is registered, an OTP has been sent."})

        user_name = row[1]

        # Generate OTP
        otp = generate_otp()
        expiry = datetime.now() + timedelta(minutes=10)
        c.execute("DELETE FROM otp_verification WHERE email = ?", (email,))
        c.execute("INSERT INTO otp_verification (email, otp, expiry_time, attempts) VALUES (?, ?, ?, 0)",
                  (email, otp, expiry))
        conn.commit()
        conn.close()

        # Session backup
        session[f'otp_{email}'] = {'otp': otp, 'expiry': expiry.isoformat()}
        session.permanent = True

        html = f"""
<div style="font-family:Arial,sans-serif;max-width:500px;margin:0 auto">
  <div style="background:linear-gradient(135deg,#FFC107,#1565C0);padding:24px;border-radius:12px 12px 0 0;text-align:center">
    <h2 style="color:white;margin:0">🔑 Password Reset</h2>
    <p style="color:rgba(255,255,255,0.9);margin:6px 0 0">RakshaRide Account Recovery</p>
  </div>
  <div style="background:#fff;border:1px solid #e0e0e0;padding:28px;border-radius:0 0 12px 12px">
    <p style="color:#333">Hi <strong>{user_name}</strong>,</p>
    <p style="color:#555">Your password reset OTP is:</p>
    <div style="background:#f5f5f5;border:2px dashed #FFC107;border-radius:10px;padding:20px;text-align:center;margin:20px 0">
      <span style="font-size:36px;font-weight:900;letter-spacing:10px;color:#1565C0">{otp}</span>
    </div>
    <p style="color:#666;font-size:14px">Valid for <strong>10 minutes</strong>. Do not share this code.</p>
    <p style="color:#999;font-size:12px;margin-top:16px">If you didn't request this, ignore this email. Your password remains unchanged.</p>
  </div>
</div>"""

        send_email_async(email, "RakshaRide — Password Reset OTP", html,
                         f"Your password reset OTP: {otp} (valid 10 min)")
        print(f"[FORGOT] OTP sent to {email} for {user_type}")

        return jsonify({"success": True, "message": f"OTP sent to {email}"})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500


@app.route('/api/reset_password', methods=['POST'])
def api_reset_password():
    """Verify OTP and set new password."""
    try:
        data         = request.get_json() or {}
        email        = (data.get('email') or '').strip().lower()
        otp          = (data.get('otp') or '').strip()
        new_password = (data.get('new_password') or '').strip()
        user_type    = (data.get('user_type') or 'driver').strip()

        if not email or not otp or not new_password:
            return jsonify({"success": False, "message": "Email, OTP and new password required"}), 400
        if len(new_password) < 6:
            return jsonify({"success": False, "message": "Password must be at least 6 characters"}), 400

        # Verify OTP — check DB first, then session backup
        conn = get_db_conn()
        c = conn.cursor()
        c.execute("SELECT otp, expiry_time FROM otp_verification WHERE email = ?", (email,))
        row = c.fetchone()

        verified = False
        if row:
            stored_otp, expiry_str = row
            try:
                expiry = datetime.fromisoformat(expiry_str.replace(' ', 'T'))
            except Exception:
                expiry = datetime.strptime(expiry_str, '%Y-%m-%d %H:%M:%S.%f')
            if datetime.now() <= expiry and otp == stored_otp:
                verified = True
                c.execute("DELETE FROM otp_verification WHERE email = ?", (email,))
                conn.commit()
        else:
            # Session fallback
            sess_data = session.get(f'otp_{email}')
            if sess_data:
                try:
                    expiry = datetime.fromisoformat(sess_data['expiry'])
                    if datetime.now() <= expiry and otp == sess_data['otp']:
                        verified = True
                        session.pop(f'otp_{email}', None)
                except Exception:
                    pass

        if not verified:
            conn.close()
            return jsonify({"success": False, "message": "Invalid or expired OTP. Please request a new one."}), 400

        # Update password
        hashed = hash_password(new_password)
        if user_type == 'driver':
            c.execute("UPDATE drivers SET password=?, first_login=0 WHERE email=?", (hashed, email))
        else:
            c.execute("UPDATE passengers SET password=? WHERE email=?", (hashed, email))

        if c.rowcount == 0:
            conn.close()
            return jsonify({"success": False, "message": "Account not found"}), 404

        conn.commit()
        conn.close()
        print(f"[RESET] Password updated for {email} ({user_type})")
        return jsonify({"success": True, "message": "Password reset successfully! You can now login."})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500


# ── FARE ESTIMATE (live preview during ride) ──────────────────────────────────
@app.route('/api/fare_estimate')
def api_fare_estimate():
    """Return live fare estimate given distance_km and duration_minutes."""
    try:
        dist = request.args.get('distance_km', 0, type=float)
        mins = request.args.get('duration_minutes', 0, type=float)
        fare = calculate_fare(mins, dist)
        breakdown = {
            "base_fare": 25.0,
            "distance_charge": round(dist * 12.0, 2),
            "time_charge": round(mins * 1.0, 2),
            "total": fare,
            "distance_km": round(dist, 2),
            "duration_minutes": round(mins, 1)
        }
        return jsonify({"success": True, "fare": fare, "breakdown": breakdown})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500


@app.route('/api/update_payment_qr', methods=['POST'])
def api_update_payment_qr():
    current_user = get_current_user()
    if not current_user or current_user.get('user_type') != 'driver':
        return jsonify({"success": False, "message": "Driver auth required"}), 401
    try:
        data = request.get_json()
        qr_image = data.get('qr_image', '')
        upi_id = data.get('upi_id', '')
        conn = sqlite3.connect('database_enhanced.db')
        c = conn.cursor()
        c.execute("UPDATE drivers SET payment_qr_image=?, upi_id=? WHERE id=?",
                  (qr_image, upi_id, current_user['user_id']))
        conn.commit()
        conn.close()
        return jsonify({"success": True, "message": "Payment QR updated"})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500


@app.route('/api/get_passenger_location')
def api_get_passenger_location():
    """Get passenger live location — used by driver during active ride."""
    current_user = get_current_user()
    if not current_user:
        return jsonify({"success": False}), 401
    try:
        ride_id = request.args.get('ride_id')
        passenger_id = request.args.get('passenger_id', type=int)
        conn = sqlite3.connect('database_enhanced.db')
        c = conn.cursor()
        if not passenger_id and ride_id:
            c.execute("SELECT passenger_id FROM rides WHERE id=?", (ride_id,))
            row = c.fetchone()
            if row:
                passenger_id = row[0]
        if not passenger_id:
            conn.close()
            return jsonify({"success": False, "message": "passenger_id required"})
        c.execute("SELECT latitude, longitude, updated_at FROM live_locations WHERE user_id=? AND role='passenger'",
                  (passenger_id,))
        loc = c.fetchone()
        conn.close()
        if loc and loc[0]:
            return jsonify({"success": True, "lat": loc[0], "lng": loc[1], "updated_at": loc[2]})
        return jsonify({"success": False, "message": "No location data"})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500


# ============================================================================
# Run Application
# ============================================================================

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_ENV') != 'production'
    print(f"\n  RakshaRide — running on http://0.0.0.0:{port}")
    init_db()
    app.run(debug=debug, host='0.0.0.0', port=port)



