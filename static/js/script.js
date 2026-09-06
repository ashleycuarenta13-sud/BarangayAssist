const wrapper = document.getElementById('wrapper');
const loginLink = document.querySelector('.login-link');
const registerLink = document.querySelector('.register-link');
const btnPopup = document.querySelector('.btnLogin-popup');
const iconClose = document.getElementById('iconClose');
const menuToggle = document.getElementById('menuToggle');
const navLinks = document.getElementById('navLinks');
const mainHeader = document.getElementById('mainHeader');


// ==============================
// LOGIN / REGISTER SWITCH
// ==============================

if (registerLink) {
    registerLink.addEventListener('click', (e) => {
        e.preventDefault();
        wrapper.classList.add('active');
    });
}

if (loginLink) {
    loginLink.addEventListener('click', (e) => {
        e.preventDefault();
        wrapper.classList.remove('active');
    });
}


// ==============================
// LOGIN POPUP
// ==============================

if (btnPopup) {
    btnPopup.addEventListener('click', () => {
        wrapper.classList.remove('active');
        wrapper.classList.add('active-popup');
        document.body.classList.add('active-popup');
    });
}

if (iconClose) {
    iconClose.addEventListener('click', () => {
        wrapper.classList.remove('active-popup');
        document.body.classList.remove('active-popup');
    });
}


// ==============================
// CLOSE POPUP WHEN CLICKING OUTSIDE
// ==============================

document.body.addEventListener('click', (e) => {
    if (
        document.body.classList.contains('active-popup') &&
        wrapper &&
        !wrapper.contains(e.target) &&
        e.target !== btnPopup
    ) {
        wrapper.classList.remove('active-popup');
        document.body.classList.remove('active-popup');
    }
});


// ==============================
// MOBILE MENU
// ==============================

if (menuToggle && navLinks) {
    menuToggle.addEventListener('click', () => {
        navLinks.classList.toggle('active');
    });
}


// ==============================
// HEADER SCROLL EFFECT
// ==============================

window.addEventListener('scroll', () => {
    if (mainHeader) {
        mainHeader.classList.toggle('scrolled', window.scrollY > 40);
    }
});


// ==============================
// SHOW / HIDE PASSWORD
// ==============================

function toggleVis(id) {
    const el = document.getElementById(id);
    const icon = document.getElementById('eye-' + id);

    if (el && icon) {
        const showing = el.type === 'password';
        el.type = showing ? 'text' : 'password';
        icon.setAttribute('name', showing ? 'eye-off' : 'eye');
    }
}


// ==============================
// ERROR HANDLER
// ==============================

function setError(id, show) {
    const box = document.getElementById('box-' + id);
    const error = document.getElementById('err-' + id);

    if (box) {
        box.classList.toggle('invalid', show);
    }

    if (error) {
        error.classList.toggle('show', show);
    }
}


// ==============================
// LOGIN FORM
// ==============================

const loginForm = document.getElementById('loginForm');
if (loginForm) {
    loginForm.addEventListener('submit', function(e) {
        e.preventDefault();

        const email = document.getElementById('loginEmail');
        const pass = document.getElementById('loginPassword');

        const emailOk = /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email.value.trim());
        const passOk = pass.value.length > 0;

        setError('loginEmail', !emailOk);
        setError('loginPassword', !passOk);

        const status = document.getElementById('loginStatus');
        if (status) {
            status.classList.remove('ok', 'bad', 'show');
        }

        if (emailOk && passOk) {
            this.submit(); // I-submit sa Django Backend
        } else if (status) {
            status.textContent = 'Please fix the highlighted fields.';
            status.classList.add('bad', 'show');
        }
    });
}


// ==============================
// PASSWORD STRENGTH METER
// ==============================

const regPassword = document.getElementById('regPassword');
if (regPassword) {
    regPassword.addEventListener('input', function() {
        const v = regPassword.value;
        let score = 0;

        if (v.length >= 8) score++;
        if (/[A-Z]/.test(v)) score++;
        if (/[0-9]/.test(v)) score++;
        if (/[^A-Za-z0-9]/.test(v)) score++;

        const fill = document.getElementById('meterFill');
        if (fill) {
            fill.style.width = (score / 4 * 100) + '%';
            fill.style.background =
                score <= 1 ? '#8B2E28' :
                score <= 2 ? '#B9873A' : '#3F5B44';
        }
    });
}


// ==============================
// REGISTER FORM
// ==============================

const registerForm = document.getElementById('registerForm');
if (registerForm) {
    registerForm.addEventListener('submit', function(e) {
        e.preventDefault();

        const name = document.getElementById('regName');
        const purok = document.getElementById('regPurok');
        const contact = document.getElementById('regContact');
        const email = document.getElementById('regEmail');
        const pass = document.getElementById('regPassword');
        const confirm = document.getElementById('regConfirm');
        const consent = document.getElementById('regConsent');

        const nameOk = name ? name.value.trim().length > 1 : false;
        const purokOk = purok ? purok.value.trim().length > 0 : false;
        const contactOk = contact ? /^0\d{10}$/.test(contact.value.trim()) : false;
        const emailOk = email ? /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email.value.trim()) : false;
        const passOk = pass ? pass.value.length >= 8 : false;
        const confirmOk = confirm && pass ? confirm.value === pass.value && confirm.value.length > 0 : false;
        const consentOk = consent ? consent.checked : false;

        // Show errors
        setError('regName', !nameOk);
        setError('regPurok', !purokOk);
        setError('regContact', !contactOk);
        setError('regEmail', !emailOk);
        setError('regPassword', !passOk);
        setError('regConfirm', !confirmOk);

        const consentError = document.getElementById('err-regConsent');
        if (consentError) {
            consentError.classList.toggle('show', !consentOk);
        }

        const status = document.getElementById('registerStatus');
        if (status) {
            status.classList.remove('ok', 'bad', 'show');
        }

        const allOk = nameOk && purokOk && contactOk && emailOk && passOk && confirmOk && consentOk;

        if (allOk) {
            this.submit(); // I-submit sa Django Backend
        } else if (status) {
            status.textContent = 'Please complete and correct the highlighted fields.';
            status.classList.add('bad', 'show');
        }
    });
}