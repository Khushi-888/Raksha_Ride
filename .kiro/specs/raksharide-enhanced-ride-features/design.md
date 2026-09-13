# Design Document — RakshaRide Enhanced Ride Features

## Overview

This document describes the technical design to fix and complete the RakshaRide ride-sharing platform. The system uses a Flask (Python) backend with SQLite, Leaflet.js maps, and vanilla JS frontends for driver and passenger dashboards.

The four critical broken flows are:
1. Profile data not loading (blank fields)
2. Nearby drivers showing stale/no locations
3. Driver QR scan → ride connection broken
4. Ride start/end lifecycle not completing correctly

---

## Architecture

```
Browser (Passenger/Driver Dashboard)
    │
    ├── authFetch() — JWT + session dual auth
    │
    ├── /api/driver_profile          ← Fix: add address, gender fields
    ├── /api/passenger_profile       ← Fix: add unique_id field
    ├── /api/get_nearby_drivers      ← Fix: join live_locations table
    ├── /api/scan_driver_qr          ← Fix: allow pending/approved status
    ├── /api/start_ride              ← Fix: pass GPS coords from frontend
    ├── /api/update_gps              ← Fix: upsert live_locations correctly
    ├── /api/complete_ride           ← Fix: update driver total_rides
    └── /api/get_active_ride         ← Fix: return correct fields
    
Flask Backend (app_enhanced.py)
    │
    └── SQLite (database_enhanced.db)
            ├── drivers              — profile, availability, static GPS
            ├── passengers           — profile, emergency contact
            ├── rides                — ride lifecycle
            ├── live_locations       — real-time GPS (upsert per user)
            └── payments             — payment confirmation
```

---

## Component Designs

### 1. Profile Loading Fix

**Problem:** `/api/driver_profile` SELECT omits `address` and `gender` columns. Frontend JS maps fields but `address` textarea stays blank.

**Fix — Backend (`app_enhanced.py`):**
- Add `address`, `gender` to the SELECT in `api_driver_profile()`
- Add `address` to the `cols` list
- Add `address` to `api_update_driver_profile()` UPDATE statement

**Fix — Frontend (`dashboard_driver_new.html`):**
- In `loadDriverData()`, map `drv.address` → `document.getElementById('editAddress').value`
- In `saveProfile()`, include `address` in the POST body

**Passenger profile:** Add `unique_id` generation (`PAX-` + zero-padded id) to the profile display.

---

### 2. Nearby Drivers — Real-Time GPS

**Problem:** `/api/get_nearby_drivers` queries `drivers.latitude` / `drivers.longitude` which are only updated on registration. Real-time positions are in `live_locations` table.

**Fix — Backend:**
```sql
SELECT d.id, d.name, d.vehicle_type, d.vehicle_number, d.rating, 
       d.total_rides, d.gender, d.unique_id,
       COALESCE(ll.latitude, d.latitude) AS latitude,
       COALESCE(ll.longitude, d.longitude) AS longitude,
       ll.updated_at
FROM drivers d
LEFT JOIN live_locations ll ON ll.user_id = d.id AND ll.role = 'driver'
WHERE d.is_available = 1
  AND (ll.updated_at IS NULL OR ll.updated_at > datetime('now', '-10 minutes'))
```

**Fix — Frontend:**
- Accept `lat` / `lng` query params from passenger's current GPS
- Calculate Haversine distance server-side and return `distance_km` per driver
- Filter: only show drivers within 10 km (configurable)
- Sort by distance ascending

**Haversine helper (already exists as `_haversine_m`)** — reuse it.

---

### 3. QR Scan → Driver Connection Flow

**Problem A:** QR has 15-minute expiry (`QR_VALIDITY_MINUTES = 15` in `security_enhancements.py`). Drivers generate QR at login; by the time passenger scans it's expired.

**Fix:** Increase `QR_VALIDITY_MINUTES` to `1440` (24 hours). QR is regenerated on each driver login anyway.

**Problem B:** `scan_driver_qr` checks `vstatus not in ['approved', 'verified']` — but new drivers have `verification_status = 'pending'`. This blocks all unverified drivers.

**Fix:** Change check to allow `pending` drivers with a warning, or change the default `verification_status` to `'approved'` for self-registered drivers (since admin approval is optional in this system).

**Problem C:** Manual driver ID lookup (`lookupDriver()`) calls `/api/get_driver_profile_for_passenger?driver_id=X` but the endpoint expects `unique_id` param, not numeric `id`.

**Fix:** Update `get_driver_profile_for_passenger` to accept both `driver_id` (numeric) and `unique_id` (string like `DRV-XXXXX`).

**QR Scanner Library:** The `dashboard_passenger_new.html` uses a custom scanner but doesn't load `jsQR`. Add CDN script tag for `jsQR` and wire the `scannerVideo` → canvas → `jsQR.decode()` loop.

---

### 4. Ride Start / End Lifecycle

**Ride Start Flow:**
```
Passenger scans QR → confirmDriver() → selectedDriver set
→ showSection('tracking') → startRideFromRoute()
→ POST /api/start_ride { driver_id, pickup_location, dropoff_location, latitude, longitude }
→ ride_id stored in activeRideId
→ GPS polling starts (every 5s POST /api/update_gps)
→ Driver dashboard polls GET /api/get_active_ride (every 5s)
→ Driver sees "Passenger Connected" banner
```

**Problem:** `startRideFromRoute()` in passenger dashboard doesn't send `latitude`/`longitude`. The proximity check in `start_ride()` then can't compute distance.

**Fix:** Capture `navigator.geolocation.getCurrentPosition()` before calling `startRideFromRoute()` and include coords in the POST body.

**Ride End Flow:**
```
Passenger clicks "End Ride"
→ POST /api/complete_ride { ride_id, distance_km, route_coordinates }
→ Backend: calculates fare, updates ride status='completed'
→ Backend: updates driver is_available=1, total_rides+1, total_earned+fare
→ Backend: updates passenger total_rides+1, total_spent+fare
→ Returns { fare, payment_qr, upi_id }
→ Frontend shows payment section with QR
→ Passenger clicks "Payment Done"
→ POST /api/confirm_payment { ride_id, fare }
→ Driver sees payment notification banner
→ Driver clicks "Confirm Received"
→ POST /api/driver_confirm_payment { ride_id }
→ Ride fully complete
```

**Problem:** `complete_ride()` doesn't update `driver.total_rides`. Fix: add `UPDATE drivers SET total_rides=total_rides+1` in `complete_ride()`.

---

### 5. GPS Location Update

**Current endpoint:** `/api/update_driver_location` only updates `drivers.latitude/longitude` (static columns), not `live_locations`.

**Fix:** Create unified `/api/update_gps` endpoint that:
1. Upserts `live_locations` (primary real-time store)
2. Also updates `drivers.latitude/longitude` as fallback

```python
INSERT INTO live_locations (user_id, role, latitude, longitude, accuracy, speed, updated_at)
VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
ON CONFLICT(user_id) DO UPDATE SET
  latitude=excluded.latitude, longitude=excluded.longitude,
  accuracy=excluded.accuracy, speed=excluded.speed,
  updated_at=CURRENT_TIMESTAMP
```

---

### 6. Driver Dashboard — Active Ride Polling

**Problem:** Driver has no way to know a passenger started a ride with them. The `activeRideBanner` exists in HTML but is never shown because there's no polling.

**Fix:** In `loadDriverData()`, after loading profile, call `checkActiveRide()` which polls `/api/get_active_ride` every 5 seconds. When a ride is found:
- Show `activeRideBanner` with passenger name
- Show `passengerBadge` on the map
- Plot passenger marker on `driverMap`

---

### 7. Database Schema — Missing Columns

Run migrations on startup (already handled by `init_db()` migration list). Add:
- `rides.route_coordinates` — already exists
- `rides.sos_triggered` — add to migration list
- `drivers.address` — add to migration list  
- `passengers.unique_id` — add to migration list

---

## Data Flow Diagrams

### QR Scan → Ride Start
```
[Passenger] → startScanner() → camera → jsQR.decode()
    → POST /api/scan_driver_qr { qr_data }
    → verify HMAC + expiry (24h window)
    → GET driver from DB
    → return driver details
    → showDriverDetails() → confirmDriver()
    → selectedDriver = { id, name, vehicle, ... }
    → showSection('tracking')
    → startRideFromRoute()
    → getCurrentPosition() → POST /api/start_ride
    → activeRideId = ride.id
    → startGPSTracking() → POST /api/update_gps every 5s
```

### Driver Sees Passenger
```
[Driver] → loadDriverData() → checkActiveRide() every 5s
    → GET /api/get_active_ride
    → if ride found: showActiveRideBanner()
    → initDriverMap() → plotPassengerMarker()
    → GET /api/get_other_location every 5s → update marker
```

---

## API Contract Summary

| Endpoint | Method | Auth | Fix Needed |
|---|---|---|---|
| `/api/driver_profile` | GET | Driver | Add address, gender to SELECT |
| `/api/update_driver_profile` | POST | Driver | Add address to UPDATE |
| `/api/passenger_profile` | GET | Passenger | Add unique_id to response |
| `/api/get_nearby_drivers` | GET | None | Join live_locations, add distance calc |
| `/api/scan_driver_qr` | POST | Passenger | Allow pending status, 24h QR |
| `/api/get_driver_profile_for_passenger` | GET | Passenger | Accept numeric driver_id |
| `/api/start_ride` | POST | Passenger | Receive lat/lng from frontend |
| `/api/update_gps` | POST | Any | New unified GPS upsert endpoint |
| `/api/complete_ride` | POST | Passenger | Add driver total_rides update |
| `/api/get_active_ride` | GET | Any | Already works — verify fields |

---

## Security Considerations

- All ride APIs use `_require_driver()` / `_require_passenger()` dual-auth (JWT + session)
- QR HMAC signature verified on every scan
- SQL uses parameterized queries throughout
- GPS coordinates validated as floats before storage
- No PII exposed in nearby drivers list (no phone/email)
