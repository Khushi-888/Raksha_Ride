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
    const method = (options.method || 'GET').toUpperCase();

    // Only set Content-Type for requests with a body
    const headers = { ...(options.headers || {}) };
    if (method !== 'GET' && method !== 'HEAD' && !headers['Content-Type']) {
        headers['Content-Type'] = 'application/json';
    }
    if (token) {
        headers['Authorization'] = `Bearer ${token}`;
    }

    let response;
    try {
        response = await fetch(url, {
            ...options,
            method,
            headers,
            credentials: 'include',
        });
    } catch (networkErr) {
        console.error('Network error:', networkErr);
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

    // Handle 401
    if (response.status === 401) {
        const code = bodyData && bodyData.code;
        if (code === 'AUTH_REQUIRED' && !token) {
            // No token at all — redirect to login
            clearToken();
            const userType = localStorage.getItem(RR_USER_TYPE_KEY) || 'passenger';
            setTimeout(() => { window.location.href = `/login/${userType}`; }, 800);
            return null;
        }
        // Has token but got 401 — return the response so caller can handle
        return {
            ok: false,
            status: 401,
            headers: response.headers,
            json: async () => bodyData,
            text: async () => bodyText,
            _data: bodyData
        };
    }

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
        if (!r) {
            return !!getToken();
        }
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
        return !!getToken();
    }
}
