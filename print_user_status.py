#!/usr/bin/env python3
from pathlib import Path
from app import create_app
from app.models.user import User
from app.extensions import db

lines = []

def print_status(email: str):
    user = User.query.filter_by(email=email).first()
    if not user:
        lines.append(f"User {email}: NOT FOUND")
        return
    lines.append(
        f"User {email}: id={user.id}, admin={getattr(user,'is_admin',False)}, has_subscription={getattr(user,'has_subscription',False)}, type={getattr(user,'subscription_type',None)}"
    )
    # portfolios
    try:
        from app.models.portfolio import Portfolio, PortfolioStock
        ports = Portfolio.query.filter_by(user_id=user.id).all()
        lines.append(f"  Portfolios: {len(ports)}")
        if ports:
            first = ports[0]
            stocks = PortfolioStock.query.filter_by(portfolio_id=first.id).all()
            lines.append(f"  First portfolio '{first.name}' stocks: {len(stocks)}")
    except Exception as e:
        lines.append(f"  Portfolio check error: {e}")

if __name__ == '__main__':
    app = create_app('development')
    with app.app_context():
        for email in (
            'test@aksjeradar.trade',
            'investor@aksjeradar.trade',
            'testuser@aksjeradar.trade',
            'jarle@aksjeradar.trade',
            'helene721@gmail.com',
            'eirik@example.com',
        ):
            print_status(email)
    Path("print_user_status_result.txt").write_text("\n".join(lines), encoding="utf-8")
