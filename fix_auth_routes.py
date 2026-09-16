"""Fix all API routes to use get_current_user() instead of session checks"""
import re

content = open('app_enhanced.py', encoding='utf-8').read()

# Replace all session-based auth checks with get_current_user()
replacements = [
    # passenger profile
    (
        "def api_passenger_profile():\n    if 'user_id' not in session or session.get('user_type') != 'passenger':\n        return jsonify({\"success\": False, \"message\": \"Not authenticated\"}), 401",
        "def api_passenger_profile():\n    current_user = get_current_user()\n    if not current_user:\n        return jsonify({\"success\": False, \"message\": \"Not authenticated — please login\", \"code\": \"AUTH_REQUIRED\"}), 401"
    ),
    # update passenger profile
    (
        "def api_update_passenger_profile():\n    if 'user_id' not in session:\n        return jsonify({\"success\": False, \"message\": \"Not authenticated\"}), 401",
        "def api_update_passenger_profile():\n    current_user = get_current_user()\n    if not current_user:\n        return jsonify({\"success\": False, \"message\": \"Not authenticated — please login\", \"code\": \"AUTH_REQUIRED\"}), 401"
    ),
    # update emergency contact
    (
        "def api_update_emergency_contact():\n    if 'user_id' not in session:\n        return jsonify({\"success\": False, \"message\": \"Not authenticated — please login again\"}), 401",
        "def api_update_emergency_contact():\n    current_user = get_current_user()\n    if not current_user:\n        return jsonify({\"success\": False, \"message\": \"Not authenticated — please login\", \"code\": \"AUTH_REQUIRED\"}), 401"
    ),
    # sos alert
    (
        "def api_sos_alert():\n    if 'user_id' not in session:\n        return jsonify({\"success\": False, \"message\": \"Not authenticated — please login again\"}), 401",
        "def api_sos_alert():\n    current_user = get_current_user()\n    if not current_user:\n        return jsonify({\"success\": False, \"message\": \"Not authenticated — please login\", \"code\": \"AUTH_REQUIRED\"}), 401"
    ),
]

for old, new in replacements:
    if old in content:
        content = content.replace(old, new)
        print(f"Fixed: {old[:60]}...")
    else:
        print(f"NOT FOUND: {old[:60]}...")

# Now replace session['user_id'] with current_user['user_id'] in the affected functions
# We need to do this carefully for each function

open('app_enhanced.py', 'w', encoding='utf-8').write(content)
print("Done")
