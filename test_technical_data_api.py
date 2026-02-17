import pytest
from app import create_app
from app.extensions import db
from app.models.user import User

@pytest.fixture
def app_instance():
    app = create_app('testing')
    with app.app_context():
        db.create_all()
        user = User(email='techuser@example.com', username='techuser', password='pass')
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
            user = User.query.filter_by(email='techuser@example.com').first()
            sess['_user_id'] = str(user.id)
    return client

EXPECTED_TECH_KEYS = {'success','symbol','data','data_points','cache_hit','data_source','authenticated'}


def test_demo_technical_data_shape(client):
    resp = client.get('/stocks/api/demo/technical-data/EQNR.OL')
    assert resp.status_code == 200
    data = resp.get_json()
    for k in EXPECTED_TECH_KEYS:
        assert k in data, f"Missing key {k} in demo response"
    assert data['symbol'] == 'EQNR.OL'
    assert data['success'] in (True, False)
    assert isinstance(data['data'], dict)
    assert data['data_points'] == len(data['data'].keys()) or data['data_points'] == 0


def test_authenticated_technical_data_shape(auth_client):
    resp = auth_client.get('/stocks/api/technical-data/DNB.OL')
    assert resp.status_code == 200
    data = resp.get_json()
    for k in EXPECTED_TECH_KEYS:
        assert k in data, f"Missing key {k} in auth response"
    assert data['symbol'] == 'DNB.OL'
    assert data['success'] in (True, False)
    assert isinstance(data['data'], dict)


def test_technical_data_caching(auth_client):
    r1 = auth_client.get('/stocks/api/technical-data/DNB.OL')
    d1 = r1.get_json()
    # Allow first request to be either a miss (False) or a hit (True) if cache warmed by prior tests
    assert d1.get('cache_hit') in (False, True)
    r2 = auth_client.get('/stocks/api/technical-data/DNB.OL')
    d2 = r2.get_json()
    assert d2.get('cache_hit') is True


def test_technical_data_error_fallback(monkeypatch, client):
    from app.services.data_service import DataService
    def boom(*args, **kwargs):
        raise RuntimeError('forced tech error')
    # Force failure in historical data retrieval used by api_technical_data logic
    monkeypatch.setattr(DataService, 'get_historical_data', boom)
    resp = client.get('/stocks/api/demo/technical-data/ERRORSYM')
    assert resp.status_code == 200
    data = resp.get_json()
    for k in EXPECTED_TECH_KEYS:
        assert k in data, f"Missing key {k} in error fallback"
    assert data['success'] is False
    assert data['data_source'] in ('ERROR FALLBACK','NO DATA')
    assert data['data_points'] in (0,4)
