import pytest

from flask import Flask

from flask_login import LoginManager, UserMixin

@pytest.fixture

def app():

    app = Flask(__name__)

    app.config['TESTING'] = True

    app.config['SECRET_KEY'] = 'test_secret'

    login_manager = LoginManager()

    login_manager.init_app(app)

    class TestUser(UserMixin):

        def __init__(self, id):

            self.id = id

            self.email = 'test@example.com'

            self.is_authenticated = True

            self.subscription_type = 'premium'

            self.has_subscription = True

    @login_manager.user_loader

    def load_user(user_id):

        return TestUser(user_id)

    # Dummy routes for testing

    @app.route('/profile')

    def profile():

        return "Profile Page", 200

    @app.route('/favorites')

    def favorites():

        return "Favorites Page", 200

    @app.route('/watchlist')

    def watchlist():

        return "Watchlist Page", 200

    @app.route('/portfolio')

    def portfolio():

        return "Portfolio Page", 200

    @app.route('/price-alerts')

    def price_alerts():

        return "Price Alerts Page", 200

    return app

@pytest.fixture

def client(app):

    return app.test_client()

def test_profile_page(client):

    response = client.get('/profile')

    assert response.status_code == 200

    assert b"Profile Page" in response.data

def test_favorites_page(client):

    response = client.get('/favorites')

    assert response.status_code == 200

    assert b"Favorites Page" in response.data

def test_watchlist_page(client):

    response = client.get('/watchlist')

    assert response.status_code == 200

    assert b"Watchlist Page" in response.data

def test_portfolio_page(client):

    response = client.get('/portfolio')

    assert response.status_code == 200

    assert b"Portfolio Page" in response.data

def test_price_alerts_page(client):

    response = client.get('/price-alerts')

    assert response.status_code == 200

    assert b"Price Alerts Page" in response.data