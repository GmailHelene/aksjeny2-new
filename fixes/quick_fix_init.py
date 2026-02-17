"""
Quick fix for app/__init__.py to resolve blueprint conflict
Replace the problematic section in create_app function
"""

def create_app(config_name):
    from flask import Flask
    from config import config
    
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    
    # ...existing code...
    
    # Blueprint registration with conflict check
    blueprints_to_register = []
    
    # Main blueprints
    from app.main import main as main_bp
    blueprints_to_register.append((main_bp, {'url_prefix': '/'}))
    
    # Auth blueprint
    from app.auth import auth as auth_bp
    blueprints_to_register.append((auth_bp, {'url_prefix': '/auth'}))
    
    # Stocks blueprint
    from app.stocks import stocks as stocks_bp
    blueprints_to_register.append((stocks_bp, {'url_prefix': '/stocks'}))
    
    # Analysis blueprint
    from app.analysis import analysis as analysis_bp
    blueprints_to_register.append((analysis_bp, {'url_prefix': '/analysis'}))
    
    # Portfolio blueprint
    from app.portfolio import portfolio as portfolio_bp
    blueprints_to_register.append((portfolio_bp, {'url_prefix': '/portfolio'}))
    
    # Forum blueprint
    from app.forum import forum as forum_bp
    blueprints_to_register.append((forum_bp, {'url_prefix': '/forum'}))
    
    # Price alerts blueprint
    from app.price_alerts import price_alerts as alerts_bp
    blueprints_to_register.append((alerts_bp, {'url_prefix': '/price-alerts'}))
    
    # Pro tools blueprint
    from app.pro_tools import pro_tools as pro_bp
    blueprints_to_register.append((pro_bp, {'url_prefix': '/pro-tools'}))
    
    # External data - only register once
    try:
        from app.external_data import external_data_bp
        blueprints_to_register.append((external_data_bp, {'url_prefix': '/external-data', 'name': 'external_data_main'}))
    except ImportError:
        pass
    
    # Market intel - separate from external data
    try:
        from app.market_intel import market_intel_bp
        blueprints_to_register.append((market_intel_bp, {'url_prefix': '/market-intel', 'name': 'market_intel'}))
    except ImportError:
        pass
    
    # Register all blueprints
    registered = set()
    for blueprint, options in blueprints_to_register:
        bp_name = options.get('name', blueprint.name)
        if bp_name not in registered:
            app.register_blueprint(blueprint, **options)
            registered.add(bp_name)
    
    # ...existing code...
    
    return app