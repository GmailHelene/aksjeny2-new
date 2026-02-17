// pwa-installer.js - Hjelper brukere med å installere appen som en PWA

document.addEventListener('DOMContentLoaded', function() {
    let deferredPrompt;
    const installButton = document.createElement('button');
    installButton.style.display = 'none';
    installButton.classList.add('btn', 'btn-primary', 'install-button');
    installButton.textContent = 'Installer Aksjeradar';

    // Sjekk om vi allerede har lagt til installasjonsknappen
    if (!document.querySelector('.install-container')) {
        // Opprett en container for installasjonsknappen
        const installContainer = document.createElement('div');
        installContainer.classList.add('install-container');
        installContainer.style.position = 'fixed';
        installContainer.style.bottom = '20px';
        installContainer.style.right = '20px';
        installContainer.style.zIndex = '1000';
        installContainer.appendChild(installButton);
        document.body.appendChild(installContainer);
    }

    // Lytt etter 'beforeinstallprompt' hendelsen
    window.addEventListener('beforeinstallprompt', (e) => {
        // Forhindre Chrome 67 og tidligere fra å automatisk vise installasjonsruten
        e.preventDefault();
        // Lagre hendelsen slik at den kan utløses senere
        deferredPrompt = e;
        // Oppdater UI for å vise installasjonsknappen
        installButton.style.display = 'block';
        
        // Legg til en kort tooltip-melding
        const tooltip = document.createElement('div');
        tooltip.classList.add('install-tooltip');
        tooltip.style.position = 'absolute';
        tooltip.style.bottom = '50px';
        tooltip.style.right = '0';
        tooltip.style.backgroundColor = '#212529';
        tooltip.style.color = 'white';
        tooltip.style.padding = '8px 12px';
        tooltip.style.borderRadius = '4px';
        tooltip.style.fontSize = '14px';
        tooltip.style.boxShadow = '0 2px 10px rgba(0,0,0,0.2)';
        tooltip.style.maxWidth = '220px';
        tooltip.textContent = 'Installer Aksjeradar på enheten din for raskere tilgang og offline-bruk!';
        
        document.querySelector('.install-container').appendChild(tooltip);
        
        // Fjern tooltip etter 8 sekunder
        setTimeout(() => {
            if (tooltip.parentNode) {
                tooltip.parentNode.removeChild(tooltip);
            }
        }, 8000);
    });

    // Håndter klikk på installasjonsknappen
    installButton.addEventListener('click', (e) => {
        // Skjul installasjonsknappen
        installButton.style.display = 'none';
        // Vis installasjonsruten
        deferredPrompt.prompt();
        // Vent på at brukeren skal svare på installasjonsruten
        deferredPrompt.userChoice.then((choiceResult) => {
            if (choiceResult.outcome === 'accepted') {
                console.log('Bruker aksepterte installasjonsruten');
                
                // Vis en bekreftelsesmelding
                const successMessage = document.createElement('div');
                successMessage.classList.add('alert', 'alert-success', 'install-success');
                successMessage.style.position = 'fixed';
                successMessage.style.bottom = '20px';
                successMessage.style.left = '50%';
                successMessage.style.transform = 'translateX(-50%)';
                successMessage.style.zIndex = '1000';
                successMessage.style.padding = '10px 20px';
                successMessage.style.borderRadius = '4px';
                successMessage.textContent = 'Takk for at du installerte Aksjeradar! Du kan nå bruke appen fra din startskjerm.';
                document.body.appendChild(successMessage);
                
                // Fjern meldingen etter 5 sekunder
                setTimeout(() => {
                    if (successMessage.parentNode) {
                        successMessage.parentNode.removeChild(successMessage);
                    }
                }, 5000);
            } else {
                console.log('Bruker avviste installasjonsruten');
                // Vis installasjonsknappen igjen
                setTimeout(() => {
                    installButton.style.display = 'block';
                }, 30000); // Vent 30 sekunder før vi viser knappen igjen
            }
            deferredPrompt = null;
        });
    });

    // Sjekk om appen allerede er installert
    window.addEventListener('appinstalled', (evt) => {
        console.log('Aksjeradar er installert');
        installButton.style.display = 'none';
    });
    
    // Hvis vi er i standalone-modus (PWA), er appen allerede installert
    if (window.matchMedia('(display-mode: standalone)').matches || window.navigator.standalone === true) {
        installButton.style.display = 'none';
    }
});
