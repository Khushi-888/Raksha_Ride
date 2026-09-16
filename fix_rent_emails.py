content = open('app_enhanced.py', encoding='utf-8').read()

# Find and replace send_owner_approval_email
start = content.find('def send_owner_approval_email(')
if start == -1:
    print("Not found!")
    exit()

next_func = content.find('\ndef ', start + 50)
old_func = content[start:next_func]
print(f"Found send_owner_approval_email, length: {len(old_func)}")

new_func = '''def send_owner_approval_email(owner_email, renter_name, vehicle_details, token):
    """Send approval request to owner — uses Brevo via send_email_async (non-blocking)."""
    approval_url = f"{BASE_URL}/owner_confirm?token={token}"
    subject = "RakshaRide — Driver Authorization Request"
    html = (
        "<div style='font-family:Arial,sans-serif;max-width:600px;margin:0 auto'>"
        "<div style='background:linear-gradient(135deg,#1565C0,#FFC107);padding:24px;border-radius:12px 12px 0 0;text-align:center'>"
        "<h1 style='color:white;margin:0'>RakshaRide</h1>"
        "<p style='color:rgba(255,255,255,0.9);margin:6px 0 0'>Vehicle Owner Action Required</p>"
        "</div>"
        "<div style='background:#fff;border:1px solid #e0e0e0;padding:28px;border-radius:0 0 12px 12px'>"
        "<h2 style='color:#1565C0'>Driver Authorization Request</h2>"
        "<p>Dear Vehicle Owner,</p>"
        f"<p>Driver <strong>{renter_name}</strong> wants to operate your vehicle <strong>{vehicle_details}</strong> on RakshaRide.</p>"
        "<div style='background:#f5f5f5;border-radius:10px;padding:16px;margin:20px 0'>"
        f"<p style='margin:0'><strong>Driver:</strong> {renter_name}</p>"
        f"<p style='margin:8px 0 0'><strong>Vehicle:</strong> {vehicle_details}</p>"
        "</div>"
        "<div style='text-align:center;margin:24px 0'>"
        f"<a href='{approval_url}' style='background:#1565C0;color:white;padding:14px 32px;"
        "text-decoration:none;border-radius:8px;font-weight:bold;font-size:16px;display:inline-block'>"
        "Review &amp; Approve Request</a>"
        "</div>"
        "<p style='color:#666;font-size:13px'>If you did not expect this, please ignore this email.</p>"
        "</div></div>"
    )
    plain = f"Driver {renter_name} wants to use your vehicle ({vehicle_details}). Approve: {approval_url}"
    send_email_async(owner_email, subject, html, plain)
    print(f"[OWNER EMAIL] Queued for {owner_email}")
    return True

'''

content = content[:start] + new_func + content[next_func:]

# Also fix the owner_confirm_action emails to use send_email_async properly
# Find and fix the renter approval notification
old_renter_email = '''            send_email_async(
                renter_email,
                "RakshaRide - Owner Approved Your Request",
                f"""<h2>Great News!</h2>'''

if old_renter_email in content:
    print("Found renter approval email - already using send_email_async")
else:
    print("Renter approval email pattern not found - checking...")
    idx = content.find('Owner Approved Your Request')
    if idx != -1:
        print("Found at:", idx)
        print(repr(content[max(0,idx-200):idx+200]))

open('app_enhanced.py', 'w', encoding='utf-8').write(content)
print("Done!")
