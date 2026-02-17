import pytest
from app import create_app, db
from app.models.user import User
from flask_login import login_user


@pytest.fixture
def app_instance():
    app = create_app('testing')
    with app.app_context():
        db.create_all()
        user = User(email='pricealertsapi@example.com', username='pricealertsapi', password='pass')
        db.session.add(user)
        db.session.commit()
    yield app


@pytest.fixture
def client(app_instance):
    return app_instance.test_client()


def login(client):
    # Reuse existing login route form logic; if not present we simulate session directly
    return client.post('/login', data={'email': 'pricealertsapi@example.com', 'password': 'pass'}, follow_redirects=True)


def test_price_alerts_api_empty_and_cache(client, app_instance):
    # Login first
    rlogin = login(client)
    assert rlogin.status_code == 200
    # First request: expect cache_hit False
    r1 = client.get('/notifications/api/price_alerts')
    assert r1.status_code == 200
    d1 = r1.get_json()
    assert d1['success'] is True
    assert d1['cache_hit'] is False
    assert d1['data_source'] in ('DB', 'DB_ERROR_FALLBACK')  # fresh load uses DB or fallback
    # Second request should be served from cache
    r2 = client.get('/notifications/api/price_alerts')
    d2 = r2.get_json()
    assert d2['success'] is True
    assert d2['cache_hit'] is True
    # Field consistency
    for key in ['success', 'alerts', 'data_points', 'cache_hit', 'data_source', 'authenticated']:
        assert key in d2


def test_price_alerts_api_error_handling(monkeypatch, client, app_instance):
    login(client)
    # Force exception inside handler by monkeypatching model query attribute
    from app.routes import notifications as notifications_module
    def boom(*a, **k):
        raise RuntimeError('db down')
    class DummyQuery:
        def filter_by(self, **k):
            raise RuntimeError('db down')
    # monkeypatch PriceAlert query to raise
    dummy = type('D', (), {'query': DummyQuery()})
    monkeypatch.setitem(notifications_module.__dict__, 'PriceAlert', dummy)
    r = client.get('/notifications/api/price_alerts')
    data = r.get_json()
    assert data['success'] is False
    # Error path now emits UNKNOWN as data_source per refactor
    assert data['data_source'] in ('ERROR','UNKNOWN')
    assert data['cache_hit'] is False
