import asyncio
import os
import sys
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

# Ensure current directory is in path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import database
from otp_manager import OTPManager

async def debug_create_otp():
    print("Initializing DB...")
    await database.init_production_db()
    
    async with database.SessionLocal() as db:
        print("Attempting to create OTP for new user...")
        try:
            otp = await OTPManager.create_otp(db, "9999999998", "passenger")
            print(f"OTP created successfully: {otp}")
        except Exception as e:
            import traceback
            print(f"FAILED with exception: {e}")
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(debug_create_otp())
