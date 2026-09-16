content = open('templates/admin_dashboard.html', encoding='utf-8').read()

# Find the nav-right div and add DB Viewer link
idx = content.find('class="nav-right"')
if idx != -1:
    # Find the end of this div
    end_idx = content.find('</div>', idx)
    old_nav = content[idx:end_idx+6]
    
    # Build new nav with DB Viewer button
    new_nav = '''class="nav-right">
            <span class="badge-admin">KYC Dashboard</span>
            <a href="/dbview" style="background:rgba(255,193,7,0.15);border:1px solid rgba(255,193,7,0.4);color:#FFC107;padding:8px 16px;border-radius:8px;font-size:0.82rem;font-weight:600;text-decoration:none;margin-right:8px">🗄️ DB Viewer</a>
            <button class="btn-logout" onclick="doLogout()">Logout</button>
        </div>'''
    
    content = content.replace(old_nav, new_nav, 1)
    print("Added DB Viewer link to admin nav")
else:
    print("nav-right not found")

open('templates/admin_dashboard.html', 'w', encoding='utf-8').write(content)
print("Done")
