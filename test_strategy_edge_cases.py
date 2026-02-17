import json
import pytest
from app.extensions import db
from app.models.strategy import Strategy
from app.models.strategy_version import StrategyVersion

@pytest.fixture
def base_strategy(auth_client):
    client, user = auth_client
    s = Strategy(user_id=user.id, name='EdgeOne', buy_rules={'a':1}, sell_rules={'b':2}, risk_rules={'sl':5})
    db.session.add(s); db.session.commit()
    # Initial version
    v = StrategyVersion(strategy_id=s.id, user_id=user.id, version=1, name=s.name, buy_rules=s.buy_rules, sell_rules=s.sell_rules, risk_rules=s.risk_rules)
    db.session.add(v); db.session.commit()
    return s

def test_duplicate_name_rejected(auth_client, base_strategy):
    client, user = auth_client
    payload = {'name':'EdgeOne','buy':{'indicator':'sma','condition':'above','value':10},'sell':{'indicator':'ema','condition':'below','value':5},'risk':{'stop_loss':4,'take_profit':9}}
    r = client.post('/analysis/api/strategies', data=json.dumps(payload), content_type='application/json')
    assert r.status_code in (400,409)
    js = r.get_json() or {}
    assert js.get('success') is False


def test_long_name_rejected(auth_client):
    client, user = auth_client
    long_name = 'X'*170
    payload = {'name':long_name,'buy':{'indicator':'sma','condition':'above','value':10},'sell':{'indicator':'ema','condition':'below','value':5},'risk':{'stop_loss':4,'take_profit':9}}
    r = client.post('/analysis/api/strategies', data=json.dumps(payload), content_type='application/json')
    assert r.status_code in (400,422)


def test_unchanged_update_skips_snapshot(auth_client, base_strategy):
    client, user = auth_client
    versions_before = client.get(f'/analysis/api/strategies/{base_strategy.id}/versions').get_json()['versions']
    r = client.patch(f'/analysis/api/strategies/{base_strategy.id}', data=json.dumps({'name':'EdgeOne'}), content_type='application/json')
    assert r.status_code == 200
    js = r.get_json() or {}
    assert js.get('message') == 'Ingen endringer'
    versions_after = client.get(f'/analysis/api/strategies/{base_strategy.id}/versions').get_json()['versions']
    assert len(versions_after) == len(versions_before)


def test_invalid_rollback_id(auth_client, base_strategy):
    client, user = auth_client
    bad_id = 999999
    r = client.post(f'/analysis/api/strategies/{base_strategy.id}/rollback/{bad_id}')
    assert r.status_code in (404,400)
    js = r.get_json() or {}
    assert js.get('success') is False
