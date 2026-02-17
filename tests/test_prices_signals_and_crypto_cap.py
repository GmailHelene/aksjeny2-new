import re


def test_prices_page_signals_and_marketcap(client):
    # Render the prices page
    resp = client.get('/stocks/prices')
    assert resp.status_code == 200
    html = resp.data.decode('utf-8')

    # Check that signal badges do not display raw 'N/A' text; allow em dash or specific labels
    assert '>' + 'N/A' + '<' not in html  # we render '—' when missing

    # Narrow to crypto tab content by splitting around the id="crypto" marker
    crypto_split = html.split('id="crypto"')
    assert len(crypto_split) >= 2
    tail = crypto_split[1]
    # Look only within the first table after crypto tab marker
    table_seg = tail.split('</table>', 1)[0]

    # In crypto rows, market cap cell should not show explicit zero like '$0M' (allow numbers containing '0M' as part of larger value)
    assert '$0M' not in table_seg

    # If there is a numeric millions value, it should be either '—' or a positive number ending with M
    for m in re.finditer(r"\$([0-9][0-9,]*)M", table_seg):
        num = m.group(1).replace(',', '')
        assert float(num) > 0.0
