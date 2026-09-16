content = open('app_enhanced.py', encoding='utf-8').read()

# Find the send_otp function
start = content.find('@app.route(\'/api/send_otp\', methods=[\'POST\'])')
if start == -1:
    print("Route not found!")
    exit()

# Find the next route after send_otp
next_route = content.find('\n@app.route', start + 50)
old_func = content[start:next_route]
print(f"Found send_otp, length: {len(old_func)}")

new_func = '''@app.route('/api/send_otp', methods=['POST'])
def send_otp():
    """Send OTP — saves to DB immediately, sends email in background (non-blocking)."""
    try:
        data = request.get_json() or {}
        email = data.get('email', '').strip()

        if not email or not is_valid_email(email):
            return jsonify({"success": False, "message": "Invalid email address"}), 400

        # Rate limit: max 3 per 60s per email
        if not rate_limit(f"otp_{email}", limit=3, window=60):
            return jsonify({"success": False, "message": "Too many requests. Wait 60 seconds."}), 429

        # Check already registered
        conn = get_db_conn()
        c = conn.cursor()
        c.execute("SELECT id FROM passengers WHERE email = ?", (email,))
        if c.fetchone():
            conn.close()
            return jsonify({"success": False, "message": "Email already registered. Please login."}), 400
        c.execute("SELECT id FROM drivers WHERE email = ?", (email,))
        if c.fetchone():
            conn.close()
            return jsonify({"success": False, "message": "Email already registered as driver. Please login."}), 400

        # Generate OTP and save to DB immediately
        otp = generate_otp()
        expiry_time = datetime.now() + timedelta(minutes=5)
        c.execute("DELETE FROM otp_verification WHERE email = ?", (email,))
        c.execute("INSERT INTO otp_verification (email, otp, expiry_time, attempts) VALUES (?, ?, ?, 0)",
                  (email, otp, expiry_time))
        conn.commit()
        conn.close()

        # Send email in background thread — response returns immediately
        html = (
            "<div style='font-family:Arial;padding:20px;max-width:500px'>"
            "<h2 style='color:#1565C0'>RakshaRide OTP</h2>"
            "<p>Your verification code is:</p>"
            "<div style='font-size:36px;font-weight:900;letter-spacing:10px;color:#FFC107;"
            "padding:20px;background:#f5f5f5;border-radius:10px;text-align:center'>"
            + otp +
            "</div>"
            "<p style='color:#666;margin-top:16px'>Valid for <strong>5 minutes</strong>. Do not share.</p>"
            "</div>"
        )
        send_email_async(email, "RakshaRide — Your OTP", html, f"Your OTP: {otp} (valid 5 min)")

        print(f"[OTP] Generated for {email}: {otp}")
        return jsonify({
            "success": True,
            "message": f"Verification code sent to {email}. Check your inbox and spam folder.",
            "email_sent": True
        })

    except Exception as e:
        print(f"[send_otp ERROR] {e}")
        return jsonify({"success": False, "message": "Server error. Please try again."}), 500

'''

content = content[:start] + new_func + content[next_route:]
open('app_enhanced.py', 'w', encoding='utf-8').write(content)
print("Fixed send_otp route!")
