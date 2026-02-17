import re
from app import create_app, db
from app.models.portfolio import Portfolio, PortfolioStock
from app.models import User

app = create_app('development')

def get_csrf(html):
    m = re.search(r'name="csrf_token"[^>]*value="([^"]+)"', html)
    return m.group(1) if m else None

with app.test_client() as client, app.app_context():
    user = User.query.filter_by(email='test@example.com').first()
    if not user:
        print('Test user test@example.com not found; aborting CRUD verification.')
        raise SystemExit(1)
    login_page = client.get('/login')
    csrf = get_csrf(login_page.data.decode())
    if not csrf:
        print('Could not extract CSRF token')
        raise SystemExit(1)
    resp = client.post('/auth/login', data={'csrf_token': csrf, 'email': 'test@example.com', 'password': 'testpassword'}, follow_redirects=False)
    print('Login status', resp.status_code)
    # Ensure portfolio
    portfolio = Portfolio.query.filter_by(user_id=user.id, name='CRUD Verify').first()
    if not portfolio:
        portfolio = Portfolio(user_id=user.id, name='CRUD Verify')
        db.session.add(portfolio)
        db.session.commit()
        print('Created portfolio id', portfolio.id)
    # Ensure stock
    stock = PortfolioStock.query.filter_by(portfolio_id=portfolio.id, ticker='EQNR.OL', deleted_at=None).first()
    if not stock:
        stock = PortfolioStock(portfolio_id=portfolio.id, ticker='EQNR.OL', shares=5, purchase_price=120)
        db.session.add(stock)
        db.session.commit()
        print('Added stock id', stock.id)
    # Remove stock via JSON
    r = client.post(f'/portfolio/{portfolio.id}/remove/{stock.id}', headers={'Accept':'application/json','X-CSRFToken':csrf})
    print('Remove stock status', r.status_code, r.json)
    # Delete portfolio via JSON
    r2 = client.post(f'/portfolio/delete/{portfolio.id}', headers={'Accept':'application/json'})
    print('Delete portfolio status', r2.status_code, r2.json)
