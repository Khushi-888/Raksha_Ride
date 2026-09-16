content = open('templates/dashboard_driver_new.html', encoding='utf-8').read()

# Add auth.js script tag after leaflet
content = content.replace(
    '<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>',
    '<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>\n<script src="/static/js/auth.js"></script>'
)

import re
content = re.sub(r"await fetch\('(/api/[^']+)'", r"await authFetch('\1'", content)
content = re.sub(r'await fetch\("(/api/[^"]+)"', r'await authFetch("\1"', content)
content = re.sub(r"await fetch\(`(/api/[^`]+)`", r"await authFetch(`\1`", content)
content = content.replace(",credentials:'include'", "")
content = content.replace(
    "await fetch('/api/logout',{method:'POST'})",
    "await authFetch('/api/logout',{method:'POST'})"
)

open('templates/dashboard_driver_new.html', 'w', encoding='utf-8').write(content)
count = content.count('authFetch(')
print(f"Done — {count} authFetch calls in driver dashboard")
