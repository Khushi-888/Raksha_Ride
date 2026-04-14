/**
 * RakshaRide - Auth Utility
 * Handles JWT token storage and authenticated API calls
 */

const RR_TOKEN_KEY = 'rr_token';
const RR_USER_TYPE_KEY = 'rr_user_type';

function getToken() {
    return localStorage.getItem(RR_TOKEN_KEY) || '';
}

function setToken(token, userType) {
    localStorage.setItem(RR_TOKEN_KEY, token);
    if (userType) localStorage.setItem(RR_USER_TYPE_KEY, userType);
}

function clearToken() {
    localStorage.removeItem(RR_TOKEN_KEY);
    localStorage.removeItem(RR_USER_TYPE_KEY);
    localStorage.removeItem('user');
}

/**
 * Authenticated fetch — adds Authorization header, handles 401 gracefully.
 * IMPORTANT: Returns a Response-like object with a cached .json() method
 * so the body can be read multiple times without "stream already read" error.
 */
async function authFetch(url, options = {}) {
    const token = getToken();
    const headers = {
        'Content-Type': 'application/json',
        ...(options.headers || {}),
    };
    if (token) {
        headers['Authorization'] = `Bearer ${token}`;
    }

    let response;
    try {
        response = await fetch(url, {
            ...options,
            headers,
            credentials: 'include',
        });
    } catch (networkErr) {
        console.error('Network error:', networkErr);
        // Return a fake failed response
        return {
            ok: false,
            status: 0,
            json: async () => ({ success: false, message: 'Network error: ' + networkErr.message })
        };
    }

    // Read body ONCE and cache it
    let bodyText = '';
    let bodyData = null;
    try {
        bodyText = await response.text();
        bodyData = JSON.parse(bodyText);
    } catch (e) {
        bodyData = { success: false, message: bodyText || 'Invalid response' };
    }

    // Handle 401 — redirect to login only if no token at all
    if (response.status === 401) {
        const code = bodyData && bodyData.code;
        if (code === 'AUTH_REQUIRED') {
            clearToken();
            const userType = localStorage.getItem(RR_USER_TYPE_KEY) || 'passenger';
            setTimeout(() => { window.location.href = `/login/${userType}`; }, 800);
            return null;
        }
        // If we have a token but got 401, token may be expired — clear and redirect
        if (!token) {
            clearToken();
            const userType = localStorage.getItem(RR_USER_TYPE_KEY) || 'passenger';
            setTimeout(() => { window.location.href = `/login/${userType}`; }, 800);
            return null;
        }
    }

    // Return a wrapper with cached json() so it can be called multiple times
    return {
        ok: response.ok,
        status: response.status,
        headers: response.headers,
        json: async () => bodyData,
        text: async () => bodyText,
        _data: bodyData
    };
}

/** Check if user is authenticated */
async function checkAuth(redirectType = 'passenger') {
    try {
        const r = await authFetch('/api/session_check');
        if (!r) return false;
        const d = await r.json();
        if (!d.logged_in) {
            clearToken();
            window.location.href = `/login/${redirectType}`;
            return false;
        }
        return true;
    } catch (e) {
        return false;
    }
}
