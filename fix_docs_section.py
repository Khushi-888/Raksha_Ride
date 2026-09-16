content = open('templates/dashboard_driver_new.html', encoding='utf-8').read()

# Find and replace the documents section
start_marker = '    <!-- DOCUMENTS -->'
end_marker = '    <!-- PAYMENT -->'

start_idx = content.find(start_marker)
end_idx = content.find(end_marker)

if start_idx == -1 or end_idx == -1:
    print(f"Markers not found! start={start_idx}, end={end_idx}")
    # Show what's around line 170
    lines = content.split('\n')
    for i, line in enumerate(lines[165:195], start=166):
        print(f"{i}: {line[:80]}")
else:
    new_docs_section = '''    <!-- DOCUMENTS -->
    <div id="section-documents" class="hidden">
      <div class="dash-header">
        <div>
          <div class="dash-title">📄 Documents</div>
          <div class="dash-subtitle" id="docSubtitle">Loading your documents...</div>
        </div>
        <div id="docUploadBtn"></div>
      </div>
      <div id="rentNotice" class="hidden">
        <div class="alert alert-warn" style="margin-bottom:20px">
          🔒 You are a <strong>Rent Driver</strong>. Documents are uploaded by the vehicle owner. You can view but not edit or delete.
        </div>
      </div>
      <div id="verifiedBanner" class="hidden" style="background:linear-gradient(135deg,#E8F5E9,#F1F8E9);border:2px solid #4CAF50;border-radius:16px;padding:16px 20px;margin-bottom:20px;display:flex;align-items:center;gap:12px">
        <span style="font-size:28px">✅</span>
        <div><div style="font-weight:700;color:#2E7D32">All Documents Verified</div>
          <div style="font-size:0.85rem;color:#388E3C">Your account is fully verified and active</div></div>
      </div>
      <div id="docsGrid" style="display:grid;grid-template-columns:repeat(auto-fill,minmax(280px,1fr));gap:20px">
        <div style="height:220px;background:var(--bg3);border-radius:16px;animation:shimmer 1.5s infinite"></div>
        <div style="height:220px;background:var(--bg3);border-radius:16px;animation:shimmer 1.5s infinite"></div>
        <div style="height:220px;background:var(--bg3);border-radius:16px;animation:shimmer 1.5s infinite"></div>
      </div>
    </div>

    <!-- Document Full-Screen Viewer -->
    <div id="docViewModal" style="display:none;position:fixed;inset:0;background:rgba(0,0,0,0.92);z-index:9999;align-items:center;justify-content:center;flex-direction:column;gap:16px;padding:20px">
      <div style="background:var(--card);border-radius:16px;padding:24px;max-width:720px;width:100%;max-height:90vh;overflow-y:auto">
        <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:16px">
          <h3 id="docViewTitle" style="font-size:1.1rem;font-weight:700"></h3>
          <div style="display:flex;gap:8px">
            <button id="docDownloadBtn" class="btn btn-yellow btn-sm" onclick="downloadCurrentDoc()">⬇️ Download</button>
            <button class="btn btn-sm" style="background:#C62828;color:white" onclick="closeDocModal()">✕ Close</button>
          </div>
        </div>
        <div id="docViewContent" style="text-align:center;min-height:200px;display:flex;align-items:center;justify-content:center"></div>
        <div style="margin-top:12px" id="docViewStatus"></div>
      </div>
    </div>

    '''

    content = content[:start_idx] + new_docs_section + content[end_idx:]
    open('templates/dashboard_driver_new.html', 'w', encoding='utf-8').write(content)
    print("Documents section replaced successfully!")
