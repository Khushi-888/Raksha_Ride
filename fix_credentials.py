content = open('templates/dashboard_passenger_new.html', encoding='utf-8').read()

old = "method:'POST',headers:{'Content-Type':'application/json'}"
new = "method:'POST',headers:{'Content-Type':'application/json'},credentials:'include'"

fixed = content.replace(old, new)

# Also add credentials to GET fetch calls for APIs
fixed = fixed.replace(
    "const r=await fetch('/api/passenger_profile');",
    "const r=await fetch('/api/passenger_profile',{credentials:'include'});"
)
fixed = fixed.replace(
    "const r=await fetch('/api/get_active_ride');",
    "const r=await fetch('/api/get_active_ride',{credentials:'include'});"
)
fixed = fixed.replace(
    "const r=await fetch('/api/passenger_ride_history?limit=3');",
    "const r=await fetch('/api/passenger_ride_history?limit=3',{credentials:'include'});"
)
fixed = fixed.replace(
    "const r=await fetch('/api/passenger_ride_history');",
    "const r=await fetch('/api/passenger_ride_history',{credentials:'include'});"
)

open('templates/dashboard_passenger_new.html', 'w', encoding='utf-8').write(fixed)
count = fixed.count("credentials:'include'")
print(f"Done — credentials:include added to {count} fetch calls")
