-- Create Database
CREATE DATABASE IF NOT EXISTS raksharide;
USE raksharide;

-- Drivers Table
CREATE TABLE IF NOT EXISTS drivers (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    phone VARCHAR(20) NOT NULL,
    password VARCHAR(255) NOT NULL,
    profile_image VARCHAR(255) DEFAULT 'default_driver.png',
    is_verified TINYINT(1) DEFAULT 0,
    
    -- Vehicle Details
    vehicle_number VARCHAR(50),
    vehicle_type ENUM('bike', 'car', 'auto'),
    vehicle_model VARCHAR(100),
    vehicle_color VARCHAR(50),
    
    -- Professional Details
    license_number VARCHAR(100),
    rating DECIMAL(3, 2) DEFAULT 4.5,
    total_rides INT DEFAULT 0,
    availability_status ENUM('available', 'busy', 'offline') DEFAULT 'offline',
    qr_code_url VARCHAR(255),

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Passengers Table
CREATE TABLE IF NOT EXISTS passengers (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    phone VARCHAR(20) NOT NULL,
    password VARCHAR(255) NOT NULL,
    profile_image VARCHAR(255) DEFAULT 'default_passenger.png',
    is_verified TINYINT(1) DEFAULT 0,
    
    preferred_payment ENUM('cash', 'online') DEFAULT 'online',
    current_ride_id INT DEFAULT NULL,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- OTP Verification Table
CREATE TABLE IF NOT EXISTS otp_verification (
    id INT AUTO_INCREMENT PRIMARY KEY,
    email VARCHAR(100) NOT NULL,
    user_type ENUM('driver', 'passenger') NOT NULL,
    otp VARCHAR(6) NOT NULL,
    expiry_time DATETIME NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Common Ride Attributes
CREATE TABLE IF NOT EXISTS rides (
    id INT AUTO_INCREMENT PRIMARY KEY,
    passenger_id INT NOT NULL,
    driver_id INT,
    
    start_location VARCHAR(255) NOT NULL,
    end_location VARCHAR(255) NOT NULL,
    distance DECIMAL(10, 2), 
    calculated_fare DECIMAL(10, 2),
    route_coordinates TEXT,
    
    payment_qr_generated TINYINT(1) DEFAULT 0,
    payment_status ENUM('unpaid', 'paid') DEFAULT 'unpaid',
    
    status ENUM('pending', 'accepted', 'ongoing', 'completed', 'cancelled') DEFAULT 'pending',
    
    start_time DATETIME,
    end_time DATETIME,
    
    -- Real-time Tracking
    curr_lat DECIMAL(10, 8),
    curr_lng DECIMAL(11, 8),
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (passenger_id) REFERENCES passengers(id),
    FOREIGN KEY (driver_id) REFERENCES drivers(id)
);
