content = open('app_enhanced.py', encoding='utf-8').read()

# Find the second (broken) _send_credentials_email function
idx = content.find('def _send_credentials_email(email, name, unique_id, password):\n    """Notify driver of their official login credentials via Flask-Mail"""')
if idx == -1:
    print("Second _send_credentials_email not found")
else:
    next_func = content.find('\ndef ', idx + 50)
    old_func = content[idx:next_func]
    print(f"Found broken _send_credentials_email, length: {len(old_func)}")

    new_func = '''def _send_credentials_email(email, name, unique_id, password):
    """Send driver login credentials via Brevo (non-blocking)."""
    subject = "RakshaRide — Your Account is Approved!"
    html = (
        "<div style='font-family:Arial,sans-serif;max-width:600px;margin:0 auto'>"
        "<div style='background:linear-gradient(135deg,#2E7D32,#FFC107);padding:24px;border-radius:12px 12px 0 0;text-align:center'>"
        "<h1 style='color:white;margin:0'>RakshaRide</h1>"
        "<p style='color:rgba(255,255,255,0.9);margin:6px 0 0'>Account Approved!</p>"
        "</div>"
        "<div style='background:#fff;border:1px solid #e0e0e0;padding:28px;border-radius:0 0 12px 12px'>"
        f"<h2 style='color:#2E7D32'>Welcome, {name}!</h2>"
        "<p>Your RakshaRide driver account has been verified and approved.</p>"
        "<div style='background:#f5f5f5;border-radius:10px;padding:20px;margin:20px 0'>"
        "<h3 style='margin:0 0 12px;color:#1565C0'>Your Login Credentials</h3>"
        f"<p style='margin:6px 0'><strong>User ID:</strong> <code style='background:#e3f2fd;padding:4px 8px;border-radius:4px'>{unique_id}</code></p>"
        f"<p style='margin:6px 0'><strong>Password:</strong> <code style='background:#e3f2fd;padding:4px 8px;border-radius:4px'>{password}</code></p>"
        "</div>"
        f"<div style='text-align:center;margin:24px 0'>"
        f"<a href='{BASE_URL}/login/driver' style='background:#1565C0;color:white;padding:14px 32px;"
        "text-decoration:none;border-radius:8px;font-weight:bold;font-size:16px;display:inline-block'>"
        "Login to Dashboard</a>"
        "</div>"
        "<p style='color:#C62828;font-size:13px'><strong>Important:</strong> Change your password after first login.</p>"
        "</div></div>"
    )
    plain = f"Your RakshaRide credentials — User ID: {unique_id} | Password: {password} | Login: {BASE_URL}/login/driver"
    send_email_async(email, subject, html, plain)
    print(f"[CREDENTIALS EMAIL] Queued for {email}")
    return True

'''
    content = content[:idx] + new_func + content[next_func:]
    print("Fixed _send_credentials_email!")

# Fix _send_owner_creds_notification
idx2 = content.find('def _send_owner_creds_notification(owner_email, owner_name, renter_name, unique_id):')
if idx2 != -1:
    next_func2 = content.find('\ndef ', idx2 + 50)
    old_func2 = content[idx2:next_func2]
    print(f"Found _send_owner_creds_notification, length: {len(old_func2)}")

    new_func2 = '''def _send_owner_creds_notification(owner_email, owner_name, renter_name, unique_id):
    """Notify owner that their renter is verified — uses Brevo."""
    subject = f"RakshaRide — Renter {renter_name} Account Activated"
    html = (
        "<div style='font-family:Arial,sans-serif;max-width:600px;margin:0 auto'>"
        "<div style='background:linear-gradient(135deg,#1565C0,#FFC107);padding:24px;border-radius:12px 12px 0 0;text-align:center'>"
        "<h1 style='color:white;margin:0'>RakshaRide</h1>"
        "</div>"
        "<div style='background:#fff;border:1px solid #e0e0e0;padding:28px;border-radius:0 0 12px 12px'>"
        f"<h2 style='color:#1565C0'>Renter Account Activated</h2>"
        f"<p>Dear {owner_name},</p>"
        f"<p>Your renter <strong>{renter_name}</strong> has been verified and is now active on RakshaRide.</p>"
        "<div style='background:#f5f5f5;border-radius:10px;padding:16px;margin:20px 0'>"
        f"<p style='margin:0'><strong>Renter:</strong> {renter_name}</p>"
        f"<p style='margin:8px 0 0'><strong>Renter ID:</strong> {unique_id}</p>"
        "</div>"
        "<p>They are now authorized to provide rides using your vehicle.</p>"
        "</div></div>"
    )
    plain = f"Your renter {renter_name} (ID: {unique_id}) is now verified on RakshaRide."
    send_email_async(owner_email, subject, html, plain)
    print(f"[OWNER CREDS EMAIL] Queued for {owner_email}")

'''
    content = content[:idx2] + new_func2 + content[next_func2:]
    print("Fixed _send_owner_creds_notification!")

open('app_enhanced.py', 'w', encoding='utf-8').write(content)
print("Done!")
