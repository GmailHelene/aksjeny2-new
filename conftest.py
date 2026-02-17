# Root-level conftest to expose fixtures to tests located at repository root.
# Re-export everything from tests/conftest.py
import os
import tempfile
import warnings
import pytest
from app import create_app, db
from config import TestingConfig as BaseTestingConfig

# Suppress noisy third-party DeprecationWarnings (distutils/eventlet)
warnings.filterwarnings('ignore', category=DeprecationWarning, message=r'distutils Version classes are deprecated')
warnings.filterwarnings('ignore', category=DeprecationWarning, message=r'.*distutils\.version\.LooseVersion.*')
warnings.filterwarnings('ignore', category=DeprecationWarning, module=r'eventlet.support.*')

class TestingConfig(BaseTestingConfig):
	_temp_db_path = None
	@classmethod
	def init_temp_db(cls):
		if cls._temp_db_path is None:
			fd, path = tempfile.mkstemp(prefix='test_db_root_', suffix='.sqlite')
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
	"""Provide a clean database session per test using the global db.session.

	We avoid deprecated create_scoped_session (Flask-SQLAlchemy 3.x) and instead
	manually truncate tables after each test for isolation.
	"""
	with app.app_context():
		# Ensure strategy tables exist if not created by create_all earlier (idempotent)
		try:
			from app.models.strategy import Strategy  # noqa: F401
			from app.models.strategy_version import StrategyVersion  # noqa: F401
			db.create_all()
		except Exception:
			pass
		yield db.session
		# Cleanup: delete all rows (simple & deterministic for small test datasets)
		for table in reversed(db.metadata.sorted_tables):
			try:
				db.session.execute(table.delete())
			except Exception:
				pass
		db.session.commit()
		# Reset in-memory strategy rate limiter store if present
		try:
			from app.routes.analysis import strategy_rate_limit
			if hasattr(strategy_rate_limit, '_store'):
				strategy_rate_limit._store.clear()
		except Exception:
			pass

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
	# Trigger a benign request so flask-login loads current_user for subsequent tests
	try:
		client.get('/')  # root route should exist; ignore response
	except Exception:
		pass
	return client, user
