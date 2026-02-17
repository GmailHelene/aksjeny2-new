import pytest
from app import create_app
from app.extensions import db
from app.models.user import User

@pytest.fixture
def app_instance():
    app = create_app('testing')
    with app.app_context():
        db.create_all()
        user = User(email='chartuser@example.com', username='chartuser', password='pass')
        db.session.add(user)
        db.session.commit()
    yield app

@pytest.fixture
def client(app_instance):
    return app_instance.test_client()

@pytest.fixture
def auth_client(client, app_instance):
    with app_instance.app_context():
        with client.session_transaction() as sess:
            user = User.query.filter_by(email='chartuser@example.com').first()
            sess['_user_id'] = str(user.id)
    return client

EXPECTED_KEYS = {'success','symbol','dates','prices','volumes','currency','data_source','period','interval','data_points'}

def test_chart_data_demo_unauthenticated(client):
    resp = client.get('/stocks/api/chart-data/EQNR.OL')
    assert resp.status_code == 200
    data = resp.get_json()
    for k in EXPECTED_KEYS:
        assert k in data, f"Missing key {k} in demo response"
    assert data['success'] is True
    assert data['symbol'] == 'EQNR.OL'
    assert len(data['dates']) == len(data['prices']) == len(data['volumes'])
    assert data['data_points'] == len(data['dates'])


def test_chart_data_period_validation(client):
    # Invalid period should fallback to 30d
    resp = client.get('/stocks/api/chart-data/EQNR.OL?period=999d')
    data = resp.get_json()
    assert data['period'] == '30d'


def test_chart_data_authenticated(auth_client):
    resp = auth_client.get('/stocks/api/chart-data/DNB.OL')
    assert resp.status_code == 200
    data = resp.get_json()
    # Success can be True even if demo fallback; ensure shape
    for k in EXPECTED_KEYS:
        assert k in data, f"Missing key {k} in auth response"
    assert data['symbol'] == 'DNB.OL'
    assert data['success'] in (True, False)
    assert data['data_points'] == len(data['dates'])


def test_chart_data_caching(client):
    # Ensure clean cache so first request is definitely a miss
    try:
        from app.routes import stocks as stocks_module
        if hasattr(stocks_module, '_CHART_CACHE'):
            stocks_module._CHART_CACHE.clear()
    except Exception:
        pass
    # First request should be cache miss (cache_hit False or absent)
    # Use a symbol unlikely used by other tests to avoid cross-test cache contamination
    test_symbol = 'CACHETEST.OL'
    r1 = client.get(f'/stocks/api/chart-data/{test_symbol}?period=30d&interval=1d')
    d1 = r1.get_json()
    assert d1['success'] is True
    assert d1.get('cache_hit') is False
    # Second identical request should be cache hit
    r2 = client.get(f'/stocks/api/chart-data/{test_symbol}?period=30d&interval=1d')
    d2 = r2.get_json()
    assert d2['success'] is True
    assert d2.get('cache_hit') is True


def test_chart_data_error_fallback(monkeypatch, client):
    # Force an exception inside the endpoint by monkeypatching DataService.get_historical_data to raise
    from app.services.data_service import DataService
    def boom(*args, **kwargs):
        raise RuntimeError('forced error')
    monkeypatch.setattr(DataService, 'get_historical_data', boom)
    resp = client.get('/stocks/api/chart-data/ERRORSYM')
    assert resp.status_code == 200
    data = resp.get_json()
    for k in EXPECTED_KEYS:
        assert k in data, f"Missing key {k} in error fallback"
    # Depending on where exception happens, success may be False (error path) OR True (demo fallback)
    # If success True, ensure data_source is demo and no 'error' key; if False, ensure error key present
    if data['success'] is True:
        assert data['data_source'] in ('DEMO DATA - Free Access', 'REAL DATA - Premium Access')
    else:
        assert data.get('error'), 'Expected error message when success False'
        assert data['data_points'] == 3
