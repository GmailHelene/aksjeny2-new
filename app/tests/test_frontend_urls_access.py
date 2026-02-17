import pytest
import requests

pytestmark = pytest.mark.e2e

BASE_URL = "http://localhost:5002"
USERS = {
    "demo": {"email": "demo@aksjeradar.test", "password": "demo123"},
    "paid": {"email": "helene721@gmail.com", "password": "password123"}
}

FRONTEND_URLS = [
    "/", "/analysis", "/portfolio", "/portfolio/advanced",
    "/features/analyst-recommendations", "/features/social-sentiment",
    # "/features/ai-predictions",  # deprecated
    "/market-intel", "/profile", "/notifications"
]

@pytest.fixture(params=USERS.items(), ids=lambda u: u[0])
def user_session(request):
    user_type, creds = request.param
    session = requests.Session()
    login_resp = session.post(f"{BASE_URL}/login", data=creds)
    assert login_resp.status_code == 200
    return session

@pytest.mark.parametrize("path", FRONTEND_URLS)
def test_frontend_urls_access(user_session, path):
    resp = user_session.get(BASE_URL + path)
    assert resp.status_code == 200
