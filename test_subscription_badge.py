#!/usr/bin/env python3
"""
Test script to verify subscription badge appears in navigation
"""
import requests
from bs4 import BeautifulSoup
import re

BASE_URL = 'http://127.0.0.1:5000'
EMAIL = 'jarle@aksjeradar.trade'
PASSWORD = 'aksjeradar2024'

def test_subscription_badge():
    """Test that subscription badge appears for logged-in premium user"""
    
    print("Testing subscription badge display...")
    
    # Create session
    session = requests.Session()
    
    # Step 1: Get login page and extract CSRF token
    print("Step 1: Fetch login page")
    login_response = session.get(f'{BASE_URL}/login')
    if login_response.status_code != 200:
        print(f"❌ Failed to access login page: {login_response.status_code}")
        return False
    
    # Extract CSRF token
    soup = BeautifulSoup(login_response.text, 'html.parser')
    csrf_token = None
    csrf_input = soup.find('input', {'name': 'csrf_token'})
    if csrf_input:
        csrf_token = csrf_input.get('value')
        print(f"  CSRF token extracted: {csrf_token[:20]}...")
    
    # Step 2: Login
    print("Step 2: Login")
    login_data = {
        'email': EMAIL,
        'password': PASSWORD
    }
    if csrf_token:
        login_data['csrf_token'] = csrf_token
    
    login_post = session.post(f'{BASE_URL}/auth/login', data=login_data, allow_redirects=True)
    if login_post.status_code not in [200, 302]:
        print(f"❌ Login failed: {login_post.status_code}")
        print(f"Response: {login_post.text[:200]}...")
        return False
    
    print("  ✅ Login successful")
    
    # Step 3: Get homepage and check for subscription badge
    print("Step 3: Check subscription badge on homepage")
    homepage_response = session.get(f'{BASE_URL}/')
    if homepage_response.status_code != 200:
        print(f"❌ Failed to access homepage: {homepage_response.status_code}")
        return False
    
    # Check for subscription badge in navigation
    soup = BeautifulSoup(homepage_response.text, 'html.parser')
    
    # Look for the Konto dropdown - search more broadly
    konto_links = soup.find_all('a', string=re.compile(r'.*Konto.*'))
    if not konto_links:
        # Try finding by href or id containing profile/konto
        konto_links = soup.find_all('a', href=re.compile(r'.*(profile|konto).*', re.I))
    
    # Also check for Bootstrap dropdown toggles with "Konto" text
    if not konto_links:
        dropdowns = soup.find_all('a', class_='dropdown-toggle')
        for dropdown in dropdowns:
            if 'Konto' in dropdown.get_text():
                konto_links = [dropdown]
                break
    
    if not konto_links:
        print("❌ Could not find 'Konto' link in navigation")
        # Debug: show navigation structure
        nav = soup.find('nav') or soup.find('div', class_='navbar')
        if nav:
            print(f"  Navigation structure: {nav.get_text()[:200]}...")
        else:
            print("  No navigation found")
        return False
    
    konto_link = konto_links[0]
    print(f"  Found Konto link: {konto_link.get_text().strip()}")
    
    # Check if badge is present
    badge_element = konto_link.find('span', class_='badge')
    if badge_element:
        badge_text = badge_element.get_text().strip()
        badge_class = ' '.join(badge_element.get('class', []))
        print(f"  ✅ Subscription badge found!")
        print(f"    Text: {badge_text}")
        print(f"    Classes: {badge_class}")
        
        # Verify it shows Premium
        if 'Premium' in badge_text:
            print("  ✅ Badge correctly shows 'Premium' status")
            return True
        else:
            print(f"  ⚠️  Badge shows '{badge_text}' instead of 'Premium'")
            return False
    else:
        print("  ❌ No subscription badge found in Konto link")
        # Show the full HTML of the konto link for debugging
        print(f"  Full Konto link HTML: {konto_link}")
        return False

if __name__ == '__main__':
    success = test_subscription_badge()
    if success:
        print("\n🎉 SUCCESS: Subscription badge is working correctly!")
    else:
        print("\n❌ FAILED: Subscription badge is not working properly")