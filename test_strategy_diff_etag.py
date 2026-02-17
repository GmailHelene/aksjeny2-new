import json

def test_diff_checksum_equal(auth_client):
    client, user = auth_client
    # Create strategy
    r = client.post('/analysis/api/strategies', data=json.dumps({"name":"DiffTest","buy":{},"sell":{},"risk":{}}), content_type='application/json')
    sid = r.get_json()['id']
    # Patch with real change
    client.patch(f'/analysis/api/strategies/{sid}', data=json.dumps({"name":"DiffTest2"}), content_type='application/json')
    # Get versions list with checksum
    versions = client.get(f'/analysis/api/strategies/{sid}/versions?include_checksum=1').get_json()['versions']
    assert len(versions) >= 2
    latest = versions[0]
    # Diff identical (latest vs itself)
    d = client.get(f"/analysis/api/strategies/{sid}/diff/{latest['version']}/{latest['version']}").get_json()
    assert d['success'] and d['identical'] and d['checksum_equal']


def test_strategy_etag_304(auth_client):
    client, user = auth_client
    r = client.post('/analysis/api/strategies', data=json.dumps({"name":"ETagTest","buy":{},"sell":{},"risk":{}}), content_type='application/json')
    sid = r.get_json()['id']
    first = client.get(f'/analysis/api/strategies/{sid}')
    etag = first.headers.get('ETag')
    assert etag, 'Expected ETag header'
    # Conditional GET
    second = client.get(f'/analysis/api/strategies/{sid}', headers={'If-None-Match': etag})
    assert second.status_code == 304
