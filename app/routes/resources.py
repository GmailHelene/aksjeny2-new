from flask import Blueprint, render_template
from flask_login import current_user
from ..utils.access_control import access_required

resources_bp = Blueprint('resources', __name__, url_prefix='/resources')

@resources_bp.route('/')
@resources_bp.route('')
def index():
    """Main resources page with overview of all available resources"""
    
    # Overview data for resources landing page
    resource_categories = [
        {
            'title': 'Analyseverktøy',
            'description': 'Omfattende verktøy for teknisk og fundamental analyse',
            'icon': 'bi-graph-up',
            'link': '/resources/analysis-tools',
            'count': '15+ verktøy'
        },
        {
            'title': 'Investeringsguider',
            'description': 'Detaljerte guider for å lære investering fra bunnen av',
            'icon': 'bi-book',
            'link': '/investment-guides',
            'count': '25+ guider'
        },
        {
            'title': 'Sammenligning av verktøy',
            'description': 'Sammenlign forskjellige analyse- og handelsplattformer',
            'icon': 'bi-bar-chart',
            'link': '/resources/comparison',
            'count': '10+ plattformer'
        },
        {
            'title': 'Markedsdata',
            'description': 'Tilgang til sanntidsdata og historiske markedsdata',
            'icon': 'bi-database',
            'link': '/financial-dashboard',
            'count': 'Live data'
        },
        {
            'title': 'Utdanning',
            'description': 'Kurs og workshops for å forbedre dine investeringsferdigheter',
            'icon': 'bi-mortarboard',
            'link': '/resources/guides',
            'count': '20+ kurs'
        },
        {
            'title': 'API og Utviklere',
            'description': 'API-tilgang for utviklere og avanserte brukere',
            'icon': 'bi-code-slash',
            'link': '/api/docs',
            'count': 'RESTful API'
        }
    ]
    
    return render_template('resources/index.html',
                         categories=resource_categories,
                         title='Ressurser - Aksjeradar')

@resources_bp.route('/analysis-tools')
@access_required
def analysis_tools():
    """Show comprehensive analysis tools and resources"""
    
    # Global analysis tools
    global_tools = [
        {
            'name': 'TradingView',
            'url': 'https://tradingview.com',
            'description': 'Avanserte tekniske analyser, live charts og sosial trading-plattform',
            'features': ['Sanntids-charts', 'Tekniske indikatorer', 'Paper trading', 'Screener'],
            'pricing': 'Gratis basis, Premium fra $14.95/mnd',
            'category': 'technical',
            'rating': 4.8,
            'logo': '/static/images/tradingview-logo.png'
        },
        {
            'name': 'MarketBeat',
            'url': 'https://marketbeat.com',
            'description': 'Analyserating, nyheter og markedsinnsikt fra profesjonelle analytikere',
            'features': ['Analyserating', 'Earnings calendar', 'Insider trading', 'News alerts'],
            'pricing': 'Gratis basis, Premium fra $25/mnd',
            'category': 'fundamental',
            'rating': 4.5,
            'logo': '/static/images/marketbeat-logo.png'
        },
        {
            'name': 'TipRanks',
            'url': 'https://tipranks.com',
            'description': 'AI-drevet analyseaggregering og analytiker-tracking',
            'features': ['Analytiker-konsensus', 'Smart Score', 'Insider sentiment', 'Hedge fund trends'],
            'pricing': 'Gratis basis, Premium fra $29.95/mnd',
            'category': 'ai',
            'rating': 4.6,
            'logo': '/static/images/tipranks-logo.png'
        },
        {
            'name': 'Yahoo Finance',
            'url': 'https://finance.yahoo.com',
            'description': 'Omfattende finansiell data, nyheter og porteføljeanalyse',
            'features': ['Free real-time data', 'Portfolio tracking', 'Screener', 'Financial statements'],
            'pricing': 'Helt gratis',
            'category': 'data',
            'rating': 4.3,
            'logo': '/static/images/yahoo-finance-logo.png'
        },
        {
            'name': 'Seeking Alpha',
            'url': 'https://seekingalpha.com',
            'description': 'Crowdsourced aksjeanalyse og investeringsresearch',
            'features': ['Independent research', 'Earnings transcripts', 'Dividend analysis', 'Quant ratings'],
            'pricing': 'Gratis basis, Premium fra $19.99/mnd',
            'category': 'research',
            'rating': 4.4,
            'logo': '/static/images/seeking-alpha-logo.png'
        }
    ]
    
    # Insider trading tools
    insider_tools = [
        {
            'name': 'InsiderInsights',
            'url': 'https://insiderinsights.com',
            'description': 'Spesialisert på innsidehandel-analyse og -signaler',
            'features': ['Insider transaction alerts', 'Cluster analysis', 'Historical tracking', 'Screening tools'],
            'pricing': 'Fra $49/mnd',
            'category': 'insider',
            'rating': 4.2,
            'logo': '/static/images/insider-insights-logo.png'
        },
        {
            'name': 'InsiderScreener',
            'url': 'https://insiderscreener.com',
            'description': 'Avansert screening av innsidehandel og corporate actions',
            'features': ['Real-time insider filings', 'Bulk transaction alerts', 'Executive tracking', 'Custom filters'],
            'pricing': 'Fra $39/mnd',
            'category': 'insider',
            'rating': 4.1,
            'logo': '/static/images/insider-screener-logo.png'
        },
        {
            'name': 'InsiderViz',
            'url': 'https://insiderviz.com',
            'description': 'Visualisering og analyse av innsidehandel-data',
            'features': ['Interactive charts', 'Trend analysis', 'Company insider profiles', 'Data export'],
            'pricing': 'Fra $29/mnd',
            'category': 'insider',
            'rating': 4.0,
            'logo': '/static/images/insider-viz-logo.png'
        },
        {
            'name': 'SmartInsiderTrades',
            'url': 'https://smartinsidertrades.com',
            'description': 'AI-basert analyse av innsidehandel-mønstre',
            'features': ['Pattern recognition', 'Sentiment analysis', 'Predictive modeling', 'Risk assessment'],
            'pricing': 'Fra $79/mnd',
            'category': 'ai-insider',
            'rating': 4.3,
            'logo': '/static/images/smart-insider-logo.png'
        }
    ]
    
    # Norwegian specific tools  
    norwegian_tools = [
        {
            'name': 'Aksje.io',
            'url': 'https://aksje.io',
            'description': 'Norsk aksjeanalyse med fokus på Oslo Børs og teknisk analyse',
            'features': ['Oslo Børs focus', 'Norwegian market data', 'Technical indicators', 'Sector analysis'],
            'pricing': 'Gratis basis, Premium fra 249 NOK/mnd',
            'category': 'norwegian',
            'rating': 4.2,
            'logo': '/static/images/aksje-io-logo.png'
        },
        {
            'name': 'Innsideanalyse.no',
            'url': 'https://innsideanalyse.no',
            'description': 'Spesialisert på innsidehandel i norske selskaper',
            'features': ['Oslo Børs insider data', 'Norwegian regulatory filings', 'Executive tracking', 'Alerts'],
            'pricing': 'Fra 299 NOK/mnd',
            'category': 'norwegian-insider',
            'rating': 4.0,
            'logo': '/static/images/innsideanalyse-logo.png'
        },
        {
            'name': 'Investorkurs.no',
            'url': 'https://investorkurs.no',
            'description': 'Norsk investeringsutdanning og analyse-ressurser',
            'features': ['Educational content', 'Market analysis', 'Investment courses', 'Norwegian focus'],
            'pricing': 'Kurs fra 2499 NOK',
            'category': 'education',
            'rating': 4.1,
            'logo': '/static/images/investorkurs-logo.png'
        },
        {
            'name': 'Netfonds',
            'url': 'https://netfonds.no',
            'description': 'Norsk nettmegler med avanserte analysevarktøy',
            'features': ['Free real-time Nordic data', 'Advanced charting', 'Screening tools', 'Nordic markets'],
            'pricing': 'Gratis data, handel fra 39 NOK',
            'category': 'broker',
            'rating': 4.3,
            'logo': '/static/images/netfonds-logo.png'
        }
    ]
    
    # Categories for filtering
    categories = {
        'technical': 'Teknisk analyse',
        'fundamental': 'Fundamental analyse', 
        'ai': 'AI-baserte verktøy',
        'data': 'Markedsdata',
        'research': 'Investeringsresearch',
        'insider': 'Innsidehandel',
        'ai-insider': 'AI Innsidehandel',
        'norwegian': 'Norske verktøy',
        'norwegian-insider': 'Norsk innsidehandel',
        'education': 'Utdanning',
        'broker': 'Meglere'
    }
    
    return render_template('resources/analysis_tools.html',
                         global_tools=global_tools,
                         insider_tools=insider_tools,
                         norwegian_tools=norwegian_tools,
                         categories=categories,
                         title="Analyseverktøy og ressurser")

@resources_bp.route('/comparison')
@access_required
def tool_comparison():
    """Compare different analysis tools"""
    return render_template('resources/tool_comparison.html',
                         title="Verktøy-sammenligning")

@resources_bp.route('/guides')
@access_required 
def guides():
    """Show analysis guides and tutorials"""
    
    guides = [
        {
            'title': 'Hvordan bruke teknisk analyse',
            'description': 'Komplett guide til tekniske indikatorer og chart-mønstre',
            'category': 'technical',
            'difficulty': 'Beginner',
            'time_to_read': '15 min'
        },
        {
            'title': 'Fundamental analyse for nybegynnere', 
            'description': 'Lær å analysere selskapers finansielle data og verdsettelse',
            'category': 'fundamental',
            'difficulty': 'Beginner',
            'time_to_read': '20 min'
        },
        {
            'title': 'Forstå innsidehandel-signaler',
            'description': 'Hvordan tolke og bruke innsidehandel i din investeringsstrategi',
            'category': 'insider',
            'difficulty': 'Intermediate',
            'time_to_read': '12 min'
        },
        {
            'title': 'AI i aksjeanalyse',
            'description': 'Hvordan AI-verktøy kan forbedre dine investeringsbeslutninger',
            'category': 'ai',
            'difficulty': 'Intermediate', 
            'time_to_read': '18 min'
        }
    ]
    
    return render_template('resources/guides.html',
                         guides=guides,
                         title="Analyse-guider")
