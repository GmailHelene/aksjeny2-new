"""Norwegian market intelligence routes — real data via yfinance.

For analyses that have public data sources (oil correlation, shipping,
market overview) we compute on demand. For ones that don't (social
sentiment without Twitter API, government impact without a structured
source) we keep an honest placeholder with explanation.
"""
import logging
import math
from flask import Blueprint, render_template
from flask_login import login_required

logger = logging.getLogger(__name__)

norwegian_intel = Blueprint('norwegian_intel', __name__)


def _pearson(xs, ys):
    """Pearson correlation between two equal-length numeric lists."""
    if len(xs) != len(ys) or len(xs) < 2:
        return None
    n = len(xs)
    mean_x = sum(xs) / n
    mean_y = sum(ys) / n
    num = sum((x - mean_x) * (y - mean_y) for x, y in zip(xs, ys))
    den_x = math.sqrt(sum((x - mean_x) ** 2 for x in xs))
    den_y = math.sqrt(sum((y - mean_y) ** 2 for y in ys))
    if not den_x or not den_y:
        return None
    return num / (den_x * den_y)


def _daily_returns(closes):
    """List of daily returns from a list of closing prices."""
    out = []
    for i in range(1, len(closes)):
        if closes[i - 1]:
            out.append((closes[i] - closes[i - 1]) / closes[i - 1])
    return out


def _fetch_history(symbol, period='3mo'):
    """Fetch closing prices via yfinance. Returns list of floats or []."""
    try:
        import yfinance as yf
        hist = yf.Ticker(symbol).history(period=period, interval='1d', auto_adjust=False)
        if hist is None or len(hist) == 0:
            return []
        return [float(c) for c in hist['Close'].tolist() if c is not None]
    except Exception as e:
        logger.debug(f"_fetch_history({symbol}) failed: {e}")
        return []


@norwegian_intel.route('/')
@login_required
def index():
    """Norway market overview — current snapshot via yfinance."""
    snapshot = {}
    try:
        import yfinance as yf
        for symbol, key, label in [
            ('^OSEAX', 'osebx', 'Oslo Børs Hovedindeks'),
            ('BZ=F', 'brent', 'Brent olje (USD)'),
            ('USDNOK=X', 'usd_nok', 'USD/NOK'),
            ('EURNOK=X', 'eur_nok', 'EUR/NOK'),
        ]:
            try:
                hist = yf.Ticker(symbol).history(period='5d', interval='1d', auto_adjust=False)
                if hist is None or len(hist) < 2:
                    continue
                last = float(hist.iloc[-1]['Close'])
                prev = float(hist.iloc[-2]['Close'])
                change_pct = ((last - prev) / prev) * 100 if prev else 0.0
                snapshot[key] = {
                    'label': label,
                    'value': round(last, 2 if last >= 10 else 4),
                    'change_pct': round(change_pct, 2),
                }
            except Exception as e:
                logger.debug(f"index snapshot {symbol} failed: {e}")
    except Exception:
        pass
    return render_template('norwegian_intel/index.html',
                           title='Norge Oversikt',
                           snapshot=snapshot)


# /social-sentiment fjernet — krever Twitter/Reddit paid API som ikke
# er konfigurert. Direkte tilgang gir nå 404.


@norwegian_intel.route('/oil-correlation')
@login_required
def oil_correlation():
    """Pearson correlation between Brent oil and Norwegian energy stocks
    over the last ~90 trading days. Real data, no fabrication."""
    brent = _fetch_history('BZ=F', period='3mo')
    norwegian_energy = [
        ('EQNR.OL', 'Equinor'),
        ('AKERBP.OL', 'Aker BP'),
        ('NHY.OL', 'Norsk Hydro'),
        ('TGS.OL', 'TGS'),
        ('PGS.OL', 'PGS'),
        ('SUBC.OL', 'Subsea 7'),
        ('SCATC.OL', 'Scatec'),
    ]
    rows = []
    if brent and len(brent) > 5:
        brent_returns = _daily_returns(brent)
        for symbol, name in norwegian_energy:
            closes = _fetch_history(symbol, period='3mo')
            if not closes or len(closes) < 5:
                continue
            stock_returns = _daily_returns(closes)
            # Align lengths
            n = min(len(brent_returns), len(stock_returns))
            if n < 5:
                continue
            corr = _pearson(brent_returns[-n:], stock_returns[-n:])
            if corr is None:
                continue
            rows.append({
                'symbol': symbol,
                'name': name,
                'correlation': round(corr, 3),
                'days': n,
            })
        rows.sort(key=lambda r: abs(r['correlation']), reverse=True)
    return render_template(
        'norwegian_intel/oil_correlation.html',
        title='Olje-korrelasjon',
        rows=rows,
        period_days=len(brent),
    )


# /government-impact fjernet — krever strukturert policy-database
# som ikke er konfigurert. Direkte tilgang gir nå 404.


@norwegian_intel.route('/shipping-intelligence')
@login_required
def shipping_intelligence():
    """Correlation between Baltic Dry Index proxy (BDRY ETF) and Norwegian
    shipping stocks. Real data."""
    # BDRY ETF (Breakwave Dry Bulk Shipping ETF) tracks BDI futures
    bdry = _fetch_history('BDRY', period='3mo')
    shipping_stocks = [
        ('FRO.OL', 'Frontline'),
        ('GOGL.OL', 'Golden Ocean'),
        ('MPCC.OL', 'MPC Container Ships'),
        ('BWE.OL', 'BW Energy'),
        ('SUBC.OL', 'Subsea 7'),
        ('WAWI.OL', 'Wallenius Wilhelmsen'),
    ]
    rows = []
    if bdry and len(bdry) > 5:
        bdry_returns = _daily_returns(bdry)
        for symbol, name in shipping_stocks:
            closes = _fetch_history(symbol, period='3mo')
            if not closes or len(closes) < 5:
                continue
            stock_returns = _daily_returns(closes)
            n = min(len(bdry_returns), len(stock_returns))
            if n < 5:
                continue
            corr = _pearson(bdry_returns[-n:], stock_returns[-n:])
            if corr is None:
                continue
            # Latest price for context
            last_price = closes[-1] if closes else None
            rows.append({
                'symbol': symbol,
                'name': name,
                'correlation': round(corr, 3),
                'days': n,
                'last_price': round(last_price, 2) if last_price else None,
            })
        rows.sort(key=lambda r: abs(r['correlation']), reverse=True)

    bdry_last = round(bdry[-1], 2) if bdry else None
    return render_template(
        'norwegian_intel/shipping_intelligence.html',
        title='Shipping Intelligence',
        rows=rows,
        bdry_last=bdry_last,
        period_days=len(bdry),
    )
