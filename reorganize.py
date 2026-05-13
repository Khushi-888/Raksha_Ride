"""
Reorganize RakshaRide into 3 professional folders:
  frontend/   - templates/ + static/
  backend/    - Python files + config
  database/   - DB files

Moves files using git mv so history is preserved.
"""
import subprocess, os, shutil

ROOT = r"C:\Users\Acer\OneDrive\Desktop\New folder\Minor Project"

def run(cmd):
    result = subprocess.run(cmd, shell=True, cwd=ROOT, capture_output=True, text=True)
    if result.returncode != 0 and result.stderr:
        print(f"  WARN: {result.stderr.strip()[:100]}")
    return result.returncode == 0

# Create folders
for folder in ['frontend', 'backend', 'database']:
    os.makedirs(os.path.join(ROOT, folder), exist_ok=True)

print("Moving templates/ -> frontend/templates/")
run("git mv templates frontend/templates")

print("Moving static/ -> frontend/static/")
run("git mv static frontend/static")

print("Moving backend Python files...")
backend_files = [
    'app_enhanced.py', 'auth_utils.py', 'wsgi.py', 'Procfile',
    'requirements.txt', 'build.sh', 'Dockerfile',
    'ai_verification.py', 'security_enhancements.py',
]
for f in backend_files:
    if os.path.exists(os.path.join(ROOT, f)):
        run(f"git mv {f} backend/{f}")
        print(f"  {f} -> backend/")

print("Moving database files...")
db_files = ['database_enhanced.db', 'database_schema.sql', 'document_encryption.key']
for f in db_files:
    if os.path.exists(os.path.join(ROOT, f)):
        run(f"git mv {f} database/{f}")
        print(f"  {f} -> database/")

print("\nDone! Now update Flask app to use new paths.")
