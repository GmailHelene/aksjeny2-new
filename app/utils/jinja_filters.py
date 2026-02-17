"""
Custom Jinja filters for the application
"""
from datetime import datetime
from flask import Blueprint
import json

jinja_filters = Blueprint('filters', __name__)

@jinja_filters.app_template_filter('fromjson')
def fromjson(value):
    """Convert JSON string to Python object"""
    if not value:
        return []
    try:
        return json.loads(value)
    except (json.JSONDecodeError, TypeError):
        return []

@jinja_filters.app_template_filter('timeago')
def timeago(dt):
    """Convert datetime to human readable time ago string"""
    if not dt:
        return "Ukjent tid"
    
    now = datetime.utcnow()
    diff = now - dt
    
    if diff.days > 7:
        return f"{diff.days} dager siden"
    elif diff.days > 0:
        return f"{diff.days} dag{'er' if diff.days > 1 else ''} siden"
    elif diff.seconds > 3600:
        hours = diff.seconds // 3600
        return f"{hours} time{'r' if hours > 1 else ''} siden"
    elif diff.seconds > 60:
        minutes = diff.seconds // 60
        return f"{minutes} minutt{'er' if minutes > 1 else ''} siden"
    else:
        return "Nå nettopp"
