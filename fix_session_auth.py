"""
Fix all remaining session-only auth checks in app_enhanced.py
Replace with dual-auth helpers (_require_driver / _require_passenger / get_current_user)
"""
import re

with open('app_enhanced.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Pattern 1: driver session check + driver_id = session['user_id']
content = content.replace(
    "        if 'user_id' not in session or session.get('user_type') != 'driver':\n"
    "            return jsonify({\"success\": False, \"message\": \"Unauthorized\"}), 401\n"
    "        \n"
    "        driver_id = session['user_id']",
    "        driver_id, err = _require_driver()\n"
    "        if err: return err"
)

# Pattern 1b: driver session check + driver_id = session['user_id'] (no trailing space)
content = content.replace(
    "        if 'user_id' not in session or session.get('user_type') != 'driver':\n"
    "            return jsonify({\"success\": False, \"message\": \"Unauthorized\"}), 401\n"
    "\n"
    "        driver_id = session['user_id']",
    "        driver_id, err = _require_driver()\n"
    "        if err: return err"
)

# Pattern 2: passenger session check + passenger_id = session['user_id']
content = content.replace(
    "        if 'user_id' not in session or session.get('user_type') != 'passenger':\n"
    "            return jsonify({\"success\": False, \"message\": \"Unauthorized\"}), 401\n"
    "        \n"
    "        passenger_id = session['user_id']",
    "        passenger_id, err = _require_passenger()\n"
    "        if err: return err"
)

# Pattern 2b: passenger session check + passenger_id = session['user_id'] (no trailing space)
content = content.replace(
    "        if 'user_id' not in session or session.get('user_type') != 'passenger':\n"
    "            return jsonify({\"success\": False, \"message\": \"Unauthorized\"}), 401\n"
    "\n"
    "        passenger_id = session['user_id']",
    "        passenger_id, err = _require_passenger()\n"
    "        if err: return err"
)

# Pattern 3: driver check with different message
content = content.replace(
    "        if 'user_id' not in session or session.get('user_type') != 'driver':\n"
    "            return jsonify({\"success\": False, \"message\": \"Unauthorized\"}), 401\n"
    "        driver_id = session['user_id']",
    "        driver_id, err = _require_driver()\n"
    "        if err: return err"
)

# Pattern 4: passenger check with different message
content = content.replace(
    "        if 'user_id' not in session or session.get('user_type') != 'passenger':\n"
    "            return jsonify({\"success\": False, \"message\": \"Unauthorized\"}), 401\n"
    "        driver_id = session['user_id']",
    "        passenger_id, err = _require_passenger()\n"
    "        if err: return err"
)

# Pattern 5: standalone driver check (no driver_id assignment after)
content = content.replace(
    "    if 'user_id' not in session or session.get('user_type') != 'driver':\n"
    "        return jsonify({\"success\": False, \"message\": \"Unauthorized\"}), 401\n"
    "    try:",
    "    driver_id, err = _require_driver()\n"
    "    if err: return err\n"
    "    try:"
)

# Pattern 6: standalone passenger check (no passenger_id assignment after)
content = content.replace(
    "    if 'user_id' not in session or session.get('user_type') != 'passenger':\n"
    "        return jsonify({\"success\": False, \"message\": \"Unauthorized\"}), 401\n"
    "    try:",
    "    passenger_id, err = _require_passenger()\n"
    "    if err: return err\n"
    "    try:"
)

with open('app_enhanced.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Done! Checking remaining session checks...")

# Count remaining
remaining = content.count("if 'user_id' not in session")
print(f"Remaining 'if user_id not in session' occurrences: {remaining}")

# Show lines with remaining occurrences
for i, line in enumerate(content.split('\n'), 1):
    if "if 'user_id' not in session" in line:
        print(f"  Line {i}: {line.strip()}")
