"""
RakshaRide Database Backup Script
Run this locally whenever you want to save current data to GitHub backup.

Usage:
    python backup_db.py

Then commit and push:
    git add backup/database_enhanced.db
    git commit -m "backup: update database"
    git push origin main
"""
import os
import shutil
import sqlite3
from datetime import datetime

DB_SOURCE = 'database_enhanced.db'
BACKUP_DIR = 'backup'
BACKUP_FILE = os.path.join(BACKUP_DIR, 'database_enhanced.db')

def backup():
    # Create backup directory if needed
    os.makedirs(BACKUP_DIR, exist_ok=True)

    if not os.path.exists(DB_SOURCE):
        print(f"❌ Source DB not found: {DB_SOURCE}")
        return False

    size = os.path.getsize(DB_SOURCE)
    if size < 1000:
        print(f"⚠️ Source DB seems empty ({size} bytes) — skipping backup")
        return False

    # Verify DB is valid SQLite
    try:
        conn = sqlite3.connect(DB_SOURCE)
        tables = conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
        conn.close()
        print(f"✅ DB valid — {len(tables)} tables found")
    except Exception as e:
        print(f"❌ DB validation failed: {e}")
        return False

    # Copy to backup
    shutil.copy2(DB_SOURCE, BACKUP_FILE)
    backup_size = os.path.getsize(BACKUP_FILE)
    print(f"✅ Backup saved: {BACKUP_FILE} ({backup_size} bytes)")
    print(f"   Tables: {[t[0] for t in tables]}")
    print(f"   Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    print("Next steps to save to GitHub:")
    print("  git add backup/database_enhanced.db")
    print('  git commit -m "backup: update database"')
    print("  git push origin main")
    return True

if __name__ == '__main__':
    backup()
