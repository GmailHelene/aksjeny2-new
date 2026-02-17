import os
import tempfile
import pytest
from app import create_app, db
from config import TestingConfig as BaseTestingConfig

class TestingConfig(BaseTestingConfig):
    _temp_db_path = None
    @classmethod
    def init_temp_db(cls):
        if cls._temp_db_path is None:
            fd, path = tempfile.mkstemp(prefix='test_db_sub_', suffix='.sqlite')
            os.close(fd)
            cls._temp_db_path = path
        return cls._temp_db_path

TestingConfig.SQLALCHEMY_DATABASE_URI = f"sqlite:///{TestingConfig.init_temp_db()}"
TestingConfig.TESTING = True
TestingConfig.WTF_CSRF_ENABLED = False
TestingConfig.SERVER_NAME = 'localhost'

@pytest.fixture(scope='session')
def app():
    app = create_app(TestingConfig)
    with app.app_context():
        db.create_all()
    yield app
    with app.app_context():
        db.session.remove()
        db.drop_all()
    try:
        if TestingConfig._temp_db_path and os.path.exists(TestingConfig._temp_db_path):
            os.remove(TestingConfig._temp_db_path)
    except Exception:
        pass

@pytest.fixture(scope='function')
def session(app):
    with app.app_context():
        yield db.session
        for table in reversed(db.metadata.sorted_tables):
            try:
                db.session.execute(table.delete())
            except Exception:
                pass
        db.session.commit()

@pytest.fixture(scope='function')
def client(app, session):
    return app.test_client()

@pytest.fixture
def user_factory(session):
    from app.models.user import User
    def factory(**kwargs):
        username = kwargs.pop('username', 'user')
        email = kwargs.pop('email', f"{username}@example.com")
        password = kwargs.pop('password', 'Pass1234!')
        u = User(username=username, email=email, **kwargs)
        if hasattr(u, 'set_password'):
            u.set_password(password)
        session.add(u)
        session.commit()
        return u
    return factory

@pytest.fixture
def auth_client(client, user_factory):
    user = user_factory(username='authuser')
    with client.session_transaction() as sess:
        sess['_user_id'] = str(user.id)
        sess['_fresh'] = True
    try:
        client.get('/')
    except Exception:
        pass
    return client, user

def pytest_collection_modifyitems(config, items):
    """Skip integration service thread tests when SKIP_INTEGRATION_THREADS env var is set."""
    if os.getenv('SKIP_INTEGRATION_THREADS') not in ('1','true','True'):
        return
    skip_marker = pytest.mark.skip(reason="SKIP_INTEGRATION_THREADS active")
    for item in items:
        # Heuristic: mark tests that reference 'integration' in nodeid or file name
        if 'integration' in item.nodeid.lower() or 'test_integration_services' in item.nodeid:
            item.add_marker(skip_marker)
