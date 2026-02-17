#!/usr/bin/env python3

# Test which import is causing the pandas issue

print("Testing imports...")

try:
    print("1. Importing portfolio_optimization_service...")
    from app.services.portfolio_optimization_service import PortfolioOptimizationService
    print("   ✅ Success")
except Exception as e:
    print(f"   ❌ Error: {e}")

try:
    print("2. Importing performance_tracking_service...")
    from app.services.performance_tracking_service import PerformanceTrackingService
    print("   ✅ Success")
except Exception as e:
    print(f"   ❌ Error: {e}")

print("Test complete.")
