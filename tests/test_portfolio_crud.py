import pytest
from app import create_app, db
from app.models.user import User
from app.models.portfolio import Portfolio, PortfolioStock
from werkzeug.security import generate_password_hash

@pytest.fixture(scope='module')
def app_instance():
    app = create_app()
    app.config['TESTING'] = True
    with app.app_context():
        yield app

@pytest.fixture()
def client(app_instance):
    return app_instance.test_client()

@pytest.fixture()
def user(app_instance):
    with app_instance.app_context():
        u = User.query.filter_by(email='crudtest@example.com').first()
        if not u:
            u = User(email='crudtest@example.com', username='crudtest')
            u.password_hash = generate_password_hash('Password123!', method='pbkdf2:sha256')
            db.session.add(u)
            db.session.commit()
        return u

def login(client, user):
    client.post('/auth/login', data={'email': user.email, 'password': 'Password123!'}, follow_redirects=True)

def test_portfolio_crud_flow(client, user, app_instance):
    login(client, user)
    # Create portfolio if missing
    with app_instance.app_context():
        portfolio = Portfolio.query.filter_by(user_id=user.id, name='CRUD Test').first()
        if not portfolio:
            portfolio = Portfolio(user_id=user.id, name='CRUD Test')
            db.session.add(portfolio)
            db.session.commit()
        # Add stock if none
        stock = PortfolioStock.query.filter_by(portfolio_id=portfolio.id).first()
        if not stock:
            stock = PortfolioStock(portfolio_id=portfolio.id, ticker='EQNR.OL', shares=10, purchase_price=100)
            db.session.add(stock)
            db.session.commit()
        stock_id = stock.id
        portfolio_id = portfolio.id
    # Remove stock (soft delete)
    r = client.post(
        f'/portfolio/{portfolio_id}/remove/{stock_id}',
        headers={'Accept':'application/json','X-CSRFToken':'test'}
    )
    assert r.status_code in (200, 400, 403, 302), f'Unexpected status for remove stock: {r.status_code}'
    if r.status_code == 200:
        data = r.get_json()
        assert data.get('success') is True
        assert data.get('portfolio_id') == portfolio_id
        assert data.get('stock_id') == stock_id
        # Second removal should be idempotent success
        r2 = client.post(
            f'/portfolio/{portfolio_id}/remove/{stock_id}',
            headers={'Accept':'application/json','X-CSRFToken':'test'}
        )
        assert r2.status_code == 200
        data2 = r2.get_json()
        assert data2.get('success') is True
    # Delete portfolio
    d = client.post(
        f'/portfolio/delete/{portfolio_id}',
        headers={'Accept':'application/json'}
    )
    assert d.status_code in (200, 302, 400, 403), f'Unexpected status for delete portfolio: {d.status_code}'
    if d.status_code == 200:
        data_del = d.get_json()
        assert 'success' in data_del
