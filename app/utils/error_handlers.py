"""
Error handlers and error boundary components
"""
from functools import wraps
from flask import render_template, jsonify, request, current_app
from werkzeug.exceptions import HTTPException
import traceback


def handle_analysis_error(error_type: str = 'general'):
    """Decorator for handling errors in analysis routes"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except HTTPException:
                # Re-raise HTTP exceptions (404, 403, etc.)
                raise
            except Exception as e:
                current_app.logger.error(f"Analysis error in {func.__name__}: {str(e)}")
                current_app.logger.error(traceback.format_exc())
                
                # Determine error context
                error_context = {
                    'data_source': 'Kunne ikke hente data fra ekstern kilde',
                    'calculation': 'Feil ved beregning av analyse',
                    'ai': 'AI-tjenesten er midlertidig utilgjengelig',
                    'general': 'En uventet feil oppstod'
                }
                
                error_message = error_context.get(error_type, error_context['general'])
                
                # Return JSON for API endpoints
                if request.path.startswith('/api/'):
                    return jsonify({
                        'success': False,
                        'error': error_message,
                        'details': str(e) if current_app.debug else None
                    }), 500
                
                # Return error template for web pages
                return render_template('analysis/error.html',
                                     error_message=error_message,
                                     error_details=str(e) if current_app.debug else None,
                                     back_url=request.referrer or '/analysis'), 500
        
        return wrapper
    return decorator


class DataError(Exception):
    """Custom exception for data-related errors"""
    pass


class CalculationError(Exception):
    """Custom exception for calculation errors"""
    pass


class ExternalAPIError(Exception):
    """Custom exception for external API errors"""
    pass
