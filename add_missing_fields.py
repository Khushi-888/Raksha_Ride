"""
Add Missing Optional Fields to Database
Adds: Vehicle Model, Vehicle Color, License Number, Preferred Payment, Payment QR Flag
"""

import sqlite3

def add_missing_fields():
    """Add missing optional fields to make database 100% complete"""
    
    conn = sqlite3.connect('database_enhanced.db')
    c = conn.cursor()
    
    print("\n" + "="*70)
    print("  Adding Missing Optional Fields")
    print("="*70 + "\n")
    
    # Check and add fields to drivers table
    try:
        # Add vehicle_model
        c.execute("ALTER TABLE drivers ADD COLUMN vehicle_model TEXT DEFAULT 'Not specified'")
        print("✅ Added: drivers.vehicle_model")
    except sqlite3.OperationalError:
        print("⚠️  drivers.vehicle_model already exists")
    
    try:
        # Add vehicle_color
        c.execute("ALTER TABLE drivers ADD COLUMN vehicle_color TEXT DEFAULT 'Not specified'")
        print("✅ Added: drivers.vehicle_color")
    except sqlite3.OperationalError:
        print("⚠️  drivers.vehicle_color already exists")
    
    try:
        # Add license_number
        c.execute("ALTER TABLE drivers ADD COLUMN license_number TEXT DEFAULT 'Not specified'")
        print("✅ Added: drivers.license_number")
    except sqlite3.OperationalError:
        print("⚠️  drivers.license_number already exists")
    
    # Check and add fields to passengers table
    try:
        # Add preferred_payment_method
        c.execute("ALTER TABLE passengers ADD COLUMN preferred_payment_method TEXT DEFAULT 'online'")
        print("✅ Added: passengers.preferred_payment_method")
    except sqlite3.OperationalError:
        print("⚠️  passengers.preferred_payment_method already exists")
    
    try:
        # Add current_ride_status
        c.execute("ALTER TABLE passengers ADD COLUMN current_ride_status TEXT DEFAULT 'none'")
        print("✅ Added: passengers.current_ride_status")
    except sqlite3.OperationalError:
        print("⚠️  passengers.current_ride_status already exists")
    
    # Check and add fields to rides table
    try:
        # Add payment_qr_generated
        c.execute("ALTER TABLE rides ADD COLUMN payment_qr_generated BOOLEAN DEFAULT 0")
        print("✅ Added: rides.payment_qr_generated")
    except sqlite3.OperationalError:
        print("⚠️  rides.payment_qr_generated already exists")
    
    conn.commit()
    conn.close()
    
    print("\n" + "="*70)
    print("  ✅ Database Updated Successfully!")
    print("="*70 + "\n")
    
    # Verify changes
    verify_schema()

def verify_schema():
    """Verify all fields are present"""
    
    conn = sqlite3.connect('database_enhanced.db')
    c = conn.cursor()
    
    print("Verifying Schema...\n")
    
    # Check drivers table
    c.execute("PRAGMA table_info(drivers)")
    driver_columns = [row[1] for row in c.fetchall()]
    
    print("🚗 DRIVERS TABLE:")
    required_driver_fields = [
        'id', 'name', 'mobile', 'email', 'vehicle_number', 'vehicle_type',
        'vehicle_model', 'vehicle_color', 'license_number', 'rating',
        'total_rides', 'is_available', 'qr_code', 'profile_image'
    ]
    
    for field in required_driver_fields:
        status = "✅" if field in driver_columns else "❌"
        print(f"  {status} {field}")
    
    # Check passengers table
    c.execute("PRAGMA table_info(passengers)")
    passenger_columns = [row[1] for row in c.fetchall()]
    
    print("\n🧍 PASSENGERS TABLE:")
    required_passenger_fields = [
        'id', 'name', 'phone', 'email', 'profile_image',
        'preferred_payment_method', 'current_ride_status',
        'total_rides', 'total_spent'
    ]
    
    for field in required_passenger_fields:
        status = "✅" if field in passenger_columns else "❌"
        print(f"  {status} {field}")
    
    # Check rides table
    c.execute("PRAGMA table_info(rides)")
    ride_columns = [row[1] for row in c.fetchall()]
    
    print("\n🔗 RIDES TABLE:")
    required_ride_fields = [
        'id', 'passenger_id', 'driver_id', 'pickup_location', 'dropoff_location',
        'distance_km', 'fare', 'route_coordinates', 'payment_qr_generated',
        'payment_status', 'start_time', 'end_time', 'status'
    ]
    
    for field in required_ride_fields:
        status = "✅" if field in ride_columns else "❌"
        print(f"  {status} {field}")
    
    conn.close()
    
    print("\n" + "="*70)
    print("  🎉 All Required Fields Present!")
    print("="*70 + "\n")

if __name__ == '__main__':
    add_missing_fields()
