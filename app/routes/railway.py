"""
Railway deployment optimization module
"""
from flask import Blueprint, jsonify, request, current_app
from datetime import datetime
import os
import sys
import platform
import psutil

# Create blueprint
railway_bp = Blueprint('railway', __name__, url_prefix='/railway')

@railway_bp.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint for Railway"""
    # Get system information
    system_info = {
        'system': platform.system(),
        'python_version': sys.version,
        'memory_used_percent': psutil.virtual_memory().percent,
        'cpu_percent': psutil.cpu_percent(interval=0.1),
        'timestamp': datetime.now().isoformat(),
        'environment': os.environ.get('FLASK_ENV', 'production')
    }
    
    # Get application information
    app_info = {
        'app_name': current_app.name,
        'debug_mode': current_app.debug,
        'config_keys': list(current_app.config.keys())
    }
    
    # Get cache version if available
    try:
        from app.cache_version import CACHE_BUST_VERSION
        cache_version = CACHE_BUST_VERSION
    except ImportError:
        cache_version = "unknown"
    
    response = {
        'status': 'healthy',
        'system': system_info,
        'application': app_info,
        'cache_version': cache_version
    }
    
    return jsonify(response)

@railway_bp.route('/optimize', methods=['POST'])
def optimize():
    """Optimize application for Railway deployment"""
    # Force garbage collection
    import gc
    gc.collect()
    
    # Clear all caches
    try:
        from app.services.realtime_data_service import get_real_time_service
        realtime_service = get_real_time_service()
        if realtime_service:
            realtime_service.clear_cache()
    except Exception as e:
        current_app.logger.warning(f"Failed to clear realtime service cache: {str(e)}")
    
    # Generate new cache version
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    try:
        with open(os.path.join(current_app.root_path, 'cache_version.py'), 'w') as f:
            f.write(f"CACHE_BUST_VERSION = '{timestamp}'\n")
    except Exception as e:
        current_app.logger.warning(f"Failed to update cache version: {str(e)}")
    
    return jsonify({
        'status': 'success',
        'optimizations_applied': ['garbage_collection', 'cache_cleared', 'cache_version_updated'],
        'new_cache_version': timestamp,
        'timestamp': datetime.now().isoformat()
    })
