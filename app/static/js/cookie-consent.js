// Enkel cookie consent placeholder
console.log("Cookie consent loaded.");

document.addEventListener('DOMContentLoaded', function() {
    if (!localStorage.getItem('cookieConsent')) {
        const consentBar = document.createElement('div');
        consentBar.id = 'cookieConsentBar';
        consentBar.style.position = 'fixed';
        consentBar.style.bottom = '0';
        consentBar.style.left = '0';
        consentBar.style.width = '100%';
        consentBar.style.background = '#212529';
        consentBar.style.color = '#fff';
        consentBar.style.padding = '1rem';
        consentBar.style.zIndex = '9999';
        consentBar.innerHTML = `
            <div class="container d-flex flex-column flex-md-row align-items-center justify-content-between">
                <span>
                    Aksjeradar bruker kun nødvendige cookies for innlogging og brukeropplevelse. Ved å bruke tjenesten godtar du dette. 
                    <a href="/privacy" class="text-info text-decoration-underline">Les mer</a>
                </span>
                <div class="mt-2 mt-md-0">
                    <button id="acceptCookies" class="btn btn-success btn-sm me-2">Godta</button>
                    <button id="declineCookies" class="btn btn-outline-light btn-sm">Avslå</button>
                </div>
            </div>
        `;
        document.body.appendChild(consentBar);

        document.getElementById('acceptCookies').onclick = function() {
            localStorage.setItem('cookieConsent', 'accepted');
            consentBar.remove();
        };
        document.getElementById('declineCookies').onclick = function() {
            localStorage.setItem('cookieConsent', 'declined');
            consentBar.remove();
        };
    }
});
