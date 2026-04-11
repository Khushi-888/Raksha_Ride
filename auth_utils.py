"""
RakshaRide - JWT Authentication Utilities
Handles token generation, validation, and user extraction
"""
import jwt
import sqlite3
from datetime import datetime, timedelta
from functools import wraps
from flask import request, jsonify, session

JWT_SECRET = 'raksharide-jwt-secret-2024-secure'
JWT_ALGORITHM = 'HS256'
JWT_EXPIRY_HOURS = 24
DB_PATH = 'database_enhanced.db'


def generate_token(user_id: int, user_type: str, name: str) -> str:
    """Generate a JWT token for authenticated user"""
    payload = {
        'user_id': user_id,
        'user_type': user_type,
        'name': name,
        'iat': datetime.utcnow(),
        'exp': datetime.utcnow() + timedelta(hours=JWT_EXPIRY_HOURS)
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def decode_token(token: str) -> dict | None:
    """Decode and validate a JWT token. Returns payload or None."""
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None


def get_current_user():
    """
    Extract authenticated user from request.
    Checks (in order):
      1. Authorization: Bearer <token> header
      2. X-Auth-Token header
      3. Flask session (fallback for cookie-based auth)
    Returns dict with user_id, user_type, name — or None.
    """
    # 1. Check Authorization header
    auth_header = request.headers.get('Authorization', '')
    if auth_header.startswith('Bearer '):
        token = auth_header[7:]
        payload = decode_token(token)
        if payload:
            return payload

    # 2. Check X-Auth-Token header
    token = request.headers.get('X-Auth-Token', '')
    if token:
        payload = decode_token(token)
        if payload:
            return payload

    # 3. Fallback: Flask session
    if 'user_id' in session:
        return {
            'user_id': session['user_id'],
            'user_type': session.get('user_type', ''),
            'name': session.get('user_name') or session.get('name', '')
        }

    return None


def require_auth(user_type: str = None):
    """
    Decorator factory for protecting routes.
    Usage:
        @require_auth()           — any logged-in user
        @require_auth('passenger') — only passengers
        @require_auth('driver')    — only drivers
    """
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            user = get_current_user()
            if not user:
                return jsonify({
                    "success": False,
                    "message": "Authentication required. Please login.",
                    "code": "AUTH_REQUIRED"
                }), 401
            if user_type and user.get('user_type') != user_type:
                return jsonify({
                    "success": False,
                    "message": f"Access denied. {user_type.capitalize()} account required.",
                    "code": "WRONG_ROLE"
                }), 403
            # Inject user into kwargs
            kwargs['current_user'] = user
            return f(*args, **kwargs)
        return wrapper
    return decorator
