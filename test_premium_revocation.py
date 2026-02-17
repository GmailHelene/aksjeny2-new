import pytest
from app.models.user import User

def test_eirik_not_premium(auth_client, session):
    client, user = auth_client
    # Create Eirik user explicitly
    eirik = User(username='Eirik', email='eirik@example.com')
    if hasattr(eirik, 'set_password'):
        eirik.set_password('Secret123!')
    session.add(eirik)
    session.commit()
    # Log in as Eirik
    with client.session_transaction() as sess:
        sess['_user_id'] = str(eirik.id)
        sess['_fresh'] = True
    # Access a premium-protected endpoint (choose strategies list if decorated)
    r = client.get('/analysis/api/strategies')
    # Expect denial; depending on implementation could be 403 or JSON success false.
    if r.status_code == 200:
        data = r.get_json() or {}
        # If success true this would indicate premium bypass which should not happen
        assert not data.get('success') or data.get('strategies') == [], 'Eirik should not have premium strategy access'
    else:
        assert r.status_code in (302,401,403)
