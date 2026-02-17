import pytest

from app import create_app, db
from app.models.user import User


@pytest.fixture(scope='module')
def app_client():
    app = create_app()
    app.config['TESTING'] = True
    app.config['EKTE_ONLY'] = True
    with app.app_context():
        yield app.test_client()


def test_ai_page_no_predictions(app_client):
    # Query AI page with a ticker
    resp = app_client.get('/analysis/ai?ticker=AAPL', follow_redirects=True)
    assert resp.status_code == 200
    body = resp.get_data(as_text=True)
    # Should not contain prediction-related terms
    assert 'Prediksjon:' not in body
    assert 'Målpris' not in body
    assert 'Konfidens' not in body
    # Should show neutral EKTE-only message when no data
    assert 'Ingen analyse tilgjengelig' in body or 'Se analyse' in body


def test_screener_get_loads(app_client):
    resp = app_client.get('/analysis/screener')
    assert resp.status_code == 200
    body = resp.get_data(as_text=True)
    assert 'Avansert Aksje Screener' in body


def test_screener_post_with_filters_no_fabrication(app_client):
    # Use a simple preset filter that maps to service keys
    resp = app_client.post('/analysis/screener', data={'filters': ['pe_low']}, follow_redirects=True)
    assert resp.status_code == 200
    body = resp.get_data(as_text=True)
    # Page renders; results may be empty if no real service available but must not error
    assert 'Ingen resultater ennå' in body or '<table' in body


def test_demo_disabled(app_client):
    resp = app_client.get('/demo')
    assert resp.status_code == 410
    assert 'deaktivert' in resp.get_data(as_text=True)
