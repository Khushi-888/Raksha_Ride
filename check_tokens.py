import sqlite3
conn = sqlite3.connect('database_enhanced.db')
c = conn.cursor()
c.execute("SELECT id, approval_token, status FROM renter_requests")
print(c.fetchall())
