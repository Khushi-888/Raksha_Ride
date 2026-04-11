# Project Documentation: RakshaRide - Secure QR-Based Transportation

## 1. Introduction
**RakshaRide** is a safety-centric, full-stack ride-hailing application designed to provide transparency and security in the unorganized transportation sector (Rickshaws/Taxis). The system utilizes dynamic QR code generation and real-time database synchronization to ensure that every journey is verified, tracked, and securely recorded for both passengers and drivers.

---

## 2. Project Objectives

### 2.1 Driver & Vehicle Transparency via QR
The primary objective is to eliminate "shadow" drivers. Before a ride begins, the passenger scans a unique QR code displayed by the driver. This fetches real-time data from the database, allowing the rider to verify the driver’s identity, license status, and vehicle details (Mode, Color, Plate Number) instantly on their device.

### 2.2 Verified Ride Completion & Payment
The system automates the closure of the "Trust Loop." A ride is only marked as "Completed" in the database once the passenger triggers the QR-based verification at the destination. This ensures that the payment and history logs of both entities are synchronized, preventing disputes over fare or trip occurrence.

### 2.3 Automated Fare & Route Tracking
To prevent overcharging, the system calculates fares based on the exact distance covered using GPS coordinates. This route is stored as a series of coordinates in the `Common Ride Table`, allowing users to review their exact travel path in their ride history.

---

## 3. Database Design

The system follows a Relational Database Management System (RDBMS) structure. 

### 3.1 Table Structures & Attributes

#### **A. Drivers Table**
Stores the profile and authorization level of the service provider.
*   **Personal:** `Driver_ID`, `Full_Name`, `Profile_Image`, `Phone`, `Email`.
*   **Vehicle:** `Vehicle_Number`, `Vehicle_Type` (Bike/Auto/Car), `Model`, `Color`.
*   **Professional:** `License_Number`, `Rating`, `Total_Rides`, `Availability_Status` (Available/Busy).

#### **B. Passengers (Riders) Table**
Manages the identity and preferences of the service consumer.
*   **Attributes:** `Rider_ID`, `Full_Name`, `Profile_Image`, `Phone`, `Email`, `Preferred_Payment_Method`.

#### **D. Common Ride Table (Central Ledger)**
This table links the Driver and Passenger and acts as the "Source of Truth" for every transaction.
*   **Foreign Keys:** `Driver_ID`, `Rider_ID`.
*   **Geospatial:** `Start_Location`, `End_Location`, `Route_Coordinates`, `Distance`.
*   **Financial:** `Calculated_Fare`, `Payment_Status` (Paid/Unpaid).
*   **Temporal:** `Ride_Start_Time`, `Ride_End_Time`, `Ride_Status` (Pending/Accepted/Completed).

---

## 4. System Workflow (Data Flow)

1.  **Identity Verification:** A user registers via Email OTP. Upon verification, Drivers are assigned a unique QR string (`RAKSHARIDE_VERIFIED:[ID]`).
2.  **Request Phase:** The Passenger selects an "Available" driver from the dashboard. A new record is created in the `Common Ride Table` with status `Pending`.
3.  **Acceptance Phase:** The Driver receives a notification. Upon clicking "Accept," their status in the `Drivers` table changes to `Busy`, and the ride status becomes `Accepted`.
4.  **Verification Phase (Destination):** At the end of the trip, the Passenger "Scans" (simulated via verification button) the Driver's QR. 
5.  **Completion Phase:** The system updates `Ride_Status` to `Completed`, updates the Driver's `Total_Rides`, and sets the `Payment_Status` to `Paid`.

---

## 5. Role of QR Code in Security & Payment

The QR code acts as a **Digital Handshake**. 
*   **Safety:** It prevents "Unauthorized Vehicles" from picking up passengers because only verified IDs in the database can generate a valid QR.
*   **Payment Confirmation:** The QR code contains the encrypted `Ride_ID`. When scanned by the passenger, the server confirms that the specific passenger and specific driver are at the same logical destination, triggering the fund transfer and ride closure.

---

## 6. Entity Relationship (ER) Summary
*   **Driver to Ride:** 1-to-Many (One driver can complete multiple rides).
*   **Passenger to Ride:** 1-to-Many (One passenger can book multiple rides).
*   **Ride to Payment:** 1-to-1 (Every ride has exactly one payment status).

---

## 7. Technology Stack

*   **Backend:** **Python Flask** - Handles API routing, session management, and server-side logic.
*   **Database:** **MySQL** - Stores structured data for users, drivers, and ride logs.
*   **Frontend:** **HTML5, Vanilla CSS, JavaScript** - Provides a high-fidelity, responsive user interface with glassmorphism effects.
*   **Mapping:** **Leaflet.js / OpenStreetMap** - Used for visualizing routes and tracking distance.
*   **Security:** **SMTP (SSL)** - Secure Email OTP verification for account protection.
*   **WSGI Server:** **Waitress** - Ensures the application is production-ready and stable.

---

## 8. Conclusion
RakshaRide successfully digitizes the rickshaw booking process by introducing **accountability**. It moves away from verbal agreements to a data-driven system where fares are transparent, drivers are verified, and history is permanently logged. This system significantly improves passenger safety in urban environments.
