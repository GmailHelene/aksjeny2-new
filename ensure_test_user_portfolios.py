#!/usr/bin/env python3
"""
Ensure that test users have at least one portfolio and a default stock.
"""
from datetime import datetime
from pathlib import Path
from app import create_app, db
from app.models.user import User
from app.models.portfolio import Portfolio, PortfolioStock

TEST_EMAILS = [
    'test@aksjeradar.trade',
    'investor@aksjeradar.trade',
    'testuser@aksjeradar.trade',
]

LOG = []

def log(line: str):
    LOG.append(line)

def ensure_portfolio_for_user(user: User) -> bool:
    created_any = False
    portfolios = Portfolio.query.filter_by(user_id=user.id).all()
    log(f"User {user.email} has {len(portfolios)} portfolio(s)")
    if not portfolios:
        try:
            log("Creating default portfolio...")
            portfolio = Portfolio(
                name='Test Portfolio',
                description='Auto-created portfolio for test user',
                user_id=user.id,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
                is_watchlist=False,
            )
            db.session.add(portfolio)
            db.session.commit()
            created_any = True
            log(f"Created portfolio id={portfolio.id}")
            # Add a default stock
            stock = PortfolioStock(
                portfolio_id=portfolio.id,
                ticker='AAPL',
                shares=5,
                purchase_price=150.0,
                purchase_date=datetime.utcnow(),
                notes='Seed stock',
            )
            db.session.add(stock)
            db.session.commit()
            log(f"Added stock AAPL to portfolio {portfolio.id}")
        except Exception as e:
            db.session.rollback()
            log(f"ERROR creating portfolio/stock: {e}")
    return created_any

if __name__ == '__main__':
    app = create_app('development')
    with app.app_context():
        changed = 0
        for email in TEST_EMAILS:
            user = User.query.filter_by(email=email).first()
            if not user:
                log(f"User not found: {email}")
                continue
            if ensure_portfolio_for_user(user):
                changed += 1
        log(f"Ensured portfolios. Users updated: {changed}")
    Path("ensure_portfolio_result.txt").write_text("\n".join(LOG), encoding="utf-8")
