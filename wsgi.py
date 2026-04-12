"""
RakshaRide WSGI entry point — optimized for Render free tier.
Uses lazy imports to reduce startup memory.
"""
import os

# Patch for gevent before anything else
from gevent import monkey
monkey.patch_all()

from app_enhanced import app, init_db

# Initialize DB on startup
init_db()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
