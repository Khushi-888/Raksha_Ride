"""
Apply all remaining fixes to app_enhanced.py:
1. Fix remaining session-only auth checks
2. Fix encoding issues (em-dash in docstrings)
Run this once then delete it.
"""
import re

with open('app_enhanced.py', 'r', encoding='utf-8') as f:
    content = f.read()

original_len = len(content)

# ── Fix 1: upload_driver_document ────────────────────────────────────────────
old = '''    try:
        if 'user_id' not in session or session.get('user_type') != 'driver':
            return jsonify({"success": False, "message": "Unauthorized"}), 401

        data     = request.get_json()
        doc_type = data.get('doc_type', '').upper()
        image    = data.get('image', '')
        uploader_id = session['user_id']'''

new = '''    try:
        driver_id, err = _require_driver()
        if err: return err

        data     = request.get_json()
        doc_type = data.get('doc_type', '').upper()
        image    = data.get('image', '')
        uploader_id = driver_id'''

if old in content:
    content = content.replace(old, new, 1)
    print("Fixed: upload_driver_document")
else:
    print("SKIP: upload_driver_document (not found or already fixed)")

# ── Fix 2: get_my_documents ───────────────────────────────────────────────────
old2 = '''    if 'user_id' not in session or session.get('user_type') != 'driver':
        return jsonify({"success": False, "message": "Unauthorized"}), 401
    try:
        driver_id = session['user_id']
        conn = get_db_conn()
        c = conn.cursor()
        c.execute("""
            SELECT id, doc_type, ai_status, ai_score, created_at
            FROM driver_documents WHERE driver_id = ?
            ORDER BY created_at DESC""", (driver_id,))'''

new2 = '''    driver_id, err = _require_driver()
    if err: return err
    try:
        conn = get_db_conn()
        c = conn.cursor()
        c.execute("""
            SELECT id, doc_type, ai_status, ai_score, created_at
            FROM driver_documents WHERE driver_id = ?
            ORDER BY created_at DESC""", (driver_id,))'''

if old2 in content:
    content = content.replace(old2, new2, 1)
    print("Fixed: get_my_documents")
else:
    print("SKIP: get_my_documents (not found or already fixed)")

# ── Fix 3: Any remaining session-only driver checks with driver_id assignment ─
# Pattern: 8-space indent
patterns_driver = [
    (
        "        if 'user_id' not in session or session.get('user_type') != 'driver':\n"
        "            return jsonify({\"success\": False, \"message\": \"Unauthorized\"}), 401\n"
        "\n"
        "        driver_id = session['user_id']",
        "        driver_id, err = _require_driver()\n"
        "        if err: return err"
    ),
    (
        "        if 'user_id' not in session or session.get('user_type') != 'driver':\n"
        "            return jsonify({\"success\": False, \"message\": \"Unauthorized\"}), 401\n"
        "        \n"
        "        driver_id = session['user_id']",
        "        driver_id, err = _require_driver()\n"
        "        if err: return err"
    ),
    (
        "        if 'user_id' not in session or session.get('user_type') != 'driver':\n"
        "            return jsonify({\"success\": False, \"message\": \"Unauthorized\"}), 401\n"
        "\n"
        "        owner_id = session['user_id']",
        "        driver_id, err = _require_driver()\n"
        "        if err: return err\n"
        "        owner_id = driver_id"
    ),
    (
        "        if 'user_id' not in session or session.get('user_type') != 'driver':\n"
        "            return jsonify({\"success\": False, \"message\": \"Unauthorized\"}), 401\n"
        "\n"
        "        renter_id = session['user_id']",
        "        driver_id, err = _require_driver()\n"
        "        if err: return err\n"
        "        renter_id = driver_id"
    ),
    (
        "        if 'user_id' not in session or session.get('user_type') != 'driver':\n"
        "            return jsonify({\"success\": False, \"message\": \"Unauthorized\"}), 401\n"
        "\n"
        "        uploader_id = session['user_id']",
        "        driver_id, err = _require_driver()\n"
        "        if err: return err\n"
        "        uploader_id = driver_id"
    ),
]

for old_p, new_p in patterns_driver:
    count = content.count(old_p)
    if count > 0:
        content = content.replace(old_p, new_p)
        print(f"Fixed {count}x driver pattern")

# ── Fix 4: Remaining passenger checks ────────────────────────────────────────
patterns_passenger = [
    (
        "        if 'user_id' not in session or session.get('user_type') != 'passenger':\n"
        "            return jsonify({\"success\": False, \"message\": \"Unauthorized\"}), 401\n"
        "\n"
        "        passenger_id = session['user_id']",
        "        passenger_id, err = _require_passenger()\n"
        "        if err: return err"
    ),
    (
        "        if 'user_id' not in session or session.get('user_type') != 'passenger':\n"
        "            return jsonify({\"success\": False, \"message\": \"Unauthorized\"}), 401\n"
        "        \n"
        "        passenger_id = session['user_id']",
        "        passenger_id, err = _require_passenger()\n"
        "        if err: return err"
    ),
]

for old_p, new_p in patterns_passenger:
    count = content.count(old_p)
    if count > 0:
        content = content.replace(old_p, new_p)
        print(f"Fixed {count}x passenger pattern")

# ── Fix 5: Standalone driver checks (no variable assignment after) ────────────
# These are checks where the session check is at function top level (4 spaces)
standalone_driver = (
    "    if 'user_id' not in session or session.get('user_type') != 'driver':\n"
    "        return jsonify({\"success\": False, \"message\": \"Unauthorized\"}), 401\n"
    "    try:"
)
standalone_driver_new = (
    "    driver_id, err = _require_driver()\n"
    "    if err: return err\n"
    "    try:"
)
count = content.count(standalone_driver)
if count > 0:
    content = content.replace(standalone_driver, standalone_driver_new)
    print(f"Fixed {count}x standalone driver check")

# ── Fix 6: Remaining inline driver checks (no try block) ─────────────────────
# Pattern where check is inside try block but no variable after
inline_driver_no_var = (
    "        if 'user_id' not in session or session.get('user_type') != 'driver':\n"
    "            return jsonify({\"success\": False, \"message\": \"Unauthorized\"}), 401\n"
    "\n"
    "        data"
)
inline_driver_no_var_new = (
    "        driver_id, err = _require_driver()\n"
    "        if err: return err\n"
    "\n"
    "        data"
)
count = content.count(inline_driver_no_var)
if count > 0:
    content = content.replace(inline_driver_no_var, inline_driver_no_var_new)
    print(f"Fixed {count}x inline driver check (no var)")

# ── Fix 7: Remaining inline passenger checks ──────────────────────────────────
inline_pass_no_var = (
    "        if 'user_id' not in session or session.get('user_type') != 'passenger':\n"
    "            return jsonify({\"success\": False, \"message\": \"Unauthorized\"}), 401\n"
    "\n"
    "        data"
)
inline_pass_no_var_new = (
    "        passenger_id, err = _require_passenger()\n"
    "        if err: return err\n"
    "\n"
    "        data"
)
count = content.count(inline_pass_no_var)
if count > 0:
    content = content.replace(inline_pass_no_var, inline_pass_no_var_new)
    print(f"Fixed {count}x inline passenger check (no var)")

# ── Write back ────────────────────────────────────────────────────────────────
with open('app_enhanced.py', 'w', encoding='utf-8') as f:
    f.write(content)

print(f"\nDone. File size: {original_len} -> {len(content)} chars")

# ── Report remaining ──────────────────────────────────────────────────────────
remaining = [(i+1, line.strip()) for i, line in enumerate(content.split('\n'))
             if "if 'user_id' not in session" in line and not line.strip().startswith('#')]
print(f"\nRemaining session checks: {len(remaining)}")
for lineno, line in remaining:
    print(f"  Line {lineno}: {line}")
