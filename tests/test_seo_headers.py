import re


def test_noindex_headers_on_non_canonical_host(client):
    # Default test server host is localhost -> non-canonical
    r = client.get('/')
    # Header should be present enforcing noindex on non-canonical envs
    assert r.headers.get('X-Robots-Tag') == 'noindex, nofollow, noarchive'
    html = r.get_data(as_text=True)
    # Meta robots tag should also indicate noindex on non-canonical
    assert 'name="robots"' in html and 'noindex' in html
    # Canonical should still point at production domain
    assert 'link rel="canonical"' in html
    assert 'https://aksjeradar.trade/' in html


def test_canonical_host_has_no_noindex_and_correct_canonical(client):
    # Simulate canonical host request
    r = client.get('/', headers={'Host': 'www.aksjeradar.trade'})
    # X-Robots-Tag should not be set for canonical host
    assert 'X-Robots-Tag' not in r.headers
    html = r.get_data(as_text=True)
    # No meta robots noindex on canonical host
    assert 'name="robots" content="noindex' not in html
    # Canonical should point to production domain
    m = re.search(r'<link rel="canonical" href="([^"]+)">', html)
    assert m, 'canonical link tag missing'
    assert m.group(1).startswith('https://aksjeradar.trade/')
