import json

def test_strategy_create_rate_limit(auth_client):
    client, user = auth_client
    payload = {"name":"RLTest","buy":{},"sell":{},"risk":{}}
    # Hit limit (30 per 60s). Create 30 should succeed, 31st should 429.
    success = 0
    for i in range(30):
        p = payload.copy()
        p['name'] = f"RLTest{i}"
        r = client.post('/analysis/api/strategies', data=json.dumps(p), content_type='application/json')
        assert r.status_code in (200,201), f"Unexpected status {r.status_code} at iteration {i}"
        if r.status_code in (200,201):
            success += 1
    assert success == 30
    # 31st attempt
    p['name'] = "RLTest_exceed"
    r = client.post('/analysis/api/strategies', data=json.dumps(p), content_type='application/json')
    # Allow for rare race where earlier failures reduce count; require 429 OR success if decorator not applied (will fail test if not limited)
    assert r.status_code == 429, f"Expected 429 after exceeding limit, got {r.status_code}"
    data = r.get_json()
    assert data and data.get('error') == 'Rate limit'


def test_strategy_update_rate_limit(auth_client):
    client, user = auth_client
    # Create one strategy
    r = client.post('/analysis/api/strategies', data=json.dumps({"name":"UpdBase","buy":{},"sell":{},"risk":{}}), content_type='application/json')
    sid = r.get_json()['id']
    # Perform 15 updates then verify still under limit (sanity) and then burst to exceed
    body = json.dumps({"name":"UpdBase"})
    for i in range(15):
        up = client.patch(f'/analysis/api/strategies/{sid}', data=body, content_type='application/json')
        assert up.status_code == 200
    # Rapid additional 50 updates to cross 60 threshold
    exceeded = False
    for i in range(50):
        up = client.patch(f'/analysis/api/strategies/{sid}', data=body, content_type='application/json')
        if up.status_code == 429:
            exceeded = True
            assert up.get_json().get('error') == 'Rate limit'
            break
    assert exceeded, "Did not hit rate limit after burst updates"
