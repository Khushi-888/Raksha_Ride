content = open('templates/dashboard_driver_new.html', encoding='utf-8').read()

# Find and replace the loadDocuments function
idx = content.find('let currentDocData = null;')
if idx == -1:
    idx = content.find('async function loadDocuments(){')
    print(f"Found loadDocuments at: {idx}")
else:
    print(f"Found currentDocData at: {idx}")

# Find the end of the loadDocuments function
func_start = content.find('async function loadDocuments(){', idx if idx != -1 else 0)
if func_start == -1:
    print("ERROR: loadDocuments not found!")
    exit()

# Find end of function
depth = 0
i = func_start
while i < len(content):
    if content[i] == '{': depth += 1
    elif content[i] == '}':
        depth -= 1
        if depth == 0:
            func_end = i + 1
            break
    i += 1

old_func = content[func_start:func_end]
print(f"Old loadDocuments length: {len(old_func)}")

new_func = '''async function loadDocuments(){
  const grid = document.getElementById('docsGrid');
  const subtitle = document.getElementById('docSubtitle');
  
  // Show loading state
  grid.innerHTML = `
    <div style="height:220px;background:var(--bg3);border-radius:16px;animation:shimmer 1.5s infinite"></div>
    <div style="height:220px;background:var(--bg3);border-radius:16px;animation:shimmer 1.5s infinite"></div>
    <div style="height:220px;background:var(--bg3);border-radius:16px;animation:shimmer 1.5s infinite"></div>`;

  try{
    const r = await authFetch('/api/get_driver_documents');
    if(!r){ subtitle.textContent = 'Authentication error — please refresh'; return; }
    
    const d = await r.json();
    
    if(!d.success){
      subtitle.textContent = 'Error: ' + (d.message || 'Failed to load');
      grid.innerHTML = `<div style="grid-column:1/-1;text-align:center;padding:40px;color:var(--red)">
        <div style="font-size:48px;margin-bottom:12px">⚠️</div>
        <p>${d.message || 'Failed to load documents'}</p>
        <button class="btn btn-yellow btn-sm" style="margin-top:12px" onclick="loadDocuments()">🔄 Retry</button>
      </div>`;
      return;
    }

    const docs = d.documents || {};
    const isRent = d.is_rent;
    const canUpload = d.can_upload;
    const allVerified = d.driver_verified;
    const uploadedCount = Object.keys(docs).length;

    subtitle.textContent = uploadedCount > 0
      ? `${uploadedCount} of ${DOC_TYPES.length} documents uploaded`
      : 'No documents uploaded yet';

    if(isRent) document.getElementById('rentNotice').classList.remove('hidden');
    if(allVerified) document.getElementById('verifiedBanner').classList.remove('hidden');

    const uploadBtn = document.getElementById('docUploadBtn');
    if(canUpload){
      uploadBtn.innerHTML = `<button class="btn btn-yellow" onclick="triggerDocUpload()">📤 Upload Documents</button>`;
    }

    if(uploadedCount === 0){
      grid.innerHTML = `<div style="grid-column:1/-1;text-align:center;padding:48px;background:var(--card);border-radius:16px;border:2px dashed var(--border)">
        <div style="font-size:64px;margin-bottom:16px">📄</div>
        <h3 style="margin-bottom:8px">No Documents Uploaded</h3>
        <p style="color:var(--text2);margin-bottom:20px">Upload your Aadhaar, License, RC Book, and Selfie to get verified</p>
        ${canUpload ? `<button class="btn btn-yellow btn-lg" onclick="triggerDocUpload()">📤 Upload Documents Now</button>` : ''}
      </div>`;
      return;
    }

    grid.innerHTML = DOC_TYPES.map(dt => {
      const info = docs[dt.key];
      const hasDoc = info && info.uploaded;
      const preview = info && info.preview;
      const hasPreview = info && info.has_preview;
      const verified = info && info.verified;

      const statusBadge = verified
        ? `<span style="background:#E8F5E9;color:#2E7D32;padding:3px 10px;border-radius:20px;font-size:0.72rem;font-weight:700">✅ Verified</span>`
        : hasDoc
          ? `<span style="background:#E3F2FD;color:#1565C0;padding:3px 10px;border-radius:20px;font-size:0.72rem;font-weight:700">📤 Uploaded</span>`
          : `<span style="background:#FFF8E1;color:#F57F17;padding:3px 10px;border-radius:20px;font-size:0.72rem;font-weight:700">⏳ Not Uploaded</span>`;

      const previewHtml = hasPreview && preview
        ? `<img src="${preview}" style="width:100%;height:140px;object-fit:cover;border-radius:10px;margin-bottom:12px;cursor:pointer;border:1px solid var(--border)" onclick="openDocViewer('${dt.key}','${dt.label}')" loading="lazy" onerror="this.style.display='none';this.nextElementSibling.style.display='flex'">`
          + `<div style="display:none;width:100%;height:140px;background:var(--bg3);border-radius:10px;margin-bottom:12px;align-items:center;justify-content:center;font-size:48px">${dt.icon}</div>`
        : `<div style="width:100%;height:140px;background:var(--bg3);border-radius:10px;margin-bottom:12px;display:flex;align-items:center;justify-content:center;font-size:48px">${dt.icon}</div>`;

      return `<div style="background:var(--card);border:2px solid ${hasDoc?'#1565C0':'var(--border)'};border-radius:16px;padding:20px;transition:all 0.3s;cursor:${hasDoc?'pointer':'default'}"
        onmouseover="this.style.transform='translateY(-4px)';this.style.boxShadow='0 8px 30px var(--shadow)'"
        onmouseout="this.style.transform='';this.style.boxShadow=''"
        onclick="${hasDoc?`openDocViewer('${dt.key}','${dt.label}')`:''}" >
        ${previewHtml}
        <div style="font-weight:700;margin-bottom:8px">${dt.label}</div>
        <div style="display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:6px">
          ${statusBadge}
          ${hasDoc ? `<button class="btn btn-sm btn-yellow" onclick="event.stopPropagation();openDocViewer('${dt.key}','${dt.label}')">👁 View</button>` : ''}
        </div>
        ${hasDoc && canUpload ? `<button class="btn btn-sm btn-outline" style="width:100%;margin-top:10px" onclick="event.stopPropagation();uploadSingleDoc('${dt.key}','${dt.label}')">🔄 Update</button>` : ''}
        ${!hasDoc && canUpload ? `<button class="btn btn-sm btn-blue" style="width:100%;margin-top:10px;color:white;background:var(--blue)" onclick="event.stopPropagation();uploadSingleDoc('${dt.key}','${dt.label}')">📤 Upload</button>` : ''}
      </div>`;
    }).join('');

  }catch(e){
    subtitle.textContent = 'Error loading documents';
    grid.innerHTML = `<div style="grid-column:1/-1;text-align:center;padding:40px;color:var(--red)">
      <p>Error: ${e.message}</p>
      <button class="btn btn-yellow btn-sm" style="margin-top:12px" onclick="loadDocuments()">🔄 Retry</button>
    </div>`;
  }
}'''

content = content[:func_start] + new_func + content[func_end:]
open('templates/dashboard_driver_new.html', 'w', encoding='utf-8').write(content)
print(f"Replaced loadDocuments. New length: {len(new_func)}")
