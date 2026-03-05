import sqlite3
import datetime
import random
from flask import Blueprint, request, jsonify, current_app
from flask_bcrypt import Bcrypt
import jwt

bcrypt = Bcrypt()
auth = Blueprint('auth', __name__)

# Temporary in-memory OTP store (in production, use Redis or a DB table)
OTP_STORE = {}

def get_db():
    conn = sqlite3.connect(current_app.config['DATABASE_PATH'])
    conn.row_factory = sqlite3.Row
    return conn

def generate_token(user_id, role):
    payload = {
        'id': user_id,
        'role': role,
        'exp': datetime.datetime.utcnow() + datetime.timedelta(days=7)
    }
    return jwt.encode(payload, current_app.config['SECRET_KEY'], algorithm="HS256")

@auth.route('/api/verify-rc', methods=['POST'])
def verify_rc():
    """Mock API representing external transport department registry."""
    data = request.json
    rc = data.get('rcNo', '')
    vno = data.get('vehicleNumber', '')
    if rc.startswith('RC') and len(rc) >= 5 and vno:
        return jsonify({"valid": True, "message": "RC and Vehicle Number verified successfully."})
    return jsonify({"valid": False, "message": "Invalid RC or Vehicle Number according to RTO registry."}), 400

@auth.route('/api/register/driver', methods=['POST'])
def register_driver():
    data = request.json
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        # Check existing
        cursor.execute("SELECT id FROM drivers WHERE email = ? OR vehicle_number = ?", 
                      (data['email'].lower(), data['vehicleNumber'].upper()))
        if cursor.fetchone():
            return jsonify({"error": "Driver with this email or vehicle number already exists"}), 400
        
        # Generate ID
        cursor.execute("SELECT COUNT(*) FROM drivers")
        count = cursor.fetchone()[0]
        new_id = f"DRV-{2001 + count}"
        
        # Hash password
        hashed_pw = bcrypt.generate_password_hash(data['password']).decode('utf-8')
        photo = f"https://i.pravatar.cc/300?u={new_id}"
        
        cursor.execute("""
            INSERT INTO drivers 
            (id, name, age, mobile, email, vehicle_number, rc_number, pick_location, password_hash, photo)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            new_id, data['name'], int(data['age']), data['mobile'], data['email'].lower(),
            data['vehicleNumber'].upper(), data['rcNo'].upper(), data['pickLocation'],
            hashed_pw, photo
        ))
        conn.commit()
        
        cursor.execute("SELECT * FROM drivers WHERE id = ?", (new_id,))
        driver = dict(cursor.fetchone())
        driver.pop('password_hash', None)
        
        return jsonify({"message": "Driver registered", "driver": driver}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 400
    finally:
        conn.close()

@auth.route('/api/register/passenger', methods=['POST'])
def register_passenger():
    data = request.json
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        mobile = data['mobile']
        email = data.get('email', '').lower()
        
        if email:
            cursor.execute("SELECT id FROM passengers WHERE mobile = ? OR email = ?", (mobile, email))
        else:
            cursor.execute("SELECT id FROM passengers WHERE mobile = ?", (mobile,))
            
        if cursor.fetchone():
            return jsonify({"error": "Passenger with this mobile or email already exists"}), 400
            
        hashed_pw = bcrypt.generate_password_hash(data['password']).decode('utf-8')
        
        cursor.execute("SELECT COUNT(*) FROM passengers")
        count = cursor.fetchone()[0]
        new_id = f"USR-{6001 + count}"
        
        if not email:
            email = f"{data['name'].lower().replace(' ', '')}{new_id.lower()}@rider.in"
            
        joined = datetime.datetime.now().strftime("%b %Y")
        photo = f"https://i.pravatar.cc/300?u={new_id}"
        
        cursor.execute("""
            INSERT INTO passengers 
            (id, name, mobile, email, password_hash, joined_date, photo)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (new_id, data['name'], mobile, email, hashed_pw, joined, photo))
        conn.commit()
        
        cursor.execute("SELECT * FROM passengers WHERE id = ?", (new_id,))
        pax = dict(cursor.fetchone())
        pax.pop('password_hash', None)
        
        return jsonify({"message": "Passenger registered", "passenger": pax}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 400
    finally:
        conn.close()

@auth.route('/api/request-otp', methods=['POST'])
def request_registration_otp():
    data = request.json
    mobile = data.get('mobile', '')
    if not mobile:
        return jsonify({"error": "Mobile number is required"}), 400
    
    otp = str(random.randint(100000, 999999))
    OTP_STORE[f"reg_{mobile}"] = {
        "otp": otp,
        "exp": datetime.datetime.now() + datetime.timedelta(minutes=5)
    }
    # Simulate SMS
    print(f"\n[SMS MOCK] => Registration OTP '{otp}' sent to: {mobile}\n", flush=True)
    return jsonify({"message": "OTP sent successfully"})

@auth.route('/api/verify-otp', methods=['POST'])
def verify_registration_otp():
    data = request.json
    mobile = data.get('mobile', '')
    provided_otp = data.get('otp', '')
    
    store_key = f"reg_{mobile}"
    if store_key not in OTP_STORE:
        return jsonify({"error": "Please request an OTP first"}), 400
        
    stored = OTP_STORE[store_key]
    if datetime.datetime.now() > stored["exp"]:
        del OTP_STORE[store_key]
        return jsonify({"error": "OTP has expired"}), 400
        
    if provided_otp != stored["otp"]:
        return jsonify({"error": "Invalid OTP"}), 401
    
    # Valid OTP
    del OTP_STORE[store_key]
    return jsonify({"success": True, "message": "Mobile number verified!"})

@auth.route('/api/login/request-otp/driver', methods=['POST'])
def request_otp_driver():
    data = request.json
    email = data.get('email', '').lower()
    
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM drivers WHERE email = ?", (email,))
    row = cursor.fetchone()
    conn.close()
    
    if row:
        driver = dict(row)
        # Verify password first (so they must know password to get OTP)
        # OR as user said "mobile otp system when we login": we can just skip password and use OTP
        # based on credentials. Let's just use email/mobile.
        otp = str(random.randint(100000, 999999))
        OTP_STORE[f"drv_{email}"] = {
            "otp": otp,
            "exp": datetime.datetime.now() + datetime.timedelta(minutes=5)
        }
        # Simulate SMS
        print(f"\n[SMS MOCK] => Sent OTP '{otp}' to Driver Mobile: {driver['mobile']}\n", flush=True)
        return jsonify({"message": "OTP sent successfully"})
        
    return jsonify({"error": "No driver found with this email"}), 404

@auth.route('/api/login/driver', methods=['POST'])
def login_driver():
    data = request.json
    email = data.get('email', '').lower()
    provided_otp = data.get('otp', '')
    
    # Check OTP
    store_key = f"drv_{email}"
    if store_key not in OTP_STORE:
        return jsonify({"error": "Please request an OTP first"}), 400
        
    stored = OTP_STORE[store_key]
    if datetime.datetime.now() > stored["exp"]:
        del OTP_STORE[store_key]
        return jsonify({"error": "OTP has expired"}), 400
        
    if provided_otp != stored["otp"]:
        return jsonify({"error": "Invalid OTP"}), 401
    
    # Valid OTP
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM drivers WHERE email = ?", (email,))
    row = cursor.fetchone()
    conn.close()
    
    if row:
        driver = dict(row)
        del OTP_STORE[store_key] # Consume OTP
        driver.pop('password_hash', None)
        token = generate_token(driver['id'], 'driver')
        return jsonify({"token": token, "user": driver})
            
    return jsonify({"error": "Driver not found"}), 404

@auth.route('/api/login/request-otp/passenger', methods=['POST'])
def request_otp_passenger():
    data = request.json
    cred = data.get('credential', '').lower()
    
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM passengers WHERE email = ? OR mobile = ?", (cred, cred))
    row = cursor.fetchone()
    conn.close()
    
    if row:
        pax = dict(row)
        otp = str(random.randint(100000, 999999))
        OTP_STORE[f"pax_{cred}"] = {
            "otp": otp,
            "exp": datetime.datetime.now() + datetime.timedelta(minutes=5)
        }
        # Simulate SMS
        print(f"\n[SMS MOCK] => Sent OTP '{otp}' to Passenger Mobile: {pax['mobile']}\n", flush=True)
        return jsonify({"message": "OTP sent successfully"})
        
    return jsonify({"error": "No passenger found with this credential"}), 404

@auth.route('/api/login/passenger', methods=['POST'])
def login_passenger():
    data = request.json
    cred = data.get('credential', '').lower()
    provided_otp = data.get('otp', '')
    
    # Check OTP
    store_key = f"pax_{cred}"
    if store_key not in OTP_STORE:
        return jsonify({"error": "Please request an OTP first"}), 400
        
    stored = OTP_STORE[store_key]
    if datetime.datetime.now() > stored["exp"]:
        del OTP_STORE[store_key]
        return jsonify({"error": "OTP has expired"}), 400
        
    if provided_otp != stored["otp"]:
        return jsonify({"error": "Invalid OTP"}), 401
    
    # Valid OTP
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM passengers WHERE email = ? OR mobile = ?", (cred, cred))
    row = cursor.fetchone()
    conn.close()
    
    if row:
        pax = dict(row)
        del OTP_STORE[store_key] # Consume OTP
        pax.pop('password_hash', None)
        token = generate_token(pax['id'], 'passenger')
        return jsonify({"token": token, "user": pax})
            
    return jsonify({"error": "Passenger not found"}), 404
