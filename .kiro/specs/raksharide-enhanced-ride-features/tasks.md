# Tasks

## Task 1: Fix Profile Loading — Driver and Passenger Dashboards
Fix the "Loading..." blank profile fields by correcting backend SELECT queries and frontend field mapping.

### Sub-tasks
- [ ] 1.1 In `app_enhanced.py` `api_driver_profile()`: add `address`, `gender` to the SELECT query and to the `cols` list
- [ ] 1.2 In `app_enhanced.py` `api_update_driver_profile()`: add `address` to the UPDATE statement
- [ ] 1.3 In `templates/dashboard_driver_new.html` `loadDriverData()`: map `drv.address` → `editAddress` textarea value
- [ ] 1.4 In `templates/dashboard_driver_new.html` `saveProfile()`: include `address` in the POST body JSON
- [ ] 1.5 In `app_enhanced.py` `api_passenger_profile()`: add `unique_id` field to response (generate as `PAX-` + zero-padded id if not stored)
- [ ] 1.6 In `templates/dashboard_passenger_new.html` `loadPassengerData()`: ensure all profile fields (name, phone, email, emergency contacts) are correctly mapped from API response

## Task 2: Fix Nearby Drivers — Real-Time GPS
Replace the stale `drivers.latitude/longitude` query with a join on `live_locations` for accurate real-time positions.

### Sub-tasks
- [ ] 2.1 In `app_enhanced.py` `get_nearby_drivers()`: rewrite the SQL query to LEFT JOIN `live_locations` table using `COALESCE(ll.latitude, d.latitude)` and `COALESCE(ll.longitude, d.longitude)`
- [ ] 2.2 Add server-side Haversine distance calculation: accept `lat` and `lng` query params from passenger, compute `distance_km` for each driver, filter to within 10 km, sort by distance ascending
- [ ] 2.3 Add `gender`, `unique_id`, `distance_km`, `eta_minutes` (distance/30*60) to each driver object in the response
- [ ] 2.4 Filter out drivers whose `live_locations.updated_at` is older than 10 minutes (stale GPS)
- [ ] 2.5 In `templates/dashboard_passenger_new.html` `refreshNearby()`: pass current passenger GPS coords as `?lat=X&lng=Y` query params when calling `/api/get_nearby_drivers`
- [ ] 2.6 In the nearby drivers list rendering: display `distance_km` and `eta_minutes` per driver card

## Task 3: Fix QR Code Scan and Driver Verification Flow
Fix the QR expiry issue, verification status check, and jsQR library integration.

### Sub-tasks
- [ ] 3.1 In `security_enhancements.py`: change `QR_VALIDITY_MINUTES` from `15` to `1440` (24 hours)
- [ ] 3.2 In `app_enhanced.py` `scan_driver_qr()`: change the verification status check to allow `pending`, `approved`, and `verified` statuses (remove the hard block on pending drivers)
- [ ] 3.3 In `app_enhanced.py` `get_driver_profile_for_passenger()`: update to accept both `unique_id` (string like `DRV-XXXXX`) and numeric `driver_id` query params
- [ ] 3.4 In `templates/dashboard_passenger_new.html`: add `<script src="https://cdn.jsdelivr.net/npm/jsqr@1.4.0/dist/jsQR.min.js"></script>` in the `<head>`
- [ ] 3.5 In `templates/dashboard_passenger_new.html` `startScanner()`: implement the jsQR decode loop — draw video frame to hidden canvas, call `jsQR(imageData, width, height)`, on detection call `handleQRResult(data)`
- [ ] 3.6 In `templates/dashboard_passenger_new.html`: implement `handleQRResult(qrData)` — POST to `/api/scan_driver_qr`, on success call `showDriverDetails(driver)`, on failure show toast error
- [ ] 3.7 In `templates/dashboard_passenger_new.html` `lookupDriver()`: fix the manual lookup to POST to `/api/scan_driver_qr` with `{ qr_data: JSON.stringify({driver_id: id, type:'driver'}) }` OR call `/api/get_driver_profile_for_passenger?driver_id=X`

## Task 4: Fix Ride Start — GPS Coordinates and Connection
Fix the ride start flow so passenger GPS coordinates are sent and the driver sees the connection.

### Sub-tasks
- [ ] 4.1 In `templates/dashboard_passenger_new.html` `startRideFromRoute()`: call `navigator.geolocation.getCurrentPosition()` before the API call and include `latitude`, `longitude` in the POST body to `/api/start_ride`
- [ ] 4.2 In `templates/dashboard_passenger_new.html` `confirmDriver()`: store `selectedDriver` with all fields (id, name, vehicle_number, vehicle_type, rating) and navigate to tracking section
- [ ] 4.3 In `templates/dashboard_passenger_new.html`: show the "Start Ride" button (`startRideContainer`) only when `selectedDriver` is set AND both pickup/dropoff inputs are filled
- [ ] 4.4 In `app_enhanced.py` `start_ride()`: ensure the proximity warning is returned but does NOT block ride creation (already done — verify this works)
- [ ] 4.5 In `templates/dashboard_driver_new.html`: add `checkActiveRide()` function that calls `GET /api/get_active_ride` and shows `activeRideBanner` with passenger name when a ride is found
- [ ] 4.6 In `templates/dashboard_driver_new.html` `loadDriverData()`: call `checkActiveRide()` after profile loads, and set a `setInterval(checkActiveRide, 5000)` to poll every 5 seconds

## Task 5: Create Unified GPS Update Endpoint
Create `/api/update_gps` that upserts `live_locations` AND updates `drivers.latitude/longitude`.

### Sub-tasks
- [ ] 5.1 In `app_enhanced.py`: add new route `POST /api/update_gps` that accepts `{ latitude, longitude, accuracy, speed, role }` — authenticates via `_require_driver()` or `_require_passenger()` based on role
- [ ] 5.2 The endpoint must upsert into `live_locations` using `INSERT ... ON CONFLICT(user_id) DO UPDATE SET ...`
- [ ] 5.3 If role is `driver`, also update `drivers SET latitude=?, longitude=? WHERE id=?`
- [ ] 5.4 In `templates/dashboard_driver_new.html` GPS tracking loop: change `POST /api/update_driver_location` calls to `POST /api/update_gps` with `{ latitude, longitude, accuracy, speed, role: 'driver' }`
- [ ] 5.5 In `templates/dashboard_passenger_new.html` GPS tracking loop: add passenger GPS updates via `POST /api/update_gps` with `{ latitude, longitude, role: 'passenger' }` every 5 seconds during active ride

## Task 6: Fix Ride Completion and Payment Flow
Fix the complete_ride endpoint to update driver stats and ensure payment QR is shown correctly.

### Sub-tasks
- [ ] 6.1 In `app_enhanced.py` `complete_ride()`: add `UPDATE drivers SET total_rides=total_rides+1, total_earned=total_earned+? WHERE id=?` after the ride status update
- [ ] 6.2 In `app_enhanced.py` `complete_ride()`: add `route_coordinates` parameter — accept from POST body and store in rides table
- [ ] 6.3 In `templates/dashboard_passenger_new.html` `endRide()`: collect `totalDistance` and `routeCoordinates` (array of [lat,lng] from tracking), send in POST body to `/api/complete_ride`
- [ ] 6.4 In `templates/dashboard_passenger_new.html`: after `complete_ride` success, show `paymentSection` with the returned `payment_qr` image and `fare` amount
- [ ] 6.5 In `templates/dashboard_passenger_new.html` `confirmPayment()`: POST to `/api/confirm_payment` with `{ ride_id: activeRideId, fare: finalFare }`, then show "Waiting for driver confirmation" message
- [ ] 6.6 In `templates/dashboard_driver_new.html`: poll `GET /api/get_active_ride` — when `payment_status === 'passenger_confirmed'`, show `paymentNotifBanner` with fare amount and "Confirm Received" button

## Task 7: Fix Database Schema — Missing Columns
Ensure all required columns exist via the startup migration system.

### Sub-tasks
- [ ] 7.1 In `app_enhanced.py` `init_db()` migrations list: add `('drivers', 'address', 'TEXT')` if not already present
- [ ] 7.2 In `app_enhanced.py` `init_db()` migrations list: add `('rides', 'sos_triggered', 'INTEGER DEFAULT 0')` if not already present
- [ ] 7.3 In `app_enhanced.py` `init_db()` migrations list: add `('rides', 'route_coordinates', 'TEXT')` if not already present (it may already exist)
- [ ] 7.4 Verify `live_locations` table is created before the migration loop runs (move table creation before migration list execution if needed)
- [ ] 7.5 Run `python app_enhanced.py` locally to confirm no startup errors and all tables/columns are created

## Task 8: End-to-End Integration Test
Verify the complete ride flow works from QR scan to payment confirmation.

### Sub-tasks
- [ ] 8.1 Register a test driver and test passenger using the registration forms
- [ ] 8.2 Verify driver profile loads correctly (name, age, mobile, email, address all populated)
- [ ] 8.3 Verify passenger profile loads correctly (name, phone, email, emergency contact populated)
- [ ] 8.4 Driver enables GPS tracking — verify location appears in `live_locations` table
- [ ] 8.5 Passenger opens "Nearby Drivers" — verify driver appears on map with correct distance
- [ ] 8.6 Passenger scans driver QR code — verify driver details panel shows correctly
- [ ] 8.7 Passenger confirms driver and starts ride — verify ride record created in `rides` table with status `active`
- [ ] 8.8 Driver dashboard shows "Active Ride" banner with passenger name within 5 seconds
- [ ] 8.9 Passenger ends ride — verify `rides` table updated with `status=completed`, `fare`, `distance_km`
- [ ] 8.10 Payment QR shown to passenger — passenger confirms payment — driver sees notification and confirms receipt
