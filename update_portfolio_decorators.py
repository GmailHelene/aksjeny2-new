# Script to update all @access_required decorators in portfolio.py
import re
import os
import sys
from datetime import datetime
import traceback

PORTFOLIO_FILE = os.path.join('app', 'routes', 'portfolio.py')
BACKUP_FILE = f"{PORTFOLIO_FILE}.bak.{datetime.now().strftime('%Y%m%d_%H%M%S')}"

def create_backup():
    try:
        with open(PORTFOLIO_FILE, 'r', encoding='utf-8') as src:
            content = src.read()
            
        with open(BACKUP_FILE, 'w', encoding='utf-8') as dst:
            dst.write(content)
            
        print(f"Created backup at {BACKUP_FILE}")
        return content
    except Exception as e:
        print(f"Error creating backup: {e}")
        traceback.print_exc()
        sys.exit(1)

def update_decorators(content):
    try:
        # Replace @access_required with @unified_access_required
        new_content = content.replace('@access_required', '@unified_access_required')
        
        # Replace @demo_access with @unified_access_required
        new_content = new_content.replace('@demo_access', '@unified_access_required')
        
        # Count replacements
        access_required_count = content.count('@access_required')
        demo_access_count = content.count('@demo_access')
        
        # Only write if changes were made
        if new_content != content:
            with open(PORTFOLIO_FILE, 'w', encoding='utf-8') as f:
                f.write(new_content)
                
            print(f"Updated {PORTFOLIO_FILE}:")
            print(f"  - Replaced {access_required_count} @access_required decorators")
            print(f"  - Replaced {demo_access_count} @demo_access decorators")
            return True
        else:
            print("No changes needed")
            return False
    except Exception as e:
        print(f"Error updating decorators: {e}")
        traceback.print_exc()
        return False

def main():
    print(f"Updating decorators in {PORTFOLIO_FILE}...")
    content = create_backup()
    if update_decorators(content):
        print("Successfully updated portfolio.py")
    else:
        print("No changes made to portfolio.py")

if __name__ == "__main__":
    main()
