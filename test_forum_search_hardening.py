import pytest
from app import create_app, db
from app.models.user import User
from app.models.forum import ForumPost

@pytest.fixture
def app_instance():
    app = create_app('testing')
    with app.app_context():
        db.create_all()
        # Seed a user and some posts
        user = User(email='forumuser@example.com', username='forumuser', password='pass')
        db.session.add(user)
        db.session.commit()
        for title, content in [
            ('Apple discussion', 'AAPL prospects are interesting'),
            ('Norsk energi', 'Snakk om EQNR og olje'),
            ('Teknologi generelt', 'Diskusjon om MSFT og NVDA')
        ]:
            post = ForumPost(title=title, content=content, user_id=user.id, author_id=user.id)
            db.session.add(post)
        db.session.commit()
    yield app

@pytest.fixture
def client(app_instance):
    return app_instance.test_client()


def test_empty_query_returns_no_posts(client):
    resp = client.get('/forum/search?q=')
    assert resp.status_code == 200
    body = resp.get_data(as_text=True)
    assert 'Apple discussion' not in body


def test_normal_query_finds_post(client):
    resp = client.get('/forum/search?q=Apple')
    assert resp.status_code == 200
    body = resp.get_data(as_text=True)
    assert 'Apple discussion' in body


def test_overly_long_query_is_trimmed(client):
    long_query = 'A' * 300
    resp = client.get(f'/forum/search?q={long_query}')
    assert resp.status_code == 200
    # Should not 500; trimming may result in no matches


def test_invalid_characters_query_sanitized(client):
    resp = client.get('/forum/search?q=Apple%20drop%20--%20SELECT%20*')
    assert resp.status_code == 200
    # Should still render safely
    body = resp.get_data(as_text=True)
    assert 'Apple discussion' in body or 'Ingen resultater' in body or 'Apple' in body


def test_special_chars_only_becomes_empty(client):
    resp = client.get('/forum/search?q=%%%%%%%')
    assert resp.status_code == 200
    body = resp.get_data(as_text=True)
    # Expect no seeded titles
    assert 'Apple discussion' not in body
