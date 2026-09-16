import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Credentials from app_enhanced.py
GMAIL_EMAIL = "riksharide2026@gmail.com"
GMAIL_APP_PASSWORD = "evsz tunv eoqi lawu"
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 465 # SSL Port

def test_send():
    print(f"Testing Gmail SSL for: {GMAIL_EMAIL}")
    try:
        clean_password = GMAIL_APP_PASSWORD.replace(" ", "").replace("-", "")
        message = MIMEMultipart()
        message["From"] = f"RakshaRide <{GMAIL_EMAIL}>"
        message["To"] = "khushisaharan42@gmail.com"
        message["Subject"] = "Test OTP SSL Verification"
        body = "Test code: 123456"
        message.attach(MIMEText(body, "plain"))
        
        # Use SMTP_SSL
        server = smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT, timeout=10)
        server.login(GMAIL_EMAIL, clean_password)
        server.send_message(message)
        server.quit()
        print("SUCCESS: Email sent successfully via SSL!")
        return True
    except Exception as e:
        print(f"FAILURE: {str(e)}")
        return False

if __name__ == "__main__":
    test_send()
