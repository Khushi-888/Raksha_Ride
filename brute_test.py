import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

emails = ["rakshride2026@gmail.com", "raksharide2026@gmail.com"]
passwords = ["uhnzgwqdjeamzjgr", "uhnzgwqdjeamzigr", "vdqwvrkcjkmenvvn", "vdqwwrkcjkmenvvn"]

def test_combo(email, password):
    clean_password = password.replace(" ", "").replace("-", "")
    print(f"Testing: {email} | {password} ... ", end="")
    try:
        server = smtplib.SMTP("smtp.gmail.com", 587, timeout=5)
        server.starttls()
        server.login(email, clean_password)
        server.quit()
        print("SUCCESS! ✅")
        return True
    except Exception as e:
        print(f"FAILED: {str(e)[:50]}")
        return False

if __name__ == "__main__":
    for e in emails:
        for p in passwords:
            if test_combo(e, p):
                print(f"\n🎉 FOUND WORKING CREDENTIALS:")
                print(f"Email: {e}")
                print(f"Password: {p}")
                exit(0)
    print("\n❌ All combinations failed.")
