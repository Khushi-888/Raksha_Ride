from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from database import get_db_connection
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import random
from datetime import datetime, timedelta
import qrcode
import os
import ssl
try:
    from waitress import serve
except ImportError:
    serve = None

app = Flask(__name__)
app.secret_key = 'raksharide_premium_secret_key'

# --- EMAIL CONFIGURATION# Gmail SMTP Configuration
SENDER_EMAIL = "riksharide2026@gmail.com"
APP_PASSWORD = "evsz tunv eoqi lawu"  # ✅ CONFIRMED PASSCODE
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587  # TLS Port

QR_FOLDER = os.path.join('static', 'qrcodes')
os.makedirs(QR_FOLDER, exist_ok=True)

# -------------------- HELPER FUNCTIONS --------------------

def send_email_otp(recipient_email, otp):
    subject = "RakshaRide - Your Security Code"
    body = f"Hello! Your OTP for RakshaRide account verification is: {otp}\n\nThis code expires in 10 minutes."
    
    msg = MIMEMultipart()
    msg['From'] = SENDER_EMAIL
    msg['To'] = recipient_email
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain'))

    try:
        # Using TLS instead of SSL as per user request
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(SENDER_EMAIL, APP_PASSWORD)
        server.send_message(msg)
        server.quit()
        return True
    except Exception as e:
        print(f"!!! EMAIL FAILED: {e}")
        return False

def generate_driver_qr(driver_id, name, vehicle_num):
    qr_data = f"RAKSHARIDE_VERIFIED:{driver_id}:{name}:{vehicle_num}"
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(qr_data)
    qr.make(fit=True)
    img = qr.make_image(fill_color="#fca311", back_color="#1e222d") # Themed colors
    filename = f"qr_driver_{driver_id}.png"
    filepath = os.path.join(QR_FOLDER, filename)
    img.save(filepath)
    return filename

# -------------------- ROUTES --------------------

@app.route('/')
def index():
    if 'user_id' in session:
        if session['role'] == 'driver':
            return redirect(url_for('driver_dashboard'))
        return redirect(url_for('passenger_dashboard'))
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        role = request.form.get('role')
        name = request.form.get('name')
        email = request.form.get('email')
        phone = request.form.get('phone')
        password = request.form.get('password')
        
        # Vehicle (for drivers)
        v_num = request.form.get('vehicle_number', '')
        v_type = request.form.get('vehicle_type', 'auto')
        v_model = request.form.get('vehicle_model', '')
        v_color = request.form.get('vehicle_color', '')
        license_num = request.form.get('license_number', '')

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        table = "drivers" if role == 'driver' else "passengers"
        
        # Check exists
        cursor.execute(f"SELECT id FROM {table} WHERE email = %s", (email,))
        if cursor.fetchone():
            flash('Email already registered!', 'error')
            return redirect(url_for('register'))

        p_hash = generate_password_hash(password)
        
        if role == 'driver':
            cursor.execute(f"""
                INSERT INTO drivers (name, email, phone, password, vehicle_number, vehicle_type, vehicle_model, vehicle_color, license_number) 
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (name, email, phone, p_hash, v_num, v_type, v_model, v_color, license_num))
        else:
            cursor.execute(f"INSERT INTO passengers (name, email, phone, password) VALUES (%s, %s, %s, %s)", 
                           (name, email, phone, p_hash))
        
        # OTP Generation
        otp = str(random.randint(100000, 999999))
        expiry = datetime.now() + timedelta(minutes=5)
        cursor.execute("DELETE FROM otp_verification WHERE email = %s", (email,))
        cursor.execute("INSERT INTO otp_verification (email, user_type, otp, expiry_time) VALUES (%s, %s, %s, %s)",
                       (email, role, otp, expiry))
        
        conn.commit()
        
        # Send Email
        if send_email_otp(email, otp):
            session['reg_email'] = email
            session['reg_role'] = role
            flash('OTP sent to your email! Please verify.', 'success')
            return redirect(url_for('verify_otp'))
        else:
            # Bypass for local if email fails
            session['reg_email'] = email
            session['reg_role'] = role
            print(f"DEBUG: OTP for {email} is {otp}")
            flash('Failed to send email. Use bypass code 123456.', 'error')
            return redirect(url_for('verify_otp'))
            
    return render_template('register.html')

@app.route('/verify-otp', methods=['GET', 'POST'])
def verify_otp():
    if 'reg_email' not in session:
        return redirect(url_for('register'))
    
    if request.method == 'POST':
        otp_input = request.form.get('otp')
        email = session['reg_email']
        role = session['reg_role']
        
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM otp_verification WHERE email = %s AND otp = %s", (email, otp_input))
        record = cursor.fetchone()
        
        # Allow 123456 as universal bypass for testing
        if record or otp_input == '123456':
            table = "drivers" if role == 'driver' else "passengers"
            cursor.execute(f"UPDATE {table} SET is_verified = 1 WHERE email = %s", (email,))
            
            # If driver, generate their permanent QR now
            if role == 'driver':
                cursor.execute("SELECT id, name, vehicle_number FROM drivers WHERE email = %s", (email,))
                d = cursor.fetchone()
                qr_file = generate_driver_qr(d['id'], d['name'], d['vehicle_number'])
                cursor.execute("UPDATE drivers SET qr_code_url = %s WHERE id = %s", (qr_file, d['id']))
                
            conn.commit()
            session.pop('reg_email', None)
            flash('Verification successful! You can now login.', 'success')
            return redirect(url_for('login'))
        else:
            flash('Invalid or expired OTP!', 'error')
            
    return render_template('verify_otp.html', email=session['reg_email'])

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        role = request.form.get('role')
        
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        table = "drivers" if role == 'driver' else "passengers"
        
        cursor.execute(f"SELECT * FROM {table} WHERE email = %s", (email,))
        user = cursor.fetchone()
        
        if user and check_password_hash(user['password'], password):
            if not user['is_verified']:
                session['reg_email'] = email
                session['reg_role'] = role
                flash('Please verify your email first.', 'error')
                return redirect(url_for('verify_otp'))
            
            session['user_id'] = user['id']
            session['name'] = user['name']
            session['role'] = role
            
            # Set driver status to available on login
            if role == 'driver':
                cursor.execute("UPDATE drivers SET availability_status = 'available' WHERE id = %s", (user['id'],))
                conn.commit()
                
            return redirect(url_for('index'))
        else:
            flash('Invalid credentials!', 'error')
            
    return render_template('login.html')

@app.route('/logout')
def logout():
    if session.get('role') == 'driver':
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE drivers SET availability_status = 'offline' WHERE id = %s", (session['user_id'],))
        conn.commit()
        
    session.clear()
    return redirect(url_for('index'))

# -------------------- PASSENGER DASHBOARD --------------------

@app.route('/passenger/dashboard')
def passenger_dashboard():
    if session.get('role') != 'passenger': return redirect(url_for('login'))
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    # Get history
    cursor.execute("""
        SELECT r.*, d.name as driver_name, d.vehicle_number, d.vehicle_type 
        FROM rides r 
        LEFT JOIN drivers d ON r.driver_id = d.id 
        WHERE r.passenger_id = %s ORDER BY r.created_at DESC
    """, (session['user_id'],))
    history = cursor.fetchall()
    
    # Get available drivers for booking
    cursor.execute("SELECT id, name, vehicle_type, vehicle_number, rating FROM drivers WHERE availability_status = 'available'")
    available_drivers = cursor.fetchall()
    
    return render_template('passenger_dashboard.html', history=history, drivers=available_drivers)

@app.route('/ride/request', methods=['POST'])
def request_ride():
    if session.get('role') != 'passenger': return jsonify({'success': False})
    
    passenger_id = session['user_id']
    driver_id = request.form.get('driver_id')
    pickup = request.form.get('pickup')
    dropoff = request.form.get('dropoff')
    
    fare = random.randint(80, 250)
    dist = round(random.uniform(2.5, 12.0), 1)
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO rides (passenger_id, driver_id, start_location, end_location, distance, calculated_fare, status) 
        VALUES (%s, %s, %s, %s, %s, %s, 'pending')
    """, (passenger_id, driver_id, pickup, dropoff, dist, fare))
    conn.commit()
    
    flash('Ride requested! Waiting for driver to accept.', 'success')
    return redirect(url_for('passenger_dashboard'))

@app.route('/ride/verify_qr/<int:ride_id>', methods=['POST'])
def verify_ride_qr(ride_id):
    if session.get('role') != 'passenger': return redirect(url_for('login'))
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    # Check if this ride belongs to this passenger and is accepted
    cursor.execute("SELECT * FROM rides WHERE id = %s AND passenger_id = %s AND status = 'accepted'", (ride_id, session['user_id']))
    ride = cursor.fetchone()
    
    if ride:
        cursor.execute("UPDATE rides SET status = 'ongoing' WHERE id = %s", (ride_id,))
        conn.commit()
        flash('QR Verified! Ride has started.', 'success')
    else:
        flash('Verification failed or ride not ready.', 'error')
        
    return redirect(url_for('passenger_dashboard'))

# -------------------- DRIVER DASHBOARD --------------------

@app.route('/driver/dashboard')
def driver_dashboard():
    if session.get('role') != 'driver': return redirect(url_for('login'))
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    # Get My Stats
    cursor.execute("SELECT * FROM drivers WHERE id = %s", (session['user_id'],))
    driver = cursor.fetchone()
    
    # Get pending requests
    cursor.execute("""
        SELECT r.*, p.name as passenger_name, p.phone as passenger_phone 
        FROM rides r 
        JOIN passengers p ON r.passenger_id = p.id 
        WHERE r.driver_id = %s AND r.status = 'pending'
    """, (session['user_id'],))
    requests = cursor.fetchall()
    
    # Get history
    cursor.execute("""
        SELECT r.*, p.name as passenger_name 
        FROM rides r 
        JOIN passengers p ON r.passenger_id = p.id 
        WHERE r.driver_id = %s AND r.status != 'pending' ORDER BY r.created_at DESC
    """, (session['user_id'],))
    history = cursor.fetchall()
    
    return render_template('driver_dashboard.html', driver=driver, requests=requests, history=history)

@app.route('/ride/accept/<int:ride_id>')
def accept_ride(ride_id):
    if session.get('role') != 'driver': return redirect(url_for('login'))
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Accept ride and set driver to busy
    cursor.execute("UPDATE rides SET status = 'accepted', start_time = %s WHERE id = %s", (datetime.now(), ride_id))
    cursor.execute("UPDATE drivers SET availability_status = 'busy' WHERE id = %s", (session['user_id'],))
    conn.commit()
    
    flash('Ride Accepted! Show your QR code to the passenger to start.', 'success')
    return redirect(url_for('driver_dashboard'))

@app.route('/ride/complete/<int:ride_id>', methods=['POST'])
def complete_ride(ride_id):
    # This is triggered by PASSENGER after "scanning" (clicking verify)
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    cursor.execute("SELECT driver_id FROM rides WHERE id = %s", (ride_id,))
    ride = cursor.fetchone()
    
    # Update ride to completed and paid
    cursor.execute("""
        UPDATE rides 
        SET status = 'completed', payment_status = 'paid', end_time = %s 
        WHERE id = %s
    """, (datetime.now(), ride_id))
    
    # Driver is available again
    cursor.execute("UPDATE drivers SET availability_status = 'available', total_rides = total_rides + 1 WHERE id = %s", (ride['driver_id'],))
    conn.commit()
    
    flash('Ride Completed & Payment Verified via QR!', 'success')
    return redirect(url_for('passenger_dashboard'))

@app.route('/ride/update_location/<int:ride_id>', methods=['POST'])
def update_location(ride_id):
    # Simulated location update
    lat = request.json.get('lat')
    lng = request.json.get('lng')
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE rides SET curr_lat = %s, curr_lng = %s WHERE id = %s", (lat, lng, ride_id))
    conn.commit()
    return jsonify({'success': True})

@app.route('/api/ride_status/<int:ride_id>')
def get_ride_status(ride_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT status, curr_lat, curr_lng FROM rides WHERE id = %s", (ride_id,))
    data = cursor.fetchone()
    return jsonify(data)

if __name__ == '__main__':
    if serve:
        print("\n" + "★"*50)
        print("   RAKSHARIDE PRODUCTION SERVER STARTED")
        print("   Listening on: http://localhost:5000")
        print("★"*50 + "\n")
        serve(app, host='0.0.0.0', port=5000)
    else:
        app.run(debug=True, port=5000)
