import sqlite3
import os

def init_db():
    conn = sqlite3.connect('raksharide_final.db')
    c = conn.cursor()
    
    # Drivers Table
    c.execute('''CREATE TABLE IF NOT EXISTS drivers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        phone TEXT NOT NULL,
        password TEXT NOT NULL,
        driver_type TEXT NOT NULL, -- 'owner' or 'renter'
        status TEXT DEFAULT 'pending', -- 'pending', 'pending_approval', 'approved', 'verified'
        owner_email TEXT, -- for renters
        profile_image TEXT,
        qr_code TEXT,
        vehicle_details TEXT
    )''')
    
    # Driver Documents Table
    c.execute('''CREATE TABLE IF NOT EXISTS driver_documents (
        driver_id INTEGER PRIMARY KEY,
        aadhar TEXT,
        license TEXT,
        rc TEXT,
        FOREIGN KEY (driver_id) REFERENCES drivers (id)
    )''')
    
    # Passengers Table
    c.execute('''CREATE TABLE IF NOT EXISTS passengers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        mobile TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL
    )''')
    
    # OTP Verification Table
    c.execute('''CREATE TABLE IF NOT EXISTS otp_verification (
        email TEXT PRIMARY KEY,
        otp TEXT NOT NULL,
        expiry_time DATETIME NOT NULL
    )''')
    
    # Rides Table
    c.execute('''CREATE TABLE IF NOT EXISTS rides (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        passenger_id INTEGER,
        driver_id INTEGER,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
        status TEXT DEFAULT 'completed',
        FOREIGN KEY (passenger_id) REFERENCES passengers (id),
        FOREIGN KEY (driver_id) REFERENCES drivers (id)
    )''')
    
    # Ratings Table
    c.execute('''CREATE TABLE IF NOT EXISTS ratings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        ride_id INTEGER,
        passenger_id INTEGER,
        driver_id INTEGER,
        rating INTEGER,
        comment TEXT,
        FOREIGN KEY (ride_id) REFERENCES rides (id),
        FOREIGN KEY (passenger_id) REFERENCES passengers (id),
        FOREIGN KEY (driver_id) REFERENCES drivers (id)
    )''')
    
    conn.commit()
    conn.close()
    
    # Create upload directories
    base_dir = 'static/uploads'
    subdirs = ['documents', 'profile', 'qr']
    for subdir in subdirs:
        path = os.path.join(base_dir, subdir)
        if not os.path.exists(path):
            os.makedirs(path)
            print(f"Created directory: {path}")

if __name__ == '__main__':
    init_db()
    print("Database and directories initialized successfully.")
