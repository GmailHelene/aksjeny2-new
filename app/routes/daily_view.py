from flask import Blueprint, render_template, current_app
from datetime import datetime, date as date_cls

# Minimal placeholder blueprint to satisfy navigation and templates
# Will later be expanded with real data services

daily_view = Blueprint('daily_view', __name__, template_folder='../templates/daily_view')


def _mock_insights():
    now = datetime.utcnow()
    # Provide a few placeholder insights matching template fields
    return [
        {
            'time': (now.replace(minute=0, second=0, microsecond=0)).strftime('%H:%M'),
            'title': 'Oslo Børs åpner svakt opp',
            'summary': 'Hovedindeksen starter dagen moderat positiv etter blandede signaler fra USA og Asia.',
            'category': 'Marked',
            'impact': 'Positiv',
            'affected_stocks': ['EQNR', 'DNB', 'NHY']
        },
        {
            'time': (now.replace(minute=30, second=0, microsecond=0)).strftime('%H:%M'),
            'title': 'Oljeprisen stiger',
            'summary': 'Brent opp over 1% på forventninger om strammere tilbud.',
            'category': 'Råvarer',
            'impact': 'Meget Positiv',
            'affected_stocks': ['EQNR', 'AKRBP']
        }
    ]


def _mock_movers():
    return {
        'gainers': [
            {'ticker': 'EQNR', 'change': '+2.4%', 'price': '298.50'},
            {'ticker': 'AKRBP', 'change': '+1.9%', 'price': '270.10'},
            {'ticker': 'TGS', 'change': '+1.6%', 'price': '145.30'}
        ],
        'losers': [
            {'ticker': 'NEL', 'change': '-3.1%', 'price': '7.82'},
            {'ticker': 'KOA', 'change': '-2.7%', 'price': '19.40'},
            {'ticker': 'REC', 'change': '-2.2%', 'price': '11.15'}
        ]
    }


def _mock_events():
    return [
        {'time': '08:00', 'event': 'BNP (foreløpig) - Eurosonen', 'importance': 'Medium', 'expected': '0.3%', 'previous': '0.2%'},
        {'time': '10:00', 'event': 'Industriproduksjon - Norge', 'importance': 'Høy', 'expected': '0.5%', 'previous': '-0.1%'},
        {'time': '14:30', 'event': 'Jobless Claims - USA', 'importance': 'Høy', 'expected': '225K', 'previous': '228K'}
    ]


def _mock_analysis(selected_date_str: str):
    # Provide a minimal structure expected by analysis template
    return {
        'market_summary': 'Markedet viser blandet utvikling med energi i førersetet og teknologi svakt ned.',
        'sector_performance': [
            {'sector': 'Energi', 'performance': '+1.8%', 'leader': 'EQNR'},
            {'sector': 'Finans', 'performance': '+0.6%', 'leader': 'DNB'},
            {'sector': 'Industri', 'performance': '-0.4%', 'leader': 'TOM'},
            {'sector': 'Teknologi', 'performance': '-1.1%', 'leader': 'KIT'}
        ],
        'key_events': [
            f"{selected_date_str} 09:00 – Oljepris i fokus etter OPEC-kommentarer",
            f"{selected_date_str} 10:00 – Norsk industriproduksjon publisert",
            f"{selected_date_str} 14:30 – Amerikanske jobless claims gir retning"
        ]
    }


@daily_view.route('/')
def index():
    """Daily market overview placeholder page."""
    try:
        today = datetime.utcnow()
        context = {
            'date': today,
            'insights': _mock_insights(),
            'movers': _mock_movers(),
            'events': _mock_events()
        }
        return render_template('daily_view/index.html', **context)
    except Exception as e:
        current_app.logger.warning(f"daily_view.index failed: {e}")
        # Render with minimal safe context to avoid template errors
        return render_template('daily_view/index.html', date=datetime.utcnow(), insights=[], movers={}, events=[])


@daily_view.route('/analysis/<date>')
def daily_analysis(date):  # date parameter used by template
    try:
        # Validate/parse date
        try:
            parsed = datetime.strptime(date, '%Y-%m-%d')
        except ValueError:
            parsed = datetime.utcnow()
            date = parsed.strftime('%Y-%m-%d')
        analysis_data = _mock_analysis(date)
        return render_template('daily_view/analysis.html', date=date, analysis=analysis_data)
    except Exception as e:
        current_app.logger.warning(f"daily_view.daily_analysis failed: {e}")
        return render_template('daily_view/analysis.html', date=date, analysis={'sector_performance': [], 'key_events': []})
