# Comprehensive diagnostic tool for access control issues
# This will help identify exactly why users are being redirected to demo page

from flask import Blueprint, jsonify, render_template, current_app, url_for, request
from flask_login import current_user
import inspect
import sys
import traceback
import logging

diagnostic = Blueprint('diagnostic', __name__, url_prefix='/diagnostic')
logger = logging.getLogger(__name__)

@diagnostic.route('/auth-status')
def auth_status():
    """Display detailed authentication and access control status"""
    try:
        # Get information about current user
        user_info = {
            'is_authenticated': current_user.is_authenticated,
            'id': getattr(current_user, 'id', None),
            'email': getattr(current_user, 'email', None),
            'username': getattr(current_user, 'username', None),
        }
        
        # Get subscription information
        subscription_info = {}
        if current_user.is_authenticated:
            # Try different attributes that might exist
            possible_attrs = [
                'subscription_status', 'subscription_type', 
                'has_subscription', 'is_premium', 'demo_access',
                'lifetime_access', 'subscription_end'
            ]
            
            for attr in possible_attrs:
                if hasattr(current_user, attr):
                    value = getattr(current_user, attr)
                    # Handle callable attributes
                    if callable(value):
                        try:
                            subscription_info[f"{attr}()"] = value()
                        except Exception as e:
                            subscription_info[f"{attr}() ERROR"] = str(e)
                    else:
                        subscription_info[attr] = value
        
        # Get access control information
        access_control_info = {}
        try:
            # Import both access control systems
            from app.utils.access_control_unified import (
                is_exempt_user, has_active_subscription, 
                get_access_level, check_endpoint_access,
                ALWAYS_ACCESSIBLE, DEMO_ACCESSIBLE, PREMIUM_ONLY
            )
            
            # Test unified access control
            is_exempt = is_exempt_user()
            access_level = get_access_level()
            
            # Check some important endpoints
            endpoints_to_check = [
                'profile.profile_page',
                'portfolio.portfolio_overview',
                'portfolio.view_portfolio',
                'portfolio.create_portfolio',
                'main.profile',
                'portfolio.index'
            ]
            
            endpoint_results = {}
            for endpoint in endpoints_to_check:
                allowed, redirect_to, message = check_endpoint_access(endpoint)
                endpoint_results[endpoint] = {
                    'allowed': allowed,
                    'redirect_to': redirect_to,
                    'message': message
                }
            
            # Check current endpoint
            current_endpoint = request.endpoint
            current_allowed, current_redirect, current_message = check_endpoint_access(current_endpoint)
            
            # Get relevant route lists
            demo_accessible_routes = sorted(list(DEMO_ACCESSIBLE))
            premium_only_routes = sorted(list(PREMIUM_ONLY))
            always_accessible_routes = sorted(list(ALWAYS_ACCESSIBLE))
            
            # Compile access control info
            access_control_info.update({
                'is_exempt_user': is_exempt,
                'has_active_subscription': has_active_subscription(),
                'access_level': access_level,
                'endpoint_access': endpoint_results,
                'current_endpoint': {
                    'name': current_endpoint,
                    'allowed': current_allowed,
                    'redirect_to': current_redirect,
                    'message': current_message
                },
                'demo_accessible_routes': demo_accessible_routes,
                'premium_only_routes': premium_only_routes,
                'always_accessible_routes': always_accessible_routes
            })
            
        except Exception as ac_error:
            access_control_info['error'] = str(ac_error)
            access_control_info['traceback'] = traceback.format_exc()
        
        # Check for middleware registration
        middleware_info = {}
        try:
            # Get the before_request functions
            before_request_funcs = current_app.before_request_funcs
            if before_request_funcs:
                middleware_info['before_request_funcs'] = {}
                for blueprint, funcs in before_request_funcs.items():
                    if funcs:
                        middleware_info['before_request_funcs'][blueprint or 'app'] = [
                            f.__name__ if hasattr(f, '__name__') else str(f) for f in funcs
                        ]
            
            # Try to find global access control middleware
            try:
                from app.middleware.access_control import apply_global_access_control
                if apply_global_access_control:
                    middleware_info['global_access_control_imported'] = True
                    
                    # Check if it's in any of the before_request functions
                    if before_request_funcs:
                        for blueprint, funcs in before_request_funcs.items():
                            if funcs and any(f == apply_global_access_control for f in funcs):
                                middleware_info['global_access_control_active'] = True
                                middleware_info['global_access_control_blueprint'] = blueprint or 'app'
                    
            except ImportError:
                middleware_info['global_access_control_imported'] = False
                
        except Exception as mid_error:
            middleware_info['error'] = str(mid_error)
            middleware_info['traceback'] = traceback.format_exc()
        
        # Check Flask-Login unauthorized handler
        unauthorized_handler_info = {}
        try:
            from flask_login import login_manager
            if hasattr(login_manager, '_unauthorized_callback'):
                unauthorized_handler = login_manager._unauthorized_callback
                unauthorized_handler_info['registered'] = True
                unauthorized_handler_info['handler'] = str(unauthorized_handler)
            else:
                unauthorized_handler_info['registered'] = False
        except Exception as unh_error:
            unauthorized_handler_info['error'] = str(unh_error)
        
        # Combine all diagnostic information
        diagnostic_info = {
            'user': user_info,
            'subscription': subscription_info,
            'access_control': access_control_info,
            'middleware': middleware_info,
            'unauthorized_handler': unauthorized_handler_info,
            'request': {
                'endpoint': request.endpoint,
                'url': request.url,
                'path': request.path,
                'method': request.method,
                'blueprint': request.blueprint,
                'is_json': request.is_json,
                'headers': dict(request.headers)
            }
        }
        
        # Log the results for server-side analysis
        logger.info(f"ACCESS DIAGNOSTIC: {diagnostic_info}")
        
        # Return as JSON or rendered template based on Accept header
        if request.headers.get('Accept') == 'application/json':
            return jsonify(diagnostic_info)
        else:
            # Create a pretty HTML view
            return render_template('diagnostic/auth_status.html', 
                                  data=diagnostic_info, 
                                  title="Authentication & Access Control Diagnostic")
    
    except Exception as e:
        error_info = {
            'error': str(e),
            'traceback': traceback.format_exc()
        }
        logger.error(f"Error in diagnostic route: {error_info}")
        if request.headers.get('Accept') == 'application/json':
            return jsonify(error_info), 500
        else:
            return f"""
            <h1>Diagnostic Error</h1>
            <pre>{error_info['error']}</pre>
            <h2>Traceback</h2>
            <pre>{error_info['traceback']}</pre>
            """

# Register this blueprint in app/__init__.py
