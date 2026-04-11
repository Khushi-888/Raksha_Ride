from flask import Flask, render_template, request, redirect, url_for, session, jsonify, send_from_directory
from flask_mail import Mail, Message
import sqlite3
import os
import secrets
import qrcode
from datetime import datetime, timedelta
from itsdangerous import URLSafeTimedSerializer, SignatureExpired
from werkzeug.utils import secure_filename
import random

app = Flask(__name__)
app.secret_key = secrets.token_hex(16)
DB_FILE = 'raksharide_final.db'

# --- EMAIL CONFIGURATION ---
# Note: These are your verified riksharide2026@gmail.com credentials.
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'riksharide2026@gmail.com'
app.config['MAIL_PASSWORD'] = 'evsz tunv eoqi lawu'
app.config['MAIL_DEFAULT_SENDER'] = ('RakshaRide Official', 'riksharide2026@gmail.com')

mail = Mail(app)
serializer = URLSafeTimedSerializer(app.secret_key)

# --- UPLOAD CONFIGURATION ---
UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'pdf'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# --- DB HELPERS ---
def get_db_connection():
    conn = sqlite3.connect(DB_FILE, timeout=30)
    conn.row_factory = sqlite3.Row
    # WAL mode allows concurrent reads + one writer without locking errors
    conn.execute('PRAGMA journal_mode=WAL;')
    conn.execute('PRAGMA busy_timeout=30000;')
    return conn

# --- ROUTES: GENERAL ---
@app.route('/')
def index():
    return render_template('index_premium.html')

# --- ROUTES: PASSENGER SYSTEM ---
@app.route('/api/send_otp', methods=['POST'])
def send_otp():
    """Send OTP to email for both citizens and drivers."""
    data = request.get_json()
    email = data.get('email', '').strip()
    
    if not email:
        return jsonify({"success": False, "message": "Email address required"}), 400
        
    otp = str(random.randint(100000, 999999))
    expiry = datetime.now() + timedelta(minutes=5)
    
    conn = get_db_connection()
    c = conn.cursor()
    # Replace existing OTP if any
    c.execute("DELETE FROM otp_verification WHERE email = ?", (email,))
    c.execute("INSERT INTO otp_verification (email, otp, expiry_time) VALUES (?, ?, ?)",
                 (email, otp, expiry))
    conn.commit()
    conn.close()
    
    # Send email
    try:
        print(f"\n--- [DEBUG] OUTGOING EMAIL ---")
        print(f"To: {email}")
        print(f"OTP Code: {otp}")
        print(f"Using SMTP: {app.config['MAIL_SERVER']}:{app.config['MAIL_PORT']}")
        
        subject = "RakshaRide - Your Security OTP"
        body = f"Hello!\n\nYour RakshaRide verification code is:\n\n    {otp}\n\nThis code is valid for 5 minutes.\n⚠️ For your safety, do not share this code.\n\nBest regards,\nRakshaRide Safety Team"
        
        # Clean the app password (remove spaces and dashes) just in case
        clean_pw = app.config['MAIL_PASSWORD'].replace(" ", "").replace("-", "")
        app.config['MAIL_PASSWORD'] = clean_pw
        
        msg = Message(subject=subject, recipients=[email], body=body)
        mail.send(msg)
        print(f"✅ SUCCESS: OTP sent to {email}")
        return jsonify({"success": True, "message": f"OTP sent to {email}"})
    except Exception as e:
        print(f"❌ FAILURE: {str(e)}")
        return jsonify({"success": False, "message": "Email delivery failed"}), 500

@app.route('/api/verify_otp', methods=['POST'])
def verify_otp():
    data = request.get_json()
    email = data.get('email', '').strip()
    otp = data.get('otp', '').strip()
    
    conn = get_db_connection()
    record = conn.execute("SELECT * FROM otp_verification WHERE email = ? AND otp = ?", (email, otp)).fetchone()
    
    if record:
        expiry_time = datetime.strptime(record['expiry_time'], '%Y-%m-%d %H:%M:%S.%f')
        if datetime.now() <= expiry_time:
            conn.execute("DELETE FROM otp_verification WHERE email = ?", (email,))
            conn.commit()
            conn.close()
            return jsonify({"success": True, "message": "OTP verified successfully"})
        else:
            conn.close()
            return jsonify({"success": False, "message": "OTP has expired"}), 400
    conn.close()
    return jsonify({"success": False, "message": "Invalid OTP"}), 400

@app.route('/register/passenger', methods=['GET', 'POST'])
def register_passenger_page():
    if request.method == 'POST':
        # API request sends JSON if possible, but form sending URL encoded
        if request.is_json:
            data = request.get_json()
        else:
            data = request.form
            
        name = data.get('name')
        email = data.get('email')
        mobile = data.get('mobile')
        password = data.get('password')
        
        if not name or not mobile or not password or not email:
            return jsonify({"success": False, "message": "All fields required"}) if request.is_json else render_template('register_passenger_final.html', error="All fields required")
        
        conn = get_db_connection()
        try:
            conn.execute('INSERT INTO passengers (name, email, mobile, password) VALUES (?, ?, ?, ?)',
                         (name, email, mobile, password))
            conn.commit()
            return jsonify({"success": True, "message": "Registration successful"}) if request.is_json else redirect(url_for('login_passenger_page'))
        except sqlite3.IntegrityError:
            return jsonify({"success": False, "message": "Mobile or email already registered"}) if request.is_json else render_template('register_passenger_final.html', error="Mobile number or email already registered")
        finally:
            conn.close()
            
    return render_template('register_passenger_final.html')

@app.route('/login/passenger', methods=['GET', 'POST'])
def login_passenger_page():
    if request.method == 'POST':
        mobile = request.form.get('mobile')
        password = request.form.get('password')
        
        conn = get_db_connection()
        user = conn.execute('SELECT * FROM passengers WHERE mobile = ? AND password = ?',
                           (mobile, password)).fetchone()
        conn.close()
        
        if user:
            session['user_id'] = user['id']
            session['user_type'] = 'passenger'
            session['name'] = user['name']
            return redirect(url_for('passenger_dashboard'))
        else:
            return render_template('login_passenger_final.html', error="Invalid mobile or password")
            
    return render_template('login_passenger_final.html')

@app.route('/dashboard/passenger')
def passenger_dashboard():
    if session.get('user_type') != 'passenger':
        return redirect(url_for('login_passenger_page'))
    return render_template('dashboard_passenger_final.html', user=session)

# --- ROUTES: DRIVER SYSTEM ---
@app.route('/register/driver', methods=['GET', 'POST'])
def register_driver_page():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        phone = request.form.get('phone')
        password = request.form.get('password')
        driver_type = request.form.get('driver_type') # 'owner' or 'renter'
        owner_email = request.form.get('owner_email') if driver_type == 'renter' else None
        
        if not all([name, email, phone, password, driver_type]):
            return render_template('register_driver_final.html', error="All fields required")
        
        conn = get_db_connection()
        try:
            # If renter, needs owner approval
            status = 'pending' if driver_type == 'owner' else 'pending_approval'
            
            cursor = conn.execute('''INSERT INTO drivers (name, email, phone, password, driver_type, status, owner_email) 
                                     VALUES (?, ?, ?, ?, ?, ?, ?)''',
                                  (name, email, phone, password, driver_type, status, owner_email))
            driver_id = cursor.lastrowid
            conn.commit()
            
            if driver_type == 'renter' and owner_email:
                # Send approval email to owner
                token = serializer.dumps(driver_id, salt='owner-approval')
                approval_url = url_for('approve_renter', token=token, _external=True)
                
                msg = Message("RakshaRide - Renter Approval Request",
                              recipients=[owner_email])
                msg.body = f"Hello, Driver {name} has requested to use your vehicle on RakshaRide. Click here to approve: {approval_url}"
                mail.send(msg)
                
            return render_template('register_driver_final.html', success="Registration successful. Check email if Renter.")
        except sqlite3.IntegrityError:
            return render_template('register_driver_final.html', error="Email already registered")
        finally:
            conn.close()
            
    return render_template('register_driver_final.html')

@app.route('/approve_renter/<token>')
def approve_renter(token):
    try:
        driver_id = serializer.loads(token, salt='owner-approval', max_age=86400) # 24h
        conn = get_db_connection()
        conn.execute("UPDATE drivers SET status = 'pending' WHERE id = ? AND driver_type = 'renter'", (driver_id,))
        conn.commit()
        conn.close()
        return "Renter Approved! They can now upload documents."
    except SignatureExpired:
        return "The approval link has expired."
    except Exception as e:
        return "Invalid token."

@app.route('/login/driver', methods=['GET', 'POST'])
def login_driver_page():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        conn = get_db_connection()
        user = conn.execute('SELECT * FROM drivers WHERE email = ? AND password = ?',
                           (email, password)).fetchone()
        conn.close()
        
        if user:
            session['user_id'] = user['id']
            session['user_type'] = 'driver'
            session['name'] = user['name']
            session['driver_type'] = user['driver_type']
            return redirect(url_for('driver_dashboard'))
        else:
            return render_template('login_driver_final.html', error="Invalid email or password")
            
    return render_template('login_driver_final.html')

@app.route('/dashboard/driver')
def driver_dashboard():
    if session.get('user_type') != 'driver':
        return redirect(url_for('login_driver_page'))
    
    conn = get_db_connection()
    driver = conn.execute('SELECT * FROM drivers WHERE id = ?', (session['user_id'],)).fetchone()
    docs = conn.execute('SELECT * FROM driver_documents WHERE driver_id = ?', (session['user_id'],)).fetchone()
    conn.close()
    
    return render_template('dashboard_driver_final.html', driver=driver, docs=docs)

@app.route('/driver/upload', methods=['POST'])
def driver_upload():
    if session.get('user_type') != 'driver':
        return redirect(url_for('login_driver_page'))
    
    if session.get('driver_type') == 'renter':
        # In a real scenario, we might allow renters to upload THEIR license 
        # but the prompt says: "Owner: Can upload/edit documents ✅ Renter: Can only VIEW documents ❌"
        # Since I'm following specific prompt logic:
        return jsonify({"success": False, "message": "Renters can only view documents."})

    driver_id = session['user_id']
    files = request.files
    
    conn = get_db_connection()
    
    # Save Profile Image
    if 'profile_photo' in files:
        f = files['profile_photo']
        if f and allowed_file(f.filename):
            filename = f"profile_{driver_id}_" + secure_filename(f.filename)
            f.save(os.path.join(app.config['UPLOAD_FOLDER'], 'profile', filename))
            conn.execute("UPDATE drivers SET profile_image = ? WHERE id = ?", (filename, driver_id))

    # Save Docs
    doc_paths = {}
    for doc_type in ['aadhar', 'license', 'rc']:
        if doc_type in files:
            f = files[doc_type]
            if f and allowed_file(f.filename):
                filename = f"{doc_type}_{driver_id}_" + secure_filename(f.filename)
                f.save(os.path.join(app.config['UPLOAD_FOLDER'], 'documents', filename))
                doc_paths[doc_type] = filename

    if doc_paths:
        # Check if row exists
        exists = conn.execute("SELECT 1 FROM driver_documents WHERE driver_id = ?", (driver_id,)).fetchone()
        if exists:
            for k, v in doc_paths.items():
                conn.execute(f"UPDATE driver_documents SET {k} = ? WHERE driver_id = ?", (v, driver_id))
        else:
            conn.execute("INSERT INTO driver_documents (driver_id, aadhar, license, rc) VALUES (?, ?, ?, ?)",
                         (driver_id, doc_paths.get('aadhar'), doc_paths.get('license'), doc_paths.get('rc')))

    # Check if all 3 docs uploaded to set status to 'verified'
    all_docs = conn.execute("SELECT * FROM driver_documents WHERE driver_id = ?", (driver_id,)).fetchone()
    if all_docs and all_docs['aadhar'] and all_docs['license'] and all_docs['rc']:
        conn.execute("UPDATE drivers SET status = 'verified' WHERE id = ?", (driver_id,))
        # Pass the SAME connection so we don't open a second one (avoids 'database is locked')
        generate_qr(driver_id, conn)

    conn.commit()
    conn.close()
    return redirect(url_for('driver_dashboard'))

def generate_qr(driver_id, conn=None):
    """Generate QR code for driver. Accepts an existing connection to avoid locking."""
    qr_data = f"{request.host_url}driver/{driver_id}"
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(qr_data)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    filename = f"qr_{driver_id}.png"
    
    # Ensure QR directory exists
    qr_dir = os.path.join(app.config['UPLOAD_FOLDER'], 'qr')
    os.makedirs(qr_dir, exist_ok=True)
    img.save(os.path.join(qr_dir, filename))
    
    close_after = False
    if conn is None:
        # Called standalone — open our own connection safely
        conn = get_db_connection()
        close_after = True
    
    conn.execute("UPDATE drivers SET qr_code = ? WHERE id = ?", (filename, driver_id))
    
    if close_after:
        conn.commit()
        conn.close()

# --- ROUTES: PUBLIC DRIVER PROFILE ---
@app.route('/driver/<int:driver_id>')
def public_driver_profile(driver_id):
    conn = get_db_connection()
    driver = conn.execute('''SELECT d.*, AVG(r.rating) as avg_rating, COUNT(r.id) as total_rides 
                             FROM drivers d 
                             LEFT JOIN ratings r ON d.id = r.driver_id 
                             WHERE d.id = ?''', (driver_id,)).fetchone()
    conn.close()
    
    if not driver:
        return "Driver not found", 404
        
    return render_template('public_driver_profile.html', driver=driver)

# --- ROUTES: RIDE & RATING ---
@app.route('/api/start_ride', methods=['POST'])
def start_ride():
    if session.get('user_type') != 'passenger':
        return jsonify({"success": False, "message": "Only passengers can start rides"}), 401
    
    data = request.get_json()
    driver_id = data.get('driver_id')
    
    conn = get_db_connection()
    cursor = conn.execute("INSERT INTO rides (passenger_id, driver_id) VALUES (?, ?)",
                        (session['user_id'], driver_id))
    ride_id = cursor.lastrowid
    conn.commit()
    conn.close()
    
    return jsonify({"success": True, "ride_id": ride_id})

@app.route('/ride/<int:ride_id>/track')
def track_ride(ride_id):
    if session.get('user_type') != 'passenger':
        return redirect(url_for('login_passenger_page'))
    
    conn = get_db_connection()
    ride = conn.execute('''
        SELECT r.*, d.name as driver_name, d.vehicle_details 
        FROM rides r 
        JOIN drivers d ON r.driver_id = d.id 
        WHERE r.id = ? AND r.passenger_id = ?
    ''', (ride_id, session['user_id'])).fetchone()
    conn.close()
    
    if not ride:
        return "Ride not found or unauthorized", 404
        
    return render_template('track_ride.html', ride=ride)

@app.route('/rate_ride', methods=['POST'])
def rate_ride():
    if session.get('user_type') != 'passenger':
        return redirect(url_for('index'))
    
    ride_id = request.form.get('ride_id')
    driver_id = request.form.get('driver_id')
    rating = request.form.get('rating')
    comment = request.form.get('comment')
    
    conn = get_db_connection()
    conn.execute("INSERT INTO ratings (ride_id, passenger_id, driver_id, rating, comment) VALUES (?, ?, ?, ?, ?)",
                (ride_id, session['user_id'], driver_id, rating, comment))
    conn.commit()
    conn.close()
    
    return redirect(url_for('passenger_dashboard'))

# --- LOGOUT ---
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

@app.route('/scanner')
def scanner():
    # If not logged in, they can't scan
    if session.get('user_type') != 'passenger':
        return redirect(url_for('login_passenger_page'))
    return redirect(url_for('passenger_dashboard'))

if __name__ == '__main__':
    app.run(debug=True, port=5000)
