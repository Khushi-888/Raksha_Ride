"""Fix remaining session-only auth checks using line-based replacement"""

with open('app_enhanced.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Track changes
changes = 0
i = 0
new_lines = []

while i < len(lines):
    line = lines[i]
    
    # Pattern: session check for driver (indented with 8 spaces)
    if ("if 'user_id' not in session or session.get('user_type') != 'driver':" in line and
            "return jsonify" in lines[i+1] if i+1 < len(lines) else False):
        indent = len(line) - len(line.lstrip())
        spaces = ' ' * indent
        # Check next line is the return
        next_line = lines[i+1] if i+1 < len(lines) else ''
        if 'return jsonify' in next_line and 'Unauthorized' in next_line:
            # Check if line after that assigns driver_id from session
            after_line = lines[i+2] if i+2 < len(lines) else ''
            if "driver_id = session['user_id']" in after_line:
                new_lines.append(f"{spaces}driver_id, err = _require_driver()\n")
                new_lines.append(f"{spaces}if err: return err\n")
                i += 3  # skip the 3 lines
                changes += 1
                continue
            else:
                new_lines.append(f"{spaces}driver_id, err = _require_driver()\n")
                new_lines.append(f"{spaces}if err: return err\n")
                i += 2  # skip the 2 lines
                changes += 1
                continue
    
    # Pattern: session check for passenger (indented with 8 spaces)
    if ("if 'user_id' not in session or session.get('user_type') != 'passenger':" in line and
            i+1 < len(lines) and 'return jsonify' in lines[i+1]):
        indent = len(line) - len(line.lstrip())
        spaces = ' ' * indent
        next_line = lines[i+1]
        if 'Unauthorized' in next_line:
            after_line = lines[i+2] if i+2 < len(lines) else ''
            if "passenger_id = session['user_id']" in after_line:
                new_lines.append(f"{spaces}passenger_id, err = _require_passenger()\n")
                new_lines.append(f"{spaces}if err: return err\n")
                i += 3
                changes += 1
                continue
            else:
                new_lines.append(f"{spaces}passenger_id, err = _require_passenger()\n")
                new_lines.append(f"{spaces}if err: return err\n")
                i += 2
                changes += 1
                continue
    
    # Pattern: top-level (4 spaces) driver check
    if ("if 'user_id' not in session or session.get('user_type') != 'driver':" in line and
            i+1 < len(lines) and 'return jsonify' in lines[i+1]):
        indent = len(line) - len(line.lstrip())
        spaces = ' ' * indent
        next_line = lines[i+1]
        if 'Unauthorized' in next_line:
            after_line = lines[i+2] if i+2 < len(lines) else ''
            if "owner_id = session['user_id']" in after_line or "driver_id = session['user_id']" in after_line or "renter_id = session['user_id']" in after_line or "uploader_id = session['user_id']" in after_line:
                new_lines.append(f"{spaces}driver_id, err = _require_driver()\n")
                new_lines.append(f"{spaces}if err: return err\n")
                i += 3
                changes += 1
                continue
            else:
                new_lines.append(f"{spaces}driver_id, err = _require_driver()\n")
                new_lines.append(f"{spaces}if err: return err\n")
                i += 2
                changes += 1
                continue
    
    new_lines.append(line)
    i += 1

# Fix remaining session['user_id'] references that should use driver_id/passenger_id
content = ''.join(new_lines)

# Fix specific patterns where session['user_id'] is used after our new auth check
# These are cases where the variable name changed
import re

# Fix owner_id = session['user_id'] -> owner_id = driver_id (after _require_driver)
# Fix renter_id = session['user_id'] -> renter_id = driver_id
# Fix uploader_id = session['user_id'] -> uploader_id = driver_id

with open('app_enhanced.py', 'w', encoding='utf-8') as f:
    f.write(content)

print(f"Fixed {changes} auth check patterns")

# Count remaining
remaining_driver = content.count("if 'user_id' not in session or session.get('user_type') != 'driver'")
remaining_passenger = content.count("if 'user_id' not in session or session.get('user_type') != 'passenger'")
remaining_generic = content.count("if 'user_id' not in session\n")
print(f"Remaining driver checks: {remaining_driver}")
print(f"Remaining passenger checks: {remaining_passenger}")
print(f"Remaining generic checks: {remaining_generic}")

# Show lines
for i, line in enumerate(content.split('\n'), 1):
    if "if 'user_id' not in session" in line and '#' not in line:
        print(f"  Line {i}: {line.strip()}")
