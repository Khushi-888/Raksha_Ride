import sqlite3
import os

def check_schema():
    db_path = "production_database.db"
    if not os.path.exists(db_path):
        print(f"Database {db_path} not found.")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    tables = ['passengers', 'verified_drivers', 'pending_verification']
    for table in tables:
        print(f"\nSchema for {table}:")
        try:
            cursor.execute(f"PRAGMA table_info({table})")
            columns = cursor.fetchall()
            for col in columns:
                print(col)
        except Exception as e:
            print(f"Error checking {table}: {e}")
            
    conn.close()

if __name__ == "__main__":
    check_schema()
