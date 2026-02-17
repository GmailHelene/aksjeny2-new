from app import create_app
from app.extensions import db
from app.models.strategy import Strategy
from app.models.strategy_version import StrategyVersion
from flask_login import AnonymousUserMixin

app = create_app()

with app.app_context():
    # Try to create tables if using sqlite (fallback); ignore errors for PG
    try:
        db.create_all()
    except Exception as e:
        print('Skipping create_all (likely PG):', e)

    # Ensure a user exists (pick first user)
    from app.models.user import User
    user = User.query.first()
    if not user:
        # Create a lightweight local user (works only if sqlite fallback) else abort
        user = User(email='test_strategy_user@example.com', username='tester')
        user.set_password('password123')
        db.session.add(user)
        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            print('Could not create user:', e)

    if not user:
        print('No user available; aborting')
    else:
        strat = Strategy.query.filter_by(user_id=user.id).first()
        if not strat:
            strat = Strategy(user_id=user.id, name='Test Strategy', buy_rules={'rsi': '<30'}, sell_rules={'rsi': '>70'}, risk_rules={'stop_loss': 0.1})
            db.session.add(strat)
            db.session.commit()
            # Manually create initial version if not created by route
            if not StrategyVersion.query.filter_by(strategy_id=strat.id, version=1).first():
                v = StrategyVersion(strategy_id=strat.id, user_id=user.id, version=1, name=strat.name, buy_rules=strat.buy_rules, sell_rules=strat.sell_rules, risk_rules=strat.risk_rules)
                db.session.add(v)
                db.session.commit()
        client = app.test_client()
        # Fake login by setting user_id in session
        with client.session_transaction() as sess:
            sess['_user_id'] = str(user.id)
        resp = client.get(f"/analysis/api/strategies/{strat.id}/versions")
        print('Status:', resp.status_code)
        print(resp.get_json())
