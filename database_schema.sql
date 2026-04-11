-- RakshaRide Official Database Schema
-- Last Updated: 2026-03-07

-- Passengers Table
CREATE TABLE IF NOT EXISTS passengers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    phone TEXT NOT NULL UNIQUE,
    email TEXT NOT NULL UNIQUE,
    password TEXT NOT NULL,
    profile_image TEXT,
    total_rides INTEGER DEFAULT 0,
    total_spent REAL DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Drivers Table
CREATE TABLE IF NOT EXISTS drivers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    age INTEGER NOT NULL,
    mobile TEXT NOT NULL UNIQUE,
    email TEXT NOT NULL UNIQUE,
    vehicle_number TEXT NOT NULL,
    vehicle_type TEXT DEFAULT 'Car',
    rc_number TEXT NOT NULL,
    password TEXT NOT NULL,
    qr_code TEXT,
    profile_image TEXT,
    upi_id TEXT,
    latitude REAL,
    longitude REAL,
    is_available BOOLEAN DEFAULT 1,
    rating REAL DEFAULT 5.0,
    total_rides INTEGER DEFAULT 0,
    total_earned REAL DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- OTP Verification Table
CREATE TABLE IF NOT EXISTS otp_verification (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT NOT NULL,
    otp TEXT NOT NULL,
    expiry_time TIMESTAMP NOT NULL,
    attempts INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Rides Table
CREATE TABLE IF NOT EXISTS rides (
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
);

-- Payments Table
CREATE TABLE IF NOT EXISTS payments (
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
);
