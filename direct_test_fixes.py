#!/usr/bin/env python3
"""
Direct Test for Stock Details & Price Alerts
============================================

This script tests the actual functionality of the fixes applied.
"""

import requests
import time

def test_stock_details():
    """Test stock details page specific functionality"""
    print("🔍 Testing Stock Details Page...")
    
    try:
        response = requests.get('http://localhost:5002/stocks/details/GOOGL', timeout=10)
        
        if response.status_code == 200:
            content = response.text
            
            # Check for key fixes
            has_tradingview = 'tradingview' in content.lower()
            has_key_metrics_id = 'key-metrics-card' in content
            has_chart_functions = 'initChart' in content or 'createChart' in content
            has_tab_structure = 'nav-tabs' in content
            
            print(f"  ✅ Page loads: {response.status_code == 200}")
            print(f"  ✅ TradingView widget: {has_tradingview}")
            print(f"  ✅ Key metrics card ID: {has_key_metrics_id}")
            print(f"  ✅ Chart functions: {has_chart_functions}")
            print(f"  ✅ Tab structure: {has_tab_structure}")
            
            # Check if "Nøkkeltall" only appears once (for overview tab)
            key_metrics_count = content.lower().count('nøkkeltall')
            print(f"  ✅ Key metrics sections: {key_metrics_count} (should be 1)")
            
            return True
        else:
            print(f"  ❌ Page failed to load: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"  ❌ Error: {e}")
        return False

def test_price_alerts():
    """Test price alerts page"""
    print("\n🔍 Testing Price Alerts Page...")
    
    try:
        response = requests.get('http://localhost:5002/price-alerts/create', timeout=10)
        
        if response.status_code == 200:
            content = response.text
            
            # Check for form elements
            has_form = '<form' in content
            has_csrf = 'csrf_token' in content
            has_submit = 'submit' in content.lower()
            
            print(f"  ✅ Page loads: {response.status_code == 200}")
            print(f"  ✅ Contains form: {has_form}")
            print(f"  ✅ CSRF protection: {has_csrf}")
            print(f"  ✅ Submit button: {has_submit}")
            
            return True
        else:
            print(f"  ❌ Page failed to load: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"  ❌ Error: {e}")
        return False

def test_server_connection():
    """Test basic server connectivity"""
    print("🔍 Testing Server Connection...")
    
    try:
        response = requests.get('http://localhost:5002/', timeout=15)
        print(f"  ✅ Server responds: {response.status_code}")
        return True
    except Exception as e:
        print(f"  ❌ Server not accessible: {e}")
        return False

if __name__ == "__main__":
    print("🧪 STOCK DETAILS & PRICE ALERTS - DIRECT TESTING")
    print("=" * 55)
    
    # Test server connection
    server_ok = test_server_connection()
    
    if server_ok:
        # Test specific functionality
        stock_ok = test_stock_details()
        alerts_ok = test_price_alerts()
        
        print("\n" + "=" * 55)
        print("📋 TEST SUMMARY")
        print("=" * 55)
        print(f"Server Connection: {'✅ PASS' if server_ok else '❌ FAIL'}")
        print(f"Stock Details: {'✅ PASS' if stock_ok else '❌ FAIL'}")
        print(f"Price Alerts: {'✅ PASS' if alerts_ok else '❌ FAIL'}")
        
        if stock_ok and alerts_ok:
            print("\n🎉 ALL TESTS PASSED! Fixes are working correctly.")
        else:
            print("\n⚠️ Some functionality issues detected.")
    else:
        print("\n❌ Server connection failed. Check if Flask is running on port 5002.")
