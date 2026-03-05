-- Defines the actual database tables (Drivers, Passengers, Rides/Alerts).

CREATE TABLE IF NOT EXISTS drivers (
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
    verified BOOLEAN DEFAULT 1
);

CREATE TABLE IF NOT EXISTS passengers (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    mobile TEXT UNIQUE NOT NULL,
    email TEXT UNIQUE,
    password_hash TEXT NOT NULL,
    balance REAL DEFAULT 0.0,
    trips INTEGER DEFAULT 0,
    photo TEXT,
    joined_date TEXT
);

CREATE TABLE IF NOT EXISTS alerts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    driver_id TEXT NOT NULL,
    alert_type TEXT NOT NULL,
    lat REAL,
    lng REAL,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(driver_id) REFERENCES drivers(id)
);

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
    FOREIGN KEY(driver_id) REFERENCES drivers(id),
    FOREIGN KEY(passenger_id) REFERENCES passengers(id)
);
