import re

with open('app_enhanced.py', 'r', encoding='utf-8') as f:
    content = f.read()

old = "sqlite3.connect('database_enhanced.db')"
new = "sqlite3.connect(DB_PATH)"
count = content.count(old)
content = content.replace(old, new)

with open('app_enhanced.py', 'w', encoding='utf-8') as f:
    f.write(content)

print(f"Replaced {count} hardcoded DB paths with DB_PATH")
