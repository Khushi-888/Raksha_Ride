content = open('app_enhanced.py', encoding='utf-8').read()

# Find send_email_otp function
start = content.find('def send_email_otp(to_email, otp):')
if start == -1:
    print("ERROR: send_email_otp not found")
    exit()

# Find the next function definition after it
next_func = content.find('\ndef ', start + 10)
old_func = content[start:next_func]
print(f"Found send_email_otp, length: {len(old_func)}")

new_func = '''def send_email_otp(to_email, otp):
    """Send OTP via direct SMTP — works on Render."""
    subject = "RakshaRide — Your Verification Code"
    html_body = (
        "<div style='font-family:Arial,sans-serif;max-width:500px;margin:0 auto'>"
        "<div style='background:linear-gradient(135deg,#FFC107,#1565C0);padding:20px;border-radius:12px 12px 0 0;text-align:center'>"
        "<h1 style='color:white;margin:0'>RakshaRide</h1>"
        "<p style='color:rgba(255,255,255,0.9);margin:5px 0 0'>Verification Code</p>"
        "</div>"
        "<div style='background:#fff;border:1px solid #e0e0e0;padding:30px;border-radius:0 0 12px 12px'>"
        "<p style='color:#333;font-size:16px'>Your one-time verification code is:</p>"
        "<div style='background:#f5f5f5;border:2px dashed #FFC107;border-radius:10px;padding:20px;text-align:center;margin:20px 0'>"
        f"<span style='font-size:36px;font-weight:900;letter-spacing:10px;color:#1565C0'>{otp}</span>"
        "</div>"
        "<p style='color:#666;font-size:14px'>Valid for <strong>5 minutes</strong> only.</p>"
        "<p style='color:#666;font-size:14px'>Never share this code with anyone.</p>"
        "</div></div>"
    )
    plain = f"Your RakshaRide OTP is: {otp}\\nValid for 5 minutes. Do not share."
    ok = _smtp_send(to_email, subject, html_body, plain)
    if ok:
        return True, "OTP sent successfully"
    else:
        print(f"[OTP FALLBACK] Email failed. OTP for {to_email}: {otp}")
        return False, f"Email failed. Dev OTP: {otp}"

'''

content = content[:start] + new_func + content[next_func:]
open('app_enhanced.py', 'w', encoding='utf-8').write(content)
print("Fixed send_email_otp!")
