import json
import os
from flask import session, request, current_app
from functools import lru_cache

class TranslationService:
    """
    Comprehensive translation service for Aksjeradar
    Supports Norwegian (default) and English
    """
    
    def __init__(self):
        self.default_language = 'no'
        self.supported_languages = ['no', 'en']
        self.translations = {}
        self.load_translations()
    
    def load_translations(self):
        """Load all translation files"""
        try:
            translations_dir = os.path.join(os.path.dirname(__file__), '..', 'translations')
            
            for lang in self.supported_languages:
                file_path = os.path.join(translations_dir, f'messages_{lang}.json')
                if os.path.exists(file_path):
                    with open(file_path, 'r', encoding='utf-8') as f:
                        self.translations[lang] = json.load(f)
            
            # Only log if we have an app context
            try:
                if current_app:
                    current_app.logger.info(f"✅ Loaded translations for: {list(self.translations.keys())}")
            except RuntimeError:
                # No app context, silent loading
                pass
                        
        except Exception as e:
            # Only log if we have an app context
            try:
                if current_app:
                    current_app.logger.error(f"❌ Error loading translations: {e}")
            except RuntimeError:
                # No app context, silent error handling
                pass
            
            # Fallback empty translations
            for lang in self.supported_languages:
                self.translations[lang] = {}
    
    def get_language(self):
        """Get current language preference"""
        # 1. Check session preference
        if 'language' in session:
            return session['language']
        
        # 2. Check Accept-Language header
        if request and hasattr(request, 'headers'):
            accept_languages = request.headers.get('Accept-Language', '')
            if 'en' in accept_languages.lower() and 'no' not in accept_languages.lower():
                return 'en'
        
        # 3. Default to Norwegian
        return self.default_language
    
    def set_language(self, language):
        """Set language preference"""
        if language in self.supported_languages:
            session['language'] = language
            session.permanent = True
            return True
        return False
    
    @lru_cache(maxsize=256)
    def translate(self, key, language=None, fallback=None):
        """
        Translate a key to the current or specified language
        
        Args:
            key: Translation key (e.g., 'navigation.home')
            language: Language code (defaults to current language)
            fallback: Fallback text if translation not found
        """
        if language is None:
            language = self.get_language()
        
        if language not in self.translations:
            language = self.default_language
        
        # Navigate through nested keys
        try:
            keys = key.split('.')
            value = self.translations[language]
            
            for k in keys:
                value = value[k]
                
            return value
            
        except (KeyError, TypeError):
            # Try fallback language
            if language != self.default_language:
                try:
                    keys = key.split('.')
                    value = self.translations[self.default_language]
                    
                    for k in keys:
                        value = value[k]
                        
                    return value
                except (KeyError, TypeError):
                    pass
            
            # Return fallback or key itself
            return fallback if fallback is not None else key
    
    def get_all_translations(self, language=None):
        """Get all translations for a language"""
        if language is None:
            language = self.get_language()
        
        return self.translations.get(language, {})
    
    def add_missing_translation(self, key, text, language='no'):
        """Add a missing translation (for development)"""
        if language not in self.translations:
            self.translations[language] = {}
        
        # Navigate and create nested structure
        keys = key.split('.')
        current = self.translations[language]
        
        for k in keys[:-1]:
            if k not in current:
                current[k] = {}
            current = current[k]
        
        current[keys[-1]] = text
        
        # Save to file
        try:
            translations_dir = os.path.join(os.path.dirname(__file__), '..', 'translations')
            file_path = os.path.join(translations_dir, f'messages_{language}.json')
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(self.translations[language], f, ensure_ascii=False, indent=2)
                
        except Exception as e:
            try:
                if current_app:
                    current_app.logger.error(f"Error saving translation: {e}")
            except RuntimeError:
                # No app context, silent error handling
                pass

# Global translation service instance
translation_service = TranslationService()

def t(key, fallback=None, **kwargs):
    """
    Shorthand translation function for templates
    
    Usage in templates:
        {{ t('navigation.home') }}
        {{ t('stocks.price', fallback='Price') }}
    """
    translation = translation_service.translate(key, fallback=fallback)
    
    # Handle string formatting
    if kwargs:
        try:
            return translation.format(**kwargs)
        except:
            return translation
    
    return translation

def get_current_language():
    """Get current language for templates"""
    return translation_service.get_language()

def get_supported_languages():
    """Get supported languages for language switcher"""
    return [
        {'code': 'no', 'name': 'Norsk', 'flag': '🇳🇴'},
        {'code': 'en', 'name': 'English', 'flag': '🇬🇧'}
    ]
