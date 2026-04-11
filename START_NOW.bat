@echo off
title RakshaRide - Verified Safety Protocol
echo ==========================================
echo Starting RakshaRide Project...
echo ==========================================

cd raksharide

echo [*] Installing requirements...
pip install -r requirements.txt --quiet

echo [*] Initializing Database...
python init_db.py

echo [*] Launching Production Server...
start http://localhost:5000
python app.py

pause
