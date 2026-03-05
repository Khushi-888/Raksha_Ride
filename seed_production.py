import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import database
import auth_utils
import uuid
from datetime import datetime

async def seed_data():
    async with database.SessionLocal() as db:
        # Check if users already exist
        stmt = select(database.Passenger).where(database.Passenger.mobile == "1234567890")
        res = await db.execute(stmt)
        if res.scalar_one_or_none():
            print("Users already seeded.")
            return

        print("Seeding test users...")
        
        # 1. Create a Test Passenger
        test_pax = database.Passenger(
            id="USR-6001",
            name="Khushi Test",
            mobile="1234567890",
            email="khushi@test.com",
            password_hash=auth_utils.get_password_hash("pass123"),
            balance=500.0,
            trips=5,
            photo="https://api.dicebear.com/7.x/avataaars/svg?seed=Khushi",
            joined_date=datetime.utcnow().strftime("%Y-%m-%d")
        )
        db.add(test_pax)

        # 2. Create a Test Driver (Active)
        test_drv = database.Driver(
            id="DRV-2001",
            name="Rajesh Test",
            mobile="9876543210",
            email="rajesh@test.com",
            password_hash=auth_utils.get_password_hash("pass123"),
            vehicle_number="MH12-RN-1234",
            rc_number="RC987654321",
            pick_location="Pune Station",
            rating=4.8,
            is_active=True,
            last_lat=18.5204,
            last_lng=73.8567,
            photo="https://api.dicebear.com/7.x/avataaars/svg?seed=Rajesh"
        )
        db.add(test_drv)

        await db.commit()
        print("Production DB Seeded successfully!")

if __name__ == "__main__":
    asyncio.run(seed_data())
