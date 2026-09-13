"""
Patch app_enhanced.py using line-number-based replacement.
Avoids encoding issues with em-dash characters in docstrings.
"""

with open('app_enhanced.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

total = len(lines)
changes = []

i = 0
while i < total:
    line = lines[i]
    stripped = line.rstrip('\n')

    # ── Pattern A: driver check inside try block (8-space indent) ────────────
    if (stripped.endswith("if 'user_id' not in session or session.get('user_type') != 'driver':") and
            stripped.startswith('        ')):
        indent = '        '
        # Next line should be the return jsonify
        if i+1 < total and 'return jsonify' in lines[i+1] and 'Unauthorized' in lines[i+1]:
            # Check what comes after (skip blank lines)
            j = i + 2
            while j < total and lines[j].strip() == '':
                j += 1
            after = lines[j].strip() if j < total else ''

            if "driver_id = session['user_id']" in after:
                new_lines = [
                    f"{indent}driver_id, err = _require_driver()\n",
                    f"{indent}if err: return err\n",
                ]
                # Replace lines i, i+1, blank lines, and the driver_id line
                end = j + 1
                changes.append((i, end, new_lines))
                i = end
                continue
            elif "owner_id = session['user_id']" in after:
                new_lines = [
                    f"{indent}driver_id, err = _require_driver()\n",
                    f"{indent}if err: return err\n",
                    f"{indent}owner_id = driver_id\n",
                ]
                end = j + 1
                changes.append((i, end, new_lines))
                i = end
                continue
            elif "renter_id = session['user_id']" in after:
                new_lines = [
                    f"{indent}driver_id, err = _require_driver()\n",
                    f"{indent}if err: return err\n",
                    f"{indent}renter_id = driver_id\n",
                ]
                end = j + 1
                changes.append((i, end, new_lines))
                i = end
                continue
            elif "uploader_id = session['user_id']" in after:
                new_lines = [
                    f"{indent}driver_id, err = _require_driver()\n",
                    f"{indent}if err: return err\n",
                    f"{indent}uploader_id = driver_id\n",
                ]
                end = j + 1
                changes.append((i, end, new_lines))
                i = end
                continue
            else:
                # No variable assignment — just replace the check
                new_lines = [
                    f"{indent}driver_id, err = _require_driver()\n",
                    f"{indent}if err: return err\n",
                ]
                end = i + 2
                changes.append((i, end, new_lines))
                i = end
                continue

    # ── Pattern B: passenger check inside try block (8-space indent) ─────────
    if (stripped.endswith("if 'user_id' not in session or session.get('user_type') != 'passenger':") and
            stripped.startswith('        ')):
        indent = '        '
        if i+1 < total and 'return jsonify' in lines[i+1] and 'Unauthorized' in lines[i+1]:
            j = i + 2
            while j < total and lines[j].strip() == '':
                j += 1
            after = lines[j].strip() if j < total else ''

            if "passenger_id = session['user_id']" in after:
                new_lines = [
                    f"{indent}passenger_id, err = _require_passenger()\n",
                    f"{indent}if err: return err\n",
                ]
                end = j + 1
                changes.append((i, end, new_lines))
                i = end
                continue
            else:
                new_lines = [
                    f"{indent}passenger_id, err = _require_passenger()\n",
                    f"{indent}if err: return err\n",
                ]
                end = i + 2
                changes.append((i, end, new_lines))
                i = end
                continue

    # ── Pattern C: driver check at function level (4-space indent) ───────────
    if (stripped.endswith("if 'user_id' not in session or session.get('user_type') != 'driver':") and
            stripped.startswith('    ') and not stripped.startswith('        ')):
        indent = '    '
        if i+1 < total and 'return jsonify' in lines[i+1] and 'Unauthorized' in lines[i+1]:
            j = i + 2
            while j < total and lines[j].strip() == '':
                j += 1
            after = lines[j].strip() if j < total else ''

            if "driver_id = session['user_id']" in after or "owner_id = session['user_id']" in after:
                var = 'owner_id' if "owner_id" in after else 'driver_id'
                new_lines = [
                    f"{indent}driver_id, err = _require_driver()\n",
                    f"{indent}if err: return err\n",
                ]
                if var == 'owner_id':
                    new_lines.append(f"{indent}owner_id = driver_id\n")
                end = j + 1
                changes.append((i, end, new_lines))
                i = end
                continue
            else:
                new_lines = [
                    f"{indent}driver_id, err = _require_driver()\n",
                    f"{indent}if err: return err\n",
                ]
                end = i + 2
                changes.append((i, end, new_lines))
                i = end
                continue

    i += 1

# Apply changes in reverse order (so line numbers stay valid)
for start, end, new_lines in reversed(changes):
    lines[start:end] = new_lines

print(f"Applied {len(changes)} patches")

with open('app_enhanced.py', 'w', encoding='utf-8') as f:
    f.writelines(lines)

# Report remaining
remaining = [(i+1, l.strip()) for i, l in enumerate(lines)
             if "if 'user_id' not in session" in l and not l.strip().startswith('#')]
print(f"Remaining session checks: {len(remaining)}")
for lineno, line in remaining:
    print(f"  Line {lineno}: {line}")
