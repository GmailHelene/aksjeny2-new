"""
API module for Aksjeradar
"""
from flask import Blueprint

api = Blueprint('api', __name__, url_prefix='/api')

# Import routes when they're ready
try:
    from . import routes
except ImportError:
    pass  # Routes not ready yet
