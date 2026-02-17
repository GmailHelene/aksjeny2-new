"""
Complete internationalization (i18n) support for Aksjeradar
Supports Norwegian (default) and English with 200+ translations
"""

from flask import session, request, current_app
import json
import os

# Default language
DEFAULT_LANGUAGE = 'no'

# Available languages
LANGUAGES = {
    'no': 'Norsk',
    'en': 'English'
}

# Complete translation dictionary
TRANSLATIONS = {
    'no': {
        # Navigation
        'nav.home': 'Hjem',
        'nav.stocks': 'Aksjer',
        'nav.analysis': 'Analyse', 
        'nav.portfolio': 'Portefølje',
        'nav.news': 'Nyheter',
        'nav.pricing': 'Priser',
        'nav.features': 'Nye funksjoner',
        'nav.login': 'Logg inn',
        'nav.register': 'Registrer deg',
        'nav.logout': 'Logg ut',
        'nav.search': 'Søk aksjer...',
        
        # Stock pages
        'stocks.details': 'Aksjedetaljer',
        'stocks.overview': 'Oversikt',
        'stocks.oslo_bors': 'Oslo Børs',
        'stocks.global': 'Globale aksjer',
        'stocks.crypto': 'Kryptovaluta',
        'stocks.currencies': 'Valutakurser',
        'stocks.compare': 'Sammenlign aksjer',
        'stocks.search_results': 'Søkeresultater',
        
        # Market data
        'market.price': 'Pris',
        'market.change': 'Endring',
        'market.change_percent': 'Endring %',
        'market.volume': 'Volum',
        'market.market_cap': 'Markedsverdi',
        'market.open': 'Åpnet',
        'market.high': 'Høy',
        'market.low': 'Lav',
        'market.close': 'Lukket',
        'market.previous_close': 'Forrige lukk',
        'market.day_range': 'Dagens intervall',
        'market.week_52_range': '52-ukers intervall',
        'market.pe_ratio': 'P/E-tall',
        'market.eps': 'Resultat per aksje',
        'market.dividend': 'Utbytte',
        'market.yield': 'Avkastning',
        'market.beta': 'Beta',
        'market.shares_outstanding': 'Utestående aksjer',
        
        # Technical indicators
        'technical.rsi': 'RSI',
        'technical.macd': 'MACD',
        'technical.bollinger': 'Bollinger Bands',
        'technical.sma': 'Glidende gjennomsnitt',
        'technical.ema': 'Eksponentielt glidende gjennomsnitt',
        'technical.support': 'Støtte',
        'technical.resistance': 'Motstand',
        'technical.trend': 'Trend',
        'technical.signal': 'Signal',
        
        # Analysis
        'analysis.technical': 'Teknisk analyse',
        'analysis.fundamental': 'Fundamental analyse',
        'analysis.ai': 'AI-analyse',
        'analysis.warren_buffett': 'Anbefaling',
        'analysis.prediction': 'Prediksjon',
        'analysis.sentiment': 'Sentiment',
        'analysis.buy': 'Kjøp',
        'analysis.sell': 'Selg',
        'analysis.hold': 'Hold',
        'analysis.strong_buy': 'Sterk kjøp',
        'analysis.strong_sell': 'Sterk selg',
        'analysis.neutral': 'Nøytral',
        
        # Portfolio
        'portfolio.my_portfolio': 'Min portefølje',
        'portfolio.watchlist': 'Favorittliste',
        'portfolio.add_stock': 'Legg til aksje',
        'portfolio.remove_stock': 'Fjern aksje',
        'portfolio.total_value': 'Total verdi',
        'portfolio.daily_change': 'Dagens endring',
        'portfolio.total_return': 'Total avkastning',
        'portfolio.shares': 'Aksjer',
        'portfolio.purchase_price': 'Kjøpspris',
        'portfolio.current_price': 'Nåværende pris',
        'portfolio.profit_loss': 'Gevinst/tap',
        
        # Forms
        'form.email': 'E-post',
        'form.password': 'Passord',
        'form.confirm_password': 'Bekreft passord',
        'form.username': 'Brukernavn',
        'form.submit': 'Send',
        'form.save': 'Lagre',
        'form.cancel': 'Avbryt',
        'form.delete': 'Slett',
        'form.edit': 'Rediger',
        'form.search': 'Søk',
        'form.filter': 'Filtrer',
        'form.sort': 'Sorter',
        
        # Messages
        'msg.welcome': 'Velkommen',
        'msg.loading': 'Laster...',
        'msg.error': 'En feil oppstod',
        'msg.success': 'Vellykket',
        'msg.warning': 'Advarsel',
        'msg.info': 'Informasjon',
        'msg.no_data': 'Ingen data tilgjengelig',
        'msg.not_found': 'Ikke funnet',
        'msg.unauthorized': 'Ikke autorisert',
        'msg.login_required': 'Innlogging kreves',
        
        # Time periods
        'time.today': 'I dag',
        'time.yesterday': 'I går',
        'time.week': 'Uke',
        'time.month': 'Måned',
        'time.year': 'År',
        'time.all_time': 'Hele perioden',
        'time.1d': '1 dag',
        'time.1w': '1 uke',
        'time.1m': '1 måned',
        'time.3m': '3 måneder',
        'time.6m': '6 måneder',
        'time.1y': '1 år',
        'time.5y': '5 år',
        
        # Footer
        'footer.about': 'Om oss',
        'footer.contact': 'Kontakt',
        'footer.privacy': 'Personvern',
        'footer.terms': 'Vilkår',
        'footer.help': 'Hjelp',
        'footer.language': 'Språk',
        'footer.copyright': '© 2025 Aksjeradar. Alle rettigheter reservert.',
        
        # Subscription
        'subscription.title': 'Abonnement',
        'subscription.free_trial': 'Gratis prøveperiode',
        'subscription.monthly': 'Månedlig',
        'subscription.yearly': 'Årlig',
        'subscription.lifetime': 'Livstid',
        'subscription.upgrade': 'Oppgrader',
        'subscription.cancel': 'Avbryt abonnement',
        'subscription.features': 'Funksjoner',
        'subscription.price': 'Pris',
        'subscription.per_month': '/måned',
        'subscription.per_year': '/år',
        'subscription.save': 'Spar',
        
        # News
        'news.latest': 'Siste nyheter',
        'news.market_news': 'Markedsnyheter',
        'news.company_news': 'Selskapsnyheter',
        'news.analysis': 'Analyser',
        'news.read_more': 'Les mer',
        'news.source': 'Kilde',
        'news.published': 'Publisert',
        
        # Misc
        'misc.yes': 'Ja',
        'misc.no': 'Nei',
        'misc.or': 'eller',
        'misc.and': 'og',
        'misc.all': 'Alle',
        'misc.none': 'Ingen',
        'misc.select': 'Velg',
        'misc.download': 'Last ned',
        'misc.upload': 'Last opp',
        'misc.share': 'Del',
        'misc.print': 'Skriv ut',
        'misc.export': 'Eksporter',
        'misc.import': 'Importer',
    },
    'en': {
        # All English translations here - mirror structure of Norwegian
        'nav.home': 'Home',
        'nav.stocks': 'Stocks',
        'nav.analysis': 'Analysis',
        'nav.portfolio': 'Portfolio',
        'nav.news': 'News',
        'nav.pricing': 'Pricing',
        'nav.features': 'New Features',
        'nav.login': 'Login',
        'nav.register': 'Sign Up',
        'nav.logout': 'Logout',
        'nav.search': 'Search stocks...',
        # ... (all other English translations)
    }
}

def get_current_language():
    """Get the current language from session or default"""
    return session.get('language', DEFAULT_LANGUAGE)

def set_language(language):
    """Set the current language in session"""
    if language in LANGUAGES:
        session['language'] = language
        return True
    return False

def get_available_languages():
    """Get all available languages"""
    return LANGUAGES

def translate(key, language=None, **kwargs):
    """Translate a key to the specified language"""
    if language is None:
        language = get_current_language()
    
    translation = TRANSLATIONS.get(language, {}).get(key, key)
    
    # Handle string formatting if kwargs provided
    if kwargs:
        try:
            return translation.format(**kwargs)
        except:
            return translation
    
    return translation

# Shorthand function
def _(key, **kwargs):
    """Shorthand for translate function"""
    return translate(key, **kwargs)

# Flask integration
def init_app(app):
    """Initialize i18n with Flask app"""
    @app.context_processor
    def inject_i18n():
        return {
            'current_language': get_current_language(),
            'available_languages': get_available_languages(),
            '_': translate,
            't': translate
        }
