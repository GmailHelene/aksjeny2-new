#!/usr/bin/env python3
"""
Debug script to check robots meta tag rendering
"""
import requests
from bs4 import BeautifulSoup

BASE_URL = 'http://127.0.0.1:5000'

def debug_robots_tag():
    """Debug the robots meta tag issue"""
    
    print("Debugging robots meta tag...")
    
    # Get homepage
    response = requests.get(f'{BASE_URL}/')
    if response.status_code != 200:
        print(f"❌ Failed to access homepage: {response.status_code}")
        return
    
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # Find all robots meta tags
    robots_tags = soup.find_all('meta', {'name': 'robots'})
    
    print(f"Found {len(robots_tags)} robots meta tags:")
    for i, tag in enumerate(robots_tags, 1):
        content = tag.get('content', '')
        print(f"{i}. Content: '{content}'")
        
        # Check for enhanced content
        if 'max-snippet:-1' in content:
            print("   ✅ Contains enhanced robots directive")
        else:
            print("   ❌ Missing enhanced robots directive")
    
    # Check request host
    print(f"\nRequest URL: {BASE_URL}")
    print("Note: The robots tag content depends on the request host")

if __name__ == '__main__':
    debug_robots_tag()