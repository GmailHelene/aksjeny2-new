from app import create_app, db
from app.models import User
import re

app = create_app('development')

BANNER_SNIPPET = 'Begrenset modus:'

with app.app_context():
    user = User.query.filter_by(email='test@example.com').first()
    if not user:
        print('Premium test user missing (test@example.com)')
        raise SystemExit(1)

with app.test_client() as client, app.app_context():
    # Get login page for CSRF
    login_page = client.get('/login')
    m = re.search(r'name="csrf_token"[^>]*value="([^"]+)"', login_page.data.decode())
    token = m.group(1) if m else None
    if not token:
        print('Failed to extract CSRF token on login')
        raise SystemExit(2)
    resp = client.post('/auth/login', data={'csrf_token': token, 'email': 'test@example.com', 'password': 'testpassword'}, follow_redirects=True)
    if resp.status_code not in (200,302):
        print('Login failed status', resp.status_code)
        raise SystemExit(3)
    # Fetch portfolio page
    port = client.get('/portfolio/')
    html = port.data.decode()
    if BANNER_SNIPPET in html:
        print('FAIL: Demo banner visible for premium user')
        # Provide short context snippet
        start = html.index(BANNER_SNIPPET)-40 if BANNER_SNIPPET in html else 0
        print('Context:', html[start:start+160])
        raise SystemExit(4)
    print('OK: Demo banner is NOT visible for premium user on /portfolio/')
