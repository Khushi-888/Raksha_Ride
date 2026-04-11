import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

def test_real_email():
    email = "riksharide2026@gmail.com"
    password = "evsz tunv eoqi lawu".replace(" ", "")
    target = "riksharide2026@gmail.com" # Send to self for test
    
    print(f"Testing SMTP with {email}...")
    
    msg = MIMEMultipart()
    msg['From'] = email
    msg['To'] = target
    msg['Subject'] = "RAKSHARIDE SYSTEM TEST (No Unicode)"
    msg.attach(MIMEText("If you see this, real-world email is WORKING.", 'plain'))
    
    try:
        server = smtplib.SMTP("smtp.gmail.com", 587, timeout=15)
        server.starttls()
        print("Connected. Logging in...")
        server.login(email, password)
        print("Login successful. Sending message...")
        server.send_message(msg)
        server.quit()
        print("SUCCESS: Email delivered.")
        return True
    except Exception as e:
        print(f"FAILURE: {str(e)}")
        return False

if __name__ == "__main__":
    test_real_email()
