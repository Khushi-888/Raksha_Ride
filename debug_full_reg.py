import asyncio
import os
import sys
import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

# Ensure current directory is in path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import database
import auth_utils
from otp_manager import OTPManager

async def debug_full_registration():
    print("Initialising DB...")
    await database.init_production_db()
    
    async with database.SessionLocal() as db:
        mobile = "9999999995"
        print(f"Checking if user {mobile} exists...")
        stmt = select(database.Passenger).where(database.Passenger.mobile == mobile)
        result = await db.execute(stmt)
        if result.scalar_one_or_none():
            print("User already exists, deleting for test...")
            # Clean up for test
            from sqlalchemy import delete
            await db.execute(delete(database.Passenger).where(database.Passenger.mobile == mobile))
            await db.commit()

        print("Creating new passenger...")
        new_id = f"USR-{uuid.uuid4().hex[:6]}"
        new_pax = database.Passenger(
            id=new_id,
            name="Debug User",
            mobile=mobile,
            password_hash=auth_utils.get_password_hash("password123"),
            is_active=False
        )
        db.add(new_pax)
        await db.commit()
        print("Passenger committed.")

        print("Triggering OTP flow...")
        try:
            # Re-fetch session or reuse it? main.py reuses it correctly.
            otp = await OTPManager.create_otp(db, mobile, "passenger")
            print(f"OTP created successfully: {otp}")
        except Exception as e:
            import traceback
            print(f"FAILED with exception: {e}")
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(debug_full_registration())
