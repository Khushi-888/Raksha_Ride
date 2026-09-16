content = open('app_enhanced.py', encoding='utf-8').read()

# Fix the duplicate route and missing current_user = get_current_user()
old = """@app.route('/api/get_driver_documents')
@app.route('/api/get_driver_documents')
def api_get_driver_documents():
    if not current_user or current_user.get('user_type') != 'driver':"""

new = """def _resolve_document_preview(file_data):
    \"\"\"Resolve document file_data to a displayable data URI.
    Handles: data URI, file path, encrypted base64, raw base64.\"\"\"
    if not file_data or not isinstance(file_data, str):
        return None
    # Format 1: Already a data URI
    if file_data.startswith('data:'):
        return file_data
    # Format 2: File path
    if '/' in file_data or '\\\\' in file_data:
        try:
            clean = file_data.replace('\\\\', '/').replace('\\\\\\\\', '/')
            if os.path.exists(clean):
                with open(clean, 'rb') as f:
                    data = f.read()
                ext = clean.rsplit('.', 1)[-1].lower()
                mime = {'jpg':'image/jpeg','jpeg':'image/jpeg','png':'image/png',
                        'pdf':'application/pdf','gif':'image/gif'}.get(ext,'image/jpeg')
                return f"data:{mime};base64,{base64.b64encode(data).decode()}"
        except Exception as e:
            print(f"[DOC] File read error: {e}")
        return None
    # Format 3: Encrypted base64
    try:
        decrypted = decrypt_document(file_data)
        if decrypted:
            if isinstance(decrypted, bytes):
                decrypted = decrypted.decode('utf-8', errors='ignore')
            if decrypted.startswith('data:'):
                return decrypted
            if len(decrypted) > 100:
                return 'data:image/jpeg;base64,' + decrypted
    except Exception:
        pass
    # Format 4: Raw base64
    if len(file_data) > 100:
        try:
            import base64 as _b64
            _b64.b64decode(file_data[:100])
            return 'data:image/jpeg;base64,' + file_data
        except Exception:
            pass
    return None


@app.route('/api/get_driver_documents')
def api_get_driver_documents():
    current_user = get_current_user()
    if not current_user or current_user.get('user_type') != 'driver':"""

if old in content:
    content = content.replace(old, new, 1)
    print("Fixed duplicate route and added helper function!")
else:
    print("Pattern not found, trying line-by-line fix...")
    # Remove just the duplicate decorator
    content = content.replace(
        "@app.route('/api/get_driver_documents')\n@app.route('/api/get_driver_documents')\ndef api_get_driver_documents():\n    if not current_user",
        "@app.route('/api/get_driver_documents')\ndef api_get_driver_documents():\n    current_user = get_current_user()\n    if not current_user"
    )
    print("Applied fallback fix")

open('app_enhanced.py', 'w', encoding='utf-8').write(content)
print("Done!")
