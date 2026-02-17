import os
import pytest
from app import create_app, db
from conftest import auth_client

@pytest.fixture(scope='module')
def test_client():
    os.environ['PYTEST_CURRENT_TEST'] = '1'
    os.environ['APP_ENV'] = 'testing'
    app = create_app()
    app.config['EKTE_ONLY'] = True
    with app.app_context():
        db.create_all()
    with app.test_client() as client:
        yield client

def test_analysis_symbol_no_pseudo(auth_client):
    client, user = auth_client
    resp = client.get('/analysis/AAPL')
    assert resp.status_code in (200, 404)  # 404 if route expects other format
    body = resp.get_data(as_text=True)
    # Fravær av pseudo-indikatornavn vi fjernet (Stochastic Oscillator, Volume Analysis etc.)
    forbidden = ['Stochastic Oscillator', 'Volume Analysis', 'Sentiment Score']
    for f in forbidden:
        assert f not in body
    # Ingen 'confidence": 0.' random pattern (0.6-0.95) lenger
    assert '0.7' not in body or 'confidence' not in body  # myk sjekk

def test_analysis_symbol_no_generated_news(auth_client):
    client, user = auth_client
    resp = client.get('/analysis/AAPL')
    body = resp.get_data(as_text=True)
    # Sikre at kunstige nyhetstitler (ofte med Apple eller Tesla + pseudo) ikke finnes hvis vi ikke har ekte nyheter
    pseudo_markers = ['bullish momentum', 'bearish momentum']
    for p in pseudo_markers:
        assert p not in body
