"""
Add Payment QR Upload Feature
Allows drivers to upload their own UPI payment QR code image
"""

import sqlite3

def add_payment_qr_field():
    """Add payment_qr_image field to drivers table"""
    
    conn = sqlite3.connect('database_enhanced.db')
    c = conn.cursor()
    
    print("\n" + "="*70)
    print("  Adding Payment QR Upload Feature")
    print("="*70 + "\n")
    
    # Add payment_qr_image field to drivers table
    try:
        c.execute("ALTER TABLE drivers ADD COLUMN payment_qr_image TEXT")
        print("✅ Added: drivers.payment_qr_image")
    except sqlite3.OperationalError as e:
        if "duplicate column" in str(e):
            print("⚠️  drivers.payment_qr_image already exists")
        else:
            print(f"❌ Error: {e}")
    
    conn.commit()
    conn.close()
    
    print("\n" + "="*70)
    print("  ✅ Payment QR Upload Feature Added!")
    print("="*70 + "\n")
    
    print("Drivers can now:")
    print("  1. Upload their UPI payment QR image")
    print("  2. Save it to their account")
    print("  3. Passengers will see this QR when paying")
    print()

if __name__ == '__main__':
    add_payment_qr_field()
