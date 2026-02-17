# Script to update portfolio routes to use unified access control
# This script fixes inconsistencies between the old and new access control systems

import re
import os
import sys
from datetime import datetime

# Setup paths
PORTFOLIO_PATH = os.path.join('app', 'routes', 'portfolio.py')
BACKUP_PATH = f"{PORTFOLIO_PATH}.bak.{datetime.now().strftime('%Y%m%d_%H%M%S')}"

def update_portfolio_routes():
    """Update all portfolio routes to use unified_access_required decorator"""
    try:
        # Read the current file
        with open(PORTFOLIO_PATH, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Make a backup
        with open(BACKUP_PATH, 'w', encoding='utf-8') as f:
            f.write(content)
            print(f"Backup created at {BACKUP_PATH}")
        
        # Update imports if needed
        if 'from ..utils.access_control_unified import unified_access_required' not in content:
            content = content.replace(
                'from ..utils.access_control import access_required, demo_access',
                'from ..utils.access_control import access_required, demo_access\nfrom ..utils.access_control_unified import unified_access_required'
            )
        
        # Find all route definitions
        route_pattern = r'@portfolio\.route\([^\)]+\)\s+@(?:login_required|access_required|demo_access)'
        routes = re.findall(route_pattern, content)
        
        # Count for reporting
        total_routes = len(routes)
        updated_routes = 0
        
        # Replace old decorators with unified decorator
        modified_content = content
        for route in routes:
            # Don't change routes that already use unified_access_required
            if 'unified_access_required' in route:
                continue
                
            # Replace the old decorator pattern
            new_route = route.replace('@access_required', '@unified_access_required')
            new_route = new_route.replace('@demo_access', '@unified_access_required')
            
            # Handle login_required + unified_access_required - only need unified
            if '@login_required' in new_route and '@unified_access_required' not in new_route:
                new_route = new_route.replace('@login_required', '@unified_access_required')
            
            # Apply the replacement if it changed
            if new_route != route:
                modified_content = modified_content.replace(route, new_route)
                updated_routes += 1
        
        # Only write if changes were made
        if modified_content != content:
            with open(PORTFOLIO_PATH, 'w', encoding='utf-8') as f:
                f.write(modified_content)
            print(f"Updated {updated_routes} out of {total_routes} routes in {PORTFOLIO_PATH}")
            return True
        else:
            print(f"No changes needed in {PORTFOLIO_PATH}")
            return False
            
    except Exception as e:
        print(f"Error updating portfolio routes: {e}")
        return False

if __name__ == "__main__":
    update_portfolio_routes()
