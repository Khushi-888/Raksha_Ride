/* ================================================================
   RakshaRide — Main Application Logic
   Flow:
     Driver   → registers with Vehicle No + RC No → login via RC email
     Passenger→ registers with Name/Mobile/Email  → login via email OR mobile
   ================================================================ */

(function () {
    'use strict';

    /* ── State ─────────────────────────────────────────────── */
    let auth = JSON.parse(localStorage.getItem('raksha_auth_state')) || null;
    let currentRole = auth ? auth.role : null;
    let currentUser = null;
    let sessionToken = auth ? auth.token : null;
    let loginRoleTab = 'driver';

    // OTP state
    let otpExpiryTime = null;
    let otpInterval = null;
    let regOtpInterval = null;
    let isMobileVerified = false;

    // Seed LocalStorage if empty
    if (!localStorage.getItem('riksha_drivers')) {
        localStorage.setItem('riksha_drivers', JSON.stringify(RIKSHA_DB.drivers));
    }
    if (!localStorage.getItem('riksha_passengers')) {
        localStorage.setItem('riksha_passengers', JSON.stringify(RIKSHA_DB.passengers));
    }

    /* ── View Manager ─────────────────────────────────────── */
    function switchView(viewId) {
        // Hide ALL top-level views
        const views = ['landing', 'driver-dashboard', 'passenger-dashboard'];
        views.forEach(v => hide(v));

        // Show target
        show(viewId);

        // Reset scroll
        window.scrollTo(0, 0);

        // Update nav active states if in dashboard
        if (viewId.includes('dashboard')) {
            const role = viewId.split('-')[0];
            const activeSubView = role === 'driver' ? 'drv-profile' : 'pax-profile';
            activateSubView(role, activeSubView);
        }
    }

    function activateSubView(role, viewId) {
        const dashEl = $(role === 'driver' ? 'driver-dashboard' : 'passenger-dashboard');
        dashEl.querySelectorAll('.dash-view').forEach(v => v.classList.remove('active'));
        const target = $(viewId);
        if (target) target.classList.add('active');

        // Update sidebar links
        document.querySelectorAll(`.sb-link[data-dash="${role}"]`).forEach(b => {
            b.classList.toggle('active', b.getAttribute('data-view') === viewId);
        });
    }

    // Persistence Check on Load
    window.onload = async () => {
        if (auth && sessionToken) {
            try {
                const res = await fetch('/api/me', {
                    headers: { 'Authorization': `Bearer ${sessionToken}` }
                });
                if (!res.ok) throw new Error("Session invalid");

                const profile = await res.json();
                if (profile.role === 'driver') showDriverDashboard(profile);
                else showPassengerDashboard(profile);
            } catch (e) {
                console.warn("Auth check failed:", e);
                doLogout();
            }
        } else {
            switchView('landing');
        }
    };

    /* ── Helpers ───────────────────────────────────────────── */
    const $ = id => document.getElementById(id);
    const show = id => { const el = $(id); if (el) el.style.display = 'block'; };
    const hide = id => { const el = $(id); if (el) el.style.display = 'none'; };
    const showFlex = id => { const el = $(id); if (el) el.style.display = 'flex'; };

    function showMsg(id, txt, type) {
        const el = $(id);
        if (!el) return;
        el.textContent = txt;
        el.className = `form-msg ${type}`;
        el.style.display = 'block';
    }
    function clearMsg(id) { const el = $(id); if (el) el.style.display = 'none'; }

    function openModal(id) { const el = $(id); if (el) el.classList.remove('hidden'); }
    function closeModal(id) { const el = $(id); if (el) el.classList.add('hidden'); }

    /* ── Modal open/close wiring ───────────────────────────── */
    $('open-login-btn').onclick = () => { loginRoleTab = 'driver'; openLoginModal(); };
    $('hero-login-btn').onclick = () => { loginRoleTab = 'driver'; openLoginModal(); };
    $('open-reg-btn').onclick = () => openModal('drv-reg-modal');
    $('hero-reg-btn').onclick = () => openModal('drv-reg-modal');
    $('login-close-btn').onclick = () => closeModal('login-modal');
    $('drv-reg-close').onclick = () => closeModal('drv-reg-modal');
    $('pax-reg-close').onclick = () => closeModal('pax-reg-modal');

    // Close on backdrop click
    ['login-modal', 'drv-reg-modal', 'pax-reg-modal'].forEach(id => {
        $(id).addEventListener('click', e => { if (e.target === $(id)) closeModal(id); });
    });

    // "New passenger? Create account" link inside login modal
    $('goto-reg-link').onclick = e => {
        e.preventDefault();
        closeModal('login-modal');
        openModal('pax-reg-modal');
    };
    $('goto-login-link').onclick = e => {
        e.preventDefault();
        closeModal('pax-reg-modal');
        openLoginModal('passenger');
    };

    function openLoginModal(role) {
        clearMsg('login-err');
        clearMsg('login-ok');
        $('login-form').reset();
        resetOTPFlow();

        openModal('login-modal');
        setLoginTab(role || loginRoleTab);
    }

    function resetOTPFlow() {
        if (otpInterval) clearInterval(otpInterval);
        hide('lf-otp');
        hide('otp-resend-wrap');
        showFlex('btn-request-otp');
        hide('btn-login-submit');
        $('l-email').disabled = false;
        $('l-mobile').disabled = false;
        $('otp-timer-display').textContent = '02:00';
        $('otp-timer-display').style.color = 'var(--pri)';
    }

    function startOTPTimer(duration) {
        if (otpInterval) clearInterval(otpInterval);
        hide('otp-resend-wrap');
        let timer = duration;
        const display = $('otp-timer-display');

        display.style.color = 'var(--pri)';
        otpExpiryTime = Date.now() + (duration * 1000);

        otpInterval = setInterval(() => {
            const minutes = Math.floor(timer / 60);
            const seconds = timer % 60;

            display.textContent = `${String(minutes).padStart(2, '0')}:${String(seconds).padStart(2, '0')}`;

            if (--timer < 0) {
                clearInterval(otpInterval);
                display.textContent = 'EXPIRED';
                display.style.color = '#ff5252';
                show('otp-resend-wrap');
            }
        }, 1000);
    }

    /* ── Login tabs ────────────────────────────────────────── */
    $('lt-driver').onclick = () => setLoginTab('driver');
    $('lt-passenger').onclick = () => setLoginTab('passenger');

    function setLoginTab(role) {
        loginRoleTab = role;
        $('lt-driver').classList.toggle('active', role === 'driver');
        $('lt-passenger').classList.toggle('active', role === 'passenger');

        if (role === 'driver') {
            // Driver: email field with label "RC-registered Email"
            $('lf-email').style.display = 'block';
            $('lf-mobile').style.display = 'none';
            document.querySelector('#lf-email label').textContent = 'Email (RC-registered)';
            $('l-email').placeholder = 'rajesh1001@riksha.in';
        } else {
            // Passenger: combined email-or-mobile field
            $('lf-email').style.display = 'none';
            $('lf-mobile').style.display = 'block';
            $('l-mobile').placeholder = 'email@example.com  or  9876543210';
        }

        // Reset phase when switching tabs
        clearMsg('login-err');
        clearMsg('login-ok');
        resetOTPFlow();
    }

    /* ── Two-Phase OTP Login Flow ───────────────────────────── */

    // Unified Login Handler with Device Awareness
    $('login-form').addEventListener('submit', async e => {
        e.preventDefault();
        clearMsg('login-err');
        clearMsg('login-ok');

        const credential = loginRoleTab === 'driver' ? $('l-email').value.trim() : $('l-mobile').value.trim();
        const otp = $('l-otp').value.trim(); // Only if phase 2
        const password = $('l-password').value.trim();

        // Check for device token
        const trustToken = localStorage.getItem('raksha_trust_token');

        try {
            if (otp && window.loginPendingData) {
                // PHASE 2: Verify OTP + Trust Device
                const res = await fetch('/api/auth/verify-otp', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        credential: window.loginPendingData.credential,
                        role: window.loginPendingData.role,
                        password: window.loginPendingData.password,
                        otp: otp,
                        device_uuid: trustToken
                    })
                });

                const data = await res.json();
                if (!res.ok) throw new Error(data.detail || 'Invalid OTP');

                // Success! Save trust token and proceed
                localStorage.setItem('raksha_trust_token', data.device_uuid);
                handleLoginSuccess(data, window.loginPendingData.role);
                return;
            }

            // PHASE 1: Initial Login Check
            const res = await fetch('/api/login', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    credential: credential,
                    password: password,
                    role: loginRoleTab,
                    device_uuid: trustToken
                })
            });

            const data = await res.json();

            if (res.status === 202) {
                // OTP REQUIRED (New Device)
                showMsg('login-ok', '🔐 New device detected. Please enter the OTP sent to your phone.', 'ok');
                window.loginPendingData = { credential, role: loginRoleTab, password };

                // Show OTP input UI
                hide('btn-request-otp');
                showFlex('btn-login-submit');
                show('lf-otp');
                $('l-otp').focus();
                startOTPTimer(300);
                return;
            }

            if (!res.ok) throw new Error(data.detail || 'Invalid credentials');

            // Success (Trusted Device)
            handleLoginSuccess(data, loginRoleTab);

        } catch (err) {
            showMsg('login-err', err.message, 'err');
        }
    });

    async function handleLoginSuccess(data, role) {
        const authState = {
            user_id: data.user_id,
            role: role,
            token: data.access_token,
            timestamp: Date.now()
        };

        auth = authState;
        sessionToken = data.access_token;
        currentRole = role;

        localStorage.setItem('raksha_auth_state', JSON.stringify(authState));
        if (data.device_uuid) localStorage.setItem('raksha_trust_token', data.device_uuid);

        closeModal('login-modal');

        // Fetch full profile to populate dashboard
        try {
            const res = await fetch('/api/me', {
                headers: { 'Authorization': `Bearer ${sessionToken}` }
            });
            const profile = await res.json();
            if (role === 'driver') showDriverDashboard(profile);
            else showPassengerDashboard(profile);
        } catch (e) {
            console.error("Failed to load profile", e);
            switchView(role === 'driver' ? 'driver-dashboard' : 'passenger-dashboard');
        }
    }

    /* ── Driver Registration ────────────────────────────────── */
    $('drv-reg-form').addEventListener('submit', async e => {
        e.preventDefault();
        clearMsg('drv-reg-err'); clearMsg('drv-reg-ok');

        const formData = {
            name: $('dr-name').value.trim(),
            age: parseInt($('dr-age').value),
            mobile: $('dr-mobile').value.trim(),
            email: $('dr-email').value.trim().toLowerCase(),
            vehicle_number: $('dr-vno').value.trim().toUpperCase(),
            rc_number: $('dr-rc').value.trim().toUpperCase(),
            pick_location: $('dr-pick').value.trim(),
            password: $('dr-pass').value.trim()
        };

        if (window.regPendingOTP && $('dr-otp').value) {
            // VERIFY Phase
            try {
                const res = await fetch('/api/register/verify', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        credential: formData.email,
                        role: 'driver',
                        password: formData.password,
                        otp: $('dr-otp').value.trim(),
                        device_uuid: localStorage.getItem('raksha_trust_token')
                    })
                });
                const data = await res.json();

                if (res.status === 429) {
                    showMsg('drv-reg-err', '🚨 IP blocked for 10 minutes due to failed attempts.', 'err');
                    return;
                }

                if (!res.ok) throw new Error(data.detail || 'Verification failed');

                showMsg('drv-reg-ok', '✅ Verified! You can now complete registration.', 'ok');
                show('btn-drv-reg-submit');
                hide('drv-reg-otp-wrap');
                return;
            } catch (err) {
                showMsg('drv-reg-err', err.message, 'err');
                return;
            }
        }

        try {
            const res = await fetch('/api/register/driver', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(formData)
            });
            const data = await res.json();
            if (!res.ok) throw new Error(data.detail || 'Registration failed');

            if (data.status === 'OTP_REQUIRED') {
                showMsg('drv-reg-ok', '🔐 Registration received. Please enter the OTP sent to your email.', 'ok');
                window.regPendingOTP = true;
                show('drv-reg-otp-wrap');
                $('dr-otp').focus();
                startDrvResendTimer();
                return;
            }

            showMsg('drv-reg-ok', '✅ Registered successfully!', 'ok');
        } catch (err) {
            showMsg('drv-reg-err', err.message, 'err');
        }
    });

    let drvResendInterval = null;
    function startDrvResendTimer() {
        if (drvResendInterval) clearInterval(drvResendInterval);
        let count = 60;
        show('drv-resend-timer');
        hide('btn-drv-resend');
        drvResendInterval = setInterval(() => {
            $('drv-resend-count').textContent = --count;
            if (count <= 0) {
                clearInterval(drvResendInterval);
                hide('drv-resend-timer');
                show('btn-drv-resend');
            }
        }, 1000);
    }

    $('btn-drv-resend').onclick = async () => {
        const email = $('dr-email').value.trim();
        try {
            const res = await fetch('/api/generate-otp', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ credential: email, role: 'driver' })
            });
            if (res.ok) {
                showMsg('drv-reg-ok', '✅ OTP Resent. Check console.', 'ok');
                startDrvResendTimer();
            }
        } catch (e) { }
    };

    /* ── Passenger Registration ─────────────────────────────── */
    $('pax-reg-close').addEventListener('click', () => {
        isMobileVerified = false;
        if (regOtpInterval) clearInterval(regOtpInterval);
        resetPaxRegUI();
    });

    function resetPaxRegUI() {
        hide('pax-reg-otp-wrap');
        $('btn-pax-reg-submit').disabled = true;
        $('btn-pax-reg-submit').style.opacity = '0.5';
        $('btn-pax-reg-submit').style.cursor = 'not-allowed';
        $('pr-mobile').disabled = false;
        $('btn-pax-send-otp').disabled = false;
        $('btn-pax-send-otp').style.opacity = '1';
    }

    $('btn-pax-send-otp').addEventListener('click', async () => {
        const mobile = $('pr-mobile').value.trim();
        if (!mobile || mobile.length < 10) {
            showMsg('pax-reg-err', 'Enter a valid 10-digit mobile number.', 'err');
            return;
        }

        try {
            // Trigger backend OTP generation
            const res = await fetch('/api/register/passenger', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    name: $('pr-name').value.trim() || "Passenger",
                    mobile: mobile,
                    password: $('pr-pass').value.trim() || "temp_pass"
                })
            });
            const data = await res.json();

            if (res.status === 429) {
                showMsg('pax-reg-err', '🚨 Security Alert: Too many attempts. Your IP is blocked for 10 minutes.', 'err');
                return;
            }

            if (!res.ok && data.detail !== "Passenger already exists") {
                throw new Error(data.detail || 'Failed to send OTP');
            }

            if (data.status === 'OTP_REQUIRED' || data.detail === "Passenger already exists") {
                showMsg('pax-reg-ok', `✅ OTP sent to ${mobile}. Check server console.`, 'ok');
                show('pax-reg-otp-wrap');
                $('btn-pax-send-otp').disabled = true;
                $('btn-pax-send-otp').style.opacity = '0.5';
                startRegTimer(300); // 5 minutes
                startPaxResendTimer(); // 60s
                window.paxRegPendingOTP = true;
            }
        } catch (err) {
            showMsg('pax-reg-err', err.message, 'err');
        }
    });

    let paxResendInterval = null;
    function startPaxResendTimer() {
        if (paxResendInterval) clearInterval(paxResendInterval);
        let count = 60;
        show('pax-resend-timer');
        hide('btn-pax-resend');
        paxResendInterval = setInterval(() => {
            $('pax-resend-count').textContent = --count;
            if (count <= 0) {
                clearInterval(paxResendInterval);
                hide('pax-resend-timer');
                show('btn-pax-resend');
            }
        }, 1000);
    }

    $('btn-pax-resend').onclick = async () => {
        const mobile = $('pr-mobile').value.trim();
        try {
            const res = await fetch('/api/generate-otp', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ credential: mobile, role: 'passenger' })
            });
            if (res.ok) {
                showMsg('pax-reg-ok', '✅ OTP Resent. Check console.', 'ok');
                startPaxResendTimer();
            }
        } catch (e) { }
    };

    function startRegTimer(duration) {
        if (regOtpInterval) clearInterval(regOtpInterval);
        let timer = duration;
        const display = $('pax-reg-timer');
        regOtpInterval = setInterval(() => {
            const m = Math.floor(timer / 60);
            const s = timer % 60;
            display.textContent = `${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`;
            if (--timer < 0) {
                clearInterval(regOtpInterval);
                display.textContent = 'EXPIRED';
                resetPaxRegUI();
            }
        }, 1000);
    }


    /* ── Passenger Registration ─────────────────────────────── */
    $('pax-reg-form').addEventListener('submit', async e => {
        e.preventDefault();
        clearMsg('pax-reg-err'); clearMsg('pax-reg-ok');

        const formData = {
            name: $('pr-name').value.trim(),
            mobile: $('pr-mobile').value.trim(),
            email: $('pr-email').value.trim().toLowerCase() || null,
            password: $('pr-pass').value.trim()
        };

        if (window.paxRegPendingOTP && $('pr-otp').value) {
            // VERIFY Phase
            try {
                const res = await fetch('/api/register/verify', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        credential: formData.mobile,
                        role: 'passenger',
                        password: formData.password,
                        otp: $('pr-otp').value.trim(),
                        device_uuid: localStorage.getItem('raksha_trust_token')
                    })
                });
                const data = await res.json();

                if (res.status === 429) {
                    showMsg('pax-reg-err', '🚨 IP blocked for 10 minutes due to failed attempts.', 'err');
                    return;
                }

                if (!res.ok) throw new Error(data.detail || 'Verification failed');

                showMsg('pax-reg-ok', '✅ Verified! You can now complete registration.', 'ok');
                show('btn-pax-reg-submit'); // User requirement: show only after verification
                hide('pax-reg-otp-wrap');
                return;
            } catch (err) {
                showMsg('pax-reg-err', err.message, 'err');
                return;
            }
        }

        try {
            const res = await fetch('/api/register/passenger', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(formData)
            });
            const data = await res.json();
            if (!res.ok) throw new Error(data.detail || 'Registration failed');

            if (data.status === 'OTP_REQUIRED') {
                showMsg('pax-reg-ok', '🔐 Sent 6-digit OTP to your mobile.', 'ok');
                window.paxRegPendingOTP = true;
                show('pax-reg-otp-wrap');
                $('pr-otp').focus();
                return;
            }
        } catch (err) {
            showMsg('pax-reg-err', err.message, 'err');
        }
    });

    /* ════════════════════════════════════════════════════════
       DRIVER DASHBOARD
    ════════════════════════════════════════════════════════ */
    function showDriverDashboard(drv) {
        switchView('driver-dashboard');
        paxWalletBalance = drv.balance || 0;

        // Topbar
        $('drv-topbar-img').src = drv.photo;
        $('drv-topbar-name').textContent = drv.name;

        // Profile view
        $('drv-photo').src = drv.photo || `https://i.pravatar.cc/300?u=${drv.id}`;
        $('drv-name-h').textContent = drv.name;
        $('drv-id-p').textContent = `ID: ${drv.id}`;
        $('drv-age').textContent = drv.age;
        $('drv-mobile').textContent = drv.mobile;
        $('drv-email').textContent = drv.email;
        $('drv-pick').textContent = drv.pick_location || drv.pick;
        $('drv-rating').textContent = `${drv.rating} ★`;
        $('drv-rides-count').textContent = drv.total_rides || drv.totalRides || 0;
        $('drv-exp').textContent = drv.experience || '2 Years';

        // Vehicle view
        $('drv-vno-h').textContent = drv.vehicle_number || drv.vehicleNumber;
        $('drv-vtype-p').textContent = drv.vehicle_type || drv.vehicleType;
        $('drv-rc').textContent = drv.rc_number || drv.rcNo;
        $('drv-vno').textContent = drv.vehicle_number || drv.vehicleNumber;
        $('drv-vtype').textContent = drv.vehicle_type || drv.vehicleType;
        $('drv-inspect').textContent = drv.last_inspection || 'Dec 2025';

        // Earnings init
        drvEarnings = (drv.total_rides || drv.totalRides || 0) * 65;
        drvRidesDone = drv.total_rides || drv.totalRides || 0;
        refreshDriverEarnings();

        // History
        populateDriverHistory();

        // QR code
        setTimeout(() => {
            const qc = $('drv-qr-code');
            if (qc) {
                qc.innerHTML = '';
                try { new QRCode(qc, { text: drv.id, width: 140, height: 140, colorDark: '#FFB300', colorLight: '#161b22', correctLevel: QRCode.CorrectLevel.H }); }
                catch (e) { }
            }
        }, 100);

        // Sidebar nav
        setupSidebarNav('driver');

        // Ride button
        $('drv-start-ride').onclick = startDriverRide;
        $('drv-sos').onclick = () => {
            $('drv-alert-msg').textContent = '🚨 SOS Activated — Emergency contacts alerted!';
            $('drv-alert').classList.add('show');
        };
        $('drv-add-earn').onclick = () => {
            drvEarnings += 75; drvRidesDone++;
            refreshDriverEarnings();
            addToDriverHistory();
        };

        // Logout
        $('drv-logout').onclick = doLogout;
    }

    function refreshDriverEarnings() {
        const avg = drvRidesDone > 0 ? Math.round(drvEarnings / drvRidesDone) : 0;
        $('drv-total-earned').textContent = `₹ ${drvEarnings.toLocaleString()}`;
        $('drv-month-earned').textContent = `₹ ${Math.round(drvEarnings * 0.15).toLocaleString()}`;
        $('drv-rides-done').textContent = drvRidesDone;
        $('drv-avg-earn').textContent = `₹ ${avg}`;
        $('drv-earn-display').textContent = `₹ ${drvEarnings.toLocaleString()}`;
    }

    function populateDriverHistory() {
        const tbody = $('drv-hist-body');
        if (!tbody) return;
        tbody.innerHTML = '';
        const paxNames = RIKSHA_DB.passengers.slice(0, 8).map(p => p.name);
        const rows = [
            ['01 Mar 2026', paxNames[0] || 'Anita Singh', '3.2 km', '₹ 95', 'Completed'],
            ['01 Mar 2026', paxNames[1] || 'Rahul Kumar', '1.8 km', '₹ 60', 'Completed'],
            ['28 Feb 2026', paxNames[2] || 'Priya Verma', '5.1 km', '₹ 140', 'Completed'],
            ['28 Feb 2026', paxNames[3] || 'Amit Sharma', '2.4 km', '₹ 75', 'Completed'],
            ['27 Feb 2026', paxNames[4] || 'Meera Das', '4.0 km', '₹ 110', 'Completed'],
        ];
        rows.forEach(([date, pax, dist, fare, status]) => {
            tbody.innerHTML += `<tr>
        <td>${date}</td><td>${pax}</td><td>${dist}</td><td>${fare}</td>
        <td><span class="ht-badge ht-green">${status}</span></td>
      </tr>`;
        });
    }

    function addToDriverHistory() {
        const tbody = $('drv-hist-body');
        if (!tbody) return;
        const pax = RIKSHA_DB.passengers[Math.floor(Math.random() * RIKSHA_DB.passengers.length)];
        const now = new Date().toLocaleDateString('en-IN', { day: '2-digit', month: 'short', year: 'numeric' });
        tbody.insertAdjacentHTML('afterbegin', `<tr>
      <td>${now}</td><td>${pax.name}</td><td>${(Math.random() * 6 + 1).toFixed(1)} km</td>
      <td>₹ 75</td><td><span class="ht-badge ht-green">Completed</span></td>
    </tr>`);
    }

    /* ── Driver Ride Simulation (now Real GPS) ─────────────── */
    let watchId = null;

    function startDriverRide() {
        $('drv-start-ride').disabled = true;
        $('drv-start-ride').textContent = 'Live Tracking…';
        $('drv-alert').classList.remove('show');

        totalDist = 0; compliance = []; rideSeconds = 0;

        // Init map with a default location (Pune)
        if (!dMap) {
            dMap = L.map('d-map').setView([18.5204, 73.8567], 15);
            L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', { attribution: '© OSM' }).addTo(dMap);
            dMarker = L.marker([18.5204, 73.8567]).addTo(dMap).bindPopup('Your Rickshaw').openPopup();
        }

        // Timer
        clearInterval(timerInterval);
        timerInterval = setInterval(() => {
            rideSeconds++;
            const m = String(Math.floor(rideSeconds / 60)).padStart(2, '0');
            const s = String(rideSeconds % 60).padStart(2, '0');
            $('d-timer').textContent = `${m}:${s}`;
        }, 1000);

        // Real-Time Hardware Hook
        if (!navigator.geolocation) {
            $('d-status').textContent = 'GPS NOT SUPPORTED';
            return;
        }

        watchId = navigator.geolocation.watchPosition(
            async position => {
                const lat = position.coords.latitude;
                const lng = position.coords.longitude;

                // Sync UI
                if (dMarker && dMap) {
                    dMarker.setLatLng([lat, lng]);
                    dMap.panTo([lat, lng]);
                }

                if (lastPos) {
                    const dist = L.latLng(lastPos).distanceTo(L.latLng([lat, lng]));
                    totalDist += dist;
                    $('d-dist').textContent = totalDist.toFixed(1) + ' m';
                }
                lastPos = [lat, lng];

                // Sync Backend Safety Engine
                try {
                    const res = await fetch('/api/location/update', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                            'Authorization': `Bearer ${sessionToken}`
                        },
                        body: JSON.stringify({ lat, lng })
                    });
                    if (res.ok) {
                        const data = await res.json();
                        if (data.alert) {
                            $('d-status').textContent = '⚠ DEVATION ALERT';
                            $('drv-alert').classList.add('show');
                        }
                    }
                } catch (e) { }
            },
            err => console.error("GPS Error:", err),
            { enableHighAccuracy: true, maximumAge: 0 }
        );
    }

    function endRideSuccessfully() {
        if (watchId !== null) navigator.geolocation.clearWatch(watchId);
        clearInterval(timerInterval);
        $('d-status').textContent = '✅ Ride Complete';
        $('d-status').style.color = 'var(--acc)';
        $('drv-start-ride').disabled = false;
        $('drv-start-ride').textContent = '▶ Start Live Tracking';
        drvEarnings += 95; drvRidesDone++;
        refreshDriverEarnings();
        addToDriverHistory();
    }

    /* ════════════════════════════════════════════════════════
       PASSENGER DASHBOARD
    ════════════════════════════════════════════════════════ */
    function showPassengerDashboard(pax) {
        switchView('passenger-dashboard');
        paxWalletBalance = pax.balance || 0;
        paxRidesDone = pax.trips || 0;

        // Topbar
        $('pax-topbar-img').src = pax.photo;
        $('pax-topbar-name').textContent = pax.name;

        // Profile
        $('pax-photo').src = pax.photo;
        $('pax-name-h').textContent = pax.name;
        $('pax-id-p').textContent = `ID: ${pax.id}`;
        $('pax-mobile').textContent = pax.mobile;
        $('pax-email').textContent = pax.email || '—';
        $('pax-balance').textContent = `₹ ${pax.balance}`;
        $('pax-trips').textContent = pax.trips;
        $('pax-joined').textContent = pax.joinedDate;

        // Wallet
        refreshPaxWallet();

        // History
        populatePaxHistory();

        // Driver list for booking
        buildDriverList();

        // Sidebar nav
        setupSidebarNav('passenger');

        // Init QR scanner controls (wired once)
        initScanner();

        // End ride
        $('pax-end-ride').onclick = endPaxRide;

        // Logout
        $('pax-logout').onclick = doLogout;
    }

    function refreshPaxWallet() {
        $('pax-wallet-bal').textContent = `₹ ${paxWalletBalance}`;
        $('pax-total-spent').textContent = `₹ ${paxSpent}`;
        $('pax-rides-done').textContent = paxRidesDone;
        $('pax-topup-display').textContent = `₹ ${paxWalletBalance}`;
    }

    function populatePaxHistory() {
        const tbody = $('pax-hist-body');
        if (!tbody) return; tbody.innerHTML = '';
        const drvNames = RIKSHA_DB.drivers.slice(0, 5).map(d => d.name);
        const rows = [
            ['01 Mar 2026', drvNames[0] || 'Rajesh Kumar', '3.2 km', '₹ 95', 'Completed'],
            ['28 Feb 2026', drvNames[1] || 'Kavita Sharma', '1.8 km', '₹ 60', 'Completed'],
            ['27 Feb 2026', drvNames[2] || 'Suresh Verma', '5.1 km', '₹ 140', 'Completed'],
        ];
        rows.forEach(([date, drv, dist, fare, status]) => {
            tbody.innerHTML += `<tr>
        <td>${date}</td><td>${drv}</td><td>${dist}</td><td>${fare}</td>
        <td><span class="ht-badge ht-green">${status}</span></td>
      </tr>`;
        });
    }

    async function buildDriverList() {
        const container = $('driver-list');
        if (!container) return;
        container.innerHTML = '<div style="color:var(--text2);text-align:center;">Loading drivers...</div>';

        try {
            const res = await fetch('/api/drivers');
            const drivers = await res.json();
            container.innerHTML = '';

            drivers.slice(0, 9).forEach(drv => {
                const card = document.createElement('div');
                card.style.cssText = 'background:var(--dark3);border:1px solid var(--border);border-radius:12px;padding:1rem;cursor:pointer;transition:.2s;';
                card.innerHTML = `
            <img src="${drv.photo || `https://i.pravatar.cc/150?u=${drv.id}`}" style="width:48px;height:48px;border-radius:50%;object-fit:cover;border:2px solid var(--pri);margin-bottom:.6rem;">
            <div style="font-weight:800;color:var(--text);font-size:.92rem;">${drv.name}</div>
            <div style="font-size:.78rem;color:var(--text2);margin:.2rem 0;">${drv.vehicle_number || drv.vehicleNumber}</div>
            <div style="font-size:.78rem;color:var(--text2);">📍 ${drv.pick_location || drv.pick}</div>
            <div style="font-size:.78rem;color:var(--pri);margin-top:.3rem;">⭐ ${drv.rating}</div>
            <button style="margin-top:.8rem;width:100%;padding:.5rem;border:none;border-radius:8px;background:var(--pri);color:#000;font-weight:700;font-size:.82rem;cursor:pointer;">Book Ride</button>
        `;
                card.querySelector('button').onclick = () => startPaxRide(drv);
                card.onmouseenter = () => card.style.borderColor = 'var(--pri)';
                card.onmouseleave = () => card.style.borderColor = 'var(--border)';
                container.appendChild(card);
            });
        } catch (err) {
            container.innerHTML = '<div style="color:#ff5252;text-align:center;">Failed to load drivers.</div>';
        }
    }

    function startPaxRide(drv) {
        hide('pax-scan-zone');
        show('pax-ride-active');
        $('pax-alert').classList.remove('show');

        // Set driver details
        $('pax-drv-photo').src = drv.photo || `https://i.pravatar.cc/150?u=${drv.id}`;
        $('pax-drv-name').textContent = drv.name;
        $('pax-drv-vno').textContent = `${drv.vehicle_number || drv.vehicleNumber} • RC: ${drv.rc_number || drv.rcNo}`;

        totalDist = 0; compliance = []; rideSeconds = 0;

        // Visual timer handling
        clearInterval(timerInterval);
        timerInterval = setInterval(() => {
            rideSeconds++;
            $('p-timer').textContent =
                String(Math.floor(rideSeconds / 60)).padStart(2, '0') + ':' +
                String(rideSeconds % 60).padStart(2, '0');
        }, 1000);

        $('p-drv-status').textContent = 'En Route';
        $('p-drv-status').style.color = 'var(--acc)';
    }

    function endPaxRide() {
        clearInterval(rideInterval); clearInterval(timerInterval);
        hide('pax-ride-active');
        show('pax-scan-zone');
        $('pax-alert').classList.remove('show');
    }

    function addToPaxHistory(drv, fare) {
        const tbody = $('pax-hist-body');
        if (!tbody) return;
        const now = new Date().toLocaleDateString('en-IN', { day: '2-digit', month: 'short', year: 'numeric' });
        tbody.insertAdjacentHTML('afterbegin', `<tr>
      <td>${now}</td><td>${drv.name}</td><td>${(totalDist / 1000).toFixed(2)} km</td>
      <td>₹ ${fare}</td><td><span class="ht-badge ht-green">Completed</span></td>
    </tr>`);
    }

    /* ── Sidebar nav ─────────────────────────────────────────── */
    function setupSidebarNav(dash) {
        document.querySelectorAll(`.sb-link[data-dash="${dash}"]`).forEach(btn => {
            btn.addEventListener('click', () => {
                const view = btn.getAttribute('data-view');
                if (!view) return;
                activateSubView(dash, view);

                // Update page title
                const titles = {
                    'drv-profile': 'My Profile', 'drv-vehicle': 'Vehicle Details',
                    'drv-rides': 'Active Ride', 'drv-history': 'Ride History', 'drv-earnings': 'Earnings',
                    'pax-profile': 'My Profile', 'pax-ride': 'Active Ride',
                    'pax-history': 'Ride History', 'pax-scanner': 'Scan Driver QR'
                };
                const titleEl = $(dash === 'driver' ? 'drv-page-title' : 'pax-page-title');
                if (titleEl) titleEl.textContent = titles[view] || '';

                // Invalidate map size
                if (view === 'drv-rides' && dMap) setTimeout(() => dMap.invalidateSize(), 120);
                if (view === 'pax-ride' && pMap) setTimeout(() => pMap.invalidateSize(), 120);
            });
        });
    }

    /* ── Logout ──────────────────────────────────────────────── */
    function doLogout() {
        // Reset: Clear all intervals and state
        const highestId = window.setInterval(() => { }, 0);
        for (let i = 0; i <= highestId; i++) {
            window.clearInterval(i);
        }

        if (watchId !== null) navigator.geolocation.clearWatch(watchId);

        auth = null;
        sessionToken = null;
        currentRole = null;

        localStorage.removeItem('raksha_auth_state');
        // Keep trust token for fingerprinting but reset path
        switchView('landing');
    }


    /* ════════════════════════════════════════════════════════
       QR SCANNER  (passenger side)
    ════════════════════════════════════════════════════════ */
    let qrStream = null;     // active MediaStream (camera)
    let qrAnimId = null;     // requestAnimationFrame id
    let scannerReady = false;  // guard: init only once per login
    let scannedDriver = null;  // last driver resolved from QR

    function initScanner() {
        if (scannerReady) return;
        scannerReady = true;

        const toggleBtn = $('pax-scan-toggle');
        const viewport = $('qr-viewport');
        const statusBadge = $('pax-scan-status');
        const resultCard = $('drv-result-card');

        // ── Start / Stop toggle ────────────────────────────
        toggleBtn.onclick = () => {
            if (qrStream) {
                stopCamera();
                toggleBtn.innerHTML = '<ion-icon name="qr-code-outline"></ion-icon> Start Scanning';
                toggleBtn.classList.remove('stop');
                viewport.classList.remove('active');
                statusBadge.style.display = 'none';
            } else {
                resultCard.classList.remove('visible');
                startCamera();
            }
        };

        // ── Book this driver ───────────────────────────────
        $('drc-book-btn').onclick = () => {
            if (!scannedDriver) return;
            const rideBtn = document.querySelector('.sb-link[data-dash="passenger"][data-view="pax-ride"]');
            if (rideBtn) rideBtn.click();
            setTimeout(() => startPaxRide(scannedDriver), 80);
        };

        // ── Scan again ─────────────────────────────────────
        $('drc-rescan-btn').onclick = () => {
            scannedDriver = null;
            resultCard.classList.remove('visible');
            startCamera();
        };
    }

    function startCamera() {
        const toggleBtn = $('pax-scan-toggle');
        const viewport = $('qr-viewport');
        const statusBadge = $('pax-scan-status');

        if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
            statusBadge.style.display = 'inline-flex';
            setStatus('error', '⚠️ Camera not supported by this browser.');
            return;
        }

        navigator.mediaDevices.getUserMedia({ video: { facingMode: 'environment' } })
            .then(stream => {
                qrStream = stream;
                const video = $('qr-video');
                video.srcObject = stream;
                viewport.classList.add('active');
                toggleBtn.innerHTML = '<ion-icon name="stop-circle-outline"></ion-icon> Stop Camera';
                toggleBtn.classList.add('stop');
                statusBadge.style.display = 'inline-flex';
                setStatus('detecting', '<ion-icon name="scan-outline"></ion-icon> Scanning for QR code…');
                video.onloadedmetadata = () => runQRScan(video);
            })
            .catch(err => {
                statusBadge.style.display = 'inline-flex';
                setStatus('error', '⚠️ Camera access denied. Please allow camera permission.');
                console.warn('Camera error:', err);
            });
    }

    function stopCamera() {
        if (qrAnimId) { cancelAnimationFrame(qrAnimId); qrAnimId = null; }
        if (qrStream) { qrStream.getTracks().forEach(t => t.stop()); qrStream = null; }
        const video = $('qr-video');
        if (video) video.srcObject = null;
    }

    function runQRScan(video) {
        const canvas = $('qr-canvas');
        const ctx = canvas.getContext('2d');

        function tick() {
            if (!qrStream) return;   // camera was stopped
            if (video.readyState === video.HAVE_ENOUGH_DATA) {
                canvas.width = video.videoWidth;
                canvas.height = video.videoHeight;
                ctx.drawImage(video, 0, 0);

                const imgData = ctx.getImageData(0, 0, canvas.width, canvas.height);
                const code = jsQR(imgData.data, imgData.width, imgData.height, {
                    inversionAttempts: 'dontInvert'
                });

                if (code && code.data) {
                    stopCamera();
                    showDriverFromQR(code.data);
                    return;
                }
            }
            qrAnimId = requestAnimationFrame(tick);
        }
        qrAnimId = requestAnimationFrame(tick);
    }

    async function showDriverFromQR(driverId) {
        const toggleBtn = $('pax-scan-toggle');
        const viewport = $('qr-viewport');
        const statusBadge = $('pax-scan-status');
        const resultCard = $('drv-result-card');

        // Reset toggle button
        toggleBtn.innerHTML = '<ion-icon name="qr-code-outline"></ion-icon> Start Scanning';
        toggleBtn.classList.remove('stop');
        viewport.classList.remove('active');

        try {
            const res = await fetch('/api/drivers');
            const allDrivers = await res.json();
            const drv = allDrivers.find(d => d.id === driverId.trim());

            if (!drv) {
                statusBadge.style.display = 'inline-flex';
                setStatus('error', `❌ Unknown QR: "${driverId}". No matching driver found.`);
                return;
            }

            scannedDriver = drv;

            // Populate result card
            $('drc-photo').src = drv.photo || `https://i.pravatar.cc/150?u=${drv.id}`;
            $('drc-name').textContent = drv.name;
            $('drc-id').textContent = `ID: ${drv.id}`;
            $('drc-vno').textContent = drv.vehicle_number || drv.vehicleNumber;
            $('drc-rc').textContent = drv.rc_number || drv.rcNo;
            $('drc-vtype').textContent = drv.vehicle_type || drv.vehicleType || 'Eco-Rickshaw';
            $('drc-pick').textContent = drv.pick_location || drv.pick;
            $('drc-mobile').textContent = drv.mobile;
            $('drc-rating').textContent = `${drv.rating} ★`;
            $('drc-rides').textContent = drv.total_rides || drv.totalRides || 0;

            resultCard.classList.add('visible');
            statusBadge.style.display = 'inline-flex';
            setStatus('found', '✅ Driver verified successfully!');
        } catch (err) {
            statusBadge.style.display = 'inline-flex';
            setStatus('error', '❌ Network error looking up driver.');
        }
    }

    function setStatus(type, html) {
        const el = $('pax-scan-status');
        if (!el) return;
        el.className = `scanner-status ${type}`;
        el.innerHTML = html;
    }

    /* ── Smooth scroll for nav links ─────────────────────────── */
    document.querySelectorAll('a[href^="#"]').forEach(a => {
        a.addEventListener('click', e => {
            const target = document.querySelector(a.getAttribute('href'));
            if (target) { e.preventDefault(); target.scrollIntoView({ behavior: 'smooth' }); }
        });
    });

    /* ── Test credentials helper in console ─────────────────── */
    console.log('%c RakshaRide — Production API Connected ', 'background:#00E676;color:#000;font-weight:bold;font-size:14px;padding:4px 8px;');
    console.log(`Backend connected: Fetching live data via Flask API.`);


})();
