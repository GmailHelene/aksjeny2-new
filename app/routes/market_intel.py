from flask import Blueprint, render_template, redirect, url_for, jsonify
from flask_login import current_user
from datetime import datetime, timedelta
import logging
from app.services.data_service import (
    is_ekte_only,
)

# NOTE: Real data helper imports (add real implementations as they become available)
try:
    from app.services.market_intel_service import (
        fetch_economic_indicators_real,
        fetch_crypto_fear_greed_real,
        fetch_insider_trades_real,
        fetch_earnings_calendar_real,
        fetch_sector_performance_real,
        fetch_market_news_real,
    )
except Exception:  # pragma: no cover - optional service module
    fetch_economic_indicators_real = fetch_crypto_fear_greed_real = lambda: None
    fetch_insider_trades_real = lambda: {}
    fetch_earnings_calendar_real = lambda: []
    fetch_sector_performance_real = lambda: []
    fetch_market_news_real = lambda: []

logger = logging.getLogger(__name__)

# NOTE: This blueprint is a lightweight placeholder to satisfy navigation links
# and avoid BuildErrors. It supplies minimal safe mock data structures expected
# by the existing templates. Later, real data services can replace these mocks.

market_intel = Blueprint('market_intel', __name__)

@market_intel.route('/')
@market_intel.route('')
def index():
    """Market intelligence landing page.

    Behavior matrix:
      - EKTE_ONLY & anonymous: Empty datasets + notice (no fabrication)
      - EKTE_ONLY & authenticated: Attempt real fetch; per-section fallback to empty with partial notice messages
      - Non-EKTE mode (future deprecation): could allow illustrative placeholders (currently disabled to enforce authenticity)
    """
    base_notice = None
    economic_indicators = {}
    crypto_fear_greed = {}
    insider_data = {}
    earnings_calendar = []
    sector_performance = []
    market_news = []
    section_warnings = []

    ekte_mode = is_ekte_only()

    if ekte_mode:
        if not getattr(current_user, 'is_authenticated', False):
            base_notice = 'Ekte markedsdata krever innlogging – ingen kunstige tall vist.'
        else:
            # Authenticated: attempt real fetches individually
            def guarded(fetch_fn, default, label):
                try:
                    data = fetch_fn()
                    if not data:
                        section_warnings.append(f'{label} utilgjengelig.')
                        return default
                    return data
                except Exception as e:  # pragma: no cover - defensive
                    logger.error(f"MarketIntel fetch failed [{label}]: {e}")
                    section_warnings.append(f'{label} feil – midlertidig skjult.')
                    return default

            economic_indicators = guarded(fetch_economic_indicators_real, {}, 'Makroindikatorer')
            crypto_fear_greed = guarded(fetch_crypto_fear_greed_real, {}, 'Crypto sentiment')
            insider_data = guarded(fetch_insider_trades_real, {}, 'Innsidehandler')
            earnings_calendar = guarded(fetch_earnings_calendar_real, [], 'Resultatkalender')
            sector_performance = guarded(fetch_sector_performance_real, [], 'Sektorytelse')
            market_news = guarded(fetch_market_news_real, [], 'Markedssaker')

            if section_warnings:
                base_notice = ' / '.join(section_warnings)
    else:
        # Deprecated placeholder path intentionally removed to enforce authenticity.
        base_notice = 'Demo-modus deaktivert – aktiver EKTE_ONLY for produksjonssikker visning.'

    return render_template(
        'market_intel/index.html',
        economic_indicators=economic_indicators,
        crypto_fear_greed=crypto_fear_greed,
        insider_data=insider_data,
        earnings_calendar=earnings_calendar,
        sector_performance=sector_performance,
        market_news=market_news,
        ekte_notice=base_notice,
    )


# ---- Placeholder child routes (anchors or future dedicated pages) ----

@market_intel.route('/insider-trading')
def insider_trading():
    """Temporary: reuse index but could later serve dedicated template."""
    return redirect(url_for('market_intel.index') + '#insider')


@market_intel.route('/earnings-calendar')
def earnings_calendar():
    """Placeholder route for earnings calendar - redirects to main page section.

    Endpoint name intentionally matches template reference 'market_intel.earnings_calendar'.
    """
    return redirect(url_for('market_intel.index') + '#earnings')


@market_intel.route('/sector-analysis')
def sector_analysis():
    return redirect(url_for('market_intel.index') + '#sectors')


@market_intel.route('/economic-indicators')
def economic_indicators():
    """Placeholder route for economic indicators - redirects to main page section.

    Endpoint name intentionally matches template reference 'market_intel.economic_indicators'.
    """
    return redirect(url_for('market_intel.index') + '#economic-indicators')


# Example lightweight API endpoint used by template JS (crypto fear & greed)
@market_intel.route('/api/crypto-fear-greed')
def api_crypto_fear_greed():
    return jsonify({
        'value': 52,
        'classification': 'Neutral',
        'updated': datetime.utcnow().isoformat()
    })
