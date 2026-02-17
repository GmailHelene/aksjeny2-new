// PWA Installation functionality - Enhanced for mobile
let deferredPrompt;
let installButton;
let installBanner;

// Initialize PWA installation when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    installButton = document.getElementById('pwa-install-btn');
    installBanner = document.getElementById('pwa-install-banner');
    
    // Hide install button and banner initially
    if (installButton) {
        installButton.style.display = 'none';
    }
    if (installBanner) {
        installBanner.style.display = 'none';
    }
    
    // Check if app is already installed
    if (isAppInstalled()) {
        console.log('PWA is already installed');
        hideInstallUI();
        return;
    }
    
    // Show mobile banner for first-time mobile visitors with better logic
    if (isMobileDevice() && !localStorage.getItem('pwa-banner-dismissed') && !isAppInstalled()) {
        // Only show for supported browsers on mobile
        if ((isAndroidDevice() && isChromeBasedBrowser()) || isIOSDevice()) {
            setTimeout(() => {
                showMobileBanner();
            }, 3000); // Show after 3 seconds for better UX
        } else if (isAndroidDevice()) {
            // For non-Chrome Android browsers, show a message to switch to Chrome
            setTimeout(() => {
                showBrowserRecommendation();
            }, 5000);
        }
    }
    
    // Show install hint for desktop users
    if (!isMobileDevice() && !localStorage.getItem('pwa-install-hint-shown') && isChromeBasedBrowser()) {
        setTimeout(() => {
            showDesktopInstallHint();
        }, 8000); // Show after 8 seconds
    }
});

// Enhanced mobile device detection
function isMobileDevice() {
    const userAgent = navigator.userAgent.toLowerCase();
    const mobileKeywords = ['android', 'webos', 'iphone', 'ipad', 'ipod', 'blackberry', 'iemobile', 'opera mini', 'windows phone'];
    
    // Check user agent
    const isMobileUA = mobileKeywords.some(keyword => userAgent.includes(keyword));
    
    // Check screen size and orientation
    const isMobileScreen = window.innerWidth <= 768 || 
                          (window.innerWidth <= 1024 && window.innerHeight <= 768);
    
    // Check touch capability
    const hasTouch = 'ontouchstart' in window || 
                    navigator.maxTouchPoints > 0 || 
                    navigator.msMaxTouchPoints > 0;
    
    // Check if it's a tablet in landscape mode
    const isTablet = (window.innerWidth >= 768 && window.innerWidth <= 1024) && hasTouch;
    
    return isMobileUA || (isMobileScreen && hasTouch) || isTablet;
}

// Enhanced iOS detection
function isIOSDevice() {
    return /iPad|iPhone|iPod/.test(navigator.userAgent) && !window.MSStream;
}

// Enhanced Android detection  
function isAndroidDevice() {
    return /Android/.test(navigator.userAgent);
}

// Check if running in Chrome or Chrome-based browser
function isChromeBasedBrowser() {
    const isChrome = /Chrome/.test(navigator.userAgent) && /Google Inc/.test(navigator.vendor);
    const isEdge = /Edg/.test(navigator.userAgent);
    const isOpera = /OPR/.test(navigator.userAgent);
    const isSamsung = /SamsungBrowser/.test(navigator.userAgent);
    
    return isChrome || isEdge || isOpera || isSamsung;
}

// Check if app is already installed
function isAppInstalled() {
    // Check if running in standalone mode (iOS/Android)
    if (window.matchMedia('(display-mode: standalone)').matches) {
        return true;
    }
    
    // Check if running as PWA on iOS
    if (window.navigator.standalone === true) {
        return true;
    }
    
    // Check if installed flag is set
    if (localStorage.getItem('pwa-installed') === 'true') {
        return true;
    }
    
    return false;
}

// Show mobile-specific banner
function showMobileBanner() {
    if (installBanner && !isAppInstalled()) {
        // Only show if the browser supports PWA installation
        if ((isAndroidDevice() && isChromeBasedBrowser()) || isIOSDevice()) {
            installBanner.style.display = 'block';
            installBanner.classList.add('animate__animated', 'animate__slideInUp');
            
            // Add pulse effect to install button in banner
            const installBtn = installBanner.querySelector('button');
            if (installBtn) {
                installBtn.classList.add('animate__pulse');
            }
        }
    }
}

// Show browser recommendation for unsupported browsers
function showBrowserRecommendation() {
    if (isAndroidDevice() && !isChromeBasedBrowser()) {
        const message = `
            <strong>🌐 For best opplevelse:</strong><br>
            Åpne Aksjeradar i Chrome eller Samsung Internet for å kunne installere appen som PWA<br>
            <small class="text-muted">Din nåværende nettleser støtter ikke app-installasjon</small>
        `;
        showInstallMessage(message, 'info', 8000);
        localStorage.setItem('browser-recommendation-shown', 'true');
    }
}

// Show desktop install hint
function showDesktopInstallHint() {
    if (!deferredPrompt) {
        const hint = createInstallHint('💡 Tip: Du kan installere Aksjeradar som en app! Se etter install-ikonet i adresselinjen.');
        document.body.appendChild(hint);
        localStorage.setItem('pwa-install-hint-shown', 'true');
    }
}

// Create install hint element
function createInstallHint(message) {
    const hint = document.createElement('div');
    hint.className = 'alert alert-info alert-dismissible fade show position-fixed';
    hint.style.cssText = 'top: 80px; right: 20px; z-index: 9999; max-width: 350px; animation: slideIn 0.5s ease;';
    hint.innerHTML = `
        <div class="d-flex align-items-center">
            <i class="bi bi-lightbulb me-2"></i>
            <div class="flex-grow-1">${message}</div>
            <button type="button" class="btn-close" onclick="this.parentElement.parentElement.remove()"></button>
        </div>
    `;
    
    // Auto-remove after 8 seconds
    setTimeout(() => {
        if (hint.parentNode) {
            hint.remove();
        }
    }, 8000);
    
    return hint;
}

// Dismiss PWA banner
function dismissPWABanner() {
    localStorage.setItem('pwa-banner-dismissed', 'true');
    if (installBanner) {
        installBanner.classList.add('animate__animated', 'animate__slideOutDown');
        setTimeout(() => {
            installBanner.style.display = 'none';
        }, 500);
    }
}

// Hide all install UI elements
function hideInstallUI() {
    if (installButton) {
        installButton.style.display = 'none';
    }
    if (installBanner) {
        installBanner.style.display = 'none';
    }
}

// Listen for network status changes
window.addEventListener('online', function() {
    console.log('PWA: Back online');
    showInstallMessage('🌐 Tilbake på nett! Alle funksjoner er tilgjengelige.', 'success', 3000);
});

window.addEventListener('offline', function() {
    console.log('PWA: Gone offline');
    showInstallMessage('📡 Offline-modus aktivert. Grunnleggende funksjoner er fortsatt tilgjengelige.', 'info', 4000);
});

// Enhanced beforeinstallprompt handler with better timing
window.addEventListener('beforeinstallprompt', (e) => {
    console.log('PWA install prompt triggered');
    
    // Prevent the mini-infobar from appearing on mobile
    e.preventDefault();
    
    // Save the event so it can be triggered later
    deferredPrompt = e;
    
    // Show the install button with animation
    if (installButton && !isAppInstalled()) {
        installButton.style.display = 'inline-block';
        installButton.classList.add('animate__animated', 'animate__pulse');
        
        // Add a subtle glow effect
        installButton.style.boxShadow = '0 0 15px rgba(13, 110, 253, 0.6)';
        installButton.style.borderColor = '#0d6efd';
        
        // Add a small badge to indicate new feature
        const badge = document.createElement('span');
        badge.className = 'position-absolute translate-middle badge rounded-pill bg-success';
        badge.style.top = '0px';
        badge.style.left = '100%';
        badge.style.fontSize = '0.6rem';
        badge.textContent = 'Ny!';
        badge.style.zIndex = '1';
        installButton.style.position = 'relative';
        installButton.appendChild(badge);
        
        // Remove badge after 10 seconds
        setTimeout(() => {
            if (badge.parentNode) {
                badge.remove();
            }
        }, 10000);
    }
    
    // Show mobile banner if on mobile and not dismissed
    if (isMobileDevice() && !localStorage.getItem('pwa-banner-dismissed') && !isAppInstalled()) {
        setTimeout(() => {
            showMobileBanner();
        }, 1500); // Shorter delay since install prompt is available
    }
    
    // Track the install prompt event for analytics
    if (typeof gtag !== 'undefined') {
        gtag('event', 'pwa_install_prompt_shown', {
            'event_category': 'PWA',
            'event_label': 'Install Prompt Available'
        });
    }
});

// Enhanced install function
function installPWA() {
    console.log('Install PWA triggered');
    
    if (!deferredPrompt) {
        console.log('No install prompt available, showing manual instructions');
        showInstallInstructions();
        return;
    }
    
    // Hide the install UI immediately
    hideInstallUI();
    
    // Show loading state
    showInstallMessage('Forbereder installasjon...', 'info', 2000);
    
    // Show the install prompt
    deferredPrompt.prompt();
    
    // Wait for the user to respond to the prompt
    deferredPrompt.userChoice.then((choiceResult) => {
        if (choiceResult.outcome === 'accepted') {
            console.log('User accepted the install prompt');
            
            // Mark as installed
            localStorage.setItem('pwa-installed', 'true');
            localStorage.setItem('pwa-banner-dismissed', 'true');
            
            // Show success message
            showInstallMessage('🎉 Aksjeradar er installert! Du finner appen på hjemskjermen din.', 'success', 5000);
            
            // Hide install UI
            hideInstallUI();
        } else {
            console.log('User dismissed the install prompt');
            
            // Show info message with manual instructions
            showInstallMessage('💡 Du kan installere appen senere via nettleserens meny.', 'info', 4000);
            
            // Show install button again after a delay
            setTimeout(() => {
                if (installButton && !isAppInstalled()) {
                    installButton.style.display = 'inline-block';
                }
            }, 5000);
        }
        
        deferredPrompt = null;
    }).catch((err) => {
        console.error('Install prompt error:', err);
        showInstallMessage('Det oppstod en feil under installasjonen. Prøv igjen senere.', 'warning', 4000);
    });
}

// Show manual installation instructions based on device/browser
function showInstallInstructions() {
    let instructions = '';
    let icon = '📱';
    
    if (isIOSDevice()) {
        // iOS Safari
        instructions = `
            <strong>📱 Installer på iOS:</strong><br>
            1. Trykk på Del-knappen <i class="bi bi-share"></i> nederst i Safari<br>
            2. Scroll ned og velg "Legg til på Hjem-skjerm"<br>
            3. Trykk "Legg til" for å fullføre installasjonen<br>
            <small class="text-muted">Appen vil da være tilgjengelig på hjemskjermen din</small>
        `;
        icon = '🍎';
    } else if (isAndroidDevice() && isChromeBasedBrowser()) {
        // Android Chrome/Edge/Samsung Browser
        instructions = `
            <strong>🤖 Installer på Android:</strong><br>
            1. Trykk på meny-knappen <i class="bi bi-three-dots-vertical"></i> øverst til høyre<br>
            2. Velg "Legg til på startskjerm" eller "Installer app"<br>
            3. Følg instruksjonene for å fullføre<br>
            <small class="text-muted">Appen vil oppføre seg som en native app</small>
        `;
        icon = '🤖';
    } else if (isAndroidDevice()) {
        // Android other browsers
        instructions = `
            <strong>🤖 Installer på Android:</strong><br>
            For best opplevelse, bruk Chrome eller Samsung Internet<br>
            1. Åpne Aksjeradar i Chrome<br>
            2. Trykk på meny og velg "Legg til på startskjerm"<br>
            <small class="text-muted">Andre nettlesere støtter ikke PWA-installasjon</small>
        `;
        icon = '🤖';
    } else {
        // Desktop browsers
        instructions = `
            <strong>💻 Installer på PC/Mac:</strong><br>
            1. Se etter install-ikonet <i class="bi bi-download"></i> i adresselinjen<br>
            2. Eller gå til nettleserens meny og velg "Installer Aksjeradar"<br>
            3. Følg instruksjonene for å fullføre<br>
            <small class="text-muted">Krever Chrome, Edge eller lignende nettleser</small>
        `;
        icon = '💻';
    }
    
    showInstallMessage(`${icon} ${instructions}`, 'info', 10000);
}

// Enhanced install message function
function showInstallMessage(message, type = 'info', duration = 6000) {
    // Remove any existing messages
    const existingMessages = document.querySelectorAll('.pwa-install-message');
    existingMessages.forEach(msg => msg.remove());
    
    // Create message element
    const messageDiv = document.createElement('div');
    messageDiv.className = `alert alert-${type} alert-dismissible fade show position-fixed pwa-install-message`;
    messageDiv.style.cssText = `
        top: 20px; 
        right: 20px; 
        z-index: 9999; 
        max-width: 350px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.2);
        border: none;
        border-radius: 8px;
    `;
    
    const iconMap = {
        'success': '✅',
        'info': 'ℹ️',
        'warning': '⚠️',
        'danger': '❌'
    };
    
    messageDiv.innerHTML = `
        <div class="d-flex align-items-start">
            <span class="me-2" style="font-size: 1.2em;">${iconMap[type] || 'ℹ️'}</span>
            <div class="flex-grow-1">${message}</div>
            <button type="button" class="btn-close" onclick="this.parentElement.parentElement.remove()"></button>
        </div>
    `;
    
    // Add to body with animation
    document.body.appendChild(messageDiv);
    messageDiv.classList.add('animate__animated', 'animate__slideInRight');
    
    // Auto-remove after specified duration
    if (duration > 0) {
        setTimeout(() => {
            if (messageDiv.parentNode) {
                messageDiv.classList.add('animate__animated', 'animate__slideOutRight');
                setTimeout(() => {
                    messageDiv.remove();
                }, 500);
            }
        }, duration);
    }
}

// Listen for app installation
window.addEventListener('appinstalled', () => {
    console.log('PWA was installed successfully');
    
    // Mark as installed
    localStorage.setItem('pwa-installed', 'true');
    localStorage.setItem('pwa-banner-dismissed', 'true');
    localStorage.setItem('pwa-install-date', new Date().toISOString());
    
    // Hide install UI
    hideInstallUI();
    
    // Clear the deferredPrompt
    deferredPrompt = null;
    
    // Show enhanced success message
    const successMessage = `
        <strong>🎉 Velkommen til Aksjeradar!</strong><br>
        Appen er nå installert på enheten din.<br>
        <small class="text-success">Du finner den på hjemskjermen eller i app-menyen</small>
    `;
    showInstallMessage(successMessage, 'success', 6000);
    
    // Send analytics event
    if (typeof gtag !== 'undefined') {
        gtag('event', 'pwa_installed', {
            'event_category': 'PWA',
            'event_label': 'App Installation Completed',
            'value': 1
        });
    }
    
    // Optional: Set up push notifications after installation
    setTimeout(() => {
        requestNotificationPermission();
    }, 3000);
});

// Request notification permission after PWA installation
function requestNotificationPermission() {
    if ('Notification' in window && Notification.permission === 'default') {
        const message = `
            <strong>🔔 Vil du motta varsler?</strong><br>
            Få beskjed om viktige markedsoppdateringer og aksjetips<br>
            <button class="btn btn-sm btn-primary mt-2" onclick="enableNotifications()">Aktiver varsler</button>
            <button class="btn btn-sm btn-outline-secondary mt-2 ms-2" onclick="this.parentElement.parentElement.remove()">Ikke nå</button>
        `;
        showInstallMessage(message, 'info', 0); // Don't auto-dismiss
    }
}

// Enable notifications function
function enableNotifications() {
    Notification.requestPermission().then(permission => {
        const messageElement = document.querySelector('.pwa-install-message');
        if (messageElement) {
            messageElement.remove();
        }
        
        if (permission === 'granted') {
            showInstallMessage('🔔 Varsler er aktivert! Du vil få beskjed om viktige oppdateringer.', 'success', 4000);
            localStorage.setItem('notifications-enabled', 'true');
        } else {
            showInstallMessage('Du kan aktivere varsler senere i nettleserinnstillingene.', 'info', 3000);
        }
    });
}

// Export the notification function for global use
window.enableNotifications = enableNotifications;

// Enhanced service worker registration
if ('serviceWorker' in navigator) {
    window.addEventListener('load', function() {
        navigator.serviceWorker.register('/static/service-worker.js')
            .then(function(registration) {
                console.log('ServiceWorker registration successful:', registration.scope);
                
                // Check for updates
                registration.addEventListener('updatefound', () => {
                    const newWorker = registration.installing;
                    newWorker.addEventListener('statechange', () => {
                        if (newWorker.state === 'installed' && navigator.serviceWorker.controller) {
                            showInstallMessage(
                                '🔄 En ny versjon av appen er tilgjengelig! <br><button class="btn btn-sm btn-primary mt-2" onclick="window.location.reload()">Last på nytt</button>', 
                                'info', 
                                0 // Don't auto-dismiss
                            );
                        }
                    });
                });
                
                // Handle service worker messages
                navigator.serviceWorker.addEventListener('message', event => {
                    if (event.data && event.data.type === 'NEW_VERSION') {
                        showInstallMessage('🔄 Ny versjon tilgjengelig! Last siden på nytt.', 'info', 0);
                    }
                });
            })
            .catch(function(err) {
                console.log('ServiceWorker registration failed:', err);
            });
    });
}

// Hide install UI if app is already installed
if (isAppInstalled()) {
    hideInstallUI();
}

// Add CSS animations if not already present
if (!document.querySelector('#pwa-animations')) {
    const style = document.createElement('style');
    style.id = 'pwa-animations';
    style.textContent = `
        @keyframes slideIn {
            from { transform: translateX(100%); opacity: 0; }
            to { transform: translateX(0); opacity: 1; }
        }
        .animate__slideInRight {
            animation: slideIn 0.5s ease-out;
        }
        .animate__slideOutRight {
            animation: slideIn 0.5s ease-in reverse;
        }
        .animate__slideInUp {
            animation: slideInUp 0.5s ease-out;
        }
        .animate__slideOutDown {
            animation: slideInUp 0.5s ease-in reverse;
        }
        @keyframes slideInUp {
            from { transform: translateY(100%); opacity: 0; }
            to { transform: translateY(0); opacity: 1; }
        }
        @keyframes pulse {
            0%, 100% { transform: scale(1); }
            50% { transform: scale(1.05); }
        }
        .animate__pulse {
            animation: pulse 2s infinite;
        }
    `;
    document.head.appendChild(style);
}

// Export functions for global use
window.installPWA = installPWA;
window.dismissPWABanner = dismissPWABanner;
window.showInstallInstructions = showInstallInstructions;
