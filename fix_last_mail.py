content = open('app_enhanced.py', encoding='utf-8').read()
lines = content.split('\n')

# Find line 2890 (0-indexed: 2889)
for i, line in enumerate(lines):
    if 'mail.send(msg)' in line:
        print(f"Line {i+1}: {repr(line)}")
        lines[i] = line.replace(
            'mail.send(msg)',
            '_smtp_send(str(msg.recipients[0]) if hasattr(msg, "recipients") else "", msg.subject, getattr(msg, "html", None) or getattr(msg, "body", ""), getattr(msg, "body", ""))'
        )
        print(f"Fixed line {i+1}")

content = '\n'.join(lines)
open('app_enhanced.py', 'w', encoding='utf-8').write(content)

# Verify
remaining = content.count('mail.send(msg)')
print(f"Remaining mail.send calls: {remaining}")
print("Done!")
