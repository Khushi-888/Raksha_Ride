import math
from fastapi import FastAPI, Depends, HTTPException, status, Body
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from typing import List, Optional
from pydantic import BaseModel, EmailStr
import uuid
from datetime import datetime, timedelta
import random

import database
import auth_utils
from otp_manager import OTPManager
from fastapi import Request

app = FastAPI(title="RakshaRide Production API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Pydantic Schemas ───────────────────────────────────────────────────────
class UserLogin(BaseModel):
    credential: str  # mobile or email
    password: str
    role: str # 'driver' or 'passenger'
    device_uuid: Optional[str] = None

class OTPVerifyRequest(BaseModel):
    credential: str
    role: str
    password: str
    otp: str
    device_uuid: Optional[str] = None

# Temporary in-memory stores (Legacy - moving to DB)
# OTP_STORE = {} # { (credential, role): {"otp": str, "expires": datetime} }

class DriverRegister(BaseModel):
    name: str
    age: int
    mobile: str
    email: EmailStr
    vehicle_number: str
    rc_number: str
    pick_location: str
    password: str

class PassengerRegister(BaseModel):
    name: str
    mobile: str
    email: Optional[EmailStr] = None
    password: str

# ── Helpers ────────────────────────────────────────────────────────────────
def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    R = 6371000 # Earth radius in meters
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2) * math.sin(dlambda/2)**2
    return 2 * R * math.atan2(math.sqrt(a), math.sqrt(1 - a))

# ── Lifecycle ─────────────────────────────────────────────────────────────
@app.on_event("startup")
async def startup():
    await database.init_production_db()

# ── Auth Endpoints ────────────────────────────────────────────────────────
@app.post("/api/register/driver", status_code=status.HTTP_201_CREATED)
async def register_driver(data: DriverRegister, db: AsyncSession = Depends(database.get_db)):
    # Check existing
    stmt = select(database.Driver).where((database.Driver.email == data.email) | (database.Driver.mobile == data.mobile))
    result = await db.execute(stmt)
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Driver already exists")
    
    # Generate ID
    stmt = select(database.Driver)
    result = await db.execute(stmt)
    drivers = result.scalars().all()
    count = len(drivers)
    new_id = f"DRV-{2001 + count}"
    
    new_driver = database.Driver(
        id=new_id,
        name=data.name,
        age=data.age,
        mobile=data.mobile,
        email=data.email,
        vehicle_number=data.vehicle_number,
        rc_number=data.rc_number,
        pick_location=data.pick_location,
        password_hash=auth_utils.get_password_hash(data.password),
        is_active=False, # Inactive until verified
        verified=False
    )
    db.add(new_driver)
    await db.commit()

    # Generate Registration OTP using OTPManager (Persistent in DB)
    otp = await OTPManager.create_otp(db, data.email, "driver")
    print(f"\n[REGISTRATION OTP] For {new_id} ({data.email}): {otp}\n")

    return {
        "status": "OTP_REQUIRED",
        "message": "Registration received. Please verify your email with OTP.",
        "id": new_id,
        "credential": data.email
    }

@app.post("/api/register/passenger", status_code=status.HTTP_201_CREATED)
async def register_passenger(data: PassengerRegister, db: AsyncSession = Depends(database.get_db)):
    stmt = select(database.Passenger).where((database.Passenger.mobile == data.mobile))
    result = await db.execute(stmt)
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Passenger already exists")
    
    stmt = select(database.Passenger)
    result = await db.execute(stmt)
    passengers = result.scalars().all()
    count = len(passengers)
    new_id = f"USR-{6001 + count}"
    
    new_pax = database.Passenger(
        id=new_id,
        name=data.name,
        mobile=data.mobile,
        email=data.email,
        password_hash=auth_utils.get_password_hash(data.password),
        is_active=False, # Inactive until verified
        verified=False
    )
    db.add(new_pax)
    await db.commit()

    # Generate Registration OTP using OTPManager (Persistent in DB)
    otp = await OTPManager.create_otp(db, data.mobile, "passenger")
    print(f"\n[REGISTRATION OTP] For {new_id} ({data.mobile}): {otp}\n")

    return {
        "status": "OTP_REQUIRED",
        "message": "Registration received. Please verify your mobile with OTP.",
        "id": new_id,
        "credential": data.mobile
    }

@app.post("/api/register/verify")
async def verify_registration(request: Request, data: OTPVerifyRequest, db: AsyncSession = Depends(database.get_db)):
    ip = request.client.host
    if await OTPManager.is_ip_blocked(db, ip):
        raise HTTPException(status_code=429, detail="Too many attempts. Your IP is blocked for 10 minutes.")

    # 1. Check OTP using OTPManager
    success, message = await OTPManager.verify_otp(db, data.credential, data.role, data.otp)
    if not success:
        if "Too many failed attempts" in message:
            await OTPManager.block_ip(db, ip)
            raise HTTPException(status_code=429, detail="Too many attempts. Your IP is blocked for 10 minutes.")
        raise HTTPException(status_code=400, detail=message)

    # 2. Activate User
    if data.role == 'driver':
        stmt = select(database.Driver).where((database.Driver.email == data.credential) | (database.Driver.mobile == data.credential))
    else:
        stmt = select(database.Passenger).where((database.Passenger.email == data.credential) | (database.Passenger.mobile == data.credential))
    
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    user.is_active = True
    user.verified = True
    
    # 3. Trust the device immediately (Device Fingerprinting)
    device_uuid = data.device_uuid or str(uuid.uuid4())
    new_trust = database.TrustedDevice(
        user_id=user.id,
        role=data.role,
        device_uuid=device_uuid,
        last_verified=datetime.utcnow()
    )
    db.add(new_trust)
    
    await db.commit()
    
    token = auth_utils.create_access_token(data={"id": user.id, "role": data.role})
    
    return {
        "access_token": token,
        "token_type": "bearer",
        "user_id": user.id,
        "device_uuid": device_uuid,
        "message": "Account verified and device registered."
    }

@app.post("/api/login")
async def login(data: UserLogin, db: AsyncSession = Depends(database.get_db)):
    if data.role == 'driver':
        stmt = select(database.Driver).where((database.Driver.email == data.credential) | (database.Driver.mobile == data.credential))
    else:
        stmt = select(database.Passenger).where((database.Passenger.email == data.credential) | (database.Passenger.mobile == data.credential))
        
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()
    
    if not user or not auth_utils.verify_password(data.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    # Device awareness logic
    is_trusted = False
    if data.device_uuid:
        trust_stmt = select(database.TrustedDevice).where(
            database.TrustedDevice.user_id == user.id,
            database.TrustedDevice.device_uuid == data.device_uuid,
            database.TrustedDevice.is_active == True,
            database.TrustedDevice.last_verified > datetime.utcnow() - timedelta(days=30)
        )
        trust_res = await db.execute(trust_stmt)
        if trust_res.scalar_one_or_none():
            is_trusted = True

    if is_trusted:
        token = auth_utils.create_access_token(data={"id": user.id, "role": data.role})
        return {"access_token": token, "token_type": "bearer", "user_id": user.id, "device_trusted": True}
    
    # If not trusted, trigger OTP flow
    otp = await OTPManager.create_otp(db, data.credential, data.role)
    
    # Mock Twilio flow - print to console
    print(f"\n[LOGIN OTP] Sending secure OTP {otp} to user {user.id} ({user.mobile})\n")
    
    return {
        "detail": "OTP_REQUIRED",
        "message": "A new device was detected. Please verify with OTP.",
        "status_code": 202
    }

@app.post("/api/auth/verify-otp")
async def verify_otp(request: Request, data: OTPVerifyRequest, db: AsyncSession = Depends(database.get_db)):
    ip = request.client.host
    if await OTPManager.is_ip_blocked(db, ip):
        raise HTTPException(status_code=429, detail="Too many attempts. Your IP is blocked for 10 minutes.")

    # 1. Verify credentials again
    if data.role == 'driver':
        stmt = select(database.Driver).where((database.Driver.email == data.credential) | (database.Driver.mobile == data.credential))
    else:
        stmt = select(database.Passenger).where((database.Passenger.email == data.credential) | (database.Passenger.mobile == data.credential))
    
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()
    
    if not user or not auth_utils.verify_password(data.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    # 2. Check OTP using OTPManager
    success, message = await OTPManager.verify_otp(db, data.credential, data.role, data.otp)
    if not success:
        if "Too many failed attempts" in message:
            await OTPManager.block_ip(db, ip)
            raise HTTPException(status_code=429, detail="Too many attempts. Your IP is blocked for 10 minutes.")
        raise HTTPException(status_code=400, detail=message)

    # 3. Trust the device
    device_uuid = data.device_uuid or str(uuid.uuid4())
    
    # Upsert trusted device
    trust_stmt = select(database.TrustedDevice).where(
        database.TrustedDevice.user_id == user.id,
        database.TrustedDevice.device_uuid == device_uuid
    )
    trust_res = await db.execute(trust_stmt)
    trust_record = trust_res.scalar_one_or_none()
    
    if trust_record:
        trust_record.last_verified = datetime.utcnow()
        trust_record.is_active = True
    else:
        new_trust = database.TrustedDevice(
            user_id=user.id,
            role=data.role,
            device_uuid=device_uuid,
            last_verified=datetime.utcnow()
        )
        db.add(new_trust)
    
    await db.commit()
    
    token = auth_utils.create_access_token(data={"id": user.id, "role": data.role})
    
    return {
        "access_token": token,
        "token_type": "bearer",
        "user_id": user.id,
        "device_uuid": device_uuid
    }

@app.get("/api/me")
async def get_me(current: dict = Depends(auth_utils.get_current_user)):
    user = current["user"]
    role = current["role"]
    
    # Standardize response for frontend
    if role == "driver":
        return {
            "id": user.id,
            "name": user.name,
            "age": user.age,
            "mobile": user.mobile,
            "email": user.email,
            "vehicle_number": user.vehicle_number,
            "rc_number": user.rc_number,
            "pick_location": user.pick_location,
            "rating": user.rating,
            "total_rides": user.total_rides,
            "balance": user.balance,
            "photo": user.photo or f"https://i.pravatar.cc/300?u={user.id}",
            "vehicle_type": user.vehicle_type,
            "role": "driver"
        }
    else:
        return {
            "id": user.id,
            "name": user.name,
            "mobile": user.mobile,
            "email": user.email,
            "balance": user.balance,
            "trips": user.trips,
            "photo": user.photo or f"https://i.pravatar.cc/300?u={user.id}",
            "joined_date": user.joined_date or "Mar 2026",
            "role": "passenger"
        }

# ── Core Feature: Nearby Drivers ──────────────────────────────────────────
@app.get("/api/nearby-drivers")
async def get_nearby_drivers(lat: float, lng: float, radius: float = 5000, db: AsyncSession = Depends(database.get_db)):
    """Find drivers within X meters using Haversine algorithm."""
    stmt = select(database.Driver).where(database.Driver.is_active == True, database.Driver.last_lat != None)
    result = await db.execute(stmt)
    drivers = result.scalars().all()
    
    nearby = []
    for d in drivers:
        dist = haversine_distance(lat, lng, d.last_lat, d.last_lng)
        if dist <= radius:
            nearby.append({
                "id": d.id,
                "name": d.name,
                "vehicle_type": d.vehicle_type,
                "rating": d.rating,
                "distance_meters": round(dist),
                "lat": d.last_lat,
                "lng": d.last_lng
            })
    
    return sorted(nearby, key=lambda x: x['distance_meters'])

# ── Driver Actions ────────────────────────────────────────────────────────
@app.post("/api/location/update")
async def update_location(lat: float, lng: float, current: dict = Depends(auth_utils.get_current_user), db: AsyncSession = Depends(database.get_db)):
    if current['role'] != 'driver':
        raise HTTPException(status_code=403, detail="Forbidden")
    
    driver_id = current['user'].id
    stmt = update(database.Driver).where(database.Driver.id == driver_id).values(last_lat=lat, last_lng=lng)
    await db.execute(stmt)
    await db.commit()
    return {"status": "location updated"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
