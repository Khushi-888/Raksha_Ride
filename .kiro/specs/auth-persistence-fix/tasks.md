# Implementation Plan

- [x] 1. Write bug condition exploration test
  - **Property 1: Bug Condition** - Session Lost After Page Refresh
  - **CRITICAL**: This test MUST FAIL on unfixed code — failure confirms the bug exists
  - **DO NOT attempt to fix the test or the code when it fails**
  - **NOTE**: This test encodes the expected behavior — it will validate the fix when it passes after implementation
  - **GOAL**: Surface counterexamples that demonstrate that `currentUser` and `currentRole` are `null` after a page reload even when a valid token is in `localStorage`
  - **Scoped PBT Approach**: For this deterministic bug, scope the property to the concrete failing case: any logged-in user (driver or passenger) who refreshes the page
  - **Test setup**: Using jsdom or a browser test harness, load `raksharide/static/js/app.js` with `localStorage` pre-seeded with `rr_token`, `rr_user`, and `rr_user_type` (simulating a prior login)
  - **Test assertion**: After `DOMContentLoaded` fires, assert that `GET /api/auth/me` was called with `Authorization: Bearer <token>` AND that the driver/passenger dashboard is visible AND that the landing page is hidden
  - **Bug Condition from design**: `isBugCondition(X)` where `X.userLoggedIn = true AND X.pageRefreshed = true AND X.localStorageTokenExists = false` — on unfixed code, even when we manually seed `localStorage`, the IIFE has no `DOMContentLoaded` restore handler, so the session is never restored
  - **Expected Behavior from design**: `result.currentUser ≠ null AND result.currentRole ≠ null AND result.landingPageHidden = true AND result.dashboardVisible = true`
  - Run test on UNFIXED code
  - **EXPECTED OUTCOME**: Test FAILS (this is correct — it proves the bug exists; the landing page remains visible and `currentUser` stays `null`)
  - Document counterexamples found, e.g. "After seeding `rr_token='eyJ...'` in localStorage and firing DOMContentLoaded, `currentUser` is still `null` and `#landing` is still visible — no restore handler exists"
  - Mark task complete when test is written, run, and failure is documented
  - _Requirements: 1.2, 1.3, 1.4_

- [x] 2. Write preservation property tests (BEFORE implementing fix)
  - **Property 2: Preservation** - Non-Refresh Interactions Unchanged
  - **IMPORTANT**: Follow observation-first methodology — run the UNFIXED code first and record actual outputs before writing assertions
  - **Observe on UNFIXED code**:
    - `doLogout()` sets `currentUser = null`, `currentRole = null`, hides dashboards, shows landing — record this
    - Incorrect credentials in login form show error message, do not set `currentUser` — record this
    - When `localStorage` has no `rr_token`, the landing page is shown on load — record this
    - Dashboard sidebar navigation switches views correctly — record this
  - Write property-based tests capturing observed behavior patterns from Preservation Requirements in design:
    - **Logout property**: For any logged-in state, calling `doLogout()` always results in `currentUser = null`, `currentRole = null`, landing page visible, dashboards hidden
    - **Login error property**: For any credential pair where the email/mobile does not match a DB record, `currentUser` remains `null` and an error message is shown
    - **No-token landing property**: For any page load where `localStorage.getItem('rr_token')` returns `null` or `''`, the landing page is shown and no dashboard is visible
    - **Dashboard navigation property**: For any sidebar link click while logged in, the correct view becomes active and all other views are hidden
  - Property-based testing generates many test cases for stronger guarantees across the input domain
  - Run tests on UNFIXED code
  - **EXPECTED OUTCOME**: Tests PASS (this confirms baseline behavior to preserve)
  - Mark task complete when tests are written, run, and passing on unfixed code
  - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 3.8_

- [x] 3. Fix for auth session persistence after page refresh

  - [x] 3.1 Implement the fix in `raksharide/static/js/app.js`
    - In the `login-form` submit handler, after `currentUser = drv; currentRole = 'driver';`, add three `localStorage.setItem` calls: `rr_token` (from `drv._token || ''`), `rr_user` (JSON of `{id, name, role}`), `rr_user_type` (`'driver'`)
    - In the same handler, after `currentUser = pax; currentRole = 'passenger';`, add the same three `localStorage.setItem` calls with `role: 'passenger'`
    - In `doLogout()`, after `currentUser = null; currentRole = null;`, add `localStorage.removeItem` calls for `rr_token`, `rr_user`, and `rr_user_type`
    - At the end of the IIFE (before the closing `})();`), add a `DOMContentLoaded` listener named `restoreSession` that: reads `rr_token`, `rr_user`, `rr_user_type` from `localStorage`; returns early if any are missing; hides `landing`; calls `fetch('http://localhost:5001/api/auth/me', { headers: { 'Authorization': 'Bearer ' + savedToken } })`; on success restores `currentUser`/`currentRole` and calls `showDriverDashboard` or `showPassengerDashboard`; on 401 or network error clears `localStorage` and calls `show('landing')`
    - _Bug_Condition: `isBugCondition(X)` where `X.userLoggedIn = true AND X.pageRefreshed = true AND X.localStorageTokenExists = false` — fix eliminates this condition by writing to localStorage on login_
    - _Expected_Behavior: `result.currentUser ≠ null AND result.currentRole ≠ null AND result.landingPageHidden = true AND result.dashboardVisible = true` after DOMContentLoaded restore_
    - _Preservation: All logout, login-error, dashboard-navigation, ride-simulation, wallet, and no-token-landing behaviors must remain identical to pre-fix behavior_
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 2.7, 2.8_

  - [x] 3.2 Implement the fix in `backend/.env`
    - Change `JWT_EXPIRES_IN` from `7d` to `30d`
    - This extends the token lifetime so restored sessions remain valid for 30 days instead of 7
    - _Requirements: 2.2, 3.6_

  - [x] 3.3 Implement the fix in `raksharide/app.py`
    - After `app.secret_key = 'raksharide_premium_secret_key'`, add `app.permanent_session_lifetime = timedelta(days=30)` (`timedelta` is already imported)
    - Inside the `login()` route, after the `if user and check_password_hash(...)` check passes and before `session['user_id'] = user['id']`, add `session.permanent = True`
    - _Requirements: 2.6_

  - [x] 3.4 Implement the fix in `static/js/auth.js` checkAuth function
    - **CRITICAL**: This is the MAIN PENDING TASK that needs implementation
    - **Current Issue**: The `checkAuth()` function only checks `/api/session_check` and does not have a fallback to `GET /api/auth/me` when session check fails but a token exists in localStorage
    - **Required Change**: After `session_check` returns `logged_in: false`, check for a token via `getToken()` and fall back to `GET http://localhost:5001/api/auth/me`; if that succeeds (`r2.ok` and `d2.user` present), return `true`; otherwise call `clearToken()` and redirect to login
    - **Implementation Details**:
      - After the session_check fails (d.logged_in is false), add: `const token = getToken();`
      - If token exists, call: `const r2 = await authFetch('http://localhost:5001/api/auth/me');`
      - If r2 is ok and has d2.user, return true (session restored via token)
      - Otherwise, clear token and redirect to login as before
    - _Requirements: 2.4, 3.3_

  - [ ] 3.5 Verify bug condition exploration test now passes
    - **Property 1: Expected Behavior** - Session Restored After Page Refresh
    - **IMPORTANT**: Re-run the SAME test from task 1 — do NOT write a new test
    - The test from task 1 encodes the expected behavior: after `DOMContentLoaded` fires with `rr_token` in `localStorage`, `GET /api/auth/me` is called and the correct dashboard is shown
    - Run bug condition exploration test from step 1 against the FIXED code
    - **EXPECTED OUTCOME**: Test PASSES (confirms the `DOMContentLoaded` restore handler exists, calls the API, and restores the session)
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.7, 2.8_

  - [ ] 3.6 Verify preservation tests still pass
    - **Property 2: Preservation** - Non-Refresh Interactions Unchanged
    - **IMPORTANT**: Re-run the SAME tests from task 2 — do NOT write new tests
    - Run all preservation property tests from step 2 against the FIXED code
    - **EXPECTED OUTCOME**: Tests PASS (confirms no regressions — logout, login errors, no-token landing, and dashboard navigation all behave identically to pre-fix behavior)
    - Confirm all tests still pass after fix (no regressions)

- [ ] 4. Checkpoint — Ensure all tests pass
  - Re-run the full test suite (exploration test + all preservation tests)
  - Confirm Property 1 (Bug Condition) now PASSES on fixed code
  - Confirm Property 2 (Preservation) still PASSES on fixed code
  - Manually verify the end-to-end flow: driver login → page refresh → driver dashboard visible
  - Manually verify: passenger login → page refresh → passenger dashboard visible
  - Manually verify: login → logout → page refresh → landing page shown (no ghost session)
  - Manually verify: login → simulate expired token (mock 401 from `/api/auth/me`) → landing page shown, no crash
  - Ensure all tests pass; ask the user if questions arise
