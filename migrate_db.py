import sqlite3
import os

def migrate():
    db_path = "production_database.db"
    if not os.path.exists(db_path):
        print(f"Database {db_path} not found.")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print("Migrating passengers table...")
    try:
        # Check if verified column exists
        cursor.execute("PRAGMA table_info(passengers)")
        columns = [col[1] for col in cursor.fetchall()]
        
        if 'verified' not in columns:
            cursor.execute("ALTER TABLE passengers ADD COLUMN verified BOOLEAN DEFAULT 0")
            print("Added 'verified' column to passengers table.")
        else:
            print("'verified' column already exists in passengers table.")
            
        conn.commit()
    except Exception as e:
        print(f"Migration failed: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    migrate()
