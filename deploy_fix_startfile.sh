#!/bin/bash

echo "🚀 AKSJERADAR DEPLOYMENT SCRIPT - Fixing start_fixed.py Issue"
echo "=============================================================="

# Exit on any error
set -e

echo "📁 Current directory: $(pwd)"
echo "📋 Checking deployment configuration files..."

# Verify critical files exist
echo "✅ Checking main.py..."
if [ -f "main.py" ]; then
    echo "   ✓ main.py exists"
else
    echo "   ❌ main.py missing!"
    exit 1
fi

echo "✅ Checking railway.toml..."
if [ -f "railway.toml" ]; then
    echo "   ✓ railway.toml exists"
    grep "startCommand" railway.toml
else
    echo "   ❌ railway.toml missing!"
fi

echo "✅ Checking Dockerfile..."
if [ -f "Dockerfile" ]; then
    echo "   ✓ Dockerfile exists"
    grep "CMD" Dockerfile
else
    echo "   ❌ Dockerfile missing!"
fi

echo "✅ Checking Procfile..."
if [ -f "Procfile" ]; then
    echo "   ✓ Procfile exists"
    cat Procfile
else
    echo "   ❌ Procfile missing!"
fi

echo ""
echo "🧹 Clearing Python cache..."
find . -type f -name "*.pyc" -delete
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true

echo ""
echo "🧹 Clearing application cache..."
python3 clear_cache.py || echo "Cache clear script not found or failed"

echo ""
echo "📦 Git status check..."
git status --porcelain

echo ""
echo "➕ Adding all changes..."
git add .

echo ""
echo "📝 Committing changes..."
git commit -m "🔧 Fix deployment: Replace start_fixed.py with main.py

- Fix railway.toml startCommand
- Fix Dockerfile CMD
- Clear cache for clean deployment
- Resolve 'can't open file /app/start_fixed.py' error" || echo "No changes to commit"

echo ""
echo "🚀 Pushing to remote..."
git push origin master

echo ""
echo "✅ DEPLOYMENT COMPLETE!"
echo ""
echo "🔍 Monitor deployment at:"
echo "   • Railway Dashboard: https://railway.app/dashboard"
echo "   • Live Site: https://aksjeradar.trade"
echo "   • Health Check: https://aksjeradar.trade/health"
echo ""
echo "⏰ Deployment typically takes 2-5 minutes"
echo "🎯 Fixed issue: start_fixed.py → main.py"
