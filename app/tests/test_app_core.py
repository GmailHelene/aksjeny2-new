import pytest
import os
import tempfile
from flask import Flask
from flask_login import LoginManager, UserMixin
from app import create_app, db
from app.models.user import User

@pytest.fixture
def app():
    # Create a temporary database for testing
    db_fd, db_path = tempfile.mkstemp()
    app = create_app('testing')
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
    app.config['TESTING'] = True
    app.config['SECRET_KEY'] = 'test_secret'

    with app.app_context():
        db.create_all()
        # Create test user
        test_user = User(
            username='testuser',
            email='test@example.com',
            has_subscription=True,
            subscription_type='premium',
            is_admin=True
        )
        test_user.set_password('testpass')
        db.session.add(test_user)
        db.session.commit()

    yield app

    # Cleanup
    os.close(db_fd)
    os.unlink(db_path)

@pytest.fixture
def client(app):
    return app.test_client()

@pytest.fixture
def runner(app):
    return app.test_cli_runner()

def test_profile_page(client):
    response = client.get('/profile')
    # Assuming /profile requires login, it should redirect
    assert response.status_code == 302 or response.status_code == 200

def test_favorites_page(client):
    response = client.get('/favorites')
    assert response.status_code == 302 or response.status_code == 200

def test_watchlist_page(client):
    response = client.get('/watchlist')
    assert response.status_code == 302 or response.status_code == 200

def test_portfolio_page(client):
    response = client.get('/portfolio')
    assert response.status_code == 302 or response.status_code == 200

def test_price_alerts_page(client):
    response = client.get('/price-alerts')
    assert response.status_code == 302 or response.status_code == 200

# Additional tests for real endpoints
def test_index_page(client):
    response = client.get('/')
    assert response.status_code == 200

def test_login_page(client):
    response = client.get('/auth/login')
    assert response.status_code == 200

def test_register_page(client):
    response = client.get('/auth/register')
    assert response.status_code == 200

def test_stocks_page(client):
    response = client.get('/stocks')
    assert response.status_code == 200 or response.status_code == 302

def test_analysis_page(client):
    response = client.get('/analysis')
    assert response.status_code == 200 or response.status_code == 302

# Test authentication
def test_login_post(client):
    response = client.post('/auth/login', data={
        'email': 'test@example.com',
        'password': 'testpass'
    }, follow_redirects=True)
    assert response.status_code == 200

def test_logout(client):
    response = client.get('/auth/logout', follow_redirects=True)
    assert response.status_code == 200

# Test protected routes after login
def test_protected_profile(client):
    # Login first
    client.post('/auth/login', data={
        'email': 'test@example.com',
        'password': 'testpass'
    }, follow_redirects=True)
    
    response = client.get('/profile')
    assert response.status_code == 200

def test_protected_portfolio(client):
    # Login first
    client.post('/auth/login', data={
        'email': 'test@example.com',
        'password': 'testpass'
    }, follow_redirects=True)
    
    response = client.get('/portfolio')
    assert response.status_code == 200