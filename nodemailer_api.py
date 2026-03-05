import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

class NodemailerMock:
    """
    A Python service that mimics Nodemailer's simplicity.
    It sends real emails if configured in mail_config.env, 
    otherwise it logs to the console as a mock.
    """
    
    def __init__(self):
        self.server = os.environ.get("SMTP_SERVER", "smtp.gmail.com")
        self.port = int(os.environ.get("SMTP_PORT", 587))
        self.user = os.environ.get("SMTP_USER", "your_email@gmail.com")
        self.password = os.environ.get("SMTP_PASS", "your_app_password")
        
        # Determine if we should actually attempt to send
        self.is_mock = (self.user == "your_email@gmail.com" or not self.user)

    async def send_mail(self, to_email, subject, body):
        if self.is_mock:
            print(f"\n--- [NODEMAILER MOCK] ---")
            print(f"From: {self.user or 'system@raksharide.in'}")
            print(f"To: {to_email}")
            print(f"Subject: {subject}")
            print(f"Body: {body}")
            print(f"-------------------------\n")
            return {"status": "mock_sent", "to": to_email}
        
        try:
            msg = MIMEMultipart()
            msg['From'] = self.user
            msg['To'] = to_email
            msg['Subject'] = subject
            msg.attach(MIMEText(body, 'plain'))

            # Standard SMTP send logic
            server = smtplib.SMTP(self.server, self.port)
            server.starttls()
            server.login(self.user, self.password)
            server.send_message(msg)
            server.quit()
            
            print(f"✅ Email successfully sent to {to_email} via {self.server}")
            return {"status": "success", "to": to_email}
        except Exception as e:
            print(f"❌ Failed to send email via Nodemailer: {e}")
            return {"status": "error", "message": str(e)}

# Singleton instance
nodemailer = NodemailerMock()
