import json, os
from app import create_app, db
from app.models.user import User
from app.models.portfolio import Portfolio, PortfolioStock
from flask import url_for

app = create_app()
app.testing = True

def ensure_user(client):
    with app.app_context():
        user = User.query.filter_by(email='crudtest@example.com').first()
        if not user:
            user = User(email='crudtest@example.com', username='crudtest')
            # Use shorter hash method to avoid length constraint issues on legacy schema
            from werkzeug.security import generate_password_hash
            user.password_hash = generate_password_hash('Password123!', method='pbkdf2:sha256')
            db.session.add(user)
            db.session.commit()
        return user

def login(client, user):
    return client.post('/auth/login', data={'email': user.email, 'password': 'Password123!'}, follow_redirects=True)

with app.app_context():
    client = app.test_client()
    user = ensure_user(client)
    login(client, user)
    # Create portfolio
    p = Portfolio.query.filter_by(user_id=user.id, name='CRUD Test').first()
    if not p:
        p = Portfolio(user_id=user.id, name='CRUD Test')
        db.session.add(p)
        db.session.commit()
    # Add a stock entry
    stock = PortfolioStock.query.filter_by(portfolio_id=p.id).first()
    if not stock:
        stock = PortfolioStock(portfolio_id=p.id, ticker='EQNR.OL', shares=10, purchase_price=100)
        db.session.add(stock)
        db.session.commit()
    stock_id = stock.id

    # Test remove stock
    remove_resp = client.post(f'/portfolio/{p.id}/remove/{stock_id}', headers={'Accept': 'application/json', 'X-CSRFToken': 'test'})
    print('REMOVE STOCK STATUS', remove_resp.status_code, remove_resp.json)

    # Recreate stock to test portfolio delete
    if PortfolioStock.query.get(stock_id) and PortfolioStock.query.get(stock_id).deleted_at is None:
        pass
    else:
        stock2 = PortfolioStock(portfolio_id=p.id, ticker='DNB.OL', shares=5, purchase_price=150)
        db.session.add(stock2)
        db.session.commit()

    del_resp = client.post(f'/portfolio/delete/{p.id}', headers={'Accept': 'application/json'})
    print('DELETE PORTFOLIO STATUS', del_resp.status_code, del_resp.json)
