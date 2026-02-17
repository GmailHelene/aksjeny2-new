import json
import pytest
from app.extensions import db
from app.models.strategy import Strategy
from app.models.strategy_version import StrategyVersion

@pytest.fixture
def strategy(auth_client):
    client, user = auth_client
    strat = Strategy(user_id=user.id, name='TestStrat', buy_rules={'i':'sma'}, sell_rules={'i':'ema'}, risk_rules={'sl':5})
    db.session.add(strat)
    db.session.commit()
    # initial version should have been created by logic (if present); if not create manually for safety
    if not StrategyVersion.query.filter_by(strategy_id=strat.id).first():
        v = StrategyVersion(strategy_id=strat.id, user_id=user.id, version=1, name=strat.name,
                            buy_rules=strat.buy_rules, sell_rules=strat.sell_rules, risk_rules=strat.risk_rules)
        db.session.add(v)
        db.session.commit()
    return strat

def test_versions_list_initial(auth_client, strategy):
    client, user = auth_client
    resp = client.get(f"/analysis/api/strategies/{strategy.id}/versions")
    data = resp.get_json()
    assert resp.status_code == 200
    assert data['success'] is True
    assert len(data['versions']) >= 1
    assert data['versions'][0]['strategy_id'] == strategy.id

def test_update_creates_new_version(auth_client, strategy):
    client, user = auth_client
    patch_payload = {'name':'TestStrat2','buy':{'indicator':'rsi','condition':'above','value':70},'sell':{'indicator':'macd','condition':'below','value':0},'risk':{'stop_loss':4,'take_profit':9}}
    resp = client.patch(f"/analysis/api/strategies/{strategy.id}", data=json.dumps(patch_payload), content_type='application/json')
    assert resp.status_code in (200,201)
    rj = resp.get_json()
    assert rj['success'] is True
    versions = client.get(f"/analysis/api/strategies/{strategy.id}/versions").get_json()['versions']
    # Ensure the latest version reflects new name
    assert any(v['name']=='TestStrat2' for v in versions)
    # Versions should be ordered desc by version number
    version_numbers = [v['version'] for v in versions]
    assert version_numbers == sorted(version_numbers, reverse=True)

def test_rollback_creates_new_head(auth_client, strategy):
    client, user = auth_client
    # Create an update to have at least 2 versions
    client.patch(f"/analysis/api/strategies/{strategy.id}", data=json.dumps({'name':'AltName'}), content_type='application/json')
    versions_before = client.get(f"/analysis/api/strategies/{strategy.id}/versions").get_json()['versions']
    assert len(versions_before) >= 2
    target = versions_before[-1]  # oldest version
    rollback_resp = client.post(f"/analysis/api/strategies/{strategy.id}/rollback/{target['id']}")
    rj = rollback_resp.get_json()
    assert rollback_resp.status_code == 200
    assert rj['success'] is True
    new_versions = client.get(f"/analysis/api/strategies/{strategy.id}/versions").get_json()['versions']
    assert len(new_versions) == len(versions_before) + 1
    # New head version number should be previous max + 1
    prev_max = max(v['version'] for v in versions_before)
    new_max = max(v['version'] for v in new_versions)
    assert new_max == prev_max + 1
    # Strategy name after rollback should equal target name
    assert rj['strategy']['name'] == target['name']

def test_versions_unauthorized_access(client):
    # No auth session: expect redirect or 401 depending on auth decorator config
    resp = client.get('/analysis/api/strategies/9999/versions')
    # Accept either 302 redirect to login or 401/403 JSON depending on configuration
    assert resp.status_code in (302,401,403)
