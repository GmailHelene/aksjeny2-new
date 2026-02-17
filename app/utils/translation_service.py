"""
Simple translation utilities for the Flask application.
Provides multiple translation methods: browser-based, ConveyThis, and Google Translate API.
"""

import os
import requests
from flask import current_app, session
from typing import Optional, Dict, List


class TranslationService:
    """Handles various translation methods for the application."""
    
    def __init__(self):
        self.google_api_key = current_app.config.get('GOOGLE_TRANSLATE_API_KEY')
        self.conveythis_api_key = current_app.config.get('CONVEYTHIS_API_KEY')
        self.default_language = current_app.config.get('DEFAULT_LANGUAGE', 'no')
        self.supported_languages = current_app.config.get('SUPPORTED_LANGUAGES', ['no', 'en'])
        
    def get_user_language(self) -> str:
        """Get the user's preferred language from session or default."""
        return session.get('language', self.default_language)
        
    def set_user_language(self, language: str) -> bool:
        """Set the user's preferred language in session."""
        if language in self.supported_languages:
            session['language'] = language
            return True
        return False
        
    def translate_text_google(self, text: str, target_language: str = 'en', source_language: str = 'no') -> Optional[str]:
        """
        Translate text using Google Translate API.
        
        Args:
            text: Text to translate
            target_language: Target language code (default: 'en')
            source_language: Source language code (default: 'no')
            
        Returns:
            Translated text or None if translation failed
        """
        if not self.google_api_key:
            current_app.logger.warning("Google Translate API key not configured")
            return None
            
        try:
            url = "https://translation.googleapis.com/language/translate/v2"
            params = {
                'key': self.google_api_key,
                'q': text,
                'source': source_language,
                'target': target_language
            }
            
            response = requests.post(url, data=params, timeout=10)
            response.raise_for_status()
            
            result = response.json()
            if 'data' in result and 'translations' in result['data']:
                return result['data']['translations'][0]['translatedText']
                
        except Exception as e:
            current_app.logger.error(f"Google Translate API error: {e}")
            
        return None
        
    def get_translation_javascript(self) -> str:
        """
        Generate JavaScript code for browser-based translation.
        
        Returns:
            JavaScript code for browser translation functionality
        """
        return '''
        // Browser-based translation helpers
        function initBrowserTranslation() {
            // Add meta tags for better language detection
            if (!document.querySelector('meta[name="google"]')) {
                const meta = document.createElement('meta');
                meta.name = 'google';
                meta.content = 'translate';
                document.head.appendChild(meta);
            }
            
            // Set page language
            document.documentElement.lang = 'no';
            
            // Chrome translation trigger
            if (navigator.userAgent.includes('Chrome')) {
                window.gtranslateSettings = {
                    default_language: 'no',
                    languages: ['no', 'en'],
                    wrapper_selector: '.gtranslate_wrapper',
                    flag_style: 'text'
                };
            }
        }
        
        function requestTranslation() {
            // Try to trigger browser's built-in translation
            if (typeof google !== 'undefined' && google.translate) {
                google.translate.TranslateElement({
                    pageLanguage: 'no',
                    includedLanguages: 'en',
                    layout: google.translate.TranslateElement.InlineLayout.SIMPLE
                }, 'google_translate_element');
            } else {
                // Fallback: show instructions
                showTranslationInstructions();
            }
        }
        
        function showTranslationInstructions() {
            const instructions = [
                "Chrome/Edge: Right-click → 'Translate to English'",
                "Firefox: Install Google Translator extension",
                "Safari: Right-click → 'Translate to English'",
                "Mobile: Use browser's built-in translation"
            ];
            
            alert("Oversett siden:\\n\\n" + instructions.join("\\n"));
        }
        
        // Initialize on page load
        document.addEventListener('DOMContentLoaded', initBrowserTranslation);
        '''
        
    def get_conveythis_config(self) -> Dict:
        """
        Get ConveyThis configuration for JavaScript initialization.
        
        Returns:
            Dictionary with ConveyThis configuration
        """
        if not self.conveythis_api_key:
            return {}
            
        return {
            'api_key': self.conveythis_api_key,
            'source_language': 'no',
            'target_languages': ['en'],
            'display_mode': 'widget',
            'custom_widget': {
                'style': {
                    'button_background_color': '#007bff',
                    'button_text_color': '#ffffff',
                    'button_border_color': '#007bff'
                }
            }
        }
        
    def get_language_options(self) -> List[Dict]:
        """
        Get available language options for the UI.
        
        Returns:
            List of language options with codes and names
        """
        languages = [
            {'code': 'no', 'name': 'Norsk', 'flag': '🇳🇴'},
            {'code': 'en', 'name': 'English', 'flag': '🇺🇸'}
        ]
        return languages
        
    def detect_browser_language(self, accept_language_header: str) -> str:
        """
        Detect user's preferred language from browser Accept-Language header.
        
        Args:
            accept_language_header: The Accept-Language header from request
            
        Returns:
            Detected language code or default language
        """
        if not accept_language_header:
            return self.default_language
            
        # Parse Accept-Language header
        languages = []
        for lang in accept_language_header.split(','):
            if ';q=' in lang:
                lang_code, quality = lang.split(';q=')
                quality = float(quality)
            else:
                lang_code = lang
                quality = 1.0
                
            lang_code = lang_code.strip().lower()[:2]  # Get first 2 characters
            languages.append((lang_code, quality))
            
        # Sort by quality
        languages.sort(key=lambda x: x[1], reverse=True)
        
        # Find first supported language
        for lang_code, _ in languages:
            if lang_code in self.supported_languages:
                return lang_code
                
        return self.default_language


# Helper functions for templates
def get_translation_service():
    """Get translation service instance."""
    return TranslationService()


def translate_text(text: str, target_lang: str = 'en') -> str:
    """
    Template helper function for translating text.
    
    Args:
        text: Text to translate
        target_lang: Target language
        
    Returns:
        Translated text or original text if translation fails
    """
    try:
        service = TranslationService()
        translated = service.translate_text_google(text, target_lang)
        return translated or text
    except Exception:
        return text


# Translation mapping for common UI elements
UI_TRANSLATIONS = {
    'no': {
        'home': 'Hjem',
        'analysis': 'Analyse',
        'stocks': 'Aksjer',
        'portfolio': 'Portefølje',
        'news': 'Nyheter',
        'account': 'Konto',
        'login': 'Logg inn',
        'logout': 'Logg ut',
        'register': 'Registrer',
        'profile': 'Profil',
        'settings': 'Innstillinger',
        'help': 'Hjelp',
        'search': 'Søk',
        'loading': 'Laster...',
        'error': 'Feil',
        'success': 'Suksess',
        'welcome': 'Velkommen',
        'dashboard': 'Dashboard',
        'market': 'Marked',
        'price': 'Pris',
        'change': 'Endring',
        'volume': 'Volum',
        'buy': 'Kjøp',
        'sell': 'Selg',
        'hold': 'Hold'
    },
    'en': {
        'home': 'Home',
        'analysis': 'Analysis',
        'stocks': 'Stocks',
        'portfolio': 'Portfolio',
        'news': 'News',
        'account': 'Account',
        'login': 'Login',
        'logout': 'Logout',
        'register': 'Register',
        'profile': 'Profile',
        'settings': 'Settings',
        'help': 'Help',
        'search': 'Search',
        'loading': 'Loading...',
        'error': 'Error',
        'success': 'Success',
        'welcome': 'Welcome',
        'dashboard': 'Dashboard',
        'market': 'Market',
        'price': 'Price',
        'change': 'Change',
        'volume': 'Volume',
        'buy': 'Buy',
        'sell': 'Sell',
        'hold': 'Hold'
    }
}


def get_ui_text(key: str, language: str = None) -> str:
    """
    Get translated UI text for a given key.
    
    Args:
        key: Translation key
        language: Language code (if None, uses current session language)
        
    Returns:
        Translated text or key if not found
    """
    if language is None:
        language = session.get('language', 'no')
        
    return UI_TRANSLATIONS.get(language, {}).get(key, key)
