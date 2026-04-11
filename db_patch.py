import sqlite3

def patch_db():
    conn = sqlite3.connect('database_enhanced.db')
    c = conn.cursor()
    try:
        # Drop table and recreate it
        c.execute("DROP TABLE IF EXISTS renter_requests;")
        c.execute('''CREATE TABLE IF NOT EXISTS renter_requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            renter_id INTEGER NOT NULL,
            owner_email TEXT NOT NULL,
            owner_id INTEGER,
            approval_token TEXT UNIQUE,
            status TEXT DEFAULT 'PENDING',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (renter_id) REFERENCES drivers(id)
        )''')
        print("Successfully recreated renter_requests with approval_token.")
    except Exception as e:
        print(f"Error: {e}")
    
    conn.commit()
    conn.close()

if __name__ == "__main__":
    patch_db()
