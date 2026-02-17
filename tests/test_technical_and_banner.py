import pytest
from app import create_app, db
from app.models.user import User

@pytest.fixture(scope='module')
def test_app():
    app = create_app()
    app.config['TESTING'] = True
    with app.app_context():
        yield app

@pytest.fixture()
def client(test_app):
    return test_app.test_client()

@pytest.fixture()
def premium_user(test_app):
    with test_app.app_context():
        user = User.query.filter_by(email='pytest-premium@example.com').first()
        if not user:
            user = User(username='pytest_premium', email='pytest-premium@example.com', has_subscription=True, subscription_type='monthly')
            from werkzeug.security import generate_password_hash
            user.password_hash = generate_password_hash('Secret123!', method='pbkdf2:sha256')
            db.session.add(user)
        else:
            user.has_subscription = True
            user.subscription_type = 'monthly'
        db.session.commit()
        return user.email

def login(client, email, password='Secret123!'):
    return client.post('/auth/login', data={'email': email, 'password': password}, follow_redirects=True)

def test_technical_analysis_renders(client):
    resp = client.get('/analysis/technical?symbol=TSLA', follow_redirects=True)
    assert resp.status_code == 200
    body = resp.get_data(as_text=True)
    assert 'TSLA' in body
    assert 'technicalSearchForm' not in body, 'Legacy duplicate form should be removed'

def test_ticker_suggestions_endpoint(client):
    resp = client.get('/analysis/ticker_suggestions?q=T')
    assert resp.status_code == 200
    data = resp.get_json()
    assert isinstance(data, list)
    assert any(s.startswith('T') for s in data)

def test_premium_banner_hidden_for_premium(client, premium_user):
    login(client, premium_user)
    resp = client.get('/analysis/technical?symbol=AAPL', follow_redirects=True)
    body = resp.get_data(as_text=True)
    assert 'Begrenset modus:' not in body, 'Premium banner should be hidden for premium user'
