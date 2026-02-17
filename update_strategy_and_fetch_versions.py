from app import create_app
from app.extensions import db
from app.models.strategy import Strategy
from app.models.strategy_version import StrategyVersion

app = create_app()

with app.app_context():
    client = app.test_client()
    from app.models.user import User
    user = User.query.first()
    if not user:
        print('No user to test with')
    else:
        strat = Strategy.query.filter_by(user_id=user.id).first()
        if not strat:
            print('No strategy to update')
        else:
            with client.session_transaction() as sess:
                sess['_user_id'] = str(user.id)
                sess['_fresh'] = True
            # Perform PATCH to create new version
            patch_payload = {
                'name': strat.name + ' v2',
                'buy': {**(strat.buy_rules or {}), 'sma': '50>200'},
                'sell': strat.sell_rules or {},
                'risk': strat.risk_rules or {}
            }
            r = client.patch(
                f"/analysis/api/strategies/{strat.id}",
                json=patch_payload,
                headers={'Accept': 'application/json', 'X-CSRFToken': 'test'}
            )
            print('Patch status:', r.status_code, r.get_json())
            rv = client.get(f"/analysis/api/strategies/{strat.id}/versions")
            print('Versions after patch:', rv.status_code, rv.get_json())
