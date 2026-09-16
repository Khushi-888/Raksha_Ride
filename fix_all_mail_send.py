"""Replace all mail.send() calls with _smtp_send() calls"""
import re
content = open('app_enhanced.py', encoding='utf-8').read()

# Fix 1: send_email_async — already fixed by fix_email_async.py
# Fix 2: send_owner_approval_email
# Fix 3: _send_credentials_email  
# Fix 4: _send_owner_creds_notification

# Find all functions that use mail.send and replace them
replacements = [
    # send_owner_approval_email
    (
        "        msg = Message(subject=subject, recipients=[owner_email])\n        msg.html = body\n        mail.send(msg)\n        print(f",
        "        ok = _smtp_send(owner_email, subject, body)\n        print(f"
    ),
]

for old, new in replacements:
    if old in content:
        content = content.replace(old, new, 1)
        print(f"Fixed: {old[:50]}...")
    else:
        print(f"NOT FOUND: {old[:50]}...")

# More targeted: replace all remaining mail.send(msg) patterns
# by wrapping them with _smtp_send
count = content.count('mail.send(msg)')
print(f"Remaining mail.send(msg) calls: {count}")

# Replace each occurrence with a safe wrapper
# Pattern: find the Message() setup before each mail.send and replace
import re

# Replace the simple pattern: msg = Message(...); msg.html = body; mail.send(msg)
def replace_mail_send(match):
    return match.group(0).replace('mail.send(msg)', 
        '_smtp_send(msg["To"] if hasattr(msg, "__getitem__") else str(msg.recipients[0]), msg.subject, msg.html or "", msg.body or "")')

# Actually, simpler: just wrap mail.send in try/except that falls back to _smtp_send
old_pattern = 'mail.send(msg)'
new_pattern = '''(lambda: (mail.send(msg) if mail else None) or True)()'''

# Even simpler — just replace mail.send with a safe call
content = content.replace(
    'mail.send(msg)\n        print(f"✅ Owner approval email sent',
    '_smtp_send(owner_email, subject, body)\n        print(f"[OK] Owner approval email sent'
)

# For credentials emails, use send_email_async
content = content.replace(
    'mail.send(msg)\n        print(f"✅ Credentials ema',
    'send_email_async(email, subject, body)\n        print(f"[OK] Credentials ema'
)
content = content.replace(
    'mail.send(msg)\n    except Exception as e:\n        ',
    'send_email_async(owner_email, subject, body)\n    except Exception as e:\n        '
)

# Fix the send_email_async internal mail.send
content = content.replace(
    'mail.send(msg)\n                print(f"[OK] Email',
    '_smtp_send(to_email, subject, body)\n                print(f"[OK] Email'
)

remaining = content.count('mail.send(msg)')
print(f"Remaining after fixes: {remaining}")

open('app_enhanced.py', 'w', encoding='utf-8').write(content)
print("Done!")
