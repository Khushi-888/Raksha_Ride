"""Fix confirmDriver to use authFetch and fix GPS tracking in passenger dashboard"""
content = open('templates/dashboard_passenger_new.html', encoding='utf-8').read()

# Fix confirmDriver to use authFetch and send lat/lng
old_confirm = '''async function confirmDriver(){
  if(!selectedDriver){showToast('No driver selected','warn');return;}
  try{
    const r=await authFetch('/api/start_ride',{method:'POST',headers:{'Content-Type':'application/json'},
      body:JSON.stringify({driver_id:selectedDriver.id})});'''

new_confirm = '''async function confirmDriver(){
  if(!selectedDriver){showToast('No driver selected','warn');return;}
  // Get current location for ride start
  let lat=null,lng=null;
  try{
    const pos=await new Promise((res,rej)=>navigator.geolocation.getCurrentPosition(res,rej,{timeout:5000}));
    lat=pos.coords.latitude; lng=pos.coords.longitude;
  }catch(e){}
  try{
    const r=await authFetch('/api/start_ride',{method:'POST',
      body:JSON.stringify({driver_id:selectedDriver.id,latitude:lat,longitude:lng,
        pickup_location:'Current Location',dropoff_location:'Destination'})});'''

if old_confirm in content:
    content = content.replace(old_confirm, new_confirm)
    print("Fixed confirmDriver GPS")
else:
    print("confirmDriver pattern not found, trying partial match")
    idx = content.find('async function confirmDriver(){')
    if idx != -1:
        print(f"Found at index {idx}")
        print(repr(content[idx:idx+300]))

# Fix the ride_id extraction from response
old_ride_id = "activeRideId=d.ride_id;"
new_ride_id = "activeRideId=d.ride_id||d.ride?.id;"
content = content.replace(old_ride_id, new_ride_id)

# Fix endRide to use authFetch
old_end = "const r=await fetch('/api/complete_ride',{method:'POST',headers:{'Content-Type':'application/json'},"
new_end = "const r=await authFetch('/api/complete_ride',{method:'POST',"
content = content.replace(old_end, new_end)

open('templates/dashboard_passenger_new.html', 'w', encoding='utf-8').write(content)
print("Done!")
