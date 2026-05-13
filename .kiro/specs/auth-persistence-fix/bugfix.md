# Bugfix Requirements Document

## Introduction

After a successful login in RakshaRide, the user session is lost on every page refresh or browser reload. This happens because the main frontend (`raksharide/static/js/app.js`) stores auth state exclusively in JavaScript variables (`currentUser`, `currentRole`) which are in-memory only and are wiped when the page unloads. There is no persistence layer (e.g., `localStorage`) saving the token or user data, and no auto-restore logic on app startup.

The Node.js/Express backend already issues 7-day JWT tokens and exposes a `GET /api/auth/me` endpoint for restoring user state from a token. The Flask backend uses server-side sessions that expire when the browser closes because `session.permanent` is never set. The fix must make sessions survive page refreshes, browser restarts, and extended idle periods — without rewriting the project or altering the existing UI/design.

---

## Bug Analysis

### Current Behavior (Defect)

1.1 WHEN a user successfully logs in via the main frontend (`index.html` / `app.js`) THEN the system stores the user only in the JavaScript variables `currentUser` and `currentRole`, which are lost on any page refresh or browser reload

1.2 WHEN the page is refreshed or the browser is reloaded after login THEN the system resets `currentUser` and `currentRole` to `null`, effectively logging the user out without any explicit logout action

1.3 WHEN the login API response returns a JWT token THEN the system discards the token without saving it to `localStorage` or any persistent storage

1.4 WHEN the app initializes on page load (DOMContentLoaded) THEN the system does not check `localStorage` for a previously saved token or user, so no session is restored

1.5 WHEN a user logs out via `doLogout()` THEN the system only sets `currentUser = null` and `currentRole = null` without clearing any persistent storage (though none exists currently)

1.6 WHEN a user logs in via the Flask backend (`raksharide/app.py`) THEN the system creates a server-side session without setting `session.permanent = True`, causing the session to expire when the browser window is closed

### Expected Behavior (Correct)

2.1 WHEN a user successfully logs in via the main frontend THEN the system SHALL save the JWT token and user data to `localStorage` so they persist across page refreshes and browser restarts

2.2 WHEN the page is refreshed or the browser is reloaded after login THEN the system SHALL automatically restore the user session from `localStorage` without requiring the user to log in again

2.3 WHEN the login API response returns a JWT token THEN the system SHALL persist the token in `localStorage` under a consistent key (e.g., `rr_token`) for later retrieval

2.4 WHEN the app initializes on page load (DOMContentLoaded) THEN the system SHALL check `localStorage` for a saved token, call `GET /api/auth/me` to validate it, and restore `currentUser` and `currentRole` if the token is valid

2.5 WHEN a user logs out via `doLogout()` THEN the system SHALL clear the JWT token and user data from `localStorage` in addition to resetting the in-memory variables

2.6 WHEN a user logs in via the Flask backend THEN the system SHALL set `session.permanent = True` and configure `app.permanent_session_lifetime` so the Flask session persists beyond browser close

2.7 WHEN the app is restoring a session on startup THEN the system SHALL display a loading state to the user while the token validation request is in flight

2.8 WHEN the saved token is expired or invalid during session restore THEN the system SHALL clear `localStorage`, reset auth state, and present the landing/login screen without crashing

### Unchanged Behavior (Regression Prevention)

3.1 WHEN a user explicitly clicks logout THEN the system SHALL CONTINUE TO clear the user session and return to the landing page

3.2 WHEN a user provides incorrect credentials during login THEN the system SHALL CONTINUE TO show the appropriate error message and not log them in

3.3 WHEN a valid logged-in user navigates between dashboard sections (profile, rides, history, etc.) THEN the system SHALL CONTINUE TO display the correct dashboard without interruption

3.4 WHEN a driver logs in THEN the system SHALL CONTINUE TO show the driver dashboard with all existing features (ride simulation, earnings, QR code, etc.)

3.5 WHEN a passenger logs in THEN the system SHALL CONTINUE TO show the passenger dashboard with all existing features (booking, wallet, ride tracking, etc.)

3.6 WHEN the JWT token has genuinely expired (after 7–30 days) THEN the system SHALL CONTINUE TO reject the token and require the user to log in again

3.7 WHEN the admin deletes a user account THEN the system SHALL CONTINUE TO reject subsequent API calls from that user's token (handled by existing `GET /api/auth/me` returning 401 when user no longer exists)

3.8 WHEN the app is running without a saved token in `localStorage` THEN the system SHALL CONTINUE TO show the landing page as the default unauthenticated state

---

## Bug Condition (Pseudocode)

**Bug Condition Function** — identifies the inputs/states that trigger the bug:

```pascal
FUNCTION isBugCondition(X)
  INPUT: X of type AppState
  OUTPUT: boolean

  // Bug is triggered when:
  // - A user has logged in (token was issued by backend)
  // - AND the page is refreshed or reloaded
  // - AND no localStorage save/restore logic exists
  RETURN (X.userLoggedIn = true) AND (X.pageRefreshed = true) AND (X.localStorageTokenExists = false)
END FUNCTION
```

**Property: Fix Checking** — correct behavior for buggy inputs:

```pascal
// Property: Fix Checking — Session Persistence After Refresh
FOR ALL X WHERE isBugCondition(X) DO
  result ← restoreSession'(X)
  ASSERT result.currentUser ≠ null
  ASSERT result.currentRole ≠ null
  ASSERT result.landingPageHidden = true
  ASSERT result.dashboardVisible = true
END FOR
```

**Property: Preservation Checking** — non-buggy inputs must be unaffected:

```pascal
// Property: Preservation Checking
FOR ALL X WHERE NOT isBugCondition(X) DO
  ASSERT F(X) = F'(X)
  // i.e., logout, login errors, dashboard navigation, ride simulation
  // all behave identically before and after the fix
END FOR
```
