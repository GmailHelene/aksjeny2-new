import pytest
from conftest import auth_client

def test_compare_no_demo_prices(auth_client):
    client, user = auth_client
    resp = client.get('/stocks/compare?symbols=EQNR.OL,DNB.OL,TEL.OL')
    assert resp.status_code in (200, 400, 404)
    body = resp.get_data(as_text=True)
    # Tidligere hardkodede tall skal ikke forekomme som eksakt streng
    forbidden_exact = ['270.50', '185.20', '135.40', '485.00']
    for f in forbidden_exact:
        assert f not in body
    # Ingen tekst 'Simplified demo data'
    assert 'Simplified demo data' not in body
