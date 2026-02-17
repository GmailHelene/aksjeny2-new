import pytest
from app import create_app
from app.extensions import db
from app.models.user import User

@pytest.fixture
def app_instance():
    app = create_app('testing')
    with app.app_context():
        db.create_all()
        user = User(email='toggletest@example.com', username='toggletest', password='testpass')
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
            user = User.query.filter_by(email='toggletest@example.com').first()
            sess['_user_id'] = str(user.id)
    return client

def test_toggle_invalid_symbol_rejected(auth_client):
    # Symbol with illegal chars should be sanitized -> invalid -> 400
    resp = auth_client.post('/stocks/api/favorites/toggle/INVALID_SYMBOL_$$$$', headers={'X-CSRFToken': 'test'})
    assert resp.status_code == 400
    data = resp.get_json()
    assert data['success'] is False
    assert 'Ugyldig' in data.get('message','')


def test_toggle_normalization_structure(auth_client):
    # First valid toggle add
    resp1 = auth_client.post('/stocks/api/favorites/toggle/EQNR.OL', headers={'X-CSRFToken': 'test'})
    data1 = resp1.get_json()
    assert resp1.status_code == 200
    assert set(['success','favorited','symbol','message']).issubset(data1.keys())
    assert data1['success'] and data1['favorited'] is True

    # Force second toggle (remove)
    resp2 = auth_client.post('/stocks/api/favorites/toggle/EQNR.OL', headers={'X-CSRFToken': 'test'})
    data2 = resp2.get_json()
    assert resp2.status_code == 200
    assert data2['success'] and data2['favorited'] is False


def test_toggle_idempotent_add_remove_cycle(auth_client):
    # Add
    auth_client.post('/stocks/api/favorites/toggle/DNB.OL', headers={'X-CSRFToken': 'test'})
    # Remove
    auth_client.post('/stocks/api/favorites/toggle/DNB.OL', headers={'X-CSRFToken': 'test'})
    # Toggle again (pure toggle semantics means it should add again)
    resp = auth_client.post('/stocks/api/favorites/toggle/DNB.OL', headers={'X-CSRFToken': 'test'})
    data = resp.get_json()
    assert resp.status_code == 200
    assert data['success']
    assert data['favorited'] is True
