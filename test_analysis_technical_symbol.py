import pytest
from app import create_app, db
from app.models.user import User

@pytest.fixture
def app_instance():
    app = create_app('testing')
    with app.app_context():
        db.create_all()
        u = User(email='analyst@example.com', username='analyst', password='pass')
        db.session.add(u)
        db.session.commit()
    yield app

@pytest.fixture
def auth_client(app_instance):
    client = app_instance.test_client()
    with app_instance.app_context():
        user = User.query.filter_by(email='analyst@example.com').first()
        with client.session_transaction() as sess:
            sess['_user_id'] = str(user.id)
            sess['_fresh'] = True
    return client

def test_technical_symbol_path_redirect_free(auth_client):
    # Direct path form should render analysis for symbol
    r = auth_client.get('/analysis/technical/EQNR.OL')
    assert r.status_code == 200
    body = r.get_data(as_text=True)
    assert 'EQNR.OL' in body
    # Should not show generic search prompt marker
    assert 'show_search_prompt' not in body

def test_technical_symbol_query(auth_client):
    r = auth_client.get('/analysis/technical?symbol=EQNR.OL')
    assert r.status_code == 200
    assert 'EQNR.OL' in r.get_data(as_text=True)

def test_technical_symbol_json(auth_client):
    r = auth_client.get('/analysis/technical?symbol=EQNR.OL&format=json')
    assert r.status_code == 200
    data = r.get_json()
    assert data['success'] is True
    assert data['symbol'] == 'EQNR.OL'
    assert 'data' in data
