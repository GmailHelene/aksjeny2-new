import time
import pytest
from app import create_app, db
from app.models.user import User


@pytest.fixture
def app_instance():
    app = create_app('testing')
    with app.app_context():
        db.create_all()
        user = User(email='ttluser@example.com', username='ttluser', password='pass')
        db.session.add(user)
        db.session.commit()
    yield app


@pytest.fixture
def client(app_instance):
    return app_instance.test_client()


def login(client):
    return client.post('/login', data={'email': 'ttluser@example.com', 'password': 'pass'}, follow_redirects=True)



def test_price_alerts_cache_ttl_expiry(client):
    login(client)
    r1 = client.get('/notifications/api/price_alerts')
    d1 = r1.get_json()
    assert d1['cache_hit'] is False
    r2 = client.get('/notifications/api/price_alerts')
    d2 = r2.get_json()
    assert d2['cache_hit'] is True
    from app.routes import notifications as notif_module
    if hasattr(notif_module, '_PRICE_ALERTS_CACHE'):
        for k, v in notif_module._PRICE_ALERTS_CACHE.items():
            v['ts'] -= 120  # exceed TTL (30s)
    r3 = client.get('/notifications/api/price_alerts')
    d3 = r3.get_json()
    assert d3['cache_hit'] is False
