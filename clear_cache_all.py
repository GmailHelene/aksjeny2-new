"""
Comprehensive cache clearing script for the Flask application.
This script clears all types of caches used in the application.
"""
import os
import shutil
import sys
from pathlib import Path

def clear_flask_cache():
    """Clear Flask cache directories and files."""
    cache_dirs = [
        'app/__pycache__',
        'app/models/__pycache__',
        'app/routes/__pycache__',
        'app/static/.webassets-cache',
        'app/utils/__pycache__',
        'instance',
        '.pytest_cache',
        '__pycache__'
    ]
    
    for cache_dir in cache_dirs:
        path = Path(cache_dir)
        if path.exists() and path.is_dir():
            try:
                shutil.rmtree(path)
                print(f"✓ Cleared cache directory: {cache_dir}")
            except Exception as e:
                print(f"✗ Error clearing {cache_dir}: {e}")

def clear_temp_files():
    """Clear temporary files and compiled Python files."""
    extensions = ['.pyc', '.pyo', '.pyd', '.so', '.cache']
    count = 0
    
    # Walk through all directories
    for root, dirs, files in os.walk('.'):
        # Skip .git and virtual environment directories
        if '.git' in root or 'venv' in root or 'env' in root or '.venv' in root:
            continue
            
        for file in files:
            if any(file.endswith(ext) for ext in extensions):
                try:
                    os.remove(os.path.join(root, file))
                    count += 1
                except Exception as e:
                    print(f"✗ Error removing {file}: {e}")
    
    print(f"✓ Removed {count} temporary/compiled files")

def clear_browser_cache_files():
    """Clear browser cache files if they exist."""
    browser_cache_files = [
        'cookies.txt',
        'session.dat',
        'browser_data.json'
    ]
    
    for file in browser_cache_files:
        if os.path.exists(file):
            try:
                os.remove(file)
                print(f"✓ Removed browser cache file: {file}")
            except Exception as e:
                print(f"✗ Error removing {file}: {e}")

if __name__ == "__main__":
    print("Starting comprehensive cache clearing...")
    clear_flask_cache()
    clear_temp_files()
    clear_browser_cache_files()
    print("Cache clearing completed!")
