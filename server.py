from fastapi import FastAPI, Body
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import uvicorn
import os

# Import the existing backend app from main.py
from main import app as api_app

# The main app is the api_app itself
app = api_app

# Serve current directory for static assets (app.js, styles, etc)
base_dir = os.path.dirname(os.path.abspath(__file__))

# We mount the static files at root, but AFTER the API routes are registered
# to avoid conflicts. FastAPI checks routes in order.
# Since routes are already in api_app, we just add the static files at the end.
app.mount("/", StaticFiles(directory=base_dir, html=True), name="static")

@app.get("/", include_in_schema=False)
async def read_index():
    return FileResponse(os.path.join(base_dir, 'index.html'))

@app.post("/api/generate-otp")
async def generate_otp_api(credential: str = Body(...), role: str = Body(...)):
    """Dedicated endpoint to trigger OTP generation."""
    from database import SessionLocal
    from otp_manager import OTPManager
    async with SessionLocal() as db:
        otp = await OTPManager.create_otp(db, credential, role)
        return {"status": "success", "message": f"OTP sent to {credential}"}

if __name__ == "__main__":
    print("\nRakshaRide Production Environment Initializing...")
    print("URL: http://localhost:8000")
    print("GPS: Live Geolocation Enabled")
    print("Persistence: SQLite (production_database.db)")
    print("Serving Static Files from: " + base_dir)
    print("--------------------------------------------------\n")
    uvicorn.run(app, host="0.0.0.0", port=8000)
