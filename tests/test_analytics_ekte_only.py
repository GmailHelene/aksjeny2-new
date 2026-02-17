import os
import pytest
from app import create_app, db

@pytest.fixture(scope='module')
def client():
    os.environ['APP_ENV'] = 'testing'
    app = create_app()
    app.config['TESTING'] = True
    app.config['EKTE_ONLY'] = True
    with app.app_context():
        db.create_all()
    with app.test_client() as c:
        yield c

def test_analytics_dashboard_route_exists(client):
    resp = client.get('/analytics/')
    # Should render (may be largely empty) not 404
    assert resp.status_code == 200
    body = resp.get_data(as_text=True)
    assert 'analytics' in body.lower() or 'dashboard' in body.lower()


def test_analytics_api_dashboard_min_keys(client):
    resp = client.get('/analytics/api/dashboard/EURUSD')
    assert resp.status_code == 200
    data = resp.get_json()
    for key in ['market_data','risk_metrics','technical_analysis','pattern_recognition','performance_metrics','alerts']:
        assert key in data
    # Ensure no hardcoded fabricated SPX value appears if market_overview present
    mo = data.get('market_overview') or {}
    if isinstance(mo, dict):
        spx_val = mo.get('indices', {}).get('SPX', {}).get('value') if mo.get('indices') else None
        assert spx_val not in (4485.30, '4485.30')


def test_sentiment_history_removed_from_analysis_generation(client):
    # sentiment history previously fabricated; ensure helper now yields empty
    from app.routes.analysis import _generate_sentiment_history
    hist = _generate_sentiment_history('EQNR')
    assert isinstance(hist, dict)
    assert hist.get('dates') == []
    assert hist.get('scores') == []
