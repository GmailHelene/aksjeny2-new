import time
import pytest
from app import create_app, db
from app.models.user import User
from app.models.forum import ForumPost


@pytest.fixture
def app_instance():
    app = create_app('testing')
    with app.app_context():
        db.create_all()
        user = User(email='forumapijson@example.com', username='forumapijson', password='pass')
        db.session.add(user)
        db.session.commit()
        # Seed posts
        posts = [
            ('Alpha discussion', 'Talking about AAPL and growth'),
            ('Energy sector', 'Discussion about EQNR and oil prices'),
            ('Tech landscape', 'Content mentioning MSFT and NVDA advances'),
        ]
        for title, content in posts:
            p = ForumPost(title=title, content=content, user_id=user.id, author_id=user.id)
            db.session.add(p)
        db.session.commit()
    yield app


@pytest.fixture
def client(app_instance):
    return app_instance.test_client()


def test_api_search_empty_query(client):
    r = client.get('/forum/api/search?q=')
    assert r.status_code == 200
    data = r.get_json()
    assert data['success'] is True
    assert data['results'] == []
    assert data['data_source'] == 'EMPTY_QUERY'
    assert data['cache_hit'] is False


def test_api_search_normal_and_cache(client):
    r1 = client.get('/forum/api/search?q=Alpha')
    assert r1.status_code == 200
    d1 = r1.get_json()
    assert d1['success'] is True
    assert d1['cache_hit'] is False  # first fetch should be DB
    assert d1['data_source'] == 'DB'
    assert d1['data_points'] >= 1
    # Second request should be cache hit
    r2 = client.get('/forum/api/search?q=Alpha')
    d2 = r2.get_json()
    assert d2['success'] is True
    assert d2['cache_hit'] is True
    assert d2['data_source'] == 'CACHE'


def test_api_search_sanitization_and_trim(client):
    # Overly long plus invalid chars
    query = 'A' * 120 + '--DROP TABLE'
    r = client.get(f'/forum/api/search?q={query}')
    assert r.status_code == 200
    d = r.get_json()
    assert d['success'] is True
    # Should not raise error and should return deterministic fields
    for key in ['success', 'query', 'results', 'data_points', 'cache_hit', 'data_source', 'authenticated']:
        assert key in d


def test_api_search_rate_limit(client):
    # Perform many rapid queries to trigger limiter (31st should fail)
    last = None
    for i in range(31):
        last = client.get('/forum/api/search?q=Alpha')
    data = last.get_json()
    # Expect rate limited on final request
    assert data['success'] is False
    assert data['error'] == 'rate_limited'
    assert data['data_source'] == 'RATE_LIMIT'
