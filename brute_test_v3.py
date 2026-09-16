import smtplib
from email.mime.text import MIMEText

emails = [
    "rakshride2026@gmail.com", 
    "raksharide2026@gmail.com", 
    "khushisaharan42@gmail.com",
    "khushisaiharan42@gmail.com",
    "raksha.ride2026@gmail.com"
]
password = "evsz tunv eoqi lawu".replace(" ", "")

print(f"Brute testing passcode: {password}")

for email in emails:
    print(f"Testing {email}...", end=" ")
    try:
        server = smtplib.SMTP("smtp.gmail.com", 587, timeout=10)
        server.starttls()
        server.login(email, password)
        server.quit()
        print("SUCCESS!")
    except Exception as e:
        print(f"FAILED: {str(e)[:40]}")
