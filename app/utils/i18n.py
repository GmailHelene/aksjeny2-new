"""
Simple internationalization (i18n) support for Aksjeradar
Supports Norwegian (default) and English
"""

from flask import session, request
import json
import os

# Default language
DEFAULT_LANGUAGE = 'no'

# Available languages
LANGUAGES = {
    'no': 'Norsk',
    'en': 'English'
}

# Translation dictionary
TRANSLATIONS = {
    'no': {
        # Navigation
        'home': 'Hjem',
        'analysis': 'Analyse',
        'stocks': 'Aksjer', 
        'portfolio': 'Portefølje',
        'news': 'Nyheter',
        'pricing': 'Priser',
        'login': 'Logg inn',
        'register': 'Registrer',
        'logout': 'Logg ut',
        'search': 'Søk',
        
        # Common terms
        'loading': 'Laster...',
        'error': 'Feil',
        'success': 'Suksess',
        'save': 'Lagre',
        'cancel': 'Avbryt',
        'submit': 'Send',
        'email': 'E-post',
        'password': 'Passord',
        'username': 'Brukernavn',
        'phone': 'Telefon',
        'address': 'Adresse',
        'name': 'Navn',
        'description': 'Beskrivelse',
        'price': 'Pris',
        'change': 'Endring',
        'volume': 'Volum',
        'market_cap': 'Markedsverdi',
        
        # Analysis terms
        'buy': 'Kjøp',
        'sell': 'Selg',
        'hold': 'Hold',
        'technical_analysis': 'Teknisk analyse',
        'ai_analysis': 'AI-analyse',
        'recommendation': 'Anbefaling',
        'prediction': 'Prediksjon',
        
        # Trial and access
        'trial_expired': 'Prøveperioden er utløpt',
        'trial_time_remaining': 'Gjenstående prøvetid',
        'upgrade_now': 'Oppgrader nå',
        'free_trial': 'Gratis prøveperiode',
        'demo_access': 'Demo-tilgang',
        'full_access': 'Full tilgang',
        
        # Forms
        'confirm_password': 'Bekreft passord',
        'forgot_password': 'Glemt passord?',
        'reset_password': 'Tilbakestill passord',
        'create_account': 'Opprett konto',
        'sign_in': 'Logg inn',
        'sign_out': 'Logg ut',
        
        # Notifications
        'notifications': 'Varsler',
        'settings': 'Innstillinger',
        'profile': 'Profil',
        'account': 'Konto',
        'subscription': 'Abonnement',
        
        # Messages
        'welcome': 'Velkommen',
        'goodbye': 'Ha det bra',
        'thank_you': 'Tusen takk',
        'please_wait': 'Vennligst vent',
        'coming_soon': 'Kommer snart',
        'under_construction': 'Under konstruksjon',
    },
    'en': {
        # Navigation
        'home': 'Home',
        'analysis': 'Analysis',
        'stocks': 'Stocks',
        'portfolio': 'Portfolio', 
        'news': 'News',
        'pricing': 'Pricing',
        'login': 'Login',
        'register': 'Register',
        'logout': 'Logout',
        'search': 'Search',
        
        # Common terms
        'loading': 'Loading...',
        'error': 'Error',
        'success': 'Success',
        'save': 'Save',
        'cancel': 'Cancel',
        'submit': 'Submit',
        'email': 'Email',
        'password': 'Password',
        'username': 'Username',
        'phone': 'Phone',
        'address': 'Address',
        'name': 'Name',
        'description': 'Description',
        'price': 'Price',
        'change': 'Change',
        'volume': 'Volume',
        'market_cap': 'Market Cap',
        
        # Analysis terms
        'buy': 'Buy',
        'sell': 'Sell',
        'hold': 'Hold',
        'technical_analysis': 'Technical Analysis',
        'ai_analysis': 'AI Analysis',
        'recommendation': 'Recommendation',
        'prediction': 'Prediction',
        
        # Trial and access
        'trial_expired': 'Trial Expired',
        'trial_time_remaining': 'Trial Time Remaining',
        'upgrade_now': 'Upgrade Now',
        'free_trial': 'Free Trial',
        'demo_access': 'Demo Access',
        'full_access': 'Full Access',
        
        # Forms
        'confirm_password': 'Confirm Password',
        'forgot_password': 'Forgot Password?',
        'reset_password': 'Reset Password',
        'create_account': 'Create Account',
        'sign_in': 'Sign In',
        'sign_out': 'Sign Out',
        
        # Notifications
        'notifications': 'Notifications',
        'settings': 'Settings',
        'profile': 'Profile',
        'account': 'Account',
        'subscription': 'Subscription',
        
        # Messages
        'welcome': 'Welcome',
        'goodbye': 'Goodbye',
        'thank_you': 'Thank you',
        'please_wait': 'Please wait',
        'coming_soon': 'Coming soon',
        'under_construction': 'Under construction',
    }
}


def get_current_language():
    """Get the current language from session or default"""
    return session.get('language', DEFAULT_LANGUAGE)


def set_language(language_code):
    """Set the current language in session"""
    if language_code in LANGUAGES:
        session['language'] = language_code
        return True
    return False


def get_available_languages():
    """Get available languages"""
    return LANGUAGES


def translate(key, language=None):
    """
    Translate a key to the current or specified language
    
    Args:
        key (str): Translation key
        language (str, optional): Language code. If None, uses current language
        
    Returns:
        str: Translated text or the key if translation not found
    """
    if language is None:
        language = get_current_language()
    
    if language in TRANSLATIONS and key in TRANSLATIONS[language]:
        return TRANSLATIONS[language][key]
    
    # Fallback to Norwegian if translation not found
    if language != DEFAULT_LANGUAGE and key in TRANSLATIONS[DEFAULT_LANGUAGE]:
        return TRANSLATIONS[DEFAULT_LANGUAGE][key]
    
    # Return the key itself if no translation found
    return key


def _(key):
    """Shorthand function for translate"""
    return translate(key)


def get_browser_language():
    """Get preferred language from browser Accept-Language header"""
    if request and request.headers.get('Accept-Language'):
        # Simple parsing - just get the first language
        accept_lang = request.headers.get('Accept-Language', '')
        if 'en' in accept_lang.lower():
            return 'en'
    return DEFAULT_LANGUAGE
