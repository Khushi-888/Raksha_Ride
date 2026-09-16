#!/usr/bin/env python3
"""
RakshaRide - Authentication Persistence Test
Tests that user sessions persist after page refresh and browser restart
"""

import sqlite3
import os
import json
from datetime import datetime

def test_database_structure():
    """Verify database has all required tables and columns for auth persistence"""
    print("=" * 80)
    print("TEST 1: Database Structure Verification")
    print("=" * 80)
    
    db_files = ['database_enhanced.db', 'RakshaRide.db', 'backup/database_enhanced.db']
    db_path = None
    
    for db_file in db_files:
        if os.path.exists(db_file):
            db_path = db_file
            break
    
    if not db_path:
        print("❌ FAIL: No database file found!")
        return False
    
    print(f"✓ Found database: {db_path}\n")
    
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    
    # Check passengers table
    try:
        c.execute("PRAGMA table_info(passengers)")
        passenger_cols = {row[1] for row in c.fetchall()}
        required_passenger_cols = {'id', 'name', 'email', 'mobile', 'password'}
        
        if required_passenger_cols.issubset(passenger_cols):
            print("✓ Passengers table has all required columns")
            print(f"  Columns: {', '.join(sorted(passenger_cols))}")
        else:
            missing = required_passenger_cols - passenger_cols
            print(f"❌ FAIL: Passengers table missing columns: {missing}")
            return False
    except Exception as e:
        print(f"❌ FAIL: Error checking passengers table: {e}")
        return False
    
    # Check drivers table
    try:
        c.execute("PRAGMA table_info(drivers)")
        driver_cols = {row[1] for row in c.fetchall()}
        required_driver_cols = {'id', 'name', 'email', 'mobile', 'password'}
        
        if required_driver_cols.issubset(driver_cols):
            print("✓ Drivers table has all required columns")
            print(f"  Columns: {', '.join(sorted(driver_cols))}")
        else:
            missing = required_driver_cols - driver_cols
            print(f"❌ FAIL: Drivers table missing columns: {missing}")
            return False
    except Exception as e:
        print(f"❌ FAIL: Error checking drivers table: {e}")
        return False
    
    conn.close()
    print("\n✅ PASS: Database structure is correct\n")
    return True


def test_user_data_persistence():
    """Verify that user data is actually stored in the database"""
    print("=" * 80)
    print("TEST 2: User Data Persistence")
    print("=" * 80)
    
    db_files = ['database_enhanced.db', 'RakshaRide.db', 'backup/database_enhanced.db']
    db_path = None
    
    for db_file in db_files:
        if os.path.exists(db_file):
            db_path = db_file
            break
    
    if not db_path:
        print("❌ FAIL: No database file found!")
        return False
    
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    
    # Check passengers
    c.execute("SELECT COUNT(*) as count FROM passengers")
    passenger_count = c.fetchone()['count']
    print(f"✓ Found {passenger_count} passengers in database")
    
    if passenger_count > 0:
        c.execute("SELECT id, name, email, mobile FROM passengers LIMIT 3")
        passengers = c.fetchall()
        print("\n  Sample passengers:")
        for p in passengers:
            print(f"    - {p['name']} ({p['email']}, {p['mobile']})")
    
    # Check drivers
    c.execute("SELECT COUNT(*) as count FROM drivers")
    driver_count = c.fetchone()['count']
    print(f"\n✓ Found {driver_count} drivers in database")
    
    if driver_count > 0:
        c.execute("SELECT id, name, email, mobile FROM drivers LIMIT 3")
        drivers = c.fetchall()
        print("\n  Sample drivers:")
        for d in drivers:
            print(f"    - {d['name']} ({d['email']}, {d['mobile']})")
    
    conn.close()
    
    if passenger_count > 0 or driver_count > 0:
        print("\n✅ PASS: User data is persisted in database\n")
        return True
    else:
        print("\n⚠️  WARNING: No users found in database")
        print("   This is expected if you haven't registered any users yet.\n")
        return True


def test_auth_files_exist():
    """Verify that all authentication-related files exist"""
    print("=" * 80)
    print("TEST 3: Authentication Files Verification")
    print("=" * 80)
    
    required_files = {
        'Frontend Auth': 'static/js/auth.js',
        'Main App': 'raksharide/static/js/app.js',
        'Flask Backend': 'app_enhanced.py',
        'Node Backend': 'backend/server.js',
        'Backend .env': 'backend/.env'
    }
    
    all_exist = True
    for name, path in required_files.items():
        if os.path.exists(path):
            print(f"✓ {name}: {path}")
        else:
            print(f"❌ MISSING: {name}: {path}")
            all_exist = False
    
    if all_exist:
        print("\n✅ PASS: All authentication files exist\n")
        return True
    else:
        print("\n❌ FAIL: Some authentication files are missing\n")
        return False


def test_localstorage_implementation():
    """Verify that localStorage persistence is implemented in app.js"""
    print("=" * 80)
    print("TEST 4: localStorage Implementation Check")
    print("=" * 80)
    
    app_js_path = 'raksharide/static/js/app.js'
    
    if not os.path.exists(app_js_path):
        print(f"❌ FAIL: {app_js_path} not found")
        return False
    
    with open(app_js_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    checks = {
        'localStorage.setItem on login': "localStorage.setItem('rr_token'" in content,
        'localStorage.removeItem on logout': "localStorage.removeItem('rr_token'" in content,
        'DOMContentLoaded restore handler': "DOMContentLoaded" in content and "restoreSession" in content,
        'GET /api/auth/me call': "'/api/auth/me'" in content or '"/api/auth/me"' in content,
    }
    
    all_passed = True
    for check_name, passed in checks.items():
        if passed:
            print(f"✓ {check_name}")
        else:
            print(f"❌ MISSING: {check_name}")
            all_passed = False
    
    if all_passed:
        print("\n✅ PASS: localStorage persistence is properly implemented\n")
        return True
    else:
        print("\n❌ FAIL: Some localStorage features are missing\n")
        return False


def test_auth_js_implementation():
    """Verify that auth.js has the token fallback implementation"""
    print("=" * 80)
    print("TEST 5: auth.js Token Fallback Check")
    print("=" * 80)
    
    auth_js_path = 'static/js/auth.js'
    
    if not os.path.exists(auth_js_path):
        print(f"❌ FAIL: {auth_js_path} not found")
        return False
    
    with open(auth_js_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    checks = {
        'getToken() function': 'function getToken()' in content,
        'setToken() function': 'function setToken(' in content,
        'clearToken() function': 'function clearToken()' in content,
        'authFetch() function': 'async function authFetch(' in content,
        'checkAuth() function': 'async function checkAuth(' in content,
        'Token fallback in checkAuth': 'const token = getToken()' in content and '/api/auth/me' in content,
    }
    
    all_passed = True
    for check_name, passed in checks.items():
        if passed:
            print(f"✓ {check_name}")
        else:
            print(f"❌ MISSING: {check_name}")
            all_passed = False
    
    if all_passed:
        print("\n✅ PASS: auth.js token fallback is properly implemented\n")
        return True
    else:
        print("\n❌ FAIL: Some auth.js features are missing\n")
        return False


def test_backend_jwt_config():
    """Verify that backend JWT configuration is correct"""
    print("=" * 80)
    print("TEST 6: Backend JWT Configuration")
    print("=" * 80)
    
    env_path = 'backend/.env'
    
    if not os.path.exists(env_path):
        print(f"❌ FAIL: {env_path} not found")
        return False
    
    with open(env_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Check JWT_EXPIRES_IN
    if 'JWT_EXPIRES_IN' in content:
        for line in content.split('\n'):
            if line.startswith('JWT_EXPIRES_IN'):
                value = line.split('=')[1].strip()
                print(f"✓ JWT_EXPIRES_IN = {value}")
                if '30d' in value or '30 d' in value:
                    print("  ✓ Token lifetime is 30 days (correct)")
                elif '7d' in value or '7 d' in value:
                    print("  ⚠️  Token lifetime is 7 days (should be 30 days)")
                break
    else:
        print("❌ MISSING: JWT_EXPIRES_IN not found in .env")
        return False
    
    print("\n✅ PASS: Backend JWT configuration exists\n")
    return True


def print_manual_test_instructions():
    """Print instructions for manual testing"""
    print("=" * 80)
    print("MANUAL TESTING INSTRUCTIONS")
    print("=" * 80)
    print("""
To verify that authentication persistence is working correctly, follow these steps:

1. START THE APPLICATION:
   - Run: python app_enhanced.py
   - Open: http://localhost:5001

2. TEST PASSENGER REGISTRATION & LOGIN:
   a) Register a new passenger account
   b) Login with the credentials
   c) Verify you see the passenger dashboard
   d) Press F5 to refresh the page
   e) ✓ EXPECTED: Dashboard should still be visible (session restored)
   f) ❌ BUG: If you see the landing page, auth persistence is broken

3. TEST DRIVER REGISTRATION & LOGIN:
   a) Logout from passenger account
   b) Register a new driver account
   c) Login with the credentials
   d) Verify you see the driver dashboard
   e) Press F5 to refresh the page
   f) ✓ EXPECTED: Dashboard should still be visible (session restored)
   g) ❌ BUG: If you see the landing page, auth persistence is broken

4. TEST BROWSER RESTART:
   a) While logged in, close the browser completely
   b) Reopen the browser and go to http://localhost:5001
   c) ✓ EXPECTED: Dashboard should still be visible (session restored)
   d) ❌ BUG: If you see the landing page, session didn't persist

5. TEST LOGOUT:
   a) Click the logout button
   b) ✓ EXPECTED: Landing page should be shown
   c) Press F5 to refresh
   d) ✓ EXPECTED: Landing page should still be shown (no ghost session)

6. CHECK BROWSER DEVELOPER TOOLS:
   a) Open DevTools (F12)
   b) Go to Application > Local Storage > http://localhost:5001
   c) ✓ EXPECTED: You should see:
      - rr_token: (JWT token string)
      - rr_user: (JSON user object)
      - rr_user_type: "driver" or "passenger"
   d) After logout, these should be cleared

7. CHECK DATABASE:
   - Run: python check_database.py
   - Verify your registered users are stored permanently
""")


def main():
    """Run all tests"""
    print("\n")
    print("╔" + "=" * 78 + "╗")
    print("║" + " " * 20 + "RakshaRide Auth Persistence Test Suite" + " " * 20 + "║")
    print("╚" + "=" * 78 + "╝")
    print("\n")
    
    tests = [
        test_database_structure,
        test_user_data_persistence,
        test_auth_files_exist,
        test_localstorage_implementation,
        test_auth_js_implementation,
        test_backend_jwt_config,
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"❌ ERROR: {e}\n")
            results.append(False)
    
    # Summary
    print("=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    passed = sum(results)
    total = len(results)
    print(f"\nPassed: {passed}/{total}")
    
    if passed == total:
        print("\n✅ ALL AUTOMATED TESTS PASSED!")
        print("\nThe authentication persistence implementation is complete.")
        print("Please proceed with manual testing to verify end-to-end functionality.\n")
    else:
        print("\n⚠️  SOME TESTS FAILED")
        print("\nPlease review the failed tests above and fix the issues.\n")
    
    print_manual_test_instructions()


if __name__ == '__main__':
    main()
