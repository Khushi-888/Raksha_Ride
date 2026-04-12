"""
RakshaRide WSGI entry point — production ready for Render.
"""
import os
from app_enhanced import app, init_db

# Initialize database on startup
init_db()
