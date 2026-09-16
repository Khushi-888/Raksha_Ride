import smtplib
from email.mime.text import MIMEText

emails = ["rakshride2026@gmail.com", "raksharide2026@gmail.com", "khushisaharan42@gmail.com"]
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
        break
    except Exception as e:
        print(f"FAILED: {str(e)[:50]}")

print("\nTesting with Port 465 (SSL)...")
for email in emails:
    print(f"Testing {email}...", end=" ")
    try:
        server = smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=10)
        server.login(email, password)
        server.quit()
        print("SUCCESS!")
        break
    except Exception as e:
        print(f"FAILED: {str(e)[:50]}")
