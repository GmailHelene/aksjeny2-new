/**
 * Enhanced Language Switching for Aksjeradar
 * Integrates with existing i18n.js and provides better UX
 */

class LanguageSwitcher {
    constructor() {
        this.currentLanguage = this.getStoredLanguage() || 'no';
        this.initialize();
    }

    initialize() {
        // Initialize language dropdowns
        this.updateLanguageDisplay();
        this.translateCurrentPage();
        this.addEventListeners();
    }

    getStoredLanguage() {
        return localStorage.getItem('aksjeradar_language') || 'no';
    }

    setLanguage(language) {
        if (!['no', 'en'].includes(language)) return;
        
        this.currentLanguage = language;
        localStorage.setItem('aksjeradar_language', language);
        
        // Make server call to persist language preference
        fetch(`/set_language/${language}`, {
            method: 'GET',
            headers: {
                'X-Requested-With': 'XMLHttpRequest'
            }
        }).then(() => {
            // Update display
            this.updateLanguageDisplay();
            this.translateCurrentPage();
            this.showLanguageChangeNotification(language);
            
            // Update i18n if it exists
            if (window.i18n && typeof window.i18n.setLanguage === 'function') {
                window.i18n.setLanguage(language);
            }
            
            // Refresh page to apply server-side translations
            setTimeout(() => {
                window.location.reload();
            }, 1000);
        }).catch(error => {
            console.error('Error setting language on server:', error);
            // Continue with client-side only
            this.updateLanguageDisplay();
            this.translateCurrentPage();
            this.showLanguageChangeNotification(language);
        });
    }

    updateLanguageDisplay() {
        // Update language display in all dropdowns
        const languageElements = document.querySelectorAll('#current-language, #footer-current-language');
        languageElements.forEach(element => {
            if (element) {
                element.textContent = this.currentLanguage.toUpperCase();
            }
        });

        // Update HTML lang attribute
        document.documentElement.lang = this.currentLanguage;
    }

    translateCurrentPage() {
        // Translate elements with data-i18n attributes
        const elementsToTranslate = document.querySelectorAll('[data-i18n]');
        elementsToTranslate.forEach(element => {
            const key = element.getAttribute('data-i18n');
            const translation = this.getTranslation(key);
            if (translation) {
                element.textContent = translation;
            }
        });

        // Translate placeholders
        const placeholderElements = document.querySelectorAll('[data-i18n-placeholder]');
        placeholderElements.forEach(element => {
            const key = element.getAttribute('data-i18n-placeholder');
            const translation = this.getTranslation(key);
            if (translation) {
                element.placeholder = translation;
            }
        });

        // Translate titles
        const titleElements = document.querySelectorAll('[data-i18n-title]');
        titleElements.forEach(element => {
            const key = element.getAttribute('data-i18n-title');
            const translation = this.getTranslation(key);
            if (translation) {
                element.title = translation;
            }
        });
    }

    getTranslation(key) {
        // Use existing i18n system if available
        if (window.i18n && typeof window.i18n.t === 'function') {
            return window.i18n.t(key);
        }

        // Fallback translation for key navigation elements
        const translations = {
            'no': {
                'nav.home': 'Hjem',
                'nav.stocks': 'Aksjer',
                'nav.analysis': 'Analyse',
                'nav.portfolio': 'Portefølje',
                'nav.news': 'Nyheter',
                'nav.pricing': 'Priser',
                'nav.login': 'Logg inn',
                'nav.register': 'Registrer deg',
                'nav.search': 'Søk aksjer...',
                'btn.search': 'Søk',
                'btn.save': 'Lagre',
                'btn.cancel': 'Avbryt',
                'loading': 'Laster...',
                'language.switch': 'Bytt språk'
            },
            'en': {
                'nav.home': 'Home',
                'nav.stocks': 'Stocks',
                'nav.analysis': 'Analysis',
                'nav.portfolio': 'Portfolio',
                'nav.news': 'News',
                'nav.pricing': 'Pricing',
                'nav.login': 'Login',
                'nav.register': 'Sign Up',
                'nav.search': 'Search stocks...',
                'btn.search': 'Search',
                'btn.save': 'Save',
                'btn.cancel': 'Cancel',
                'loading': 'Loading...',
                'language.switch': 'Switch language'
            }
        };

        return translations[this.currentLanguage]?.[key] || key;
    }

    addEventListeners() {
        // Listen for language change clicks
        document.addEventListener('click', (e) => {
            if (e.target.matches('[data-lang]')) {
                e.preventDefault();
                const language = e.target.getAttribute('data-lang');
                this.setLanguage(language);
            }
        });
    }

    showLanguageChangeNotification(language) {
        // Remove existing notifications
        document.querySelectorAll('.language-notification').forEach(el => {
            if (document.body.contains(el)) {
                document.body.removeChild(el);
            }
        });

        const message = language === 'en' ? 'Switched to English' : 'Byttet til norsk';
        const notification = document.createElement('div');
        notification.className = 'toast language-notification position-fixed top-0 start-50 translate-middle-x mt-3';
        notification.style.zIndex = '9999';
        notification.innerHTML = `
            <div class="toast-body bg-info text-white rounded">
                <i class="bi bi-globe me-2"></i>
                ${message}
            </div>
        `;

        document.body.appendChild(notification);
        
        if (typeof bootstrap !== 'undefined') {
            const toast = new bootstrap.Toast(notification, { delay: 2000 });
            toast.show();
            
            notification.addEventListener('hidden.bs.toast', () => {
                if (document.body.contains(notification)) {
                    document.body.removeChild(notification);
                }
            });
        } else {
            setTimeout(() => {
                if (document.body.contains(notification)) {
                    document.body.removeChild(notification);
                }
            }, 2000);
        }
    }
}

// Global functions for template use
function switchLanguage(language) {
    if (window.languageSwitcher) {
        window.languageSwitcher.setLanguage(language);
    }
}

function getCurrentLanguage() {
    return window.languageSwitcher ? window.languageSwitcher.currentLanguage : 'no';
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.languageSwitcher = new LanguageSwitcher();
});

// Export for testing
if (typeof module !== 'undefined' && module.exports) {
    module.exports = LanguageSwitcher;
}
