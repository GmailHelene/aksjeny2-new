import pytest
import requests

pytestmark = pytest.mark.e2e

BASE_URL = "http://localhost:5002"
CREDENTIALS = {"email": "helene721@gmail.com", "password": "password123"}  # oppdater passord

@pytest.fixture
def client_session():
    session = requests.Session()
    resp = session.post(f"{BASE_URL}/login", data=CREDENTIALS)
    assert resp.status_code == 200
    return session

endpoints = [
    "/analysis",
    "/portfolio",
    "/portfolio/advanced",
    "/features/analyst-recommendations",
    "/features/social-sentiment",
    # "/features/ai-predictions",  # deprecated: returns 410 Gone
    "/market-intel",
    "/profile",
    "/notifications"
]

@pytest.mark.parametrize("endpoint", endpoints)
def test_all_endpoints_access(endpoint, client_session):
    resp = client_session.get(BASE_URL + endpoint)
    assert resp.status_code == 200
