import os
import secrets
import datetime
from sqlalchemy import select, delete, update
from sqlalchemy.ext.asyncio import AsyncSession
import database

# New API Integrations
from nodemailer_api import nodemailer
from twilio_mock import twilio

class OTPManager:
    @staticmethod
    def generate_otp(length=6):
        """Generates a secure, random n-digit OTP using CSPRNG."""
        return "".join(secrets.choice("0123456789") for _ in range(length))

    @staticmethod
    def _is_email(credential: str):
        """Simple helper to detect if a credential is an email."""
        return "@" in credential

    @staticmethod
    async def create_otp(db: AsyncSession, credential: str, role: str, expiry_minutes=5):
        """Generates and stores an OTP in the database."""
        # Delete any existing OTP for this credential
        stmt = delete(database.PendingVerification).where(
            database.PendingVerification.credential == credential,
            database.PendingVerification.role == role
        )
        await db.execute(stmt)

        otp = OTPManager.generate_otp()
        expiry = datetime.datetime.utcnow() + datetime.timedelta(minutes=expiry_minutes)
        
        new_otp = database.PendingVerification(
            credential=credential,
            role=role,
            otp=otp,
            expires_at=expiry
        )
        db.add(new_otp)
        await db.commit()

        # Handle delivery via new services
        subject = "Your RakshaRide Verification Code"
        body = f"Your secure OTP is: {otp}. It expires in {expiry_minutes} minutes. Please do not share this with anyone."

        if OTPManager._is_email(credential):
            await nodemailer.send_mail(credential, subject, body)
        else:
            await twilio.send_sms(credential, body)
            
        return otp

    @staticmethod
    async def verify_otp(db: AsyncSession, credential: str, role: str, otp: str):
        """Verifies the OTP and handles attempts/expiry."""
        stmt = select(database.PendingVerification).where(
            database.PendingVerification.credential == credential,
            database.PendingVerification.role == role
        )
        result = await db.execute(stmt)
        record = result.scalar_one_or_none()

        if not record:
            return False, "OTP not found. Please request a new one."

        if datetime.datetime.utcnow() > record.expires_at:
            await db.delete(record)
            await db.commit()
            return False, "OTP has expired."

        if record.otp != otp:
            record.attempts += 1
            await db.commit()
            if record.attempts >= 3:
                # Optionally handle IP blocking here or in the caller
                return False, "Too many failed attempts."
            return False, f"Invalid OTP. {3 - record.attempts} attempts remaining."

        # Success - clean up
        await db.delete(record)
        await db.commit()
        return True, "Verified"

    @staticmethod
    async def is_ip_blocked(db: AsyncSession, ip_address: str):
        """Checks if an IP address is currently blocked."""
        stmt = select(database.BlockedIP).where(database.BlockedIP.ip_address == ip_address)
        result = await db.execute(stmt)
        record = result.scalar_one_or_none()
        
        if record:
            if datetime.datetime.utcnow() < record.blocked_until:
                return True
            else:
                await db.delete(record)
                await db.commit()
        return False

    @staticmethod
    async def block_ip(db: AsyncSession, ip_address: str, duration_minutes=10):
        """Blocks an IP address for a specified duration."""
        expiry = datetime.datetime.utcnow() + datetime.timedelta(minutes=duration_minutes)
        new_block = database.BlockedIP(ip_address=ip_address, blocked_until=expiry)
        db.add(new_block)
        await db.commit()
