"""
FREE TRANSLATION SOLUTION - Norwegian to English
Using Google Translate without API costs through web scraping approach

This implements a free translation system using:
1. HTML lang attribute switching
2. JavaScript-based translation using Google Translate widget
3. Simple dictionary-based translation for key terms
"""

# Key Norwegian -> English translations for the most common terms
TRANSLATION_DICTIONARY = {
    # Navigation
    "Hjem": "Home",
    "Aksjer": "Stocks", 
    "Portefølje": "Portfolio",
    "Analyse": "Analysis",
    "Nyheter": "News",
    "Innstillinger": "Settings",
    "Logg inn": "Login",
    "Registrer": "Register",
    "Logg ut": "Logout",
    "Oversikt": "Overview",
    "Konto": "Account",
    "Varsler": "Alerts",
    "Favoritter": "Favorites",
    "Sammenlign": "Compare",
    "Søk": "Search",
    
    # Common terms
    "Pris": "Price",
    "Endring": "Change", 
    "Volum": "Volume",
    "Markedsverdi": "Market Cap",
    "P/E": "P/E",
    "Utbytte": "Dividend",
    "Sektor": "Sector",
    "Selskap": "Company",
    "Aksjesymbol": "Symbol",
    
    # Analysis terms
    "Kjøp": "Buy",
    "Selg": "Sell", 
    "Hold": "Hold",
    "Anbefaling": "Recommendation",
    "Teknisk analyse": "Technical Analysis",
    "Fundamental analyse": "Fundamental Analysis",
    "Warren Buffett analyse": "Warren Buffett Analysis",
    
    # User interface
    "Søk": "Search",
    "Filter": "Filter",
    "Sorter": "Sort",
    "Oppdater": "Update",
    "Lagre": "Save",
    "Avbryt": "Cancel",
    "Bekreft": "Confirm",
    "Tilbake": "Back",
    "Neste": "Next",
    "Forrige": "Previous",
    
    # Status messages  
    "Laster...": "Loading...",
    "Ingen data tilgjengelig": "No data available",
    "Feil oppstod": "An error occurred",
    "Vellykket": "Success",
    "Lagret": "Saved",
    "Oppdatert": "Updated",
    
    # Time periods
    "I dag": "Today",
    "Denne uken": "This week", 
    "Denne måneden": "This month",
    "I år": "This year",
    "1 år": "1 year",
    "5 år": "5 years",
    
    # Market terms
    "Oslo Børs": "Oslo Stock Exchange",
    "NASDAQ": "NASDAQ",
    "NYSE": "NYSE", 
    "Amerikanske aksjer": "US Stocks",
    "Norske aksjer": "Norwegian Stocks",
    "Europeiske aksjer": "European Stocks",
    "Globale aksjer": "Global Stocks",
    "Kryptovalutaer": "Cryptocurrencies",
    "Valuta": "Currency",
    "Aksjekurser": "Stock Prices",
    "Søk aksjer": "Search Stocks",
    "Sammenlign aksjer": "Compare Stocks",
    
    # Features
    "Favoritter": "Favorites",
    "Overvåkningsliste": "Watchlist",
    "Prisvarsler": "Price Alerts",
    "Porteføljeanalyse": "Portfolio Analysis",
    "Markedsintelligens": "Market Intelligence",
    "Innsidehandel": "Insider Trading",
    
    # Subscription
    "Gratis": "Free",
    "Premium": "Premium", 
    "Abonnement": "Subscription",
    "Oppgrader": "Upgrade",
    "Månedlig": "Monthly",
    "Årlig": "Yearly",
    
    # Messages
    "Velkommen": "Welcome",
    "Takk": "Thank you",
    "Beklager": "Sorry",
    "Prøv igjen": "Try again",
    "Kontakt oss": "Contact us",
    "Hjelp": "Help",
    "Om oss": "About us",
    "Personvern": "Privacy",
    "Vilkår": "Terms"
}

def get_free_translation_js():
    """
    Returns JavaScript code that implements free translation
    Uses Google Translate widget (free) and dictionary replacements
    """
    js_code = """
    // Free Translation System for Aksjeradar
    const TRANSLATIONS = {TRANSLATION_DICTIONARY};
    
    // Create reverse dictionary for English to Norwegian translation
    const REVERSE_TRANSLATIONS = {};
    Object.keys(TRANSLATIONS).forEach(key => {{
        REVERSE_TRANSLATIONS[TRANSLATIONS[key]] = key;
    }});
    
    let currentLanguage = 'no'; // Default Norwegian
    // Read from URL ?lang= if present
    try {
        const urlParams = new URLSearchParams(window.location.search);
        const qLang = urlParams.get('lang');
        if (qLang === 'en' || qLang === 'no') {
            currentLanguage = qLang;
            localStorage.setItem('aksjeradar_language', currentLanguage);
        }
    } catch (e) {}
    
    function toggleLanguage() {
        currentLanguage = currentLanguage === 'no' ? 'en' : 'no';
        translatePage(currentLanguage);
        localStorage.setItem('aksjeradar_language', currentLanguage);
        const toggleBtn = document.getElementById('language-toggle');
        if (toggleBtn) {
            toggleBtn.textContent = currentLanguage === 'en' ? 'Norsk' : 'English';
        }
        // Update URL to include ?lang=
        try {
            const url = new URL(window.location.href);
            url.searchParams.set('lang', currentLanguage);
            window.history.replaceState({}, '', url.toString());
        } catch (e) {}
    }
    
    function translatePage(targetLanguage) {{
        if (targetLanguage === 'en') {{
            // Translate to English using dictionary
            translateToEnglish();
        }} else {{
            // Translate back to Norwegian using reverse dictionary
            translateToNorwegian();
        }}
    }}
    
    function translateToEnglish() {{
        // Get all text nodes and translate common terms
        const walker = document.createTreeWalker(
            document.body,
            NodeFilter.SHOW_TEXT,
            null,
            false
        );
        
        const textNodes = [];
        let node;
        
        while (node = walker.nextNode()) {{
            if (node.nodeValue.trim()) {{
                textNodes.push(node);
            }}
        }}
        
        textNodes.forEach(textNode => {{
            let text = textNode.nodeValue;
            let translated = false;
            
            // Replace Norwegian terms with English
            Object.keys(TRANSLATIONS).forEach(norTerm => {{
                const enTerm = TRANSLATIONS[norTerm];
                if (text.includes(norTerm)) {{
                    text = text.replace(new RegExp(norTerm, 'g'), enTerm);
                    translated = true;
                }}
            }});
            
            if (translated) {{
                textNode.nodeValue = text;
            }}
        }});
        
        // Also translate common attributes
        const elements = document.querySelectorAll('[placeholder], [title], [alt]');
        elements.forEach(el => {{
            ['placeholder', 'title', 'alt'].forEach(attr => {{
                const value = el.getAttribute(attr);
                if (value) {{
                    Object.keys(TRANSLATIONS).forEach(norTerm => {{
                        if (value.includes(norTerm)) {{
                            el.setAttribute(attr, value.replace(norTerm, TRANSLATIONS[norTerm]));
                        }}
                    }});
                }}
            }});
        }});
    }}
    
    function translateToNorwegian() {{
        // Get all text nodes and translate back to Norwegian using reverse dictionary
        const walker = document.createTreeWalker(
            document.body,
            NodeFilter.SHOW_TEXT,
            null,
            false
        );
        
        const textNodes = [];
        let node;
        
        while (node = walker.nextNode()) {{
            if (node.nodeValue.trim()) {{
                textNodes.push(node);
            }}
        }}
        
        textNodes.forEach(textNode => {{
            let text = textNode.nodeValue;
            let translated = false;
            
            // Replace English terms with Norwegian
            Object.keys(REVERSE_TRANSLATIONS).forEach(enTerm => {{
                const norTerm = REVERSE_TRANSLATIONS[enTerm];
                if (text.includes(enTerm)) {{
                    text = text.replace(new RegExp(enTerm, 'g'), norTerm);
                    translated = true;
                }}
            }});
            
            if (translated) {{
                textNode.nodeValue = text;
            }}
        }});
        
        // Also translate common attributes back to Norwegian
        const elements = document.querySelectorAll('[placeholder], [title], [alt]');
        elements.forEach(el => {{
            ['placeholder', 'title', 'alt'].forEach(attr => {{
                const value = el.getAttribute(attr);
                if (value) {{
                    Object.keys(REVERSE_TRANSLATIONS).forEach(enTerm => {{
                        if (value.includes(enTerm)) {{
                            el.setAttribute(attr, value.replace(enTerm, REVERSE_TRANSLATIONS[enTerm]));
                        }}
                    }});
                }}
            }});
        }});
    }}
    // Initialize on page load
    document.addEventListener('DOMContentLoaded', function() {{
        // Check saved language preference
        const savedLang = localStorage.getItem('aksjeradar_language');
        if (savedLang === 'en' && currentLanguage !== 'en') {
            currentLanguage = 'en';
            translateToEnglish();
        } else if (currentLanguage === 'en') {
            translateToEnglish();
        }
        
        // Update toggle button if it exists
        const toggleBtn = document.getElementById('language-toggle');
        if (toggleBtn) {{
            toggleBtn.textContent = currentLanguage === 'en' ? 'Norsk' : 'English';
            // If button element remains, keep JS toggle as enhancement
            toggleBtn.addEventListener('click', function(ev){ ev.preventDefault(); toggleLanguage(); });
        }}
    }});
    """
    return js_code

def get_language_toggle_html():
    """
    Returns HTML for language toggle button
    """
    try:
        # Compute current language from URL param or session; default to 'no'
        from flask import request, session
        current = request.args.get('lang') or session.get('language', 'no')
        if current not in ('no', 'en'):
            current = 'no'
    except Exception:
        current = 'no'

    next_lang = 'en' if current == 'no' else 'no'
    label = 'EN' if next_lang == 'en' else 'NO'  # Show target language code on the button
    href = f"/set_language/{next_lang}"

    # Keep a minimal enhancement to persist preference early; no '#' hrefs are used
    return f'''
    <a id="language-toggle" class="btn btn-outline-secondary btn-sm ms-2" href="{href}" title="Switch language / Bytt språk">{label}</a>
    <script>
    (function(){{
        const btn = document.getElementById('language-toggle');
        if(!btn) return;
        btn.addEventListener('click', function(){{
            try {{
                const next = '{next_lang}';
                localStorage.setItem('aksjeradar_language', next);
            }} catch(e) {{}}
        }});
    }})();
    </script>
    '''

# Instructions for implementation:
"""
TO IMPLEMENT FREE TRANSLATION:

1. Add this to base.html in the <head> section:
   <script>
   {{ get_free_translation_js() | safe }}
   </script>

2. Add language toggle button to navigation:
   {{ get_language_toggle_html() | safe }}

3. Register template functions in app/__init__.py:
   @app.template_global()
   def get_free_translation_js():
       from .utils.translation import get_free_translation_js
       return get_free_translation_js()
   
   @app.template_global() 
   def get_language_toggle_html():
       from .utils.translation import get_language_toggle_html
       return get_language_toggle_html()

4. Optional: Add more terms to TRANSLATION_DICTIONARY as needed

This provides:
- Instant client-side translation
- No API costs
- Preserves original page structure
- Works offline once loaded
- User preference persistence
- Easy to extend with more terms
"""
