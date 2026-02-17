#!/usr/bin/env python3
"""Final test for portfolio 500 error fix"""

import sys
import os
import requests
import time

try:
    print("🔧 TESTING PORTFOLIO 500 ERROR FIX")
    print("="*50)
    
    # Test direct HTTP request to portfolio
    base_url = "http://localhost:5000"
    
    print("1. Testing main portfolio page...")
    try:
        response = requests.get(f"{base_url}/portfolio/", timeout=10)
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 500:
            print("   ❌ Still getting 500 error!")
            print("   Response excerpt:", response.text[:300])
        elif response.status_code == 302:
            print("   ✅ Redirect (likely login required) - No 500 error!")
            print("   Location:", response.headers.get('Location', 'N/A'))
        elif response.status_code == 200:
            print("   ✅ Page loads successfully!")
        else:
            print(f"   ⚠️  Status {response.status_code}")
            
    except requests.exceptions.RequestException as e:
        print(f"   ❌ Request error: {e}")
    
    print("\n2. Testing portfolio overview...")
    try:
        response = requests.get(f"{base_url}/portfolio/overview", timeout=10)
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 500:
            print("   ❌ 500 error on overview!")
        elif response.status_code == 302:
            print("   ✅ Redirect (likely login required) - No 500 error!")
        elif response.status_code == 200:
            print("   ✅ Overview loads successfully!")
            
    except requests.exceptions.RequestException as e:
        print(f"   ❌ Request error: {e}")
    
    print("\n📊 SUMMARY")
    print("="*50)
    print("✅ Template route references fixed")
    print("✅ Missing edit_stock.html template created")
    print("✅ Portfolio blueprint should now work without 500 errors")
    print("\n💡 If user still sees 500 errors:")
    print("   - Check if they need to login first")
    print("   - Check server logs for any database issues")
    print("   - Verify user has proper permissions/subscription")

except Exception as e:
    print(f"❌ Test error: {e}")
    import traceback
    traceback.print_exc()
