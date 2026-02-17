"""
Error handling middleware for production stability
"""
import logging
from flask import request, jsonify, render_template
from werkzeug.exceptions import HTTPException

logger = logging.getLogger(__name__)

def handle_http_exception(e):
    """Handle HTTP exceptions with proper fallbacks"""
    
    # Log the error with request context
    logger.error(f"HTTP {e.code} error on {request.url}: {e}")
    
    # Handle specific error codes
    if e.code == 404:
        if request.path.startswith('/api/'):
            return jsonify({
                'error': 'Endpoint not found',
                'status_code': 404,
                'path': request.path
            }), 404
        else:
            return render_template('errors/404.html'), 404
            
    elif e.code == 500:
        if request.path.startswith('/api/'):
            return jsonify({
                'error': 'Internal server error',
                'status_code': 500,
                'path': request.path
            }), 500
        else:
            return render_template('errors/500.html'), 500
            
    elif e.code == 429:
        # Rate limit exceeded
        return jsonify({
            'error': 'Rate limit exceeded',
            'status_code': 429,
            'retry_after': 60
        }), 429
    
    # Default error handling
    return str(e), e.code

def handle_general_exception(e):
    """Handle general exceptions"""
    logger.error(f"Unhandled exception on {request.url}: {e}", exc_info=True)
    
    if request.path.startswith('/api/'):
        return jsonify({
            'error': 'Internal error occurred',
            'status_code': 500
        }), 500
    else:
        return render_template('errors/500.html'), 500

def register_error_handlers(app):
    """Register error handlers with Flask app"""
    
    # Register for specific HTTP exceptions
    for code in [400, 401, 403, 404, 405, 429, 500, 502, 503]:
        app.register_error_handler(code, handle_http_exception)
    
    # Register for general exceptions
    app.register_error_handler(Exception, handle_general_exception)
