import re
content = open('app_enhanced.py', encoding='utf-8').read()

# Find and replace send_email_async
idx = content.find('def send_email_async(to_email, subject, body):')
end_idx = content.find('\n\n', idx + 50)

old_func = content[idx:end_idx]
new_func = '''def send_email_async(to_email, subject, body):
    """Send email in background thread — never blocks the request."""
    import threading as _t
    def _send():
        try:
            with app.app_context():
                msg = Message(subject=subject, recipients=[to_email])
                msg.html = body
                mail.send(msg)
                print(f"[OK] Email sent to {to_email}")
        except Exception as e:
            print(f"[WARN] Email failed to {to_email}: {e}")
    _t.Thread(target=_send, daemon=True).start()'''

content = content.replace(old_func, new_func, 1)
open('app_enhanced.py', 'w', encoding='utf-8').write(content)
print("Done — send_email_async is now non-blocking")
