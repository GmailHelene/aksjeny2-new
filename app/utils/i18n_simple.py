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
        
        # Analysis terms
        'buy': 'Kjøp',
        'sell': 'Selg',
        'hold': 'Hold',
        'technical_analysis': 'Teknisk analyse',
        'ai_analysis': 'AI-analyse',
        'recommendation': 'Anbefaling',
        
        # Trial and access
        'trial_expired': 'Prøveperioden er utløpt',
        'upgrade_now': 'Oppgrader nå',
        'free_trial': 'Gratis prøveperiode',
        'demo_access': 'Demo-tilgang',
        'full_access': 'Full tilgang',
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
        
        # Analysis terms
        'buy': 'Buy',
        'sell': 'Sell',
        'hold': 'Hold',
        'technical_analysis': 'Technical Analysis',
        'ai_analysis': 'AI Analysis',
        'recommendation': 'Recommendation',
        
        # Trial and access
        'trial_expired': 'Trial Expired',
        'upgrade_now': 'Upgrade Now',
        'free_trial': 'Free Trial',
        'demo_access': 'Demo Access',
        'full_access': 'Full Access',
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
