import re
import pytest

from app import create_app

@pytest.fixture
def client():
    app = create_app('testing')
    app.config.update(TESTING=True)
    with app.test_client() as client:
        yield client


def extract_tv_symbol(html: str):
    # Look for data-tv-symbol or tv_symbol usage in template
    m = re.search(r'data-tv-symbol="([A-Z:0-9\.-=]+)"', html)
    if m:
        return m.group(1)
    # Fallback: inline JS may include tv_symbol value in widgets
    m = re.search(r'"symbol":\s*"([A-Z:0-9\.-=]+)"', html)
    return m.group(1) if m else None


def test_ol_to_osl_mapping(client):
    resp = client.get('/stocks/details/DNB.OL')
    assert resp.status_code == 200
    sym = extract_tv_symbol(resp.get_data(as_text=True))
    assert sym is not None
    assert sym.startswith('OSL:') and sym.endswith('DNB')


def test_prefixed_osl_pass_through(client):
    resp = client.get('/stocks/details/OSL:DNB')
    assert resp.status_code == 200
    sym = extract_tv_symbol(resp.get_data(as_text=True))
    assert sym == 'OSL:DNB'


def test_us_default_nasdaq(client):
    resp = client.get('/stocks/details/AAPL')
    assert resp.status_code == 200
    sym = extract_tv_symbol(resp.get_data(as_text=True))
    assert sym.startswith('NASDAQ:') and sym.endswith('AAPL')


def test_invalid_symbol_safe(client):
    # Ensure route handles odd characters gracefully
    resp = client.get('/stocks/details/ABC$%25')
    # Might redirect or sanitize; at least should not 500
    assert resp.status_code in (200, 302)
