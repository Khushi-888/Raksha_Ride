content = open('app_enhanced.py', encoding='utf-8').read()

# Find login_passenger function
start = content.find("@app.route('/api/login_passenger', methods=['POST'])")
if start == -1:
    print("Not found!")
    exit()

# Find next route
next_route = content.find('\n@app.route', start + 50)
old_func = content[start:next_route]
print(f"Found login_passenger, length: {len(old_func)}")

new_func = '''@app.route('/api/login_passenger', methods=['POST'])
def login_passenger():
    """Passenger login — non-blocking OTP send."""
    try:
        data = request.get_json() or {}
        credential = (data.get('credential') or data.get('email') or '').strip()
        password   = (data.get('password') or '').strip()

        if not credential or not password:
            return jsonify({"success": False, "message": "Email and password required"}), 400

        hashed_password = hash_password(password)
        conn = get_db_conn()
        c = conn.cursor()
        c.execute("""SELECT id, name, email, phone FROM passengers
                     WHERE (email = ? OR phone = ?) AND password = ?""",
                  (credential, credential, hashed_password))
        result = c.fetchone()

        if not result:
            conn.close()
            return jsonify({"success": False, "message": "Invalid email/phone or password"}), 401

        user_id, name, email, phone = result

        otp = generate_otp()
        expiry_time = datetime.now() + timedelta(minutes=5)
        c.execute("DELETE FROM otp_verification WHERE email = ?", (email,))
        c.execute("INSERT INTO otp_verification (email, otp, expiry_time, attempts) VALUES (?, ?, ?, 0)",
                  (email, otp, expiry_time))
        conn.commit()
        conn.close()

        html = (
            "<div style='font-family:Arial;padding:20px'>"
            "<h2 style='color:#1565C0'>RakshaRide Login OTP</h2>"
            "<p>Your login verification code:</p>"
            "<div style='font-size:36px;font-weight:900;letter-spacing:10px;color:#FFC107;"
            "padding:20px;background:#f5f5f5;border-radius:10px;text-align:center'>"
            + otp +
            "</div>"
            "<p style='color:#666;margin-top:16px'>Valid for <strong>5 minutes</strong>.</p>"
            "</div>"
        )
        send_email_async(email, "RakshaRide Login OTP", html, f"Login OTP: {otp}")
        print(f"[LOGIN OTP] {email}: {otp}")

        return jsonify({
            "success": True,
            "requires_otp": True,
            "email": email,
            "message": f"Verification code sent to {email}. Check your inbox.",
            "email_sent": True
        })

    except Exception as e:
        print(f"[login_passenger ERROR] {e}")
        return jsonify({"success": False, "message": "An internal error occurred. Please try again."}), 500

'''

content = content[:start] + new_func + content[next_route:]
open('app_enhanced.py', 'w', encoding='utf-8').write(content)
print("Fixed login_passenger!")
