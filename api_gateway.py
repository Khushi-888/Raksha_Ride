import os
import sqlite3
import math
import datetime
from functools import wraps
from flask import Flask, request, jsonify
from flask_cors import CORS
import jwt

# App and extensions
app = Flask(__name__, static_folder='.', static_url_path='')
CORS(app)
app.config['SECRET_KEY'] = 'super-secret-raksha-key'
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['DATABASE_PATH'] = os.path.join(basedir, 'database.db')

# ── Initialization ────────────────────────────────────────────────────────
def init_db():
    db_path = app.config['DATABASE_PATH']
    schema_path = os.path.join(basedir, 'schema.sql')
    
    conn = sqlite3.connect(db_path)
    with open(schema_path, 'r') as f:
        conn.executescript(f.read())
        
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM drivers")
    if cursor.fetchone()[0] == 0:
        # Avoid direct circular imports by importing bcrypt just for seeding
        from flask_bcrypt import Bcrypt
        bcrypt = Bcrypt()
        from auth_backend import bcrypt as app_bcrypt
        
        # Seed driver
        pw = app_bcrypt.generate_password_hash("pass123").decode('utf-8')
        cursor.execute("""
            INSERT INTO drivers (id, name, age, mobile, email, vehicle_number, rc_number, password_hash, photo)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, ('DRV-1001', 'Kavita Choudhary', 32, '9876543211', 'kavita@riksha.in', 'MH-20-AW-8254', 'RC12345', pw, 'https://i.pravatar.cc/300?u=DRV-1001'))
        
        # Seed passenger
        cursor.execute("""
            INSERT INTO passengers (id, name, mobile, email, password_hash, photo)
            VALUES (?, ?, ?, ?, ?, ?)
        """, ('USR-6001', 'Amit Sharma', '9876543201', 'amit@rider.in', pw, 'https://i.pravatar.cc/300?u=USR-6001'))
        print("Database initialized & seeded from schema.sql")
    
    conn.commit()
    conn.close()

# ── Import Auth Blueprint ─────────────────────────────────────────────────
from auth_backend import auth, bcrypt
bcrypt.init_app(app)
app.register_blueprint(auth)

# ── Security Decorator ────────────────────────────────────────────────────
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        auth_header = request.headers.get('Authorization')
        if auth_header and auth_header.startswith('Bearer '):
            token = auth_header.split(" ")[1]
        
        if not token:
            return jsonify({'error': 'Token is missing!'}), 401
        
        try:
            data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=["HS256"])
            
            conn = sqlite3.connect(app.config['DATABASE_PATH'])
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            current_user = None
            if data.get('role') == 'driver':
                cursor.execute("SELECT * FROM drivers WHERE id = ?", (data['id'],))
            elif data.get('role') == 'passenger':
                cursor.execute("SELECT * FROM passengers WHERE id = ?", (data['id'],))
                
            row = cursor.fetchone()
            conn.close()
            
            if not row:
                return jsonify({'error': 'User not found!'}), 401
            
            user_dict = dict(row)
            user_dict.pop('password_hash', None)
            
            request.current_user = user_dict
            request.user_role = data.get('role')
        except jwt.ExpiredSignatureError:
            return jsonify({'error': 'Token has expired!'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'error': 'Token is invalid!'}), 401
        
        return f(*args, **kwargs)
    return decorated

# ── GPS Engine ────────────────────────────────────────────────────────────

SAFE_PATH = [
    [18.5204, 73.8567], [18.5215, 73.8580], [18.5228, 73.8595],
    [18.5240, 73.8612], [18.5252, 73.8628], [18.5265, 73.8644]
]

def haversine_distance(lat1, lon1, lat2, lon2):
    R = 6371000
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi       = math.radians(lat2 - lat1)
    dlambda    = math.radians(lon2 - lon1)
    a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2) * math.sin(dlambda/2)**2
    return 2 * R * math.atan2(math.sqrt(a), math.sqrt(1 - a))

def distance_to_path(lat, lng):
    return min(haversine_distance(lat, lng, p_lat, p_lng) for p_lat, p_lng in SAFE_PATH)

@app.route('/api/location/update', methods=['POST'])
@token_required
def update_location():
    """Connects the map to real GPS data & handles SOS logic."""
    if request.user_role != 'driver':
        return jsonify({"error": "Only drivers can update location"}), 403
        
    data = request.json
    lat, lng = data.get('lat'), data.get('lng')
    if lat is None or lng is None:
        return jsonify({"error": "Missing lat/lng"}), 400
        
    dist = distance_to_path(lat, lng)
    sos_triggered = dist > 50.0
    
    if sos_triggered:
        conn = sqlite3.connect(app.config['DATABASE_PATH'])
        cursor = conn.cursor()
        
        # Check rate limit (1 log per min)
        cursor.execute("""
            SELECT timestamp FROM alerts 
            WHERE driver_id = ? ORDER BY timestamp DESC LIMIT 1
        """, (request.current_user['id'],))
        row = cursor.fetchone()
        
        log_it = True
        if row:
            last = datetime.datetime.strptime(row[0], "%Y-%m-%d %H:%M:%S")
            if (datetime.datetime.utcnow() - last).total_seconds() < 60:
                log_it = False
                
        if log_it:
            cursor.execute("""
                INSERT INTO alerts (driver_id, alert_type, lat, lng)
                VALUES (?, ?, ?, ?)
            """, (request.current_user['id'], 'Route Deviation > 50m', lat, lng))
            conn.commit()
            print(f"🚨 SOS LOGGED for {request.current_user['id']} at lat:{lat}, lng:{lng}. Deviation: {dist:.1f}m")
        conn.close()

    integrity = max(0, min(100, 100 - ((dist - 10) / 2))) if dist > 10 else 100
    
    return jsonify({
        "status": "recorded",
        "sos_triggered": sos_triggered,
        "deviation_meters": round(dist, 1),
        "integrity": round(integrity),
        "nearest_path_node": SAFE_PATH[0]
    })

# ── General Routes ────────────────────────────────────────────────────────

@app.route('/api/me', methods=['GET'])
@token_required
def get_me():
    return jsonify(request.current_user)

@app.route('/api/drivers', methods=['GET'])
def get_all_drivers():
    conn = sqlite3.connect(app.config['DATABASE_PATH'])
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM drivers")
    drivers = [dict(row) for row in cursor.fetchall()]
    conn.close()
    
    for d in drivers:
        d.pop('password_hash', None)
    return jsonify(drivers)

@app.route('/')
def index():
    return app.send_static_file('index.html')

if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=8000, debug=True)
