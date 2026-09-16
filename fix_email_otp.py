content = open('app_enhanced.py', encoding='utf-8').read()

# Find and replace send_email_otp function
idx = content.find('def send_email_otp(to_email, otp):')
if idx == -1:
    print("send_email_otp not found!")
    exit()

# Find end of function
depth = 0
i = idx
while i < len(content):
    if content[i] == '{': depth += 1
    elif content[i] == '}': depth -= 1
    # Find the next def or end of function by looking for blank line after return
    if i > idx + 50 and content[i:i+8] == '\n\n\ndef ' or content[i:i+7] == '\n\ndef ':
        func_end = i
        break
    i += 1
else:
    func_end = len(content)

old_func = content[idx:func_end]
print(f"Found send_email_otp, length: {len(old_func)}")

new_func = '''def send_email_otp(to_email, otp):
    """Send OTP email via direct SMTP — works on Render."""
    subject = "RakshaRide — Your Verification Code"
    html_body = f"""
    <div style="font-family:Arial,sans-serif;max-width:500px;margin:0 auto;padding:20px">
      <div style="background:linear-gradient(135deg,#FFC107,#1565C0);padding:20px;border-radius:12px 12px 0 0;text-align:center">
        <h1 style="color:white;margin:0">RakshaRide</h1>
        <p style="color:rgba(255,255,255,0.9);margin:5px 0 0">Verification Code</p>
      </div>
      <div style="background:#fff;border:1px solid #e0e0e0;padding:30px;border-radius:0 0 12px 12px">
        <p style="color:#333;font-size:16px">Your one-time verification code is:</p>
        <div style="background:#f5f5f5;border:2px dashed #FFC107;border-radius:10px;padding:20px;text-align:center;margin:20px 0">
          <span style="font-size:36px;font-weight:900;letter-spacing:10px;color:#1565C0">{otp}</span>
        </div>
        <p style="color:#666;font-size:14px">Valid for <strong>5 minutes</strong> only.</p>
        <p style="color:#666;font-size:14px">Never share this code with anyone.</p>
      </div>
    </div>"""
    plain_body = f"Your RakshaRide OTP is: {otp}\\nValid for 5 minutes. Do not share."
    success = _smtp_send(to_email, subject, html_body, plain_body)
    if success:
        return True, "OTP sent successfully"
    else:
        print(f"[OTP FALLBACK] Email failed. OTP for {to_email}: {otp}")
        return False, f"Email delivery failed. Dev OTP: {otp}"

'''

content = content[:idx] + new_func + content[func_end:]
open('app_enhanced.py', 'w', encoding='utf-8').write(content)
print("Done!")
