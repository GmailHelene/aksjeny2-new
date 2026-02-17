"""
Safe import utilities to handle missing dependencies gracefully
"""
import logging

logger = logging.getLogger(__name__)

def safe_import_blueprint(module_path, blueprint_name, package=None):
    """
    Safely import a blueprint, handling missing dependencies
    """
    try:
        from importlib import import_module
        module = import_module(module_path, package=package)
        blueprint = getattr(module, blueprint_name)
        return blueprint, None
    except ImportError as e:
        logger.warning(f"Could not import {blueprint_name} from {module_path}: {e}")
        return None, str(e)
    except Exception as e:
        logger.error(f"Error importing {blueprint_name} from {module_path}: {e}")
        return None, str(e)

def create_fallback_blueprint(name, import_prefix='/fallback'):
    """
    Create a fallback blueprint for when the real one can't be imported
    """
    from flask import Blueprint, jsonify
    
    bp = Blueprint(f'fallback_{name}', __name__, url_prefix=import_prefix)
    
    @bp.route('/status')
    def status():
        return jsonify({
            'status': 'fallback',
            'message': f'Blueprint {name} is using fallback implementation',
            'original_error': 'Import failed'
        })
    
    return bp
