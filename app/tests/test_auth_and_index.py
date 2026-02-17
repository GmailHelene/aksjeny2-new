import pytest
from app import create_app
from app.extensions import db
from app.models.user import User


@pytest.fixture
def app_instance():
    app = create_app('testing')
    with app.app_context():
        db.create_all()
        # Create a test user
        user = User(email='testuser@example.com', username='testuser')
        try:
            user.set_password('password123')
        except Exception:
            pass
        db.session.add(user)
        db.session.commit()
    yield app
    with app.app_context():
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app_instance):
    return app_instance.test_client()


def test_login_get(client):
    resp = client.get('/login')
    assert resp.status_code == 200
    assert b'Logg inn' in resp.data


def test_login_invalid(client):
    resp = client.post('/login', data={
        'email': 'wrong@example.com',
        'password': 'badpass'
    }, follow_redirects=True)
    # Should not 500 and should show login page again
    assert resp.status_code == 200
    assert b'Logg inn' in resp.data


def test_login_valid_redirects(client):
    resp = client.post('/login', data={
        'email': 'testuser@example.com',
        'password': 'password123'
    })
    # Should redirect (302) after successful login
    assert resp.status_code in (301, 302)


def test_list_index_authenticated(client):
    # Login first
    client.post('/login', data={
        'email': 'testuser@example.com',
        'password': 'password123'
    })
    resp = client.get('/stocks/list/index')
    assert resp.status_code == 200
    assert b'Aksjeoversikt' in resp.data
