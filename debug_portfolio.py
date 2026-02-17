#!/usr/bin/env python3
"""
Debug portfolio blueprint registration
"""
import sys
import traceback

print("=== PORTFOLIO BLUEPRINT DEBUG ===")

try:
    print("Testing import of portfolio blueprint...")
    from app.routes.portfolio import portfolio
    print(f"✅ Portfolio blueprint imported successfully: {portfolio}")
    print(f"   - Name: {portfolio.name}")
    print(f"   - URL prefix: {portfolio.url_prefix}")
    
    # Check deferred functions
    print(f"   - Deferred functions: {len(portfolio.deferred_functions)}")
    
except Exception as e:
    print(f"❌ Error importing portfolio blueprint: {e}")
    traceback.print_exc()

print("\nTesting full app creation...")
try:
    from app import create_app
    app = create_app('development')
    
    with app.app_context():
        # Check registered blueprints
        blueprints = list(app.blueprints.keys())
        print(f"Registered blueprints: {blueprints}")
        
        if 'portfolio' in blueprints:
            print("✅ Portfolio blueprint is registered")
            
            # Find portfolio routes
            portfolio_routes = []
            for rule in app.url_map.iter_rules():
                if rule.endpoint.startswith('portfolio.'):
                    portfolio_routes.append(f"{rule.endpoint} -> {rule.rule}")
            
            print(f"Portfolio routes ({len(portfolio_routes)}):")
            for route in portfolio_routes:
                print(f"   - {route}")
        else:
            print("❌ Portfolio blueprint NOT registered")

except Exception as e:
    print(f"❌ Error creating app: {e}")
    traceback.print_exc()
