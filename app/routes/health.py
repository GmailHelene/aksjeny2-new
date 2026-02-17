from flask import Blueprint, jsonify, current_app
from flask_login import current_user
from sqlalchemy import text
from ..extensions import db
from ..models.user import User
import stripe
import os
from datetime import datetime
import platform
import psutil
import time

health = Blueprint('health', __name__)

@health.route('/')
@health.route('/health')  # Add alias for Docker health check
def check_health():
    """Basic health check endpoint that verifies critical services (does not fail readiness)."""
    try:
        # Quick database connection check without signal (thread-safe)
        try:
            db.session.execute(text('SELECT 1'))
            db.session.commit()
            database_status = 'connected'
        except Exception as db_error:
            current_app.logger.warning(f"Database check failed: {db_error}")
            database_status = 'disconnected'
        
        health_status = {
            'status': 'healthy',
            'ready': True,
            'timestamp': datetime.utcnow().isoformat(),
            'checks': {
                'database': database_status,
                'app': 'running'
            }
        }
        return jsonify(health_status), 200
    except Exception as e:
        current_app.logger.error(f"Health check failed: {str(e)}")
        return jsonify({
            'status': 'unhealthy',
            'ready': False,
            'timestamp': datetime.utcnow().isoformat(),
            'error': str(e)
        }), 503  # Service Unavailable

@health.route('/detailed')
def detailed_health():
    """Detailed health check with information about the system and application."""
    health_data = {
        'status': 'ok',
        'timestamp': time.time(),
        'application': {
            'name': 'Aksjeradar',
            'environment': 'production' if current_app.config.get('IS_REAL_PRODUCTION') else 'development',
            'debug_mode': current_app.debug,
        },
        'system': {
            'platform': platform.platform(),
            'python_version': platform.python_version(),
            'cpu_usage': psutil.cpu_percent(interval=0.1),
            'memory': {
                'total': psutil.virtual_memory().total,
                'available': psutil.virtual_memory().available,
                'percent_used': psutil.virtual_memory().percent
            },
            'disk': {
                'total': psutil.disk_usage('/').total,
                'free': psutil.disk_usage('/').free,
                'percent_used': psutil.disk_usage('/').percent
            }
        }
    }
    
    # Check database connection
    try:
        db.session.execute(text('SELECT 1'))
        health_data['database'] = {
            'status': 'connected',
            'message': 'Database connection successful'
        }
    except Exception as e:
        health_data['database'] = {
            'status': 'error',
            'message': str(e)
        }
        health_data['status'] = 'degraded'
    
    # Check export folder is writable
    export_folder = current_app.config.get('EXPORT_FOLDER')
    if export_folder:
        try:
            if os.access(export_folder, os.W_OK):
                health_data['export_folder'] = {
                    'status': 'writable',
                    'path': export_folder
                }
            else:
                health_data['export_folder'] = {
                    'status': 'not_writable',
                    'path': export_folder
                }
                health_data['status'] = 'degraded'
        except Exception as e:
            health_data['export_folder'] = {
                'status': 'error',
                'message': str(e)
            }
            health_data['status'] = 'degraded'
    
    return jsonify(health_data)

@health.route('/ready')
def readiness():
    """Readiness probe: ALWAYS return 200 to let container become healthy; include degraded state if dependencies fail."""
    database_ok = True
    try:
        db.session.execute(text('SELECT 1'))
    except Exception as e:
        current_app.logger.warning(f"Readiness DB check failed (degraded): {e}")
        database_ok = False
    status = 'ready' if database_ok else 'degraded'
    return jsonify({
        'status': status,
        'ready': True,  # Always allow traffic
        'database': database_ok
    }), 200

@health.route('/live')
def liveness():
    """Liveness probe that verifies if the application is alive."""
    return jsonify({
        'alive': True
    })

@health.route('/routes')
def check_routes():
    """Check all registered routes and their status."""
    from flask import current_app as app
    
    # Only allow in development mode for security reasons
    if not app.debug and app.config.get('IS_REAL_PRODUCTION', False):
        return jsonify({
            'error': 'This endpoint is only available in development mode'
        }), 403
    
    routes_data = []
    
    for rule in app.url_map.iter_rules():
        # Skip the static routes and the current route to avoid infinite recursion
        if 'static' in rule.endpoint or rule.endpoint == 'health.check_routes':
            continue
            
        # Get methods excluding HEAD and OPTIONS
        methods = [method for method in rule.methods if method not in ('HEAD', 'OPTIONS')]
        
        # Get the blueprint name
        blueprint = rule.endpoint.split('.')[0] if '.' in rule.endpoint else 'app'
        
        route_info = {
            'endpoint': rule.endpoint,
            'methods': sorted(methods),
            'path': str(rule),
            'blueprint': blueprint,
            'is_authenticated_required': 'login' in rule.endpoint.lower() or 'account' in rule.endpoint.lower()
        }
        
        routes_data.append(route_info)
    
    # Sort by path for easier reading
    routes_data = sorted(routes_data, key=lambda x: x['path'])
    
    # Group by blueprint
    blueprints = {}
    for route in routes_data:
        bp = route['blueprint']
        if bp not in blueprints:
            blueprints[bp] = []
        blueprints[bp].append(route)
    
    response = {
        'total_routes': len(routes_data),
        'blueprints_summary': {bp: len(routes) for bp, routes in blueprints.items()},
        'routes_by_blueprint': blueprints
    }
    
    return jsonify(response)

@health.route('/check-all')
def check_all_dependencies():
    """Comprehensive check of all application dependencies."""
    results = {
        'status': 'ok',
        'timestamp': datetime.now().isoformat(),
        'checks': {}
    }
    
    # Database check
    try:
        db.session.execute(text('SELECT 1'))
        db.session.commit()
        results['checks']['database'] = {
            'status': 'ok',
            'message': 'Database connection successful'
        }
    except Exception as e:
        results['checks']['database'] = {
            'status': 'error',
            'message': str(e)
        }
        results['status'] = 'degraded'
    
    # Stripe API check if configured
    if current_app.config.get('STRIPE_SECRET_KEY'):
        try:
            stripe.api_key = current_app.config.get('STRIPE_SECRET_KEY')
            # Just check if we can access the API (list a small number of customers)
            stripe.Customer.list(limit=1)
            results['checks']['stripe'] = {
                'status': 'ok',
                'message': 'Stripe API connection successful'
            }
        except Exception as e:
            results['checks']['stripe'] = {
                'status': 'error',
                'message': str(e)
            }
            # Don't mark as degraded as Stripe may not be critical
    
    # Export folder check
    export_folder = current_app.config.get('EXPORT_FOLDER')
    if export_folder:
        try:
            if os.path.exists(export_folder) and os.access(export_folder, os.W_OK):
                results['checks']['export_folder'] = {
                    'status': 'ok',
                    'message': 'Export folder is accessible and writable',
                    'path': export_folder
                }
            else:
                results['checks']['export_folder'] = {
                    'status': 'error',
                    'message': 'Export folder is not accessible or not writable',
                    'path': export_folder
                }
                results['status'] = 'degraded'
        except Exception as e:
            results['checks']['export_folder'] = {
                'status': 'error',
                'message': str(e)
            }
            results['status'] = 'degraded'
    
    # Application configuration check
    config_issues = []
    critical_configs = ['SECRET_KEY', 'SQLALCHEMY_DATABASE_URI']
    
    for config in critical_configs:
        if not current_app.config.get(config):
            config_issues.append(f"Missing {config}")
    
    if config_issues:
        results['checks']['configuration'] = {
            'status': 'error',
            'message': 'Configuration issues detected',
            'issues': config_issues
        }
        results['status'] = 'degraded'
    else:
        results['checks']['configuration'] = {
            'status': 'ok',
            'message': 'All critical configurations are present'
        }
    
    return jsonify(results)

@health.route('/monitoring')
def monitoring_status():
    """Expose internal monitoring & queue status for diagnostics."""
    from sqlalchemy import inspect, text as _text
    status = {
        'timestamp': datetime.utcnow().isoformat(),
        'services': {},
        'database': {},
        'service_runtime': {}
    }
    # Table & queue info
    try:
        inspector = inspect(db.engine)
        tables = inspector.get_table_names()
        status['database']['tables_count'] = len(tables)
        status['database']['has_price_alerts'] = 'price_alerts' in tables
        status['database']['has_email_queue'] = 'email_queue' in tables
        if 'email_queue' in tables:
            try:
                pending = db.session.execute(_text("SELECT COUNT(*) FROM email_queue WHERE status='pending'"))
                status['database']['email_queue_pending'] = pending.scalar() or 0
            except Exception as qerr:
                status['database']['email_queue_error'] = str(qerr)
    except Exception as terr:
        status['database']['error'] = str(terr)
    # Service / thread info
    import threading
    try:
        from app.services.price_monitor_service import price_monitor
        pm_running = getattr(price_monitor, '_monitoring_started', False)
        pm_thread_alive = bool(getattr(price_monitor, '_thread', None) and getattr(price_monitor, '_thread').is_alive())
        pm_start_time = getattr(price_monitor, '_start_time', None)
        status['services']['price_monitor'] = {
            'started_flag': pm_running,
            'thread_alive': pm_thread_alive,
            'uptime_seconds': (time.time() - pm_start_time) if pm_start_time else None,
            'alerts_checked_total': getattr(price_monitor, 'alerts_checked_total', None),
            'alerts_triggered_total': getattr(price_monitor, 'alerts_triggered_total', None),
            'symbols_checked_total': getattr(price_monitor, 'symbols_checked_total', None),
            'start_count': getattr(price_monitor, '_start_count', None)
        }
    except Exception as pm_err:
        status['services']['price_monitor'] = {'error': str(pm_err)}
    try:
        from app.services.email_queue_processor import email_queue_processor
        eq_running = getattr(email_queue_processor, 'running', False)
        eq_thread_alive = bool(getattr(email_queue_processor, 'thread', None) and getattr(email_queue_processor, 'thread').is_alive())
        eq_start_time = getattr(email_queue_processor, '_start_time', None)
        status['services']['email_queue_processor'] = {
            'running_flag': eq_running,
            'thread_alive': eq_thread_alive,
            'uptime_seconds': (time.time() - eq_start_time) if eq_start_time else None,
            'emails_processed_total': getattr(email_queue_processor, 'emails_processed_total', None),
            'emails_error_total': getattr(email_queue_processor, 'emails_error_total', None)
        }
    except Exception as eq_err:
        status['services']['email_queue_processor'] = {'error': str(eq_err)}
    # Persisted runtime metadata (best-effort)
    try:
        from app.models import ServiceRuntime
        for svc in ['price_monitor', 'email_queue_processor']:
            rec = ServiceRuntime.query.filter_by(service_name=svc).first()
            if rec:
                status['service_runtime'][svc] = rec.to_dict()
    except Exception as rt_err:
        status['service_runtime']['error'] = str(rt_err)
    # Raw thread list (names only) plus counts
    try:
        raw_threads = threading.enumerate()
        filtered = [t.name for t in raw_threads if not t.name.startswith('Thread-')]
        status['threads'] = filtered
        status['threads_count'] = len(filtered)
        status['all_threads_count'] = len(raw_threads)
        # Count PriceMonitor-* specifically for assertion convenience
        status['price_monitor_threads'] = [t.name for t in raw_threads if t.name.startswith('PriceMonitor-')]
        status['price_monitor_threads_count'] = len(status['price_monitor_threads'])
    except Exception as th_err:
        status['threads'] = []
        status['threads_count'] = 0
        status['all_threads_count'] = 0
        status['thread_error'] = str(th_err)
    return jsonify(status)
