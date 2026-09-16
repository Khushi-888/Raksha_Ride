const express = require('express');
const http = require('http');
const { Server } = require('socket.io');
const { v4: uuidv4 } = require('uuid');
const cors = require('cors');
const multer = require('multer');
const bcrypt = require('bcrypt');
const jwt = require('jsonwebtoken');

const db = require('./db');
const { runAutoVerification } = require('./ai_engine');

const app = express();
const server = http.createServer(app);
const io = new Server(server, { cors: { origin: '*' } });

app.use(cors());
app.use(express.json());

const JWT_SECRET = 'antigravity-secret-key-2026';
const upload = multer({ dest: 'uploads/' });

// --- 2. DRIVER SIDE: MULTI-ROLE FLOW ---

// Onboarding: Register Owner vs Renter
app.post('/api/driver/register', async (req, res) => {
    const { full_name, email, password, mobile, rc_number } = req.body;
    let driver_id = uuidv4();
    let hashed_pw = await bcrypt.hash(password, 10);

    // Renter Check: "Database verify karega ki ye RC kisi Owner ke naam pe toh nahi."
    db.get('SELECT driver_id FROM drivers WHERE owner_id IS NULL AND full_name LIKE ?', [`%${rc_number}%`], (err, row) => {
        let role = 'OWNER';
        let owner_id = null;
        if (row) {
            role = 'RENTER';
            owner_id = row.driver_id;
            console.log(`[Hierarchy] Found RC Match -> Registering ${full_name} as RENTER under Owner ${owner_id}`);
        } else {
            console.log(`[Hierarchy] No RC Match -> Registering ${full_name} as primary OWNER.`);
        }

        db.run('INSERT INTO drivers (driver_id, full_name, email, password, mobile, role, owner_id) VALUES (?,?,?,?,?,?,?)',
            [driver_id, full_name, email, hashed_pw, mobile, role, owner_id],
            (err) => {
                if (err) return res.status(500).json({ error: "Email exists or DB Error" });

                // Conditional Onboarding Logic
                if (role === 'RENTER') {
                    // Send notification logic to Owner (mocked here)
                    res.json({ message: "Registered as RENTER. Access restricted. OTP Notification sent to Owner." });
                } else {
                    res.json({ message: "Registered as OWNER. Complete KYC to activate account", driver_id, status: 'PENDING' });
                }
            }
        );
    });
});

// Driver Login
app.post('/api/driver/login', (req, res) => {
    const { email, password } = req.body;
    db.get('SELECT * FROM drivers WHERE email = ?', [email], async (err, driver) => {
        if (!driver || !(await bcrypt.compare(password, driver.password))) {
            return res.status(401).json({ error: "Invalid Credentials" });
        }

        const token = jwt.sign({ id: driver.driver_id, role: driver.role }, JWT_SECRET, { expiresIn: '1d' });

        // "Status Check Blockage"
        if (driver.status !== 'VERIFIED') {
            return res.json({ token, warning: "Warning: Profile Pending/Rejected. Upload KYC documents.", status: driver.status });
        }
        res.json({ token, message: "Login successful", status: driver.status });
    });
});

// Run AI Verification Engine Endpoint
app.post('/api/driver/verify', upload.fields([{ name: 'aadhaar' }, { name: 'selfie' }]), async (req, res) => {
    const { driver_id } = req.body; // In reality, get from JWT
    const aadhaarPath = req.files['aadhaar'][0].path;
    const selfiePath = req.files['selfie'][0].path;

    const result = await runAutoVerification(driver_id, aadhaarPath, selfiePath);
    res.json({ message: "AI Verification complete", result });
});

// --- 3. USER SIDE: MINIMALIST "SCAN & GO" ---

app.post('/api/user/register', async (req, res) => {
    const user_id = uuidv4();
    const hashed = await bcrypt.hash(req.body.password, 10);
    db.run("INSERT INTO users (user_id, email, password) VALUES (?,?,?)", [user_id, req.body.email, hashed], (err) => {
        if (err) return res.status(400).json({ error: "Email exists" });
        res.json({ message: "User created" });
    });
});

// The Scanner / Create Ride Bridge
app.post('/api/ride/start', (req, res) => {
    const { driver_id, user_id, current_lat_long } = req.body;
    const ride_id = uuidv4();
    const share_token = uuidv4().substring(0, 8); // Short share URL

    db.run("INSERT INTO rides (ride_id, driver_id, user_id, current_lat_long, share_token) VALUES (?,?,?,?,?)",
        [ride_id, driver_id, user_id, current_lat_long, share_token],
        (err) => {
            // Dispatch event to socket rooms
            io.to(ride_id).emit('ride_started', { ride_id, share_token, lat_long: current_lat_long });
            res.json({ message: "Ride started securely", ride_id, share_token_url: `http://localhost:3000/track/${share_token}` });
        }
    );
});

// Real-Time Safety & Hardware Bridge (WebSockets)
io.on('connection', (socket) => {
    console.log('[Socket] Client Connected: ', socket.id);

    socket.on('join_ride', (ride_id) => {
        socket.join(ride_id);
        console.log(`[Socket] Joined ride channel: ${ride_id}`);
    });

    socket.on('update_location', (data) => {
        // Broadcasts driver's GPS map point continually to frontend passenger map!
        io.to(data.ride_id).emit('location_update', data.lat_long);

        // Asynchronous processing: update DB background
        db.run('UPDATE rides SET current_lat_long = ? WHERE ride_id = ?', [data.lat_long, data.ride_id]);
    });
});

const PORT = process.env.PORT || 8001;
server.listen(PORT, () => {
    console.log(`======================================`);
    console.log(`🚀 Antigravity Core API Server Running`);
    console.log(`======================================`);
    console.log(`Port: ${PORT}`);
    console.log(`Runtime: Node.js (Async + WebSockets)`);
    console.log(`Features Active: Face-Match, Hierarchy, OCR`);
});
