content = open('templates/dashboard_passenger_new.html', encoding='utf-8').read()

# Replace fetch( with authFetch( but only in the script section
# We need to be careful not to replace the authFetch definition itself

import re

# Replace all fetch( calls that are awaited (API calls)
# Pattern: await fetch('/api/...
content = re.sub(r"await fetch\('(/api/[^']+)'", r"await authFetch('\1'", content)
content = re.sub(r'await fetch\("(/api/[^"]+)"', r'await authFetch("\1"', content)

# Also replace fetch( with authFetch( for template literal URLs
content = re.sub(r"await fetch\(`(/api/[^`]+)`", r"await authFetch(`\1`", content)

# Fix the logout call
content = content.replace(
    "await fetch('/api/logout',{method:'POST',credentials:'include'})",
    "await authFetch('/api/logout',{method:'POST'})"
)

# Remove duplicate credentials:'include' since authFetch handles it
content = content.replace(",credentials:'include'", "")

open('templates/dashboard_passenger_new.html', 'w', encoding='utf-8').write(content)
count = content.count('authFetch(')
print(f"Done — {count} authFetch calls")
