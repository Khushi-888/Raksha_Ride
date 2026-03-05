import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import String, Integer, Float, Boolean, DateTime, ForeignKey
from datetime import datetime
from typing import Optional

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE_URL = f"sqlite+aiosqlite:///{os.path.join(BASE_DIR, 'production_database.db')}"

engine = create_async_engine(DATABASE_URL)
SessionLocal = async_sessionmaker(autocommit=False, autoflush=False, bind=engine, class_=AsyncSession)

class Base(DeclarativeBase):
    pass

class Driver(Base):
    __tablename__ = "verified_drivers"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    name: Mapped[str] = mapped_column(String)
    age: Mapped[Optional[int]] = mapped_column(Integer)
    mobile: Mapped[str] = mapped_column(String, unique=True, index=True)
    email: Mapped[str] = mapped_column(String, unique=True, index=True)
    vehicle_number: Mapped[str] = mapped_column(String, unique=True)
    rc_number: Mapped[str] = mapped_column(String, unique=True)
    pick_location: Mapped[Optional[str]] = mapped_column(String)
    password_hash: Mapped[str] = mapped_column(String)
    rating: Mapped[float] = mapped_column(Float, default=4.5)
    total_rides: Mapped[int] = mapped_column(Integer, default=0)
    balance: Mapped[float] = mapped_column(Float, default=0.0)
    photo: Mapped[Optional[str]] = mapped_column(String)
    vehicle_type: Mapped[str] = mapped_column(String, default='Electric Eco-Rickshaw')
    verified: Mapped[bool] = mapped_column(Boolean, default=False)
    last_lat: Mapped[Optional[float]] = mapped_column(Float)
    last_lng: Mapped[Optional[float]] = mapped_column(Float)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

class Passenger(Base):
    __tablename__ = "passengers"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    name: Mapped[str] = mapped_column(String)
    mobile: Mapped[str] = mapped_column(String, unique=True, index=True)
    email: Mapped[Optional[str]] = mapped_column(String, unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String)
    balance: Mapped[float] = mapped_column(Float, default=0.0)
    trips: Mapped[int] = mapped_column(Integer, default=0)
    photo: Mapped[Optional[str]] = mapped_column(String)
    joined_date: Mapped[Optional[str]] = mapped_column(String)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    verified: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

class Alert(Base):
    __tablename__ = "alerts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    driver_id: Mapped[str] = mapped_column(String, ForeignKey("verified_drivers.id"))
    alert_type: Mapped[str] = mapped_column(String)
    lat: Mapped[Optional[float]] = mapped_column(Float)
    lng: Mapped[Optional[float]] = mapped_column(Float)
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

class Ride(Base):
    __tablename__ = "rides"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    driver_id: Mapped[str] = mapped_column(String, ForeignKey("verified_drivers.id"))
    passenger_id: Mapped[str] = mapped_column(String, ForeignKey("passengers.id"))
    start_lat: Mapped[Optional[float]] = mapped_column(Float)
    start_lng: Mapped[Optional[float]] = mapped_column(Float)
    end_lat: Mapped[Optional[float]] = mapped_column(Float)
    end_lng: Mapped[Optional[float]] = mapped_column(Float)
    fare: Mapped[Optional[float]] = mapped_column(Float)
    status: Mapped[str] = mapped_column(String, default='completed')
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

class TrustedDevice(Base):
    __tablename__ = "trusted_devices"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[str] = mapped_column(String, index=True)
    role: Mapped[str] = mapped_column(String)
    device_uuid: Mapped[str] = mapped_column(String, index=True)
    last_verified: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

class PendingVerification(Base):
    __tablename__ = "pending_verification"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    credential: Mapped[str] = mapped_column(String, index=True)
    role: Mapped[str] = mapped_column(String)
    otp: Mapped[str] = mapped_column(String)
    attempts: Mapped[int] = mapped_column(Integer, default=0)
    expires_at: Mapped[datetime] = mapped_column(DateTime)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

class BlockedIP(Base):
    __tablename__ = "blocked_ips"

    ip_address: Mapped[str] = mapped_column(String, primary_key=True)
    blocked_until: Mapped[datetime] = mapped_column(DateTime)

async def init_production_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

async def get_db():
    async with SessionLocal() as session:
        yield session
