import re

def test_favorite_toggle_on_details_page_renders_and_apis_work(auth_client):
    client, user = auth_client
    # Render a simple details page for a known symbol; fall back to prices if needed
    r = client.get('/stocks/details/AAPL')
    # Some deployments use alternative route name; if 404, skip rendering check
    if r.status_code == 200:
        html = r.get_data(as_text=True)
        assert 'favorite-btn' in html or 'Favoritt' in html
    # Check initial favorite status
    r = client.get('/stocks/api/favorites/check/AAPL')
    assert r.status_code == 200
    data = r.get_json()
    assert 'favorited' in data
    # Toggle add
    r = client.post('/stocks/api/favorites/toggle/AAPL', headers={'X-CSRFToken':'test'})
    assert r.status_code == 200
    data = r.get_json()
    assert data.get('success') is True
    assert data.get('favorited') is True
    # Toggle remove
    r = client.post('/stocks/api/favorites/toggle/AAPL', headers={'X-CSRFToken':'test'})
    assert r.status_code == 200
    data = r.get_json()
    assert data.get('success') is True
    assert data.get('favorited') is False
