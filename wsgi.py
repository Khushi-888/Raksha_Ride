"""
RakshaRide WSGI entry point — production ready for Render.
No gevent, no preload, standard sync workers.
"""
import os
from app_enhanced import app, init_db

# Initialize database tables on startup
init_db()
