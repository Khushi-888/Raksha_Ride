"""
Quick Gmail SMTP Test Script
Tests if your Gmail App Password is working correctly
"""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Gmail Configuration (UPDATE THESE!)
GMAIL_EMAIL = "riksharide2026@gmail.com"
GMAIL_APP_PASSWORD = "evsz tunv eoqi lawu"  # ✅ FIXED
TEST_EMAIL = "khushisaharan42@gmail.com"  # Removed extra 'i'

def test_gmail():
    print("\n" + "="*60)
    print("  Testing Gmail SMTP Configuration")
    print("="*60 + "\n")
    
    print(f"📧 From: {GMAIL_EMAIL}")
    print(f"📧 To: {TEST_EMAIL}")
    print(f"🔑 Password: {'*' * len(GMAIL_APP_PASSWORD)}")
    print()
    
    try:
        # Clean password
        clean_password = GMAIL_APP_PASSWORD.replace(" ", "").replace("-", "")
        print(f"🔧 Cleaned password length: {len(clean_password)} characters")
        
        # Create message
        message = MIMEMultipart()
        message["From"] = f"RakshaRide <{GMAIL_EMAIL}>"
        message["To"] = TEST_EMAIL
        message["Subject"] = "RakshaRide - Gmail Test"
        
        body = """Hello!

This is a test email from RakshaRide.

If you received this, your Gmail SMTP is working correctly! ✅

Test OTP: 123456

Best regards,
RakshaRide Team
"""
        message.attach(MIMEText(body, "plain"))
        
        print("📤 Connecting to Gmail SMTP server...")
        server = smtplib.SMTP("smtp.gmail.com", 587, timeout=10)
        
        print("🔒 Starting TLS encryption...")
        server.starttls()
        
        print("🔐 Logging in...")
        server.login(GMAIL_EMAIL, clean_password)
        
        print("📨 Sending email...")
        server.send_message(message)
        
        print("✅ Closing connection...")
        server.quit()
        
        print("\n" + "="*60)
        print("  ✅ SUCCESS! Email sent successfully!")
        print("="*60)
        print(f"\n📬 Check your inbox: {TEST_EMAIL}")
        print("   (Also check spam folder)")
        print("\n✅ Your Gmail configuration is working correctly!")
        print("   You can now use email OTP in RakshaRide.\n")
        
        return True
        
    except smtplib.SMTPAuthenticationError as e:
        print("\n" + "="*60)
        print("  ❌ AUTHENTICATION FAILED")
        print("="*60)
        print("\n🔴 Gmail rejected your credentials.\n")
        print("Possible reasons:")
        print("1. App Password is incorrect")
        print("2. 2-Step Verification is not enabled")
        print("3. App Password was not generated correctly")
        print("\n📖 Follow these steps:")
        print("1. Go to: https://myaccount.google.com/security")
        print("2. Enable 2-Step Verification (if not already)")
        print("3. Go to: https://myaccount.google.com/apppasswords")
        print("4. Generate NEW App Password for 'Mail' > 'Other (RakshaRide)'")
        print("5. Copy the 16-character password (with spaces)")
        print("6. Update GMAIL_APP_PASSWORD in this file")
        print("7. Run this test again")
        print(f"\nError details: {str(e)}\n")
        return False
        
    except smtplib.SMTPException as e:
        print("\n" + "="*60)
        print("  ❌ SMTP ERROR")
        print("="*60)
        print(f"\n🔴 SMTP error: {str(e)}\n")
        return False
        
    except Exception as e:
        print("\n" + "="*60)
        print("  ❌ ERROR")
        print("="*60)
        print(f"\n🔴 Error: {str(e)}\n")
        return False

if __name__ == "__main__":
    print("\n Starting test...\n")
    
    success = test_gmail()
    
    if success:
        print("\n🎉 Next steps:")
        print("   1. Update app_enhanced.py with same App Password")
        print("   2. Restart the server: python app_enhanced.py")
        print("   3. Try registering with email OTP")
    else:
        print("\n📖 Need help?")
        print("   Read: FIX_GMAIL_EMAIL.md")
        print("   Or continue using console OTP (system works without email)")
    
    print()
