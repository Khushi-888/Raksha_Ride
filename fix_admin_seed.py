"""Fix admin password seed in app_enhanced.py"""
content = open('app_enhanced.py', encoding='utf-8').read()

# Find and fix the admin seed block
old_markers = [
    "admin@RakshaRide2024",
]

for marker in old_markers:
    if marker in content:
        # Find the full seed block
        idx = content.find("c.execute('SELECT COUNT(*) FROM admins')")
        if idx == -1:
            idx = content.find('c.execute(\'SELECT COUNT(*) FROM admins\')')
        if idx != -1:
            end_idx = content.find('\n\n', idx)
            old_block = content[idx:end_idx]
            new_block = """c.execute('SELECT COUNT(*) FROM admins')
    if c.fetchone()[0] == 0:
        import hashlib as _hl, os as _os
        admin_pw_raw = _os.environ.get('ADMIN_PASSWORD', 'RakshaAdmin@2024#Secure!')
        default_pw = _hl.sha256(admin_pw_raw.encode()).hexdigest()
        c.execute("INSERT INTO admins (username, password) VALUES (?, ?)", ('admin', default_pw))
        print("[OK] Admin created — use ADMIN_PASSWORD env var to set password")"""
            content = content.replace(old_block, new_block, 1)
            print("Fixed admin seed block")
            break

open('app_enhanced.py', 'w', encoding='utf-8').write(content)
print("Done")
