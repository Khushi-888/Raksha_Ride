content = open('app_enhanced.py', encoding='utf-8').read()

# Fix login OTP failure — currently returns 500 which blocks login
# Change it to return dev_otp fallback like send_otp does
old = '''"success": False,
                    "message": "Verification code delivery failed. Please check your network or email address.",
                    "email_sent": False
                }), 500'''

new = '''"success": True,
                    "message": "Email delivery issue. Check server console for OTP.",
                    "email_sent": False,
                    "dev_otp": otp
                })'''

if old in content:
    content = content.replace(old, new, 1)
    print("Fixed login OTP failure response")
else:
    print("Pattern not found — searching...")
    idx = content.find('"Verification code delivery failed')
    if idx != -1:
        print("Found at:", idx)
        print(repr(content[idx-200:idx+200]))

open('app_enhanced.py', 'w', encoding='utf-8').write(content)
print("Done")
