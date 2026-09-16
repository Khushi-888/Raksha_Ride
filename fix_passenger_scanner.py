content = open('templates/dashboard_passenger_new.html', encoding='utf-8').read()

# Replace loadDriverDocsForPassenger with a version that shows NO documents
old_func_start = 'async function loadDriverDocsForPassenger(driverId){'
idx = content.find(old_func_start)
if idx != -1:
    depth = 0
    i = idx
    while i < len(content):
        if content[i] == '{': depth += 1
        elif content[i] == '}':
            depth -= 1
            if depth == 0:
                old_func = content[idx:i+1]
                # Replace with empty function (no docs for passengers)
                new_func = '''async function loadDriverDocsForPassenger(driverId){
  // SECURITY: Passengers cannot view driver documents
  // Only show verification status
  const docsEl = document.getElementById('passengerDriverDocs');
  if(!docsEl) return;
  docsEl.innerHTML = `
    <div style="background:var(--bg2);border-radius:10px;padding:16px;text-align:center">
      <div style="font-size:32px;margin-bottom:8px">🔒</div>
      <div style="font-weight:600;font-size:0.9rem">Documents are private</div>
      <div style="font-size:0.8rem;color:var(--text2);margin-top:4px">Driver documents are verified by admin and kept secure</div>
    </div>`;
}'''
                content = content.replace(old_func, new_func, 1)
                print(f"Replaced loadDriverDocsForPassenger (length {len(old_func)})")
                break
        i += 1
else:
    print("loadDriverDocsForPassenger not found")

# Also remove viewPassengerDoc function
old_view_start = 'function viewPassengerDoc(src,label){'
idx2 = content.find(old_view_start)
if idx2 != -1:
    depth = 0
    i = idx2
    while i < len(content):
        if content[i] == '{': depth += 1
        elif content[i] == '}':
            depth -= 1
            if depth == 0:
                old_func2 = content[idx2:i+1]
                content = content.replace(old_func2, '// viewPassengerDoc removed for security', 1)
                print("Removed viewPassengerDoc")
                break
        i += 1

open('templates/dashboard_passenger_new.html', 'w', encoding='utf-8').write(content)
print("Done!")
