import os

file_path = "app_enhanced.py"

with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

# 1. Provide uuid import if not there
if "import uuid" not in content:
    content = content.replace("import sqlite3", "import sqlite3\nimport uuid")

# 2. Fix the duplicate checks logic
duplicate_check_old = """        # 4. Check for duplicates (using the requested error message)
        conn = sqlite3.connect('database_enhanced.db')
        c = conn.cursor()

        c.execute("SELECT id FROM drivers WHERE email = ?", (email,))
        if c.fetchone():
            conn.close()
            return jsonify({"success": False, "message": "Email already registered, please login"}), 400

        c.execute("SELECT id FROM drivers WHERE mobile = ?", (mobile,))
        if c.fetchone():
            conn.close()
            return jsonify({"success": False, "message": "Mobile number is already registered"}), 400

        # 5. Database Insertion"""

duplicate_check_new = """        # 4. Check for duplicates (using the requested error message)
        conn = sqlite3.connect('database_enhanced.db')
        c = conn.cursor()

        existing_driver_id = None
        c.execute("SELECT id FROM drivers WHERE email = ?", (email,))
        em_res = c.fetchone()
        
        c.execute("SELECT id FROM drivers WHERE mobile = ?", (mobile,))
        mob_res = c.fetchone()

        if em_res or mob_res:
            if role == 'RENT':
                # No "email already exists error" for renter. Reuse existing profile!
                existing_driver_id = em_res[0] if em_res else mob_res[0]
            else:
                conn.close()
                return jsonify({"success": False, "message": "Email or Mobile already registered"}), 400

        # 5. Database Insertion"""

content = content.replace(duplicate_check_old, duplicate_check_new)

# 3. Replace token generation
token_old = """        approval_token = secrets.token_urlsafe(32)"""
token_new = """        approval_token = uuid.uuid4().hex"""
content = content.replace(token_old, token_new)

# 4. Handle insertion where driver_id exists
insert_old = """        # Credentials are NOT generated here for RENTERS (only after approval)
        # We store a hashed random placeholder to satisfy NOT NULL if exists
        placeholder_pw = hash_password(secrets.token_urlsafe(12))
        unique_id = "PENDING_" + secrets.token_hex(4).upper()

        c.execute(\"\"\"INSERT INTO drivers
                     (name, age, mobile, email, vehicle_number, vehicle_type, rc_number,
                      password, unique_id, verification_status, role, owner_id, license_number, aadhaar_number)
                     VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)\"\"\",
                  (name, age, mobile, email, vehicle_number, vehicle_type, rc_number,
                   placeholder_pw, unique_id, verification_status, role, owner_id, license_number, aadhaar_number))
        conn.commit()
        driver_id = c.lastrowid"""

insert_new = """        # Credentials are NOT generated here for RENTERS (only after approval)
        placeholder_pw = hash_password(secrets.token_urlsafe(12))
        unique_id = "PENDING_" + secrets.token_hex(4).upper()

        if not existing_driver_id:
            c.execute(\"\"\"INSERT INTO drivers
                         (name, age, mobile, email, vehicle_number, vehicle_type, rc_number,
                          password, unique_id, verification_status, role, owner_id, license_number, aadhaar_number)
                         VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)\"\"\",
                      (name, age, mobile, email, vehicle_number, vehicle_type, rc_number,
                       placeholder_pw, unique_id, verification_status, role, owner_id, license_number, aadhaar_number))
            conn.commit()
            driver_id = c.lastrowid
        else:
            driver_id = existing_driver_id"""

content = content.replace(insert_old, insert_new)

# 5. Fix the BUG in owner_confirm_action
reject_old = """        else:
            c.execute("UPDATE renter_requests SET status = 'REJECTED' WHERE status = ?", (token,))"""

reject_new = """        else:
            c.execute("UPDATE renter_requests SET status = 'REJECTED' WHERE approval_token = ?", (token,))"""
            
content = content.replace(reject_old, reject_new)

with open(file_path, "w", encoding="utf-8") as f:
    f.write(content)

print("Patch applied to app_enhanced.py")
