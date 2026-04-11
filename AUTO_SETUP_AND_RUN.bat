@echo off
echo ========================================
echo   RakshaRide - Auto Setup and Run
echo ========================================
echo.

echo [1/4] Installing dependencies...
pip install -q flask flask-cors pillow qrcode cryptography 2>nul
if errorlevel 1 (
    echo Installing dependencies...
    pip install flask flask-cors pillow qrcode cryptography
)
echo ✓ Dependencies installed
echo.

echo [2/4] Checking database...
if exist database_enhanced.db (
    echo ✓ Database exists
) else (
    echo Creating database...
)
echo.

echo [3/4] Verifying files...
if exist app_enhanced.py (
    echo ✓ Backend ready
) else (
    echo ✗ Backend missing!
    pause
    exit /b 1
)

if exist templates\driver_register_new.html (
    echo ✓ Templates ready
) else (
    echo ✗ Templates missing!
    pause
    exit /b 1
)

if exist static\css\theme.css (
    echo ✓ Theme CSS ready
) else (
    echo ✗ Theme CSS missing!
    pause
    exit /b 1
)
echo.

echo [4/4] Starting RakshaRide...
echo.
echo ========================================
echo   Server starting at:
echo   http://localhost:5000
echo ========================================
echo.
echo ✓ All changes applied automatically
echo ✓ Beautiful yellow + blue design active
echo ✓ Light/Dark mode enabled
echo ✓ Owner/Rent registration ready
echo.
echo Press Ctrl+C to stop the server
echo.

python app_enhanced.py
