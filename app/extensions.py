from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect
from flask_mailman import Mail
from flask_socketio import SocketIO
from flask_caching import Cache

db = SQLAlchemy(session_options={"expire_on_commit": False})
login_manager = LoginManager()
csrf = CSRFProtect()
mail = Mail()
socketio = SocketIO()
cache = Cache()

login_manager.login_view = 'main.login'