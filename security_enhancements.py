"""
RakshaRide Security Module
Handles: Document encryption, Dynamic HMAC QR codes, Unique ID generation, Admin auth
"""

import os
import hmac
import hashlib
import secrets
import base64
import json
from datetime import datetime, timedelta
from cryptography.fernet import Fernet

# ─── Encryption Key Management ───────────────────────────────────────────────
# Key is stored in a local file (outside static/) so it persists across restarts.
KEY_FILE = "document_encryption.key"

def load_or_create_fernet_key():
    """Load Fernet key from file, or generate and save a new one."""
    if os.path.exists(KEY_FILE):
        with open(KEY_FILE, "rb") as f:
            return f.read()
    key = Fernet.generate_key()
    with open(KEY_FILE, "wb") as f:
        f.write(key)
    print(f"[OK] New document encryption key generated -> {KEY_FILE}")
    return key

FERNET_KEY = load_or_create_fernet_key()
_fernet = Fernet(FERNET_KEY)

def encrypt_document(base64_data_uri: str) -> str:
    """Encrypt a base64 data-URI string. Returns encrypted bytes as base64 string."""
    raw = base64_data_uri.encode("utf-8")
    encrypted = _fernet.encrypt(raw)
    return base64.b64encode(encrypted).decode("utf-8")

def decrypt_document(encrypted_b64: str) -> str:
    """Decrypt back to original base64 data-URI string."""
    encrypted = base64.b64decode(encrypted_b64.encode("utf-8"))
    return _fernet.decrypt(encrypted).decode("utf-8")

# ─── HMAC QR Code Signing ────────────────────────────────────────────────────
QR_SECRET = os.environ.get("RAKSHA_QR_SECRET", "raksha-qr-secret-2024-dynamic")
QR_VALIDITY_MINUTES = 15  # QR expires after 15 minutes

def sign_qr_payload(driver_id: int, driver_name: str, vehicle_number: str, mobile: str) -> dict:
    """Create a time-limited, HMAC-signed QR payload."""
    issued_at = datetime.utcnow()
    expires_at = issued_at + timedelta(minutes=QR_VALIDITY_MINUTES)
    token = secrets.token_hex(8)  # one-time nonce

    payload = {
        "type": "driver",
        "driver_id": driver_id,
        "name": driver_name,
        "vehicle": vehicle_number,
        "mobile": mobile,
        "issued_at": issued_at.isoformat(),
        "expires_at": expires_at.isoformat(),
        "nonce": token,
    }

    # Sign the canonical payload
    message = json.dumps(payload, sort_keys=True).encode("utf-8")
    signature = hmac.new(QR_SECRET.encode("utf-8"), message, hashlib.sha256).hexdigest()
    payload["sig"] = signature
    return payload

def verify_qr_payload(qr_data_str: str) -> tuple[bool, str, dict]:
    """
    Verify HMAC signature and expiry.
    Returns (is_valid, error_message, payload_dict)
    """
    try:
        payload = json.loads(qr_data_str)
    except Exception:
        return False, "Invalid QR format", {}

    sig = payload.pop("sig", None)
    if not sig:
        # Support legacy unsigned QR codes (pre-enhancement)
        return True, "", payload

    # Re-compute signature
    message = json.dumps(payload, sort_keys=True).encode("utf-8")
    expected_sig = hmac.new(QR_SECRET.encode("utf-8"), message, hashlib.sha256).hexdigest()

    if not hmac.compare_digest(sig, expected_sig):
        return False, "Invalid QR signature — possible tampering detected", {}

    # Check expiry
    try:
        expires_at = datetime.fromisoformat(payload["expires_at"])
        if datetime.utcnow() > expires_at:
            return False, f"QR code expired. Please ask the driver to refresh their QR.", {}
    except Exception:
        pass  # Legacy QR without expiry — allow

    payload["sig"] = sig  # Restore
    return True, "", payload

# ─── Unique ID Generation ─────────────────────────────────────────────────────
def generate_unique_id(prefix: str) -> str:
    """Generate a human-readable unique ID, e.g. PSR-A3F7C or DRV-B92D1"""
    suffix = secrets.token_hex(3).upper()
    return f"{prefix}-{suffix}"

# ─── Admin Password Utilities ─────────────────────────────────────────────────
def hash_admin_password(password: str) -> str:
    """Hash admin password with SHA-256 (same as user passwords for consistency)."""
    return hashlib.sha256(password.encode()).hexdigest()

def verify_admin_password(password: str, hashed: str) -> bool:
    return hash_admin_password(password) == hashed

# ─── Aadhaar Number Masking ───────────────────────────────────────────────────
def mask_aadhaar(aadhaar: str) -> str:
    """Return masked Aadhaar: XXXX XXXX 1234"""
    digits = "".join(filter(str.isdigit, aadhaar))
    if len(digits) != 12:
        return "XXXX XXXX " + digits[-4:] if len(digits) >= 4 else "Invalid"
    return f"XXXX XXXX {digits[-4:]}"
