import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Final Test with established credentials
GMAIL_EMAIL = "riksharide2026@gmail.com"
GMAIL_APP_PASSWORD = "evsz tunv eoqi lawu"
TEST_EMAIL = "khushisaharan42@gmail.com"

def test_gmail():
    print(f"Testing Gmail: {GMAIL_EMAIL}")
    try:
        clean_password = GMAIL_APP_PASSWORD.replace(" ", "").replace("-", "")
        message = MIMEMultipart()
        message["From"] = f"RakshaRide <{GMAIL_EMAIL}>"
        message["To"] = TEST_EMAIL
        message["Subject"] = "Final Diagnostic Test"
        message.attach(MIMEText("Test successful.", "plain"))
        
        server = smtplib.SMTP("smtp.gmail.com", 587, timeout=10)
        server.starttls()
        server.login(GMAIL_EMAIL, clean_password)
        server.send_message(message)
        server.quit()
        print("RESULT: SUCCESS")
        return True
    except Exception as e:
        print(f"RESULT: FAILURE - {str(e)}")
        return False

if __name__ == "__main__":
    test_gmail()
