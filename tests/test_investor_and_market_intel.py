import os
import pytest
from app import create_app, db
from conftest import auth_client  # ensure fixture import for authenticated client

@pytest.fixture(scope='module')
def test_client():
    # Trigger testing config path in create_app
    os.environ['PYTEST_CURRENT_TEST'] = '1'
    os.environ['APP_ENV'] = 'testing'
    app = create_app()
    # Force EKTE_ONLY in test config
    app.config['EKTE_ONLY'] = True
    with app.app_context():
        db.create_all()
    with app.test_client() as client:
        yield client

def test_investor_page_200(test_client):
    resp = test_client.get('/investor/')
    assert resp.status_code == 200
    text = resp.get_data(as_text=True)
    # Ensure no mock marker words (we removed them) but page renders
    assert 'Investormuligheter' in text or 'Invester i' in text

def test_market_intel_page_200(test_client):
    resp = test_client.get('/market-intel/')
    assert resp.status_code == 200
    text = resp.get_data(as_text=True)
    # In EKTE_ONLY mode we expect notice and absence of fabricated numbers
    assert 'Markedsintelligens' in text
    # Updated notice now requires login for real data
    assert 'Ekte markedsdata krever innlogging' in text

def test_market_intel_sub_routes_redirect(test_client):
    for path in ['/market-intel/insider-trading', '/market-intel/earnings-calendar', '/market-intel/sector-analysis', '/market-intel/economic-indicators']:
        resp = test_client.get(path, follow_redirects=True)
        assert resp.status_code == 200
        assert 'Markedsintelligens' in resp.get_data(as_text=True)

def test_market_intel_no_placeholder_values_ekte_only(test_client):
    """Ensure previously used placeholder numeric values or labels are absent in EKTE_ONLY mode when not authenticated."""
    resp = test_client.get('/market-intel/')
    body = resp.get_data(as_text=True)
    forbidden_markers = ['1.8', '3.2', '82.45', 'MockNews', 'Market Update 1']
    for marker in forbidden_markers:
        assert marker not in body

def test_market_intel_authenticated_attempts_real(auth_client):
    client, user = auth_client
    resp = client.get('/market-intel/')
    assert resp.status_code == 200
    body = resp.get_data(as_text=True)
    # Authenticated path should NOT show the anonymous login-required base notice
    assert 'krever innlogging' not in body
    # It may still show section warnings (since many real fetchers return empty), which is acceptable
    # Ensure still no old placeholder markers
    for marker in ['1.8', '3.2', '82.45', 'MockNews', 'Market Update 1']:
        assert marker not in body
