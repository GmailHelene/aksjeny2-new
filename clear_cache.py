#!/usr/bin/env python
"""
Cache clearing utility for Aksjeradar
Run this script to clear all caches
"""

import os
import shutil
import sys
from pathlib import Path

def clear_pycache():
    """Remove all __pycache__ directories"""
    print("Clearing Python cache...")
    count = 0
    for root, dirs, files in os.walk('.'):
        for dir_name in dirs:
            if dir_name == '__pycache__':
                path = os.path.join(root, dir_name)
                shutil.rmtree(path)
                count += 1
    print(f"Removed {count} __pycache__ directories")

def clear_flask_cache():
    """Clear Flask cache directory"""
    print("Clearing Flask cache...")
    cache_dirs = ['cache', '.cache', 'tmp/cache']
    count = 0
    for cache_dir in cache_dirs:
        if os.path.exists(cache_dir):
            shutil.rmtree(cache_dir)
            count += 1
    print(f"Removed {count} cache directories")

def clear_static_cache():
    """Update static file versions"""
    print("Updating static file versions...")
    config_file = 'config.py'
    if os.path.exists(config_file):
        import time
        timestamp = str(int(time.time()))
        # Update ASSETS_VERSION in config
        with open(config_file, 'r') as f:
            content = f.read()
        
        import re
        pattern = r"ASSETS_VERSION\s*=\s*['\"][\d\.]+['\"]"
        replacement = f'ASSETS_VERSION = "{timestamp}"'
        content = re.sub(pattern, replacement, content)
        
        # If not found, add it
        if 'ASSETS_VERSION' not in content:
            content += f"\n    ASSETS_VERSION = '{timestamp}'\n"
        
        with open(config_file, 'w') as f:
            f.write(content)
        
        print(f"Updated ASSETS_VERSION to {timestamp}")

def main():
    print("=== Aksjeradar Cache Clearing Utility ===\n")
    
    clear_pycache()
    clear_flask_cache()
    clear_static_cache()
    
    print("\n✅ All caches cleared successfully!")
    print("\nNext steps:")
    print("1. Restart the Flask application")
    print("2. Clear browser cache (Ctrl+F5 or Cmd+Shift+R)")
    
if __name__ == "__main__":
    main()
