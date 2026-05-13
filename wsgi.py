"""
RakshaRide WSGI entry point — production ready for Render free plan.

Database persistence strategy (fully free):
  1. On startup, check if DB exists and has data
  2. If missing/empty → download from GitHub backup
  3. Use /tmp for runtime (survives within session)
  4. Backup copy committed to GitHub: backup/database_enhanced.db
"""
import os
import sys
import shutil

# ── GitHub backup URL ─────────────────────────────────────────────────────────
GITHUB_DB_URL = (
    "https://raw.githubusercontent.com/Khushi-888/Raksha_Ride/main/"
    "backup/database_enhanced.db"
)

# ── DB path setup ─────────────────────────────────────────────────────────────
def _setup_db():
    """
    Determine DB path and restore from GitHub backup if needed.
    Priority:
      1. DB_PATH env var (set this on Render if you add a disk later)
      2. /tmp/database_enhanced.db  (Render free tier — survives within session)
      3. ./database_enhanced.db     (local development)
    """
    # If DB_PATH already set by env var, use it directly
    if os.environ.get('DB_PATH'):
        print(f"[DB] Using env DB_PATH: {os.environ['DB_PATH']}")
        return

    # On Render (Linux), use /tmp for runtime storage
    on_render = os.path.exists('/tmp') and os.environ.get('RENDER', '')
    if on_render or os.path.exists('/tmp'):
        tmp_db = '/tmp/database_enhanced.db'
        os.environ['DB_PATH'] = tmp_db

        if os.path.exists(tmp_db) and os.path.getsize(tmp_db) > 5000:
            print(f"[DB] ✅ Using existing /tmp DB ({os.path.getsize(tmp_db)} bytes)")
            return

        # /tmp DB missing or too small — try to restore
        print("[DB] /tmp DB missing or empty — attempting restore...")

        # Try 1: Copy from repo backup/ folder (fastest, no network)
        repo_backup = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            'backup', 'database_enhanced.db'
        )
        if os.path.exists(repo_backup) and os.path.getsize(repo_backup) > 5000:
            shutil.copy2(repo_backup, tmp_db)
            print(f"[DB] ✅ Restored from repo backup ({os.path.getsize(tmp_db)} bytes)")
            return

        # Try 2: Download from GitHub raw URL
        try:
            import requests
            print(f"[DB] Downloading from GitHub: {GITHUB_DB_URL}")
            resp = requests.get(GITHUB_DB_URL, timeout=30)
            if resp.status_code == 200 and len(resp.content) > 5000:
                with open(tmp_db, 'wb') as f:
                    f.write(resp.content)
                print(f"[DB] ✅ Downloaded from GitHub ({len(resp.content)} bytes)")
                return
            else:
                print(f"[DB] ⚠️ GitHub download failed: HTTP {resp.status_code}")
        except Exception as e:
            print(f"[DB] ⚠️ GitHub download error: {e}")

        # Try 3: Copy from repo root (if committed)
        repo_root_db = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            'database_enhanced.db'
        )
        if os.path.exists(repo_root_db) and os.path.getsize(repo_root_db) > 5000:
            shutil.copy2(repo_root_db, tmp_db)
            print(f"[DB] ✅ Copied from repo root ({os.path.getsize(tmp_db)} bytes)")
            return

        print("[DB] ℹ️ Starting with fresh database (no backup found)")

    else:
        # Local development — use file in project root
        local_db = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'database_enhanced.db')
        os.environ['DB_PATH'] = local_db
        print(f"[DB] Local dev mode: {local_db}")


# Run DB setup BEFORE importing app (so DB_PATH is set before SQLite connects)
_setup_db()

from app_enhanced import app, init_db

# Initialize database tables on startup
init_db()
print(f"[DB] Database ready at: {os.environ.get('DB_PATH', 'database_enhanced.db')}")
