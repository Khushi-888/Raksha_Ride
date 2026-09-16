content = open('app_enhanced.py', encoding='utf-8').read()

# Remove all dev_otp from responses
import re

# Pattern: find the block containing dev_otp and replace with secure version
old = '''"success": True,
                    "message": "Email delivery issue. Check server console for OTP.",
                    "email_sent": False,
                    "dev_otp": otp
                })
            conn.close()
            return jsonify({"success": False, "message": "Invalid email/phone or password"}), 401'''

new = '''"success": False,
                    "message": "Email delivery failed. Please check your spam folder or try again.",
                    "email_sent": False
                })
            conn.close()
            return jsonify({"success": False, "message": "Invalid email/phone or password"}), 401'''

if old in content:
    content = content.replace(old, new, 1)
    print("Fixed login dev_otp")
else:
    print("Pattern not found, trying line-based fix...")
    lines = content.split('\n')
    for i, line in enumerate(lines):
        if '"dev_otp": otp' in line:
            print(f"Found dev_otp at line {i+1}: {line}")
            # Replace the entire dev_otp line
            lines[i] = line.replace('"dev_otp": otp', '"email_sent": False  # OTP sent to server log only')
    content = '\n'.join(lines)

open('app_enhanced.py', 'w', encoding='utf-8').write(content)

# Verify no dev_otp remains
remaining = content.count('dev_otp')
print(f"Remaining dev_otp: {remaining}")
print("Done!")
