def test_investor_overview_route(auth_client):
    client_authed, user = auth_client
    resp = client_authed.get('/investor/')
    assert resp.status_code == 200
    html = resp.get_data(as_text=True)
    assert 'Plattformoversikt' in html
    resp2 = client_authed.get('/investor/overview')
    assert resp2.status_code == 200
    html2 = resp2.get_data(as_text=True)
    assert 'demo-modus' not in html2.lower()
    assert 'Plattformoversikt' in html2
