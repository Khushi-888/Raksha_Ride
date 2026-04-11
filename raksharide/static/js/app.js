/* ================================================================
   RakshaRide — Main Application Logic
   Flow:
     Driver   → registers with Vehicle No + RC No → login via RC email
     Passenger→ registers with Name/Mobile/Email  → login via email OR mobile
   ================================================================ */

(function () {
    'use strict';

    /* ── State ─────────────────────────────────────────────── */
    let currentRole = null;   // 'driver' | 'passenger'
    let currentUser = null;   // record from DB
    let loginRoleTab = 'driver';

    // Ride simulation state
    let dMap = null, pMap = null;
    let dMarker = null, pMarker = null;
    let rideInterval = null, timerInterval = null;
    let rideSeconds = 0, totalDist = 0, compliance = [];

    // Earnings / wallet (session only)
    let drvEarnings = 0;
    let paxWalletBalance = 0;
    let paxSpent = 0;
    let drvRidesDone = 0, paxRidesDone = 0;

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
    if ($('open-login-btn')) $('open-login-btn').onclick = () => { loginRoleTab = 'driver'; openLoginModal(); };
    if ($('hero-login-btn')) $('hero-login-btn').onclick = () => { loginRoleTab = 'driver'; openLoginModal(); };
    if ($('open-reg-btn')) $('open-reg-btn').onclick = () => openModal('drv-reg-modal');
    if ($('hero-reg-btn')) $('hero-reg-btn').onclick = () => openModal('drv-reg-modal');
    if ($('login-close-btn')) $('login-close-btn').onclick = () => closeModal('login-modal');
    if ($('drv-reg-close')) $('drv-reg-close').onclick = () => closeModal('drv-reg-modal');
    if ($('pax-reg-close')) $('pax-reg-close').onclick = () => closeModal('pax-reg-modal');

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
        $('login-form').reset();
        openModal('login-modal');
        setLoginTab(role || loginRoleTab);
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
        clearMsg('login-err');
    }

    /* ── Login form submit ──────────────────────────────────── */
    $('login-form').addEventListener('submit', e => {
        e.preventDefault();
        clearMsg('login-err');

        const password = $('l-password').value.trim();
        if (!password) { showMsg('login-err', 'Password is required.', 'err'); return; }

        if (loginRoleTab === 'driver') {
            const email = $('l-email').value.trim().toLowerCase();
            if (!email) { showMsg('login-err', 'Email is required for driver login.', 'err'); return; }

            const drv = RIKSHA_DB.drivers.find(d => d.email.toLowerCase() === email);
            if (!drv) { showMsg('login-err', 'No driver found with that email.', 'err'); return; }
            if (drv.password !== password) { showMsg('login-err', 'Incorrect password.', 'err'); return; }

            currentUser = drv;
            currentRole = 'driver';
            closeModal('login-modal');
            showDriverDashboard(drv);

        } else {
            const credential = $('l-mobile').value.trim();
            if (!credential) { showMsg('login-err', 'Enter email or mobile number.', 'err'); return; }

            // Check pre-seeded + runtime-registered passengers
            const allPax = [...RIKSHA_DB.passengers, ...(RIKSHA_DB.registeredPassengers || [])];
            const pax = allPax.find(p =>
                (p.email && p.email.toLowerCase() === credential.toLowerCase()) ||
                (p.mobile && p.mobile === credential)
            );
            if (!pax) { showMsg('login-err', 'Passenger not found. Please register first.', 'err'); return; }
            if (pax.password !== password) { showMsg('login-err', 'Incorrect password.', 'err'); return; }

            currentUser = pax;
            currentRole = 'passenger';
            closeModal('login-modal');
            showPassengerDashboard(pax);
        }
    });

    /* ── Driver Registration ────────────────────────────────── */
    $('drv-reg-form').addEventListener('submit', e => {
        e.preventDefault();
        clearMsg('drv-reg-err'); clearMsg('drv-reg-ok');

        const name = $('dr-name').value.trim();
        const age = parseInt($('dr-age').value);
        const mobile = $('dr-mobile').value.trim();
        const email = $('dr-email').value.trim().toLowerCase();
        const vno = $('dr-vno').value.trim().toUpperCase();
        const rcNo = $('dr-rc').value.trim().toUpperCase();
        const pick = $('dr-pick').value.trim();
        const pass = $('dr-pass').value.trim();

        if (!name || !age || !mobile || !email || !vno || !rcNo || !pick || !pass) {
            showMsg('drv-reg-err', 'All fields are required.', 'err'); return;
        }
        // Duplicate check: vehicle number or email
        const dup = RIKSHA_DB.drivers.find(d => d.vehicleNumber === vno || d.email.toLowerCase() === email);
        if (dup) { showMsg('drv-reg-err', 'A driver with this Vehicle No. or Email already exists.', 'err'); return; }

        const newId = `DRV-${2001 + RIKSHA_DB.drivers.length}`;
        const newDriver = {
            id: newId, name, age, mobile, email, vehicleNumber: vno,
            pick, rcNo, password: pass,
            rating: 4.5, totalRides: 0, experience: '0 Years',
            lastInspection: 'Not yet', photo: `https://i.pravatar.cc/300?u=${newId}`,
            verified: true, vehicleType: 'Electric Eco-Rickshaw'
        };
        RIKSHA_DB.drivers.push(newDriver);

        showMsg('drv-reg-ok', `✅ Registered! Your ID: ${newId}. Email "${email}" is your login. Password = "${pass}". You can now Sign In.`, 'ok');
        $('drv-reg-form').reset();
    });

    /* ── Passenger Registration ─────────────────────────────── */
    $('pax-reg-form').addEventListener('submit', e => {
        e.preventDefault();
        clearMsg('pax-reg-err'); clearMsg('pax-reg-ok');

        const name = $('pr-name').value.trim();
        const mobile = $('pr-mobile').value.trim();
        const email = $('pr-email').value.trim().toLowerCase();
        const pass = $('pr-pass').value.trim();

        if (!name || !mobile || !pass) { showMsg('pax-reg-err', 'Name, Mobile and Password are required.', 'err'); return; }

        const allPax = [...RIKSHA_DB.passengers, ...(RIKSHA_DB.registeredPassengers || [])];
        const dup = allPax.find(p => p.mobile === mobile || (email && p.email && p.email.toLowerCase() === email));
        if (dup) { showMsg('pax-reg-err', 'An account with this mobile/email already exists. Please login.', 'err'); return; }

        const newId = `USR-${6001 + (RIKSHA_DB.registeredPassengers || []).length}`;
        const newPax = {
            id: newId, name, mobile,
            email: email || `${name.toLowerCase().replace(/\s+/g, '')}${newId.toLowerCase()}@rider.in`,
            password: pass, balance: 0, joinedDate: 'Mar 2026', trips: 0,
            photo: `https://i.pravatar.cc/300?u=${newId}`, verified: true
        };
        if (!RIKSHA_DB.registeredPassengers) RIKSHA_DB.registeredPassengers = [];
        RIKSHA_DB.registeredPassengers.push(newPax);

        showMsg('pax-reg-ok', `✅ Account created! ID: ${newId}. Login with your mobile "${mobile}"${email ? ' or email "' + email + '"' : ''} + password.`, 'ok');
        $('pax-reg-form').reset();
    });

    /* ════════════════════════════════════════════════════════
       DRIVER DASHBOARD
    ════════════════════════════════════════════════════════ */
    function showDriverDashboard(drv) {
        hide('landing');
        show('driver-dashboard');
        paxWalletBalance = drv.balance || 0;

        // Topbar
        $('drv-topbar-img').src = drv.photo;
        $('drv-topbar-name').textContent = drv.name;

        // Profile view
        $('drv-photo').src = drv.photo;
        $('drv-name-h').textContent = drv.name;
        $('drv-id-p').textContent = `ID: ${drv.id}`;
        $('drv-age').textContent = drv.age;
        $('drv-mobile').textContent = drv.mobile;
        $('drv-email').textContent = drv.email;
        $('drv-pick').textContent = drv.pick;
        $('drv-rating').textContent = `${drv.rating} ★`;
        $('drv-rides-count').textContent = drv.totalRides.toLocaleString();
        $('drv-exp').textContent = drv.experience;

        // Vehicle view
        $('drv-vno-h').textContent = drv.vehicleNumber;
        $('drv-vtype-p').textContent = drv.vehicleType;
        $('drv-rc').textContent = drv.rcNo;
        $('drv-vno').textContent = drv.vehicleNumber;
        $('drv-vtype').textContent = drv.vehicleType;
        $('drv-inspect').textContent = drv.lastInspection;

        // Earnings init
        drvEarnings = drv.totalRides * 65;
        drvRidesDone = drv.totalRides;
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

    /* ── Driver Ride Simulation ──────────────────────────────── */
    const SAFE_PATH = [
        [18.5204, 73.8567], [18.5215, 73.8580], [18.5228, 73.8595],
        [18.5240, 73.8612], [18.5252, 73.8628], [18.5265, 73.8644]
    ];

    function startDriverRide() {
        $('drv-start-ride').disabled = true;
        $('drv-start-ride').textContent = 'Ride in Progress…';
        $('drv-alert').classList.remove('show');

        totalDist = 0; compliance = []; rideSeconds = 0;

        // Init map
        if (!dMap) {
            dMap = L.map('d-map').setView(SAFE_PATH[0], 15);
            L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', { attribution: '© OSM' }).addTo(dMap);
            dMarker = L.marker(SAFE_PATH[0]).addTo(dMap).bindPopup('Your Rickshaw').openPopup();
            L.polyline(SAFE_PATH, { color: '#FFB300', weight: 4, opacity: .5 }).addTo(dMap);
        } else {
            dMarker.setLatLng(SAFE_PATH[0]); dMap.setView(SAFE_PATH[0], 15);
        }

        // Timer
        clearInterval(timerInterval);
        timerInterval = setInterval(() => {
            rideSeconds++;
            const m = String(Math.floor(rideSeconds / 60)).padStart(2, '0');
            const s = String(rideSeconds % 60).padStart(2, '0');
            $('d-timer').textContent = `${m}:${s}`;
        }, 1000);

        let step = 0;
        clearInterval(rideInterval);
        rideInterval = setInterval(() => {
            if (step >= 14) {
                clearInterval(rideInterval); clearInterval(timerInterval);
                $('d-status').textContent = '✅ Ride Complete';
                $('d-status').style.color = 'var(--acc)';
                $('drv-start-ride').disabled = false;
                $('drv-start-ride').textContent = '▶ Start Ride Simulation';
                drvEarnings += 95; drvRidesDone++;
                refreshDriverEarnings();
                addToDriverHistory();
                return;
            }
            const prev = dMarker.getLatLng();
            let next;
            if (step >= 8 && step < 11) {
                next = [prev.lat + 0.0035, prev.lng + 0.0035]; // deviation
            } else {
                next = SAFE_PATH[Math.min(step, SAFE_PATH.length - 1)];
            }
            const dist = L.latLng(prev).distanceTo(L.latLng(next));
            totalDist += dist;
            dMarker.setLatLng(next); dMap.panTo(next);
            updateRideUI('driver', next);
            step++;
        }, 2000);
    }

    function updateRideUI(who, pos) {
        let minDist = Infinity;
        SAFE_PATH.forEach(p => {
            const d = L.latLng(pos).distanceTo(L.latLng(p));
            if (d < minDist) minDist = d;
        });
        compliance.push(minDist <= 1000);
        const integ = Math.round(compliance.filter(Boolean).length / compliance.length * 100);

        if (who === 'driver') {
            $('d-dist').textContent = totalDist.toFixed(0) + ' m';
            $('d-integrity').textContent = integ + '%';
            if (minDist > 1000) {
                $('d-status').textContent = '⚠ ALERT';
                $('d-status').style.color = '#ff5252';
                $('drv-alert-msg').textContent = 'Route deviation > 1km detected!';
                $('drv-alert').classList.add('show');
            } else {
                $('d-status').textContent = 'On Route';
                $('d-status').style.color = 'var(--acc)';
                $('drv-alert').classList.remove('show');
            }
        } else {
            $('p-dist').textContent = totalDist.toFixed(0) + ' m';
            $('p-integrity').textContent = integ + '%';
            if (minDist > 1000) {
                $('p-drv-status').textContent = '⚠ THREAT';
                $('p-drv-status').style.color = '#ff5252';
                $('pax-alert-msg').textContent = 'Driver deviated > 1km from route!';
                $('pax-alert').classList.add('show');
            } else {
                $('p-drv-status').textContent = 'On Route ✓';
                $('p-drv-status').style.color = 'var(--acc)';
                $('pax-alert').classList.remove('show');
            }
        }
    }

    /* ════════════════════════════════════════════════════════
       PASSENGER DASHBOARD
    ════════════════════════════════════════════════════════ */
    function showPassengerDashboard(pax) {
        hide('landing');
        show('passenger-dashboard');
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

        // Wallet top-up
        $('pax-topup-btn').onclick = () => {
            paxWalletBalance += 200;
            refreshPaxWallet();
            $('pax-balance').textContent = `₹ ${paxWalletBalance}`;
        };

        // End / Finish ride buttons
        $('pax-end-ride').onclick = endPaxRide;
        $('pax-finish-ride').onclick = endPaxRide;

        // Payment modal buttons
        function closePayModal() {
            $('pay-modal-overlay').style.display = 'none';
            // Reset ride view
            hide('pax-ride-active');
            show('pax-scan-zone');
            $('pax-alert').classList.remove('show');
        }
        $('pay-modal-close').onclick = closePayModal;
        $('pay-modal-close2').onclick = closePayModal;
        $('pay-modal-confirm').onclick = () => {
            $('pay-modal-confirm').textContent = '✅ Done! Thanks for paying!';
            $('pay-modal-confirm').style.background = 'linear-gradient(135deg,#FFB300,#e65100)';
            setTimeout(closePayModal, 1200);
        };

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

    function buildDriverList() {
        const container = $('driver-list');
        if (!container) return;
        container.innerHTML = '';
        RIKSHA_DB.drivers.slice(0, 9).forEach(drv => {
            const card = document.createElement('div');
            card.style.cssText = 'background:var(--dark3);border:1px solid var(--border);border-radius:12px;padding:1rem;cursor:pointer;transition:.2s;';
            card.innerHTML = `
        <img src="${drv.photo}" style="width:48px;height:48px;border-radius:50%;object-fit:cover;border:2px solid var(--pri);margin-bottom:.6rem;">
        <div style="font-weight:800;color:var(--text);font-size:.92rem;">${drv.name}</div>
        <div style="font-size:.78rem;color:var(--text2);margin:.2rem 0;">${drv.vehicleNumber}</div>
        <div style="font-size:.78rem;color:var(--text2);">📍 ${drv.pick}</div>
        <div style="font-size:.78rem;color:var(--pri);margin-top:.3rem;">⭐ ${drv.rating}</div>
        <button style="margin-top:.8rem;width:100%;padding:.5rem;border:none;border-radius:8px;background:var(--pri);color:#000;font-weight:700;font-size:.82rem;cursor:pointer;">Book Ride</button>
      `;
            card.querySelector('button').onclick = () => startPaxRide(drv);
            card.onmouseenter = () => card.style.borderColor = 'var(--pri)';
            card.onmouseleave = () => card.style.borderColor = 'var(--border)';
            container.appendChild(card);
        });
    }

    function startPaxRide(drv) {
        activeRideDriver = drv; // store for payment modal
        hide('pax-scan-zone');
        show('pax-ride-active');
        $('pax-alert').classList.remove('show');

        $('pax-drv-photo').src = drv.photo;
        $('pax-drv-name').textContent = drv.name;
        $('pax-drv-vno').textContent = `${drv.vehicleNumber} • RC: ${drv.rcNo}`;

        totalDist = 0; compliance = []; rideSeconds = 0;

        // Init map
        if (!pMap) {
            pMap = L.map('p-map').setView(SAFE_PATH[0], 15);
            L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', { attribution: '© OSM' }).addTo(pMap);
            pMarker = L.marker(SAFE_PATH[0]).addTo(pMap).bindPopup(`Riding with ${drv.name}`).openPopup();
            L.polyline(SAFE_PATH, { color: '#00E676', weight: 4, opacity: .5 }).addTo(pMap);
        } else {
            pMarker.setLatLng(SAFE_PATH[0]); pMap.setView(SAFE_PATH[0], 15);
        }

        clearInterval(timerInterval);
        timerInterval = setInterval(() => {
            rideSeconds++;
            $('p-timer').textContent =
                String(Math.floor(rideSeconds / 60)).padStart(2, '0') + ':' +
                String(rideSeconds % 60).padStart(2, '0');
        }, 1000);

        let step = 0;
        clearInterval(rideInterval);
        rideInterval = setInterval(() => {
            if (step >= 14) {
                clearInterval(rideInterval); clearInterval(timerInterval);
                $('p-drv-status').textContent = '✅ Arrived!';
                $('p-drv-status').style.color = 'var(--acc)';
                const fare = 60 + Math.floor(totalDist / 100) * 5;
                // Auto show payment
                paxSpent += fare; paxWalletBalance = Math.max(0, paxWalletBalance - fare);
                paxRidesDone++;
                refreshPaxWallet();
                addToPaxHistory(drv, fare);
                // Show payment modal automatically
                setTimeout(() => showPaymentModal(drv, fare), 600);
                return;
            }
            const prev = pMarker.getLatLng();
            let next;
            if (step >= 8 && step < 11) {
                next = [prev.lat + 0.0035, prev.lng + 0.0035];
            } else {
                next = SAFE_PATH[Math.min(step, SAFE_PATH.length - 1)];
            }
            const dist = L.latLng(prev).distanceTo(L.latLng(next));
            totalDist += dist;
            pMarker.setLatLng(next); pMap.panTo(next);
            updateRideUI('passenger', next);
            step++;
        }, 2000);
    }

    // Track active driver for payment
    let activeRideDriver = null;
    let activeRideFare = 0;

    function endPaxRide() {
        clearInterval(rideInterval); clearInterval(timerInterval);
        // Calculate fare
        const fare = 60 + Math.floor(totalDist / 100) * 5;
        activeRideFare = fare;
        // Show payment modal with driver's QR
        showPaymentModal(activeRideDriver, fare);
    }

    function showPaymentModal(drv, fare) {
        const modal = $('pay-modal-overlay');
        if (!modal) return;
        $('pay-modal-fare').textContent = `₹ ${fare}`;
        const f2 = $('pay-modal-fare2'); if (f2) f2.textContent = fare;
        $('pay-modal-driver').textContent = drv ? drv.name : '—';
        $('pay-modal-vehicle').textContent = drv ? drv.vehicleNumber : '—';
        const qrWrap = $('pay-modal-qr-wrap');
        const qrImg = $('pay-modal-qr-img');
        const qrNote = $('pay-modal-qr-note');
        // Try fetching driver's payment QR from DB (driver must be logged into same session)
        const storedQR = drv && drv._paymentQR ? drv._paymentQR : null;
        if (storedQR) {
            qrImg.src = storedQR;
            qrWrap.style.display = 'block';
            if (qrNote) qrNote.style.display = 'none';
        } else {
            // Try API (works when Flask backend is running)
            fetch(`/api/get_driver_payment_qr?driver_id=${drv ? drv.id : ''}`, { credentials: 'same-origin' })
                .then(r => r.json())
                .then(d => {
                    if (d.payment_qr_image) {
                        qrImg.src = d.payment_qr_image;
                        qrWrap.style.display = 'block';
                        if (qrNote) qrNote.style.display = 'none';
                    } else {
                        qrWrap.style.display = 'none';
                        if (qrNote) qrNote.style.display = 'block';
                    }
                })
                .catch(() => {
                    qrWrap.style.display = 'none';
                    if (qrNote) qrNote.style.display = 'block';
                });
        }
        modal.style.display = 'flex';
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
                // Deactivate all
                document.querySelectorAll(`.sb-link[data-dash="${dash}"]`).forEach(b => b.classList.remove('active'));
                btn.classList.add('active');
                // Hide all views in this dashboard
                const dashEl = $(dash === 'driver' ? 'driver-dashboard' : 'passenger-dashboard');
                dashEl.querySelectorAll('.dash-view').forEach(v => v.classList.remove('active'));
                const target = $(view);
                if (target) target.classList.add('active');

                // Update page title
                const titles = {
                    'drv-profile': 'My Profile', 'drv-vehicle': 'Vehicle Details',
                    'drv-rides': 'Active Ride', 'drv-history': 'Ride History',
                    'drv-earnings': 'Earnings', 'drv-payqr': 'Payment QR',
                    'pax-profile': 'My Profile', 'pax-ride': 'Find a Ride',
                    'pax-history': 'Ride History', 'pax-wallet': 'Wallet',
                    'pax-scanner': 'Scan Driver QR'
                };
                const titleEl = $(dash === 'driver' ? 'drv-page-title' : 'pax-page-title');
                if (titleEl) titleEl.textContent = titles[view] || '';

                // Invalidate map size if switching to ride view
                if (view === 'drv-rides' && dMap) setTimeout(() => dMap.invalidateSize(), 120);
                if (view === 'pax-ride' && pMap) setTimeout(() => pMap.invalidateSize(), 120);
            });
        });
    }

    /* ── Logout ──────────────────────────────────────────────── */
    function doLogout() {
        currentUser = null; currentRole = null;
        clearInterval(rideInterval); clearInterval(timerInterval);
        dMap = null; pMap = null;
        hide('driver-dashboard');
        hide('passenger-dashboard');
        show('landing');
        window.scrollTo(0, 0);
    }

    /* ── Smooth scroll for nav links ─────────────────────────── */
    document.querySelectorAll('a[href^="#"]').forEach(a => {
        a.addEventListener('click', e => {
            const target = document.querySelector(a.getAttribute('href'));
            if (target) { e.preventDefault(); target.scrollIntoView({ behavior: 'smooth' }); }
        });
    });

    /* ── Test credentials helper in console ─────────────────── */
    console.log('%c RakshaRide — Test Credentials ', 'background:#FFB300;color:#000;font-weight:bold;font-size:14px;padding:4px 8px;');
    console.log(`Driver login → Email: ${RIKSHA_DB.drivers[0].email} | Password: ${RIKSHA_DB.drivers[0].password}`);
    console.log(`Passenger login → Mobile: ${RIKSHA_DB.passengers[0].mobile} | Password: ${RIKSHA_DB.passengers[0].password}`);

})();
