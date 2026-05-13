# Auth Persistence Fix — Bugfix Design

## Overview

After a successful login in RakshaRide, the user session is lost on every page refresh or browser
reload. The main frontend (`raksharide/static/js/app.js`) stores auth state exclusively in the
JavaScript variables `currentUser` and `currentRole` inside an IIFE — both are wiped when the page
unloads. The JWT token returned by the Node.js backend is discarded immediately after login. There
is no auto-restore logic on `DOMContentLoaded`, and the Flask backend never sets
`session.permanent = True`, so its server-side session also expires when the browser closes.

The fix is minimal and additive: persist the token and user data to `localStorage` on login, restore
them on startup via `GET /api/auth/me`, clear them on logout, extend the JWT lifetime to 30 days,
and make the Flask session permanent. No UI, routing, database schema, or feature changes are made.

---

## Glossary

- **Bug_Condition (C)**: The state that triggers the bug — a user has logged in (token was issued),
  the page is refreshed or reloaded, and no `localStorage` save/restore logic exists, so
  `currentUser` and `currentRole` are `null` after reload.
- **Property (P)**: The desired post-fix behavior — after a page refresh, `currentUser` and
  `currentRole` are restored from `localStorage` via `GET /api/auth/me`, and the correct dashboard
  is shown without requiring re-login.
- **Preservation**: All behaviors that must remain unchanged — explicit logout, login error
  handling, dashboard navigation, ride simulation, and rejection of expired/invalid tokens.
- **`currentUser`**: The in-memory variable in `raksharide/static/js/app.js` that holds the
  logged-in user record. Lives only for the page lifetime.
- **`currentRole`**: The in-memory variable in `raksharide/static/js/app.js` that holds
  `'driver'` or `'passenger'`. Lives only for the page lifetime.
- **`rr_token`**: The `localStorage` key used by both `app.js` (after fix) and
  `frontend/static/static/js/auth.js` to store the JWT token.
- **`rr_user_type`**: The `localStorage` key used by `frontend/static/static/js/auth.js` to store
  the user role. `app.js` will write this key on login so both frontends stay consistent.
- **`GET /api/auth/me`**: The existing Node.js route (port 5001) protected by the `protect`
  middleware that validates a Bearer token and returns the current user record. No changes needed.
- **`doLogout()`**: The function in `app.js` that clears in-memory state and shows the landing
  page. After the fix it also clears `localStorage`.
- **`session.permanent`**: Flask flag that, when `True`, makes the server-side session survive
  browser close for the duration of `app.permanent_session_lifetime`.

---

## Bug Details

### Bug Condition

The bug manifests when a user has successfully logged in via the main frontend (`index.html` /
`app.js`), and then refreshes or reloads the page. Because `currentUser` and `currentRole` are
plain JavaScript variables inside an IIFE, they are reset to `null` on every page load. The login
flow never writes to `localStorage`, and `DOMContentLoaded` never reads from it, so there is no
mechanism to restore the session.

**Formal Specification:**

```
FUNCTION isBugCondition(X)
  INPUT:  X of type AppState
  OUTPUT: boolean

  RETURN (X.userLoggedIn = true)
     AND (X.pageRefreshed = true)
     AND (X.localStorageTokenExists = false)
END FUNCTION
```

### Examples

- **Driver refreshes after login**: Driver logs in with email `rajesh1001@riksha.in`. Dashboard
  appears. Driver presses F5. Expected: driver dashboard restored. Actual: landing page shown,
  `currentUser = null`, `currentRole = null`.

- **Passenger closes and reopens tab**: Passenger logs in, closes the tab, reopens
  `http://localhost:5001`. Expected: passenger dashboard restored (token still valid). Actual:
  landing page shown, session lost.

- **Driver navigates away and back**: Driver opens a different URL then hits Back. Expected:
  dashboard still visible. Actual: landing page shown.

- **Token expired (edge case)**: User has a saved `rr_token` that is older than 30 days. Expected:
  `GET /api/auth/me` returns 401, `localStorage` is cleared, landing page is shown — no crash.

---

## Expected Behavior

### Preservation Requirements

**Unchanged Behaviors:**

- Explicit logout via the logout button must continue to clear the session and return to the
  landing page.
- Incorrect credentials during login must continue to show the appropriate error message and not
  log the user in.
- Valid logged-in users navigating between dashboard sections (profile, rides, history, wallet,
  earnings, QR code) must continue to see the correct view without interruption.
- The driver dashboard with ride simulation, earnings, and QR code must continue to work exactly
  as before.
- The passenger dashboard with booking, wallet, ride tracking, and payment modal must continue to
  work exactly as before.
- When the JWT token has genuinely expired (after 30 days), the backend must continue to reject it
  and the frontend must require re-login.
- When the admin deletes a user, subsequent API calls with that user's token must continue to
  return 401 (handled by existing `GET /api/auth/me` logic in `protect` middleware).
- When no token is saved in `localStorage`, the landing page must continue to be shown as the
  default unauthenticated state.

**Scope:**

All inputs that do NOT involve a page refresh/reload while a valid token exists in `localStorage`
should be completely unaffected by this fix. This includes:

- Mouse clicks on login, logout, and navigation buttons
- Form submissions (login, registration)
- Ride simulation interactions
- Wallet top-up and payment modal interactions
- Any interaction that does not involve `DOMContentLoaded` token restoration

---

## Hypothesized Root Cause

Based on code inspection of `raksharide/static/js/app.js`, the root causes are confirmed (not
merely hypothesized):

1. **No `localStorage` write on login**: The `login-form` submit handler sets `currentUser` and
   `currentRole` in memory and calls `showDriverDashboard()` / `showPassengerDashboard()`, but
   never calls `localStorage.setItem()`. The JWT token in the API response (if any is used) is
   discarded.

2. **No `DOMContentLoaded` restore logic**: The IIFE runs immediately but contains no code that
   reads `localStorage` for a saved token or calls `GET /api/auth/me`. The app always starts in
   the unauthenticated state.

3. **`doLogout()` does not clear `localStorage`**: The function only resets in-memory variables.
   After the fix adds `localStorage` writes, `doLogout()` must also clear them — otherwise a
   logged-out user who refreshes would be silently re-authenticated.

4. **Flask session not permanent**: In `raksharide/app.py`, the `login()` route sets
   `session['user_id']`, `session['name']`, and `session['role']` but never sets
   `session.permanent = True`. The `app.permanent_session_lifetime` is also not configured.
   This causes the Flask session (used by the secondary Jinja2 frontend) to expire on browser
   close.

5. **`frontend/static/static/js/auth.js` `checkAuth()` only uses `/api/session_check`**: When the
   Flask session has expired but a valid JWT token exists in `localStorage`, `checkAuth()` will
   redirect to login unnecessarily. A fallback to `GET /api/auth/me` would allow the secondary
   frontend to also benefit from token-based persistence.

---

## Correctness Properties

Property 1: Bug Condition — Session Persistence After Page Refresh

_For any_ app state `X` where the bug condition holds (`isBugCondition(X)` returns `true` — i.e.,
the user was logged in, the page was refreshed, and no `localStorage` token existed before the
fix), the fixed app SHALL, on `DOMContentLoaded`, read the saved token from `localStorage`, call
`GET /api/auth/me` with `Authorization: Bearer <token>`, restore `currentUser` and `currentRole`
from the response, and display the correct dashboard (driver or passenger) — leaving the landing
page hidden.

**Validates: Requirements 2.1, 2.2, 2.3, 2.4, 2.7, 2.8**

Property 2: Preservation — All Non-Refresh Interactions Unchanged

_For any_ app state `X` where the bug condition does NOT hold (`isBugCondition(X)` returns
`false` — i.e., the user is interacting normally without a page refresh, or no valid token is
saved), the fixed app SHALL produce exactly the same behavior as the original app, preserving
logout flow, login error handling, dashboard navigation, ride simulation, wallet interactions, and
the unauthenticated landing page state.

**Validates: Requirements 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 3.7, 3.8**

---

## Fix Implementation

### Changes Required

Assuming the root cause analysis above is correct:

---

**File 1: `raksharide/static/js/app.js`**

**Change 1 — Save token and user on driver login**

Inside the `login-form` submit handler, after `currentUser = drv; currentRole = 'driver';`, add:

```javascript
localStorage.setItem('rr_token', drv._token || '');
localStorage.setItem('rr_user', JSON.stringify({ id: drv.id, name: drv.name, role: 'driver' }));
localStorage.setItem('rr_user_type', 'driver');
```

Note: `app.js` uses a local in-memory DB (`RIKSHA_DB`), not the Node.js backend, for its login
flow. The `_token` field will be populated if the login is wired to the Node.js API. If not, the
token is stored as an empty string and the restore path will fall back to showing the landing page
(safe degradation). The user object is stored so the dashboard can be restored without a network
call in the common case.

**Change 2 — Save token and user on passenger login**

Inside the same handler, after `currentUser = pax; currentRole = 'passenger';`, add:

```javascript
localStorage.setItem('rr_token', pax._token || '');
localStorage.setItem('rr_user', JSON.stringify({ id: pax.id, name: pax.name, role: 'passenger' }));
localStorage.setItem('rr_user_type', 'passenger');
```

**Change 3 — Clear localStorage on logout**

Inside `doLogout()`, after `currentUser = null; currentRole = null;`, add:

```javascript
localStorage.removeItem('rr_token');
localStorage.removeItem('rr_user');
localStorage.removeItem('rr_user_type');
```

**Change 4 — Restore session on DOMContentLoaded**

At the end of the IIFE (before the closing `})();`), add a `DOMContentLoaded` listener:

```javascript
document.addEventListener('DOMContentLoaded', function restoreSession() {
    const savedToken = localStorage.getItem('rr_token');
    const savedUserRaw = localStorage.getItem('rr_user');
    const savedRole = localStorage.getItem('rr_user_type');

    if (!savedToken || !savedUserRaw || !savedRole) return; // no saved session

    // Show brief loading state
    hide('landing');
    // (optional: show a loading spinner element if one exists)

    fetch('http://localhost:5001/api/auth/me', {
        headers: { 'Authorization': 'Bearer ' + savedToken }
    })
    .then(function(res) { return res.json().then(function(data) { return { ok: res.ok, data: data }; }); })
    .then(function(result) {
        if (result.ok && result.data && result.data.user) {
            // Token valid — restore session
            const user = result.data.user;
            currentUser = user;
            currentRole = savedRole;
            if (savedRole === 'driver') {
                showDriverDashboard(user);
            } else {
                showPassengerDashboard(user);
            }
        } else {
            // Token invalid or expired — clear and show landing
            localStorage.removeItem('rr_token');
            localStorage.removeItem('rr_user');
            localStorage.removeItem('rr_user_type');
            show('landing');
        }
    })
    .catch(function() {
        // Network error — clear and show landing
        localStorage.removeItem('rr_token');
        localStorage.removeItem('rr_user');
        localStorage.removeItem('rr_user_type');
        show('landing');
    });
});
```

---

**File 2: `backend/.env`**

Change `JWT_EXPIRES_IN` from `7d` to `30d`:

```
JWT_EXPIRES_IN=30d
```

---

**File 3: `raksharide/app.py`**

1. After `app.secret_key = 'raksharide_premium_secret_key'`, add:

```python
app.permanent_session_lifetime = timedelta(days=30)
```

(`timedelta` is already imported from `datetime`.)

2. Inside the `login()` route, after the `if user and check_password_hash(...)` check passes and
   before `session['user_id'] = user['id']`, add:

```python
session.permanent = True
```

---

**File 4: `frontend/static/static/js/auth.js`**

Update `checkAuth()` to fall back to `GET /api/auth/me` when `/api/session_check` fails but a
token exists in `localStorage`:

```javascript
async function checkAuth(redirectType = 'passenger') {
    try {
        const r = await authFetch('/api/session_check');
        if (!r) return false;
        const d = await r.json();
        if (d.logged_in) return true;

        // session_check failed — try token-based fallback
        const token = getToken();
        if (token) {
            const r2 = await authFetch('http://localhost:5001/api/auth/me');
            if (r2 && r2.ok) {
                const d2 = await r2.json();
                if (d2 && d2.user) return true; // token valid, allow access
            }
        }

        clearToken();
        window.location.href = `/login/${redirectType}`;
        return false;
    } catch (e) {
        return false;
    }
}
```

---

## Testing Strategy

### Validation Approach

The testing strategy follows a two-phase approach: first, surface counterexamples that demonstrate
the bug on the unfixed code, then verify the fix works correctly and preserves existing behavior.

---

### Exploratory Bug Condition Checking

**Goal**: Surface counterexamples that demonstrate the bug BEFORE implementing the fix. Confirm or
refute the root cause analysis. If we refute, we will need to re-hypothesize.

**Test Plan**: Simulate the page-refresh scenario by directly invoking the `DOMContentLoaded`
restore path (or its equivalent) on the unfixed code, and assert that `currentUser` and
`currentRole` remain `null`. Run these tests on the UNFIXED code to observe failures and confirm
the root cause.

**Test Cases**:

1. **Driver login then refresh**: Log in as a driver, manually set `localStorage.rr_token` and
   `localStorage.rr_user`, reload the page — assert `currentUser` is `null` and landing page is
   visible (will demonstrate the bug on unfixed code).

2. **Passenger login then refresh**: Same as above for a passenger account.

3. **Token in localStorage, no restore logic**: Manually set `rr_token` in `localStorage` before
   page load — assert that the unfixed `DOMContentLoaded` handler does not call
   `GET /api/auth/me` and does not restore the session.

4. **Flask session expires on browser close**: Open the Flask-backed secondary frontend, log in,
   close the browser, reopen — assert the session is gone (demonstrates the `session.permanent`
   bug on unfixed code).

**Expected Counterexamples**:

- `currentUser` is `null` after page reload even when a valid token is in `localStorage`
- Landing page is shown instead of the dashboard after reload
- Possible causes: no `localStorage.setItem` on login, no `DOMContentLoaded` restore handler

---

### Fix Checking

**Goal**: Verify that for all inputs where the bug condition holds, the fixed app produces the
expected behavior.

**Pseudocode:**

```
FOR ALL X WHERE isBugCondition(X) DO
  result := restoreSession_fixed(X)
  ASSERT result.currentUser ≠ null
  ASSERT result.currentRole ≠ null
  ASSERT result.landingPageHidden = true
  ASSERT result.dashboardVisible = true
END FOR
```

---

### Preservation Checking

**Goal**: Verify that for all inputs where the bug condition does NOT hold, the fixed app produces
the same result as the original app.

**Pseudocode:**

```
FOR ALL X WHERE NOT isBugCondition(X) DO
  ASSERT app_original(X) = app_fixed(X)
  // logout, login errors, dashboard navigation, ride simulation,
  // wallet interactions all behave identically
END FOR
```

**Testing Approach**: Property-based testing is recommended for preservation checking because:

- It generates many test cases automatically across the input domain
- It catches edge cases that manual unit tests might miss
- It provides strong guarantees that behavior is unchanged for all non-buggy inputs

**Test Plan**: Observe behavior on UNFIXED code first for logout, login errors, and dashboard
interactions, then write property-based tests capturing that behavior.

**Test Cases**:

1. **Logout Preservation**: Verify that clicking logout clears `currentUser`, `currentRole`, and
   (after fix) `localStorage`, and shows the landing page — identical behavior before and after fix.

2. **Login Error Preservation**: Verify that incorrect credentials continue to show the error
   message and do not set `currentUser` or write to `localStorage`.

3. **Dashboard Navigation Preservation**: Verify that switching between sidebar views (profile,
   rides, history, wallet) continues to work correctly after the fix.

4. **Ride Simulation Preservation**: Verify that the driver and passenger ride simulations
   (map, timer, earnings, payment modal) are unaffected by the fix.

5. **No-Token Landing Page Preservation**: Verify that when `localStorage` contains no token, the
   landing page is shown as the default state — identical to pre-fix behavior.

6. **Expired Token Handling**: Verify that when `GET /api/auth/me` returns 401, `localStorage` is
   cleared and the landing page is shown — no crash, no infinite loop.

---

### Unit Tests

- Test that `localStorage.setItem('rr_token', ...)` is called after a successful driver login
- Test that `localStorage.setItem('rr_token', ...)` is called after a successful passenger login
- Test that `localStorage.removeItem('rr_token')` is called inside `doLogout()`
- Test that `DOMContentLoaded` handler calls `GET /api/auth/me` when `rr_token` is present
- Test that `DOMContentLoaded` handler shows landing page when `rr_token` is absent
- Test that `DOMContentLoaded` handler clears `localStorage` and shows landing page on 401 response
- Test that `DOMContentLoaded` handler clears `localStorage` and shows landing page on network error
- Test that `app.permanent_session_lifetime` is set to 30 days in `raksharide/app.py`
- Test that `session.permanent = True` is set in the Flask `login()` route

### Property-Based Tests

- Generate random valid user objects and verify that after simulated login + page reload, the
  dashboard is restored correctly (fix checking property)
- Generate random non-refresh interactions (logout, login errors, navigation clicks) and verify
  that behavior is identical before and after the fix (preservation property)
- Generate random expired/invalid token strings and verify that the restore path always clears
  `localStorage` and shows the landing page without crashing
- Generate random sequences of login → navigate → refresh → navigate and verify session
  consistency throughout

### Integration Tests

- Full flow: driver login → page refresh → driver dashboard visible, all sidebar views functional
- Full flow: passenger login → page refresh → passenger dashboard visible, booking flow functional
- Full flow: login → logout → page refresh → landing page shown (no ghost session)
- Full flow: login → token expires (mock 401 from `/api/auth/me`) → landing page shown
- Full flow: secondary frontend (`auth.js`) — Flask session expired but JWT token valid →
  `checkAuth()` fallback succeeds, user stays authenticated
- Full flow: `JWT_EXPIRES_IN=30d` — token issued today is still valid 8 days later (regression
  from previous 7-day limit)
