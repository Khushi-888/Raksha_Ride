// ============================================================
//  RakshaRide — Deterministic Mock Database
//  Drivers  : 50  (fields: id, name, age, mobile, email, vehicleNumber, pick, rcNo, password)
//  Passengers: 200 (fields: id, name, mobile, email, password)
//  Driver login  → email (attached to RC account) + password
//  Passenger login → email OR mobile + password
// ============================================================

// ── Seeded PRNG (Mulberry32) ─────────────────────────────────
function _seededRand(seed) {
    let t = seed >>> 0;
    return function () {
        t += 0x6D2B79F5;
        let r = Math.imul(t ^ (t >>> 15), t | 1);
        r ^= r + Math.imul(r ^ (r >>> 7), r | 61);
        return ((r ^ (r >>> 14)) >>> 0) / 4294967296;
    };
}

const _R = _seededRand(42);
function _ri(arr) { return arr[Math.floor(_R() * arr.length)]; }
function _rn(lo, hi) { return lo + Math.floor(_R() * (hi - lo + 1)); }
function _pad(n, w) { return String(n).padStart(w, '0'); }

// ── Name pools ───────────────────────────────────────────────
const _FN = ['Rajesh', 'Kavita', 'Suresh', 'Anita', 'Vikram', 'Priya', 'Amit', 'Neha',
    'Pooja', 'Rahul', 'Gita', 'Sunil', 'Ramesh', 'Deepak', 'Pankaj', 'Ritu',
    'Manish', 'Asha', 'Rohit', 'Meera', 'Arjun', 'Sneha', 'Kiran', 'Vivek',
    'Divya', 'Sanjay', 'Rekha', 'Nitin', 'Swati', 'Arun'];
const _LN = ['Kumar', 'Sharma', 'Verma', 'Choudhary', 'Singh', 'Nair', 'Mishra', 'Joshi',
    'Iyer', 'Thakur', 'Patel', 'Das', 'Gupta', 'Yadav', 'Khan', 'Rao', 'Dutta',
    'Bose', 'Kohli', 'Kapoor', 'Tiwari', 'Reddy', 'Pillai', 'Shah', 'Mehta'];
const _PICKS = ['Andheri East', 'Pune Station', 'Market Road', 'City Center',
    'Central Park', 'Old Bus Stand', 'MG Road', 'Linking Road',
    'Bandra West', 'Dadar TT', 'Kurla Station', 'Thane West',
    'Vile Parle', 'Mulund', 'Borivali'];
const _STATES = ['MH', 'DL', 'KA', 'TN', 'GJ', 'UP', 'RJ', 'MP'];
const _MONTHS = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];

// ── Generate drivers ─────────────────────────────────────────
const drivers = [];
for (let i = 0; i < 50; i++) {
    const seq = 1001 + i;
    const fn = _FN[i % _FN.length];
    const ln = _LN[(i * 3) % _LN.length];
    const name = `${fn} ${ln}`;
    const age = _rn(22, 58);
    const mobile = '9' + _pad(_rn(100000000, 999999999), 9);
    const state = _ri(_STATES);
    const dist = _pad(_rn(10, 99), 2);
    const alpha = String.fromCharCode(65 + _rn(0, 25)) + String.fromCharCode(65 + _rn(0, 25));
    const num4 = _pad(_rn(1000, 9999), 4);
    const vehicleNumber = `${state}-${dist}-${alpha}-${num4}`;
    const rcNo = `RC${_pad(seq, 6)}`;
    const pick = _ri(_PICKS);
    // email is tied to the RC account — this is what drivers use to login
    const email = `${fn.toLowerCase()}.${ln.toLowerCase()}${seq}@riksha.in`;
    const password = rcNo.slice(-4); // last 4 digits of RC number

    drivers.push({
        id: `DRV-${seq}`,
        name, age, mobile, email, vehicleNumber, pick, rcNo, password,
        // extra display fields
        rating: Math.round((_R() * 1.5 + 3.5) * 10) / 10,
        totalRides: _rn(50, 5000),
        experience: `${_rn(1, 15)} Years`,
        lastInspection: `${_pad(_rn(1, 28), 2)} ${_ri(_MONTHS)} 2024`,
        photo: `https://i.pravatar.cc/300?u=DRV-${seq}`,
        verified: true,
        vehicleType: _ri(['Electric Eco-Rickshaw', 'Standard CNG Rickshaw', 'LPG Passenger Rickshaw', 'Premium Solar Rickshaw'])
    });
}

// ── Generate passengers ──────────────────────────────────────
const passengers = [];
for (let j = 0; j < 200; j++) {
    const seq = 5001 + j;
    const fn = _FN[(j * 2) % _FN.length];
    const ln = _LN[(j * 5) % _LN.length];
    const name = `${fn} ${ln}`;
    const mobile = '8' + _pad(_rn(100000000, 999999999), 9);
    const email = `${fn.toLowerCase()}${seq}@rider.in`;
    const password = `pass${seq}`;

    passengers.push({
        id: `USR-${seq}`,
        name, mobile, email, password,
        // extra display fields
        balance: _rn(0, 1500),
        joinedDate: `${_ri(_MONTHS)} 2024`,
        photo: `https://i.pravatar.cc/300?u=USR-${seq}`,
        trips: _rn(0, 120),
        verified: true
    });
}

// ── Main database object ─────────────────────────────────────
const RIKSHA_DB = {
    drivers,
    passengers,
    payments: [],
    registeredPassengers: [] // stores new sign-ups at runtime
};

// Node.js compatibility
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { RIKSHA_DB };
}
