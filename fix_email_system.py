"""
Fix email system in app_enhanced.py:
1. Add _smtp_send helper after GMAIL config
2. Fix send_email_otp to use _smtp_send
3. Fix send_otp route to return dev_otp fallback
"""
content = open('app_enhanced.py', encoding='utf-8').read()

# ── 1. Add _smtp_send after mail = Mail(app) ─────────────────────────────────
SMTP_HELPER = '''
def _smtp_send(to_email, subject, html_body, plain_body=None):
    """Direct SMTP sender — works on Render. Falls back gracefully."""
    try:
        from email.mime.multipart import MIMEMultipart as _MM
        from email.mime.text import MIMEText as _MT
        import smtplib as _smtp
        clean_pw = GMAIL_APP_PASSWORD.replace(' ', '').replace('-', '')
        msg = _MM('alternative')
        msg['From'] = f"RakshaRide <{GMAIL_EMAIL}>"
        msg['To'] = to_email
        msg['Subject'] = subject
        msg.attach(_MT(plain_body or "View in HTML client.", 'plain'))
        msg.attach(_MT(html_body, 'html'))
        s = _smtp.SMTP("smtp.gmail.com", 587, timeout=25)
        s.ehlo(); s.starttls(); s.ehlo()
        s.login(GMAIL_EMAIL, clean_pw)
        s.sendmail(GMAIL_EMAIL, to_email, msg.as_string())
        s.quit()
        print(f"[EMAIL OK] {to_email}: {subject}")
        return True
    except Exception as e:
        print(f"[EMAIL FAIL] {to_email}: {e}")
        return False

'''

# Insert after mail = Mail(app) line
marker = 'mail = Mail(app)'
if marker in content and '_smtp_send' not in content:
    idx = content.find(marker) + len(marker)
    content = content[:idx] + '\n' + SMTP_HELPER + content[idx:]
    print("Added _smtp_send helper")
elif '_smtp_send' in content:
    print("_smtp_send already exists")
else:
    print("WARNING: mail = Mail(app) not found")

# ── 2. Fix send_otp route to return dev_otp on email failure ─────────────────
# Find the send_otp route and fix the failure response
old_failure = '''            return jsonify({
                "success": False, 
                "message": "Electronic delivery failed. Please ensure your email is correct and try again.",
                "email_sent": False
            }), 500'''

new_failure = '''            # Fallback: return OTP so user can still register
            print(f"[OTP FALLBACK] Email failed. OTP for {email}: {otp}")
            return jsonify({
                "success": True,
                "message": "Email delivery issue. Check server console for OTP.",
                "email_sent": False,
                "dev_otp": otp
            })'''

if old_failure in content:
    content = content.replace(old_failure, new_failure, 1)
    print("Fixed send_otp failure response")
else:
    print("send_otp failure pattern not found — checking alternate...")
    # Try to find and fix any 500 response in send_otp
    idx = content.find('/api/send_otp')
    if idx != -1:
        print(f"Found /api/send_otp at index {idx}")
        print("Context:", repr(content[idx:idx+500]))

open('app_enhanced.py', 'w', encoding='utf-8').write(content)
print("Done!")
