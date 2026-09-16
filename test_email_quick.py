"""
Quick Email Test - Send OTP to Real Email
"""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Your working credentials
GMAIL_EMAIL = "riksharide2026@gmail.com"
GMAIL_APP_PASSWORD = "evsz tunv eoqi lawu"
TEST_EMAIL = "khushisaharan42@gmail.com"
TEST_OTP = "123456"

print("\n" + "="*60)
print("   Testing Email with Real Credentials")
print("="*60)
print(f"\nFrom: {GMAIL_EMAIL}")
print(f"To: {TEST_EMAIL}")
print(f"OTP: {TEST_OTP}")
print("\nSending email...\n")

try:
    # Create message
    message = MIMEMultipart()
    message["From"] = f"RakshaRide <{GMAIL_EMAIL}>"
    message["To"] = TEST_EMAIL
    message["Subject"] = "RakshaRide - Your OTP Code"
    
    body = f"""Hello!

Your RakshaRide OTP verification code is:

    {TEST_OTP}

This OTP is valid for 5 minutes.

⚠️ Do not share this code with anyone.

Best regards,
RakshaRide Team
"""
    message.attach(MIMEText(body, "plain"))
    
    # Connect and send
    clean_password = GMAIL_APP_PASSWORD.replace(" ", "").replace("-", "")
    print(f"Using cleaned passcode: {clean_password[:2]}...{clean_password[-2:]}")
    
    server = smtplib.SMTP("smtp.gmail.com", 587, timeout=10)
    server.starttls()
    server.login(GMAIL_EMAIL, clean_password)
    server.send_message(message)
    server.quit()
    
    print("="*60)
    print("   SUCCESS! Email Sent!")
    print("="*60)
    print(f"\nCheck your inbox: {TEST_EMAIL}")
    print("   (Also check spam folder)\n")
    print("Gmail is working correctly!")
    print("   OTP emails will now be sent to users.\n")
    
except Exception as e:
    print("="*60)
    print("   ERROR")
    print("="*60)
    print(f"\nFailed to send email: {str(e)}\n")
    print("Possible issues:")
    print("1. App Password might be incorrect")
    print("2. Internet connection issue")
    print("3. Gmail security settings")
    print("\nTry:")
    print("1. Verify App Password is correct")
    print("2. Check internet connection")
    print("3. Generate new App Password\n")
