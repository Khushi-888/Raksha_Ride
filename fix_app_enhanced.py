import os
import re

file_path = "app_enhanced.py"

with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

# 1. Imports and Flask-Mail Init
config_old = """app = Flask(__name__)
app.secret_key = 'raksha-ride-enhanced-secret-key-2024'
CORS(app)

# Gmail Configuration (Official Secure Portal)
GMAIL_EMAIL = "riksharide2026@gmail.com"  # ✅ CONFIRMED WORKING
GMAIL_APP_PASSWORD = "evsz tunv eoqi lawu"  # ✅ CONFIRMED PASSCODE
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587"""

config_new = """from flask_mail import Mail, Message
import os

app = Flask(__name__)
app.secret_key = 'raksha-ride-enhanced-secret-key-2024'
CORS(app)

# Gmail Configuration (Official Secure Portal)
GMAIL_EMAIL = "riksharide2026@gmail.com"  # ✅ CONFIRMED WORKING
GMAIL_APP_PASSWORD = "evsz tunv eoqi lawu"  # ✅ CONFIRMED PASSCODE
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587

app.config['MAIL_SERVER'] = SMTP_SERVER
app.config['MAIL_PORT'] = SMTP_PORT
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = GMAIL_EMAIL
app.config['MAIL_PASSWORD'] = GMAIL_APP_PASSWORD.replace(' ', '').replace('-', '')
app.config['MAIL_DEFAULT_SENDER'] = f"RakshaRide <{GMAIL_EMAIL}>"

mail = Mail(app)

def send_email_async(to_email, subject, body):
    try:
        msg = Message(subject=subject, recipients=[to_email])
        msg.html = body
        mail.send(msg)
        print(f"✅ Email sent to {to_email}")
    except Exception as e:
        print(f"❌ Email sending failed: {e}")
"""

content = content.replace(config_old, config_new)

# 2. Fix verification_status logic in register_driver_v2
status_old = "verification_status = 'pending' if role == 'OWNER' else 'pending_owner_approval'"
status_new = "verification_status = 'pending'"
content = content.replace(status_old, status_new)

# 3. Fix upload driver docs
upload_old = """        # Save documents
        for doc_type, base64_data in documents.items():
            encrypted_data = encrypt_document(base64_data)
            c.execute(\"\"\"INSERT INTO driver_documents (driver_id, uploaded_by, doc_type, file_data) 
                         VALUES (?, ?, ?, ?)\"\"\", 
                      (driver_id, uploader_id, doc_type, encrypted_data))

        # ── STATUS UPDATES & CREDENTIALS ──
        # Update Renter/Driver status
        c.execute("UPDATE drivers SET verification_status = 'under_verification' WHERE id = ?", (driver_id,))
        
        # Get driver info for credential delivery
        c.execute("SELECT * FROM drivers WHERE id = ?", (driver_id,))
        driver = c.fetchone()
        
        # AS PER REQUEST: ONLY generate credentials after proper approval/upload
        # In a real system, this might wait for Admin, but the prompt says 
        # "After document upload: Update owner.status = verified, renter.status = approved"
        # and "Generate user_id and password for renter".
        
        raw_password = secrets.token_urlsafe(10)
        hashed_pw = hash_password(raw_password)
        new_unique_id = f"DRV{driver['id']:04d}"

        c.execute(\"\"\"UPDATE drivers 
                     SET verification_status = 'verified', 
                         unique_id = ?, 
                         password = ?,
                         first_login = 1 
                     WHERE id = ?\"\"\", (new_unique_id, hashed_pw, driver_id))

        # If it was an owner-renter flow, update the owner's status too
        if token and driver['owner_id']:
            c.execute("UPDATE drivers SET verification_status = 'verified' WHERE id = ?", (driver['owner_id'],))

        conn.commit()
        conn.close()

        # Send official credentials email
        _send_credentials_email(driver['email'], driver['name'], new_unique_id, raw_password)"""

upload_new = """        # Get driver info
        c.execute("SELECT * FROM drivers WHERE id = ?", (driver_id,))
        driver = c.fetchone()

        # Save documents to server folder
        upload_dir = os.path.join('static', 'uploads')
        os.makedirs(upload_dir, exist_ok=True)

        for doc_type, base64_data in documents.items():
            try:
                if 'base64,' in base64_data:
                    b64_str = base64_data.split('base64,')[1]
                else:
                    b64_str = base64_data
                    
                ext = 'jpg'
                if base64_data.startswith('data:image/png'): ext = 'png'
                elif base64_data.startswith('data:application/pdf'): ext = 'pdf'
                
                filename = f"driver_{driver_id}_{doc_type}_{secrets.token_hex(4)}.{ext}"
                filepath = os.path.join(upload_dir, filename)
                
                with open(filepath, 'wb') as f:
                    f.write(base64.b64decode(b64_str))
                    
                c.execute(\"\"\"INSERT INTO driver_documents (driver_id, uploaded_by, doc_type, file_data) 
                             VALUES (?, ?, ?, ?)\"\"\", 
                          (driver_id, uploader_id, doc_type, filepath))
            except Exception as e:
                print(f"Warning: Could not save file to disk, falling back to db. {e}")
                # Fallback to older method if parsing fails
                encrypted_data = encrypt_document(base64_data)
                c.execute(\"\"\"INSERT INTO driver_documents (driver_id, uploaded_by, doc_type, file_data) 
                             VALUES (?, ?, ?, ?)\"\"\", 
                          (driver_id, uploader_id, doc_type, encrypted_data))

        # ── STATUS UPDATES & CREDENTIALS ──
        # Update owner and renter status
        if token and driver['owner_id']:
            c.execute("UPDATE drivers SET verification_status = 'approved' WHERE id = ?", (driver_id,))
            c.execute("UPDATE drivers SET verification_status = 'verified' WHERE id = ?", (driver['owner_id'],))
        else:
            c.execute("UPDATE drivers SET verification_status = 'verified' WHERE id = ?", (driver_id,))

        raw_password = secrets.token_urlsafe(10)
        hashed_pw = hash_password(raw_password)
        new_unique_id = f"DRV{driver['id']:04d}"

        c.execute(\"\"\"UPDATE drivers 
                     SET unique_id = ?, 
                         password = ?,
                         first_login = 1 
                     WHERE id = ?\"\"\", (new_unique_id, hashed_pw, driver_id))

        conn.commit()
        conn.close()

        # Send official credentials email
        _send_credentials_email(driver['email'], driver['name'], new_unique_id, raw_password)"""

content = content.replace(upload_old, upload_new)

# 4. send_owner_approval_email replace
owner_email_old = """def send_owner_approval_email(owner_email, renter_name, vehicle_details, token):
    \"\"\"Send approval request to the vehicle owner\"\"\"
    approval_url = f"http://localhost:5000/owner/approve/{token}"
    
    subject = "RakshaRide - Vehicle Owner Approval Required"
    body = f\"\"\"
    <h2>Action Required: Driver Authorization Request</h2>
    <p>Dear Vehicle Owner,</p>
    <p>A driver, <b>{renter_name}</b>, has requested authorization to operate your vehicle (<b>{vehicle_details}</b>) on the RakshaRide platform.</p>
    
    <p>As per our safety protocols, please review and approve this request by clicking the link below:</p>
    
    <div style="margin: 20px 0;">
        <a href="{approval_url}" style="background-color: #003366; color: white; padding: 12px 25px; text-decoration: none; border-radius: 5px;">Review & Approve Request</a>
    </div>
    
    <p>If you did not authorize this, please ignore this email or report it to our security team.</p>
    
    <p>Best regards,<br>RakshaRide Governance Team</p>
    \"\"\"
    
    msg = MIMEMultipart('alternative')
    msg['From'] = f"RakshaRide Security <{GMAIL_EMAIL}>"
    msg['To'] = owner_email
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'html'))
    
    # Send asynchronously to prevent UI lag
    thread = threading.Thread(target=_deliver_email, args=(msg,))
    thread.daemon = True
    thread.start()"""

owner_email_new = """def send_owner_approval_email(owner_email, renter_name, vehicle_details, token):
    \"\"\"Send approval request to the vehicle owner using Flask-Mail\"\"\"
    approval_url = f"http://localhost:5000/owner/approve/{token}"
    
    subject = "RakshaRide - Vehicle Owner Approval Required"
    body = f\"\"\"
    <h2>Action Required: Driver Authorization Request</h2>
    <p>Dear Vehicle Owner,</p>
    <p>A driver, <b>{renter_name}</b>, has requested authorization to operate your vehicle (<b>{vehicle_details}</b>) on the RakshaRide platform.</p>
    
    <p>As per our safety protocols, please review and approve this request by clicking the link below:</p>
    
    <div style="margin: 20px 0;">
        <a href="{approval_url}" style="background-color: #003366; color: white; padding: 12px 25px; text-decoration: none; border-radius: 5px;">Review & Approve Request</a>
    </div>
    
    <p>If you did not authorize this, please ignore this email or report it to our security team.</p>
    
    <p>Best regards,<br>RakshaRide Governance Team</p>
    \"\"\"
    
    try:
        msg = Message(subject=subject, recipients=[owner_email])
        msg.html = body
        mail.send(msg)
        print(f"✅ Owner approval email sent to {owner_email}")
        return True
    except Exception as e:
        print(f"❌ Critical Email System Failure: {str(e)}")
        return False"""

content = content.replace(owner_email_old, owner_email_new)

# 5. Fix _send_credentials_email
cred_email_old = """def _send_credentials_email(email, name, unique_id, password):
    \"\"\"Notify driver of their official login credentials\"\"\"
    subject = "RakshaRide Account Approved - Official Credentials"
    body = f\"\"\"Dear {name},
    
Your RakshaRide driver account has been successfully verified!

Please use the following official credentials to log in:

User ID: {unique_id}
Temporary Password: {password}

Portal: http://localhost:5000/login/driver

⚠️ IMPORTANT: For your security, you will be required to change this password during your first login.

Safe Riding!
RakshaRide Team
\"\"\"
    msg = MIMEMultipart()
    msg['From'] = f'RakshaRide Admin <{GMAIL_EMAIL}>'
    msg['To'] = email
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain'))
    
    _deliver_email(msg)"""

cred_email_new = """def _send_credentials_email(email, name, unique_id, password):
    \"\"\"Notify driver of their official login credentials via Flask-Mail\"\"\"
    subject = "RakshaRide Account Approved - Official Credentials"
    body = f\"\"\"Dear {name},
    
Your RakshaRide driver account has been successfully verified!

Please use the following official credentials to log in:

User ID: {unique_id}
Temporary Password: {password}

Portal: http://localhost:5000/login/driver

⚠️ IMPORTANT: For your security, you will be required to change this password during your first login.

Safe Riding!
RakshaRide Team
\"\"\"
    try:
        msg = Message(subject=subject, recipients=[email], body=body)
        mail.send(msg)
        print(f"✅ Credentials email sent to {email}")
        return True
    except Exception as e:
        print(f"❌ Critical Email System Failure: {str(e)}")
        return False"""

content = content.replace(cred_email_old, cred_email_new)

# 6. Fix _send_owner_creds_notification
owner_cred_notif_old = """def _send_owner_creds_notification(owner_email, owner_name, renter_name, unique_id):
    \"\"\"Notify owner that their renter's account is verified and active\"\"\"
    subject = f"RakshaRide: Renter ({renter_name}) Account Activated"
    body = f\"\"\"Dear {owner_name},
    
This is to inform you that the driver account for your renter, {renter_name}, has been verified and activated on RakshaRide.

Renter ID: {unique_id}

They are now authorized to provide rides using your vehicle.

Thank you,
RakshaRide Team
\"\"\"
    msg = MIMEMultipart()
    msg['From'] = f'RakshaRide Admin <{GMAIL_EMAIL}>'
    msg['To'] = owner_email
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain'))
    
    _deliver_email(msg)"""

owner_cred_notif_new = """def _send_owner_creds_notification(owner_email, owner_name, renter_name, unique_id):
    \"\"\"Notify owner that their renter's account is verified and active\"\"\"
    subject = f"RakshaRide: Renter ({renter_name}) Account Activated"
    body = f\"\"\"Dear {owner_name},
    
This is to inform you that the driver account for your renter, {renter_name}, has been verified and activated on RakshaRide.

Renter ID: {unique_id}

They are now authorized to provide rides using your vehicle.

Thank you,
RakshaRide Team
\"\"\"
    try:
        msg = Message(subject=subject, recipients=[owner_email], body=body)
        mail.send(msg)
    except Exception as e:
        print(f"❌ Error sending owner creds notification: {str(e)}")"""

content = content.replace(owner_cred_notif_old, owner_cred_notif_new)

with open(file_path, "w", encoding="utf-8") as f:
    f.write(content)

print("Replacement script executed successfully.")
