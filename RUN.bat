@echo off
title RakshaRide
color 0A
cls
cd /d "%~dp0"

echo.
echo  ==========================================
echo    RAKSHARIDE - Starting...
echo  ==========================================
echo.
echo  Installing/checking packages...
pip install flask flask-cors pillow qrcode cryptography -q --disable-pip-version-check

echo.
echo  ==========================================
echo    Open browser: http://localhost:5000
echo  ==========================================
echo.

python app_enhanced.py

pause
