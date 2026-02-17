/**
 * Simple Internationalization System for Aksjeradar
 * Supports Norwegian (default) and English
 */

class SimpleI18n {
    constructor() {
        this.currentLanguage = this.getStoredLanguage() || 'no';
        this.translations = {
            'no': {
                // Navigation
                'nav.home': 'Hjem',
                'nav.stocks': 'Aksjer',
                'nav.analysis': 'Analyse', 
                'nav.portfolio': 'Portefølje',
                'nav.pricing': 'Priser',
                'nav.features': 'Nye funksjoner',
                'nav.search': 'Søk aksjer...',
                'nav.login': 'Logg inn',
                'nav.register': 'Registrer deg',
                'nav.logout': 'Logg ut',
                
                // Dropdown items
                'dropdown.overview': 'Oversikt',
                'dropdown.oslo_bors': 'Oslo Børs',
                'dropdown.global_markets': 'Globale markeder',
                'dropdown.crypto': 'Kryptovaluta',
                'dropdown.currencies': 'Valutakurser',
                'dropdown.compare': 'Sammenlign aksjer',
                'dropdown.technical': 'Teknisk analyse',
                'dropdown.predictions': 'Prisprediksjoner',
                'dropdown.ai_analysis': 'AI-analyse',
                'dropdown.market_overview': 'Markedsoversikt',
                'dropdown.portfolio': 'Min portefølje',
                'dropdown.watchlist': 'Favorittliste',
                'dropdown.tips': 'Aksjetips',
                'dropdown.analyst_rec': 'Analytiker-anbefalinger',
                'dropdown.social_sentiment': 'Sosial sentiment',
                'dropdown.ai_predictions': 'AI-prediksjoner',
                'dropdown.notifications': 'Varsler',
                'dropdown.settings': 'Innstillinger',
                
                // Common buttons and actions
                'btn.search': 'Søk',
                'btn.save': 'Lagre',
                'btn.cancel': 'Avbryt',
                'btn.close': 'Lukk',
                'btn.view_all': 'Se alle',
                'btn.install_app': 'Installer app',
                
                // Market data
                'market.change': 'Endring',
                'market.volume': 'Volum',
                'market.market_cap': 'Markedsverdi',
                'market.price': 'Pris',
                'market.open': 'Åpnet',
                'market.high': 'Høy',
                'market.low': 'Lav',
                'market.close': 'Lukket',
                
                // Time periods
                'time.today': 'I dag',
                'time.week': 'Uke',
                'time.month': 'Måned',
                'time.year': 'År',
                'time.1d': '1d',
                'time.1w': '1u',
                'time.1m': '1m',
                'time.1y': '1å',
                
                // Status messages
                'status.loading': 'Laster...',
                'status.error': 'Feil',
                'status.success': 'Vellykket',
                'status.no_data': 'Ingen data tilgjengelig',
                
                // Footer
                'footer.privacy': 'Personvern',
                'footer.terms': 'Vilkår',
                'footer.contact': 'Kontakt',
                'footer.copyright': 'Alle rettigheter reservert',
                
                // Common phrases
                'common.welcome': 'Velkommen',
                'common.loading': 'Laster...',
                'common.error': 'En feil oppstod',
                'common.try_again': 'Prøv igjen',
                'common.offline': 'Du er offline',
                
                // Trial and subscription
                'trial.expired_banner': 'Prøveperioden din er utløpt!',
                'trial.remaining_days': 'Du har {0} dager igjen av din prøveperiode.',
                'trial.upgrade_now': 'Oppgrader nå',
                'trial.view_pricing': 'Se priser',
                'trial.features_title': 'Premium-funksjoner:',
                'trial.features_list': 'Teknisk analyse • AI-prediksjoner • Porteføljetracking • Markedsinnsikt • Og mye mer!',
                'subscription.title': 'Abonnement',
                'subscription.monthly_basic': 'Månedlig Basic',
                'subscription.pro': 'Pro',
                'subscription.annual': 'Årlig',
                'subscription.most_popular': 'Mest populær',
                'subscription.save_money': 'Spar penger',
                'subscription.per_month': '/måned',
                'subscription.per_year': '/år',
                'subscription.buy_stripe': 'Kjøp med Stripe',
                'subscription.upgrade_premium': 'Oppgrader til Premium',
                'subscription.referral_discount': 'Du har 20% rabatt tilgjengelig!',
                'subscription.invite_friends': 'Inviter venner og få 20% rabatt på årlig abonnement!',
                
                // Features and analysis
                'analysis.title': 'Analyse',
                'analysis.technical': 'Teknisk analyse',
                'analysis.ai_predictions': 'AI-prediksjoner',
                'analysis.buffett': 'Warren Buffett analyse',
                'analysis.graham': 'Benjamin Graham analyse',
                'analysis.short': 'Short-analyse',
                'analysis.loading': 'Analyserer...',
                'analysis.no_data': 'Ingen analysedata tilgjengelig',
                'analysis.value_investing': 'Verdiinvestering',
                'analysis.risk_assessment': 'Risikovurdering',
                'analysis.recommendation': 'Anbefaling',
                
                // Portfolio and watchlist
                'portfolio.title': 'Portefølje',
                'portfolio.add_stock': 'Legg til aksje',
                'portfolio.remove_stock': 'Fjern aksje',
                'portfolio.total_value': 'Total verdi',
                'portfolio.daily_change': 'Dagens endring',
                'portfolio.performance': 'Ytelse',
                'watchlist.title': 'Favorittliste',
                'watchlist.add_to_watchlist': 'Legg til favoritter',
                'watchlist.remove_from_watchlist': 'Fjern fra favoritter',
                'watchlist.empty': 'Din favorittliste er tom',
                
                // User account
                'user.profile': 'Profil',
                'user.account': 'Konto',
                'user.settings': 'Innstillinger',
                'user.notifications': 'Varsler',
                'user.subscription': 'Abonnement',
                'user.billing': 'Fakturering',
                'user.referrals': 'Referanser',
                'user.logout': 'Logg ut',
                'user.login': 'Logg inn',
                'user.register': 'Registrer deg',
                'user.password': 'Passord',
                'user.email': 'E-post',
                'user.name': 'Navn',
                
                // News and market data
                'news.title': 'Nyheter',
                'news.market_news': 'Markedsnyheter',
                'news.latest': 'Siste nyheter',
                'news.source': 'Kilde',
                'news.read_more': 'Les mer',
                'news.published': 'Publisert',
                'market.today': 'I dag',
                'market.gainers': 'Vinnere',
                'market.losers': 'Tapere',
                'market.most_active': 'Mest aktive',
                'market.indices': 'Indekser',
                'market.currencies': 'Valutakurser',
                'market.commodities': 'Råvarer',
                
                // Alerts and notifications
                'alert.success': 'Vellykket!',
                'alert.warning': 'Advarsel',
                'alert.error': 'Feil',
                'alert.info': 'Informasjon',
                'notification.price_alert': 'Prisvarsel',
                'notification.news_alert': 'Nyhetsvarsel',
                'notification.portfolio_update': 'Porteføljeoppdatering',
                
                // Search and filters
                'search.placeholder': 'Søk aksjer, selskaper...',
                'search.no_results': 'Ingen resultater funnet',
                'search.searching': 'Søker...',
                'filter.all': 'Alle',
                'filter.favorites': 'Favoritter',
                'filter.sector': 'Sektor',
                'filter.market_cap': 'Markedsverdi',
                'filter.price_range': 'Prisområde',
                
                // Languages
                'language.norwegian': 'Norsk',
                'language.english': 'English',
                'language.switch': 'Bytt språk',
            },
            'en': {
                // Navigation
                'nav.home': 'Home',
                'nav.stocks': 'Stocks',
                'nav.analysis': 'Analysis',
                'nav.portfolio': 'Portfolio', 
                'nav.pricing': 'Pricing',
                'nav.features': 'New Features',
                'nav.search': 'Search stocks...',
                'nav.login': 'Login',
                'nav.register': 'Sign Up',
                'nav.logout': 'Logout',
                
                // Dropdown items
                'dropdown.overview': 'Overview',
                'dropdown.oslo_bors': 'Oslo Stock Exchange',
                'dropdown.global_markets': 'Global Markets',
                'dropdown.crypto': 'Cryptocurrency',
                'dropdown.currencies': 'Exchange Rates',
                'dropdown.compare': 'Compare Stocks',
                'dropdown.technical': 'Technical Analysis',
                'dropdown.predictions': 'Price Predictions',
                'dropdown.ai_analysis': 'AI Analysis',
                'dropdown.market_overview': 'Market Overview',
                'dropdown.portfolio': 'My Portfolio',
                'dropdown.watchlist': 'Watchlist',
                'dropdown.tips': 'Stock Tips',
                'dropdown.analyst_rec': 'Analyst Recommendations',
                'dropdown.social_sentiment': 'Social Sentiment',
                'dropdown.ai_predictions': 'AI Predictions',
                'dropdown.notifications': 'Notifications',
                'dropdown.settings': 'Settings',
                
                // Common buttons and actions
                'btn.search': 'Search',
                'btn.save': 'Save',
                'btn.cancel': 'Cancel',
                'btn.close': 'Close',
                'btn.view_all': 'View All',
                'btn.install_app': 'Install App',
                
                // Market data
                'market.change': 'Change',
                'market.volume': 'Volume',
                'market.market_cap': 'Market Cap',
                'market.price': 'Price',
                'market.open': 'Open',
                'market.high': 'High',
                'market.low': 'Low',
                'market.close': 'Close',
                
                // Time periods
                'time.today': 'Today',
                'time.week': 'Week',
                'time.month': 'Month',
                'time.year': 'Year',
                'time.1d': '1d',
                'time.1w': '1w',
                'time.1m': '1m',
                'time.1y': '1y',
                
                // Status messages
                'status.loading': 'Loading...',
                'status.error': 'Error',
                'status.success': 'Success',
                'status.no_data': 'No data available',
                
                // Footer
                'footer.privacy': 'Privacy',
                'footer.terms': 'Terms',
                'footer.contact': 'Contact',
                'footer.copyright': 'All rights reserved',
                
                // Common phrases
                'common.welcome': 'Welcome',
                'common.loading': 'Loading...',
                'common.error': 'An error occurred',
                'common.try_again': 'Try again',
                'common.offline': 'You are offline',
                
                // Trial and subscription
                'trial.expired_banner': 'Your trial period has expired!',
                'trial.remaining_days': 'You have {0} days left of your trial period.',
                'trial.upgrade_now': 'Upgrade now',
                'trial.view_pricing': 'View pricing',
                'trial.features_title': 'Premium features:',
                'trial.features_list': 'Technical analysis • AI predictions • Portfolio tracking • Market insights • And much more!',
                'subscription.title': 'Subscription',
                'subscription.monthly_basic': 'Monthly Basic',
                'subscription.pro': 'Pro',
                'subscription.annual': 'Annual',
                'subscription.most_popular': 'Most popular',
                'subscription.save_money': 'Save money',
                'subscription.per_month': '/month',
                'subscription.per_year': '/year',
                'subscription.buy_stripe': 'Buy with Stripe',
                'subscription.upgrade_premium': 'Upgrade to Premium',
                'subscription.referral_discount': 'You have a 20% discount available!',
                'subscription.invite_friends': 'Invite friends and get 20% discount on annual subscription!',
                
                // Features and analysis
                'analysis.title': 'Analysis',
                'analysis.technical': 'Technical analysis',
                'analysis.ai_predictions': 'AI predictions',
                'analysis.buffett': 'Warren Buffett analysis',
                'analysis.graham': 'Benjamin Graham analysis',
                'analysis.short': 'Short analysis',
                'analysis.loading': 'Analyzing...',
                'analysis.no_data': 'No analysis data available',
                'analysis.value_investing': 'Value investing',
                'analysis.risk_assessment': 'Risk assessment',
                'analysis.recommendation': 'Recommendation',
                
                // Portfolio and watchlist
                'portfolio.title': 'Portfolio',
                'portfolio.add_stock': 'Add stock',
                'portfolio.remove_stock': 'Remove stock',
                'portfolio.total_value': 'Total value',
                'portfolio.daily_change': 'Daily change',
                'portfolio.performance': 'Performance',
                'watchlist.title': 'Watchlist',
                'watchlist.add_to_watchlist': 'Add to watchlist',
                'watchlist.remove_from_watchlist': 'Remove from watchlist',
                'watchlist.empty': 'Your watchlist is empty',
                
                // User account
                'user.profile': 'Profile',
                'user.account': 'Account',
                'user.settings': 'Settings',
                'user.notifications': 'Notifications',
                'user.subscription': 'Subscription',
                'user.billing': 'Billing',
                'user.referrals': 'Referrals',
                'user.logout': 'Logout',
                'user.login': 'Login',
                'user.register': 'Sign Up',
                'user.password': 'Password',
                'user.email': 'Email',
                'user.name': 'Name',
                
                // News and market data
                'news.title': 'News',
                'news.market_news': 'Market news',
                'news.latest': 'Latest news',
                'news.source': 'Source',
                'news.read_more': 'Read more',
                'news.published': 'Published',
                'market.today': 'Today',
                'market.gainers': 'Gainers',
                'market.losers': 'Losers',
                'market.most_active': 'Most active',
                'market.indices': 'Indices',
                'market.currencies': 'Currencies',
                'market.commodities': 'Commodities',
                
                // Alerts and notifications
                'alert.success': 'Success!',
                'alert.warning': 'Warning',
                'alert.error': 'Error',
                'alert.info': 'Information',
                'notification.price_alert': 'Price alert',
                'notification.news_alert': 'News alert',
                'notification.portfolio_update': 'Portfolio update',
                
                // Search and filters
                'search.placeholder': 'Search stocks, companies...',
                'search.no_results': 'No results found',
                'search.searching': 'Searching...',
                'filter.all': 'All',
                'filter.favorites': 'Favorites',
                'filter.sector': 'Sector',
                'filter.market_cap': 'Market cap',
                'filter.price_range': 'Price range',
                
                // Languages
                'language.norwegian': 'Norsk',
                'language.english': 'English',
                'language.switch': 'Switch language',
            }
        };
        
        this.initializeTranslations();
    }
    
    getStoredLanguage() {
        return localStorage.getItem('language');
    }
    
    setLanguage(language) {
        this.currentLanguage = language;
        localStorage.setItem('language', language);
        this.updateLanguageDisplay();
        this.translatePage();
    }
    
    t(key, fallback = null) {
        const translation = this.translations[this.currentLanguage]?.[key];
        return translation || fallback || key;
    }
    
    translatePage() {
        // Translate elements with data-i18n attribute
        document.querySelectorAll('[data-i18n]').forEach(element => {
            const key = element.getAttribute('data-i18n');
            const translation = this.t(key);
            
            if (element.tagName === 'INPUT' && (element.type === 'search' || element.type === 'text')) {
                element.placeholder = translation;
            } else {
                element.textContent = translation;
            }
        });
        
        // Translate placeholders with data-i18n-placeholder
        document.querySelectorAll('[data-i18n-placeholder]').forEach(element => {
            const key = element.getAttribute('data-i18n-placeholder');
            element.placeholder = this.t(key);
        });
        
        // Translate titles with data-i18n-title
        document.querySelectorAll('[data-i18n-title]').forEach(element => {
            const key = element.getAttribute('data-i18n-title');
            element.title = this.t(key);
        });
    }
    
    updateLanguageDisplay() {
        const languageDisplay = document.getElementById('current-language');
        if (languageDisplay) {
            languageDisplay.textContent = this.currentLanguage.toUpperCase();
        }
        
        // Also update footer language display
        const footerLanguageDisplay = document.getElementById('footer-current-language');
        if (footerLanguageDisplay) {
            footerLanguageDisplay.textContent = this.currentLanguage.toUpperCase();
        }
    }
    
    /**
     * Update all page elements with new language translations
     */
    updatePageLanguage() {
        const elementsToTranslate = document.querySelectorAll('[data-i18n]');
        
        elementsToTranslate.forEach(element => {
            const key = element.getAttribute('data-i18n');
            const translation = this.getTranslation(key);
            
            if (translation) {
                // Check if element has a specific attribute to translate
                const attr = element.getAttribute('data-i18n-attr');
                if (attr) {
                    element.setAttribute(attr, translation);
                } else {
                    // Default to text content
                    element.textContent = translation;
                }
            }
        });
        
        // Update document language attribute
        document.documentElement.lang = this.currentLanguage;
        
        // Trigger custom event for components that need to react to language changes
        window.dispatchEvent(new CustomEvent('languageChanged', {
            detail: { language: this.currentLanguage }
        }));
    }

    initializeTranslations() {
        // Wait for DOM to be ready
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', () => {
                this.translatePage();
                this.updateLanguageDisplay();
            });
        } else {
            this.translatePage();
            this.updateLanguageDisplay();
        }
    }
}

// Initialize global i18n instance
window.i18n = new SimpleI18n();

// Global function for setting language (used by dropdown)
function setLanguage(lang) {
    window.i18n.setLanguage(lang);
}

// Global function for getting translations (helper for templates)
function t(key, fallback = null) {
    return window.i18n.t(key, fallback);
}
