-- Production Schema for RakshaRide

-- Verified Drivers Table
CREATE TABLE IF NOT EXISTS verified_drivers (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    age INTEGER,
    mobile TEXT UNIQUE NOT NULL,
    email TEXT UNIQUE NOT NULL,
    vehicle_number TEXT UNIQUE NOT NULL,
    rc_number TEXT UNIQUE NOT NULL,
    pick_location TEXT,
    password_hash TEXT NOT NULL,
    rating REAL DEFAULT 4.5,
    total_rides INTEGER DEFAULT 0,
    balance REAL DEFAULT 0.0,
    photo TEXT,
    vehicle_type TEXT DEFAULT 'Electric Eco-Rickshaw',
    verified BOOLEAN DEFAULT 1,
    last_lat REAL,
    last_lng REAL,
    is_active BOOLEAN DEFAULT 1,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Passengers Table
CREATE TABLE IF NOT EXISTS passengers (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    mobile TEXT UNIQUE NOT NULL,
    email TEXT UNIQUE,
    password_hash TEXT NOT NULL,
    balance REAL DEFAULT 0.0,
    trips INTEGER DEFAULT 0,
    photo TEXT,
    joined_date TEXT,
    is_active BOOLEAN DEFAULT 1,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Alerts Table
CREATE TABLE IF NOT EXISTS alerts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    driver_id TEXT NOT NULL,
    alert_type TEXT NOT NULL,
    lat REAL,
    lng REAL,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(driver_id) REFERENCES verified_drivers(id)
);

-- Rides Table
CREATE TABLE IF NOT EXISTS rides (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    driver_id TEXT NOT NULL,
    passenger_id TEXT NOT NULL,
    start_lat REAL,
    start_lng REAL,
    end_lat REAL,
    end_lng REAL,
    fare REAL,
    status TEXT DEFAULT 'completed',
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(driver_id) REFERENCES verified_drivers(id),
    FOREIGN KEY(passenger_id) REFERENCES passengers(id)
);

-- Pending Verification Table
CREATE TABLE IF NOT EXISTS pending_verification (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    credential TEXT NOT NULL,
    role TEXT NOT NULL,
    otp TEXT NOT NULL,
    attempts INTEGER DEFAULT 0,
    expires_at DATETIME NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Blocked IPs Table
CREATE TABLE IF NOT EXISTS blocked_ips (
    ip_address TEXT PRIMARY KEY,
    blocked_until DATETIME NOT NULL
);
