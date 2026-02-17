"""
Fix for blueprint naming conflict in app/__init__.py

The issue is that 'external_data' blueprint is being registered twice.
This needs to be fixed in the main app initialization.
"""

# In app/__init__.py, find and modify:

def create_app(config_name):
    # ...existing code...
    
    # Remove duplicate blueprint registrations
    # Check if external_data_bp is already registered before adding
    
    # Option 1: Rename one of the conflicting blueprints
    from app.external_data import external_data_bp as ext_data_bp
    from app.market_intel import market_intel_bp
    
    # Register with unique names
    app.register_blueprint(ext_data_bp, url_prefix='/external-data')
    app.register_blueprint(market_intel_bp, url_prefix='/market-intel')
    
    # ...existing code...
    
    return app