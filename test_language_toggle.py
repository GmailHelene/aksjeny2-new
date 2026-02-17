#!/usr/bin/env python3
"""
Test script to verify language toggle appears on the webpage
"""
import requests
from bs4 import BeautifulSoup

BASE_URL = 'http://127.0.0.1:5000'

def test_language_toggle():
    """Test that language toggle appears on homepage"""
    
    print("Testing language toggle visibility...")
    
    # Get homepage
    response = requests.get(f'{BASE_URL}/')
    if response.status_code != 200:
        print(f"❌ Failed to access homepage: {response.status_code}")
        return False
    
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # Look for language toggle button
    language_toggle = soup.find('a', {'id': 'language-toggle'})
    if language_toggle:
        print("✅ Language toggle button found!")
        print(f"  Button text: {language_toggle.get_text().strip()}")
        print(f"  Button href: {language_toggle.get('href')}")
        print(f"  Button title: {language_toggle.get('title')}")
        return True
    else:
        print("❌ Language toggle button not found")
        
        # Debug: check if there's any translation-related content
        translation_content = soup.find_all(string=lambda text: text and ('language' in text.lower() or 'språk' in text.lower()))
        if translation_content:
            print("  Found translation-related content:")
            for content in translation_content[:5]:
                print(f"    - {content.strip()}")
        
        # Check for any buttons
        buttons = soup.find_all('a', class_='btn')
        if buttons:
            print("  Found other buttons:")
            for btn in buttons[:3]:
                print(f"    - {btn.get_text().strip()}: {btn.get('href')}")
        
        return False

if __name__ == '__main__':
    success = test_language_toggle()
    if success:
        print("\n🎉 SUCCESS: Language toggle is visible!")
    else:
        print("\n❌ FAILED: Language toggle is not visible")