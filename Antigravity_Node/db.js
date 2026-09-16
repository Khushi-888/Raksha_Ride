const sqlite3 = require('sqlite3').verbose();
const path = require('path');

const dbPath = path.resolve(__dirname, 'antigravity.db');
const db = new sqlite3.Database(dbPath, (err) => {
    if (err) console.error("Database connection error:", err);
    else console.log("Connected to Antigravity SQLite DB.");
});

// Create tables as per the Antigravity prompt
db.serialize(() => {
    // A. Users Table (Rider/Passenger)
    db.run(`CREATE TABLE IF NOT EXISTS users (
        user_id TEXT PRIMARY KEY,
        email TEXT UNIQUE,
        password TEXT,
        is_verified BOOLEAN DEFAULT 0
    )`);

    // B. Drivers Table (The Profile)
    db.run(`CREATE TABLE IF NOT EXISTS drivers (
        driver_id TEXT PRIMARY KEY,
        full_name TEXT,
        email TEXT UNIQUE,
        password TEXT,
        mobile TEXT,
        role TEXT CHECK( role IN ('OWNER','RENTER') ) DEFAULT 'OWNER',
        owner_id TEXT,
        status TEXT CHECK( status IN ('PENDING','VERIFIED','FLAGGED','REJECTED') ) DEFAULT 'PENDING',
        qr_code_url TEXT,
        ai_face_score REAL DEFAULT 0,
        FOREIGN KEY(owner_id) REFERENCES drivers(driver_id)
    )`);

    // C. Documents Table (Secure Access)
    db.run(`CREATE TABLE IF NOT EXISTS documents (
        doc_id TEXT PRIMARY KEY,
        linked_id TEXT,
        doc_type TEXT CHECK( doc_type IN ('AADHAAR', 'RC', 'LICENSE', 'LIVE_PHOTO') ),
        file_path TEXT,
        uploaded_by TEXT,
        FOREIGN KEY(linked_id) REFERENCES drivers(driver_id),
        FOREIGN KEY(uploaded_by) REFERENCES drivers(driver_id)
    )`);

    // D. Rides Table (Live Tracking)
    db.run(`CREATE TABLE IF NOT EXISTS rides (
        ride_id TEXT PRIMARY KEY,
        driver_id TEXT,
        user_id TEXT,
        current_lat_long TEXT,
        share_token TEXT UNIQUE,
        status TEXT DEFAULT 'ACTIVE',
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(driver_id) REFERENCES drivers(driver_id),
        FOREIGN KEY(user_id) REFERENCES users(user_id)
    )`);
});

module.exports = db;
