#!/bin/bash

echo "🚀 Starting deployment..."

# Clear cache
echo "🧹 Clearing cache..."
python3 clear_cache.py

# Add all changes
echo "📦 Adding changes to git..."
git add -A

# Commit with timestamp
TIMESTAMP=$(date +"%Y-%m-%d %H:%M:%S")
echo "💾 Committing changes..."
git commit -m "Deploy: Fix currency calculator and remaining issues - $TIMESTAMP"

# Push to repository
echo "📤 Pushing to repository..."
git push origin main

echo "✅ Deployment complete!"
