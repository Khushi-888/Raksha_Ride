content = open('templates/dashboard_driver_new.html', encoding='utf-8').read()

# Remove old docModal HTML if still present
old_modal = '''<!-- Document View Modal -->
<div class="modal-overlay hidden" id="docModal">
  <div class="modal">
    <div class="modal-header">
      <h3 class="modal-title" id="docModalTitle">Document</h3>
      <button class="modal-close" onclick="closeDocModal()">✕</button>
    </div>
    <img id="docModalImg" src="" style="width:100%;border-radius:var(--radius-sm);max-height:400px;object-fit:contain">
  </div>
</div>'''
content = content.replace(old_modal, '')

# Replace loadDocuments function
old_load = '''async function loadDocuments(){
  try{
    const r=await authFetch('/api/get_driver_documents');
    const d=await r.json();
    const grid=document.getElementById('docsGrid');
    const docTypes=[
      {key:'aadhaar-front',label:'Aadhaar Front',icon:'🪪'},
      {key:'aadhaar-back',label:'Aadhaar Back',icon:'🪪'},
      {key:'license',label:'Driving License',icon:'🚗'},
      {key:'rc',label:'RC Book',icon:'📋'},
      {key:'selfie',label:'Live Selfie',icon:'🤳'}
    ];
    const isRent=driverData.role==='RENT';
    const uploadBtn=document.getElementById('docUploadBtn');
    if(!isRent){
      uploadBtn.innerHTML='<button class="btn btn-yellow" onclick="showSection(\'documents\');document.getElementById(\'docUploadModal\').classList.remove(\'hidden\')">📤 Upload Documents</button>';
    }
    const docs=d.documents||{};
    grid.innerHTML=docTypes.map(dt=>{
      const docInfo=docs[dt.key];
      const hasDoc=docInfo&&docInfo.uploaded;
      const hasImg=docInfo&&docInfo.data;
      return `<div class="doc-card ${hasDoc?'uploaded':''}" style="cursor:${hasDoc?'pointer':'default'}" onclick="${hasDoc?`viewDoc('${dt.key}','${dt.label}')`:''}" >
        ${hasImg
          ? `<img src="${docInfo.data}" style="width:100%;height:120px;object-fit:cover;border-radius:8px;margin-bottom:10px">`
          : `<span class="doc-icon">${dt.icon}</span>`
        }
        <div class="doc-name">${dt.label}</div>
        <div class="doc-status">${hasDoc?'✅ Uploaded — Click to view':'⏳ Not uploaded'}</div>
        ${hasDoc&&!isRent?`<button class="btn btn-sm btn-outline" style="margin-top:8px" onclick="event.stopPropagation();reuploadDoc('${dt.key}')">🔄 Update</button>`:''}
      </div>`;
    }).join('');
  }catch(e){showToast('Failed to load documents','error');}
}'''

new_load = '''let currentDocData = null;
const DOC_TYPES = [
  {key:'aadhaar-front', label:'Aadhaar Card (Front)', icon:'🪪', color:'#1565C0'},
  {key:'aadhaar-back',  label:'Aadhaar Card (Back)',  icon:'🪪', color:'#1565C0'},
  {key:'license',       label:'Driving License',      icon:'🚗', color:'#2E7D32'},
  {key:'rc',            label:'RC Book',               icon:'📋', color:'#E65100'},
  {key:'selfie',        label:'Live Selfie',           icon:'🤳', color:'#6A1B9A'}
];

async function loadDocuments(){
  const grid = document.getElementById('docsGrid');
  try{
    const r = await authFetch('/api/get_driver_documents');
    if(!r) return;
    const d = await r.json();
    if(!d.success){ showToast(d.message||'Failed to load documents','error'); return; }

    const docs = d.documents || {};
    const isRent = d.is_rent;
    const canUpload = d.can_upload;
    const allVerified = d.driver_verified;

    // Update subtitle
    const uploadedCount = Object.keys(docs).length;
    document.getElementById('docSubtitle').textContent =
      `${uploadedCount} of ${DOC_TYPES.length} documents uploaded`;

    // Show/hide banners
    if(isRent) document.getElementById('rentNotice').classList.remove('hidden');
    if(allVerified) document.getElementById('verifiedBanner').classList.remove('hidden');

    // Upload button for owners
    const uploadBtn = document.getElementById('docUploadBtn');
    if(canUpload){
      uploadBtn.innerHTML = `<button class="btn btn-yellow" onclick="showSection('documents');triggerDocUpload()">📤 Upload / Update Documents</button>`;
    }

    // Build document cards
    grid.innerHTML = DOC_TYPES.map(dt => {
      const info = docs[dt.key];
      const hasDoc = info && info.uploaded;
      const preview = info && info.preview;
      const verified = info && info.verified;
      const aiStatus = info && info.ai_status;

      const statusBadge = verified
        ? `<span style="background:#E8F5E9;color:#2E7D32;padding:3px 10px;border-radius:20px;font-size:0.72rem;font-weight:700">✅ Verified</span>`
        : hasDoc
          ? `<span style="background:#E3F2FD;color:#1565C0;padding:3px 10px;border-radius:20px;font-size:0.72rem;font-weight:700">📤 Uploaded</span>`
          : `<span style="background:#FFF8E1;color:#F57F17;padding:3px 10px;border-radius:20px;font-size:0.72rem;font-weight:700">⏳ Pending</span>`;

      const previewHtml = preview
        ? `<img src="${preview}" style="width:100%;height:140px;object-fit:cover;border-radius:10px;margin-bottom:12px;cursor:pointer" onclick="openDocViewer('${dt.key}','${dt.label}')" loading="lazy">`
        : `<div style="width:100%;height:140px;background:var(--bg3);border-radius:10px;margin-bottom:12px;display:flex;align-items:center;justify-content:center;font-size:48px">${dt.icon}</div>`;

      return `<div style="background:var(--card);border:2px solid ${hasDoc?'#1565C0':'var(--border)'};border-radius:16px;padding:20px;transition:all 0.3s;position:relative" onmouseover="this.style.transform='translateY(-4px)';this.style.boxShadow='0 8px 30px var(--shadow)'" onmouseout="this.style.transform='';this.style.boxShadow=''">
        ${previewHtml}
        <div style="font-weight:700;margin-bottom:6px">${dt.label}</div>
        <div style="display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:6px">
          ${statusBadge}
          ${hasDoc ? `<button class="btn btn-sm btn-yellow" onclick="openDocViewer('${dt.key}','${dt.label}')">👁 View</button>` : ''}
        </div>
        ${hasDoc && canUpload ? `<button class="btn btn-sm btn-outline" style="width:100%;margin-top:10px" onclick="reuploadDoc('${dt.key}')">🔄 Update</button>` : ''}
        ${!hasDoc && canUpload ? `<button class="btn btn-sm btn-blue" style="width:100%;margin-top:10px;color:white" onclick="uploadSingleDoc('${dt.key}','${dt.label}')">📤 Upload</button>` : ''}
      </div>`;
    }).join('');

  }catch(e){ showToast('Failed to load documents: '+e.message,'error'); }
}

async function openDocViewer(key, label){
  const modal = document.getElementById('docViewModal');
  const content = document.getElementById('docViewContent');
  const title = document.getElementById('docViewTitle');
  const status = document.getElementById('docViewStatus');

  title.textContent = label;
  content.innerHTML = '<div class="spinner" style="margin:0 auto"></div>';
  status.innerHTML = '';
  modal.style.display = 'flex';
  currentDocData = null;

  try{
    const r = await authFetch('/api/get_document/'+key);
    if(!r){ closeDocModal(); return; }
    const d = await r.json();
    if(d.success && d.data){
      currentDocData = d.data;
      if(d.data.startsWith('data:image')){
        content.innerHTML = `<img src="${d.data}" style="max-width:100%;max-height:60vh;border-radius:10px;box-shadow:0 4px 20px rgba(0,0,0,0.2)">`;
      } else if(d.data.startsWith('data:application/pdf')){
        content.innerHTML = `<iframe src="${d.data}" style="width:100%;height:60vh;border-radius:10px;border:none"></iframe>`;
      } else {
        content.innerHTML = `<img src="${d.data}" style="max-width:100%;max-height:60vh;border-radius:10px">`;
      }
      const verified = d.ai_status === 'VERIFIED';
      status.innerHTML = verified
        ? `<span style="background:#E8F5E9;color:#2E7D32;padding:6px 16px;border-radius:20px;font-weight:700">✅ Document Verified</span>`
        : `<span style="background:#E3F2FD;color:#1565C0;padding:6px 16px;border-radius:20px;font-weight:700">📤 Uploaded — Pending Verification</span>`;
    } else {
      content.innerHTML = `<div style="text-align:center;padding:40px"><div style="font-size:48px;margin-bottom:12px">📄</div><p style="color:var(--text2)">${d.message||'Document not available'}</p></div>`;
    }
  }catch(e){
    content.innerHTML = `<p style="color:var(--red)">Failed to load document</p>`;
  }
}

function closeDocModal(){
  document.getElementById('docViewModal').style.display = 'none';
  currentDocData = null;
}

function downloadCurrentDoc(){
  if(!currentDocData){ showToast('No document to download','warn'); return; }
  const a = document.createElement('a');
  a.href = currentDocData;
  a.download = document.getElementById('docViewTitle').textContent.replace(/\\s+/g,'-') + '.jpg';
  a.click();
}

function uploadSingleDoc(key, label){
  const input = document.createElement('input');
  input.type = 'file';
  input.accept = 'image/*,application/pdf';
  input.onchange = async (e) => {
    const file = e.target.files[0];
    if(!file) return;
    if(file.size > 5*1024*1024){ showToast('File too large (max 5MB)','error'); return; }
    const reader = new FileReader();
    reader.onload = async (ev) => {
      try{
        const r = await authFetch('/api/upload_driver_docs', {
          method:'POST',
          body: JSON.stringify({ driver_id: driverData.id, documents: { [key]: ev.target.result } })
        });
        const d = await r.json();
        if(d.success){ showToast(label+' uploaded!','success'); loadDocuments(); }
        else showToast(d.message,'error');
      }catch(err){ showToast('Upload failed','error'); }
    };
    reader.readAsDataURL(file);
  };
  input.click();
}

function reuploadDoc(key){ uploadSingleDoc(key, key); }
function triggerDocUpload(){ uploadSingleDoc('aadhaar-front','Aadhaar Front'); }'''

if old_load in content:
    content = content.replace(old_load, new_load)
    print("loadDocuments replaced!")
else:
    # Find and replace by function name
    import re
    pattern = r'async function loadDocuments\(\)\{.*?^(?=async function|\}$)'
    # Just append the new function and remove old
    idx = content.find('async function loadDocuments(){')
    if idx != -1:
        # Find end of function
        depth = 0
        i = idx
        while i < len(content):
            if content[i] == '{': depth += 1
            elif content[i] == '}':
                depth -= 1
                if depth == 0:
                    old_func = content[idx:i+1]
                    content = content.replace(old_func, new_load, 1)
                    print(f"Replaced loadDocuments (length {len(old_func)})")
                    break
            i += 1
    else:
        print("loadDocuments not found!")

# Also remove old viewDoc and closeDocModal
old_view = '''// ── DOCUMENTS ──
function viewDoc(key,label){
  document.getElementById('docModalTitle').textContent=label;
  document.getElementById('docModalImg').src='';
  document.getElementById('docModal').classList.remove('hidden');
  // Fetch actual image
  fetch('/api/get_document/'+key)
    .then(r=>r.json())
    .then(d=>{
      if(d.success&&d.data){
        document.getElementById('docModalImg').src=d.data;
      } else {
        document.getElementById('docModalImg').alt='Document not available';
        document.getElementById('docModalImg').style.display='none';
        document.getElementById('docModal').querySelector('.modal').insertAdjacentHTML('beforeend',
          '<p style="text-align:center;color:var(--text2);padding:20px">Document image not available</p>');
      }
    })
    .catch(()=>showToast('Failed to load document','error'));
}
function closeDocModal(){
  document.getElementById('docModal').classList.add('hidden');
  document.getElementById('docModalImg').style.display='block';
}'''
if old_view in content:
    content = content.replace(old_view, '// ── DOCUMENTS ── (handled by openDocViewer above)')
    print("Old viewDoc removed!")

open('templates/dashboard_driver_new.html', 'w', encoding='utf-8').write(content)
print("Done!")
