import sqlite3
import os

db_path = 'database_enhanced.db'
conn = sqlite3.connect(db_path)
c = conn.cursor()

# Show current counts
tables = ['passengers', 'drivers', 'rides', 'otp_verification', 'driver_documents', 'renter_requests', 'payments', 'ratings', 'sos_alerts', 'live_locations']
print("BEFORE:")
for t in tables:
    try:
        c.execute(f"SELECT COUNT(*) FROM {t}")
        print(f"  {t}: {c.fetchone()[0]}")
    except: pass

# Clear all user data (keep admins table intact)
c.execute("DELETE FROM passengers")
c.execute("DELETE FROM drivers") 
c.execute("DELETE FROM rides")
c.execute("DELETE FROM otp_verification")
c.execute("DELETE FROM driver_documents")
c.execute("DELETE FROM renter_requests")
c.execute("DELETE FROM payments")
c.execute("DELETE FROM ratings")
c.execute("DELETE FROM sos_alerts")
try:
    c.execute("DELETE FROM live_locations")
except: pass

# Reset auto-increment sequences
for t in ['passengers', 'drivers', 'rides', 'otp_verification', 'driver_documents', 'renter_requests', 'payments', 'ratings', 'sos_alerts']:
    try:
        c.execute(f"DELETE FROM sqlite_sequence WHERE name='{t}'")
    except: pass

conn.commit()

print("\nAFTER:")
for t in tables:
    try:
        c.execute(f"SELECT COUNT(*) FROM {t}")
        print(f"  {t}: {c.fetchone()[0]}")
    except: pass

# Show admins (should still be there)
c.execute("SELECT id, username FROM admins")
admins = c.fetchall()
print(f"\nAdmins kept: {admins}")

conn.close()
print("\nDatabase cleaned successfully!")
