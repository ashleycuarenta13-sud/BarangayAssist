const wrapper = document.getElementById('wrapper');

const loginLink = document.querySelector('.login-link');
const registerLink = document.querySelector('.register-link');
const btnPopup = document.querySelector('.btnLogin-popup');
const iconClose = document.getElementById('iconClose');
const menuToggle = document.getElementById('menuToggle');
const navLinks = document.getElementById('navlinks');
const mainHeader = document.getElementById('mainHeader');


// ==============================
// LOGIN / REGISTER SWITCH
// ==============================

registerLink.addEventListener('click', (e) => {
    e.preventDefault();

    wrapper.classList.add('active');
});

loginLink.addEventListener('click', (e) => {
    e.preventDefault();

    wrapper.classList.remove('active');
});


// ==============================
// LOGIN POPUP
// ==============================

btnPopup.addEventListener('click', () => {
    wrapper.classList.remove('active');
    wrapper.classList.add('active-popup');
    document.body.classList.add('active-popup');
});

iconClose.addEventListener('click', () => {
    wrapper.classList.remove('active-popup');
    document.body.classList.remove('active-popup');
});


// ==============================
// CLOSE POPUP WHEN CLICKING OUTSIDE
// ==============================

document.body.addEventListener('click', (e) => {

    if (
        document.body.classList.contains('active-popup') &&
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

menuToggle.addEventListener('click', () => {
    navLinks.classList.toggle('active');
});


// ==============================
// HEADER SCROLL EFFECT
// ==============================

window.addEventListener('scroll', () => {
    mainHeader.classList.toggle('scrolled', window.scrollY > 40);
});


// ==============================
// SHOW / HIDE PASSWORD
// ==============================

function toggleVis(id) {

    const el = document.getElementById(id);
    const icon = document.getElementById('eye-' + id);

    const showing = el.type === 'password';

    el.type = showing ? 'text' : 'password';

    icon.setAttribute(
        'name',
        showing ? 'eye-off' : 'eye'
    );
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

document.getElementById('loginForm').addEventListener('submit', function(e) {

    e.preventDefault();

    const email = document.getElementById('loginEmail');
    const pass = document.getElementById('loginPassword');

    const emailOk =
        /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(
            email.value.trim()
        );

    const passOk = pass.value.length > 0;

    setError('loginEmail', !emailOk);
    setError('loginPassword', !passOk);

    const status = document.getElementById('loginStatus');

    status.classList.remove('ok', 'bad', 'show');

    if (emailOk && passOk) {

        status.textContent =
            'Design preview only - no account has actually been authenticated.';

        status.classList.add('ok', 'show');

    } else {

        status.textContent =
            'Please fix the highlighted fields.';

        status.classList.add('bad', 'show');
    }

});


// ==============================
// PASSWORD STRENGTH METER
// ==============================

const regPassword = document.getElementById('regPassword');

regPassword.addEventListener('input', function() {

    const v = regPassword.value;

    let score = 0;

    if (v.length >= 8) score++;
    if (/[A-Z]/.test(v)) score++;
    if (/[0-9]/.test(v)) score++;
    if (/[^A-Za-z0-9]/.test(v)) score++;

    const fill = document.getElementById('meterFill');

    fill.style.width = (score / 4 * 100) + '%';

    fill.style.background =
        score <= 1 ?
        '#8B2E28' :
        score <= 2 ?
        '#B9873A' :
        '#3F5B44';

});


// ==============================
// REGISTER FORM
// ==============================

document.getElementById('registerForm').addEventListener('submit', function(e) {

    e.preventDefault();

    const name = document.getElementById('regName');
    const purok = document.getElementById('regPurok');
    const contact = document.getElementById('regContact');
    const email = document.getElementById('regEmail');
    const pass = document.getElementById('regPassword');
    const confirm = document.getElementById('regConfirm');
    const consent = document.getElementById('regConsent');

    const nameOk =
        name.value.trim().length > 1;

    const purokOk =
        purok.value.trim().length > 0;

    const contactOk =
        /^0\d{10}$/.test(contact.value.trim());

    const emailOk =
        /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(
            email.value.trim()
        );

    const passOk =
        pass.value.length >= 8;

    const confirmOk =
        confirm.value === pass.value &&
        confirm.value.length > 0;

    const consentOk =
        consent.checked;


    // Show errors

    setError('regName', !nameOk);
    setError('regPurok', !purokOk);
    setError('regContact', !contactOk);
    setError('regEmail', !emailOk);
    setError('regPassword', !passOk);
    setError('regConfirm', !confirmOk);


    // Consent error
    const consentError =
        document.getElementById('err-regConnect');

    if (consentError) {
        consentError.classList.toggle(
            'show', !consentOk
        );
    }


    // Status

    const status =
        document.getElementById('registerStatus');

    status.classList.remove('ok', 'bad', 'show');


    const allOk =
        nameOk &&
        purokOk &&
        contactOk &&
        emailOk &&
        passOk &&
        confirmOk &&
        consentOk;


    if (allOk) {

        status.textContent =
            'Design preview only - no account has actually been created.';

        status.classList.add('ok', 'show');

    } else {

        status.textContent =
            'Please complete and correct the highlighted fields.';

        status.classList.add('bad', 'show');
    }

});