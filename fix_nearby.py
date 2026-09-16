content = open('templates/dashboard_passenger_new.html', encoding='utf-8').read()

old = '''async function loadNearbyDrivers(lat,lng){
  try{
    const url=lat?`/api/nearby_drivers?lat=${lat}&lng=${lng}&radius=10`:`/api/nearby_drivers?radius=10`;
    const url=lat?`/api/nearby_drivers?lat=${lat}&lng=${lng}&radius=10`:`/api/nearby_drivers?radius=10`;
    const r=await fetch(url);const d=await r.json();'''

new = '''async function loadNearbyDrivers(lat,lng){
  try{
    const dist = document.getElementById('filterDist')?.value || '10';
    const gender = document.getElementById('filterGender')?.value || '';
    const url = lat
      ? `/api/nearby_drivers?lat=${lat}&lng=${lng}&radius=${dist}&gender=${gender}`
      : `/api/nearby_drivers?radius=${dist}&gender=${gender}`;
    const r=await authFetch(url);if(!r)return;const d=await r.json();'''

if old in content:
    content = content.replace(old, new, 1)
    print("Fixed loadNearbyDrivers!")
else:
    # Try simpler replacement
    old2 = "    const url=lat?`/api/nearby_drivers?lat=${lat}&lng=${lng}&radius=10`:`/api/nearby_drivers?radius=10`;\n    const r=await fetch(url);const d=await r.json();"
    new2 = "    const dist=document.getElementById('filterDist')?.value||'10';\n    const gender=document.getElementById('filterGender')?.value||'';\n    const url=lat?`/api/nearby_drivers?lat=${lat}&lng=${lng}&radius=${dist}&gender=${gender}`:`/api/nearby_drivers?radius=${dist}&gender=${gender}`;\n    const r=await authFetch(url);if(!r)return;const d=await r.json();"
    if old2 in content:
        content = content.replace(old2, new2, 1)
        print("Fixed with fallback!")
    else:
        print("Pattern not found!")
        idx = content.find('loadNearbyDrivers')
        print("Context:", repr(content[idx:idx+300]))

open('templates/dashboard_passenger_new.html', 'w', encoding='utf-8').write(content)
print("Done!")
