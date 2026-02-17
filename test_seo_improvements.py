#!/usr/bin/env python3
"""
Test script to verify SEO improvements are working correctly
"""
import requests
from bs4 import BeautifulSoup
import json

BASE_URL = 'http://127.0.0.1:5000'

def test_seo_improvements():
    """Test that SEO enhancements are properly implemented"""
    
    print("Testing SEO improvements...")
    
    # Get homepage
    response = requests.get(f'{BASE_URL}/')
    if response.status_code != 200:
        print(f"❌ Failed to access homepage: {response.status_code}")
        return False
    
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # Test 1: Enhanced meta description
    meta_desc = soup.find('meta', {'name': 'description'})
    if meta_desc and 'ekte data' in meta_desc.get('content', ''):
        print("✅ Enhanced meta description found")
    else:
        print("❌ Enhanced meta description not found")
    
    # Test 2: Enhanced keywords
    meta_keywords = soup.find('meta', {'name': 'keywords'})
    if meta_keywords and 'AI aksjeanalyse' in meta_keywords.get('content', ''):
        print("✅ Enhanced keywords found")
    else:
        print("❌ Enhanced keywords not found")
    
    # Test 3: Enhanced robots tags
    robots_meta = soup.find('meta', {'name': 'robots'})
    if robots_meta and 'max-snippet:-1' in robots_meta.get('content', ''):
        print("✅ Enhanced robots meta tag found")
    else:
        print("❌ Enhanced robots meta tag not found")
    
    # Test 4: Open Graph enhancements
    og_image_alt = soup.find('meta', {'property': 'og:image:alt'})
    if og_image_alt:
        print("✅ Enhanced Open Graph image alt text found")
    else:
        print("❌ Enhanced Open Graph image alt text not found")
    
    # Test 5: Twitter card enhancements  
    twitter_label1 = soup.find('meta', {'name': 'twitter:label1'})
    if twitter_label1 and twitter_label1.get('content') == 'Pris':
        print("✅ Enhanced Twitter card labels found")
    else:
        print("❌ Enhanced Twitter card labels not found")
    
    # Test 6: Preconnect links
    preconnect_links = soup.find_all('link', {'rel': 'preconnect'})
    if len(preconnect_links) >= 2:
        print(f"✅ Found {len(preconnect_links)} preconnect links for performance")
    else:
        print("❌ Preconnect links not found")
    
    # Test 7: Enhanced structured data
    ld_json_scripts = soup.find_all('script', {'type': 'application/ld+json'})
    enhanced_schemas = 0
    
    for script in ld_json_scripts:
        try:
            data = json.loads(script.string)
            if data.get('@type') == 'Organization':
                enhanced_schemas += 1
                print("✅ Organization schema found")
            elif data.get('@type') == 'FAQPage':
                enhanced_schemas += 1
                print("✅ FAQ schema found")
            elif isinstance(data.get('@type'), list) and 'SoftwareApplication' in data.get('@type'):
                enhanced_schemas += 1
                print("✅ Enhanced SoftwareApplication schema found")
        except (json.JSONDecodeError, AttributeError):
            continue
    
    # Test 8: Mobile app meta tags
    apple_mobile_capable = soup.find('meta', {'name': 'apple-mobile-web-app-capable'})
    if apple_mobile_capable and apple_mobile_capable.get('content') == 'yes':
        print("✅ Mobile app meta tags found")
    else:
        print("❌ Mobile app meta tags not found")
    
    # Test 9: Theme color
    theme_color = soup.find('meta', {'name': 'theme-color'})
    if theme_color:
        print(f"✅ Theme color found: {theme_color.get('content')}")
    else:
        print("❌ Theme color not found")
    
    # Summary
    total_tests = 9
    passed_tests = 0
    
    if meta_desc and 'ekte data' in meta_desc.get('content', ''):
        passed_tests += 1
    if meta_keywords and 'AI aksjeanalyse' in meta_keywords.get('content', ''):
        passed_tests += 1
    if robots_meta and 'max-snippet:-1' in robots_meta.get('content', ''):
        passed_tests += 1
    if og_image_alt:
        passed_tests += 1
    if twitter_label1 and twitter_label1.get('content') == 'Pris':
        passed_tests += 1
    if len(preconnect_links) >= 2:
        passed_tests += 1
    if enhanced_schemas >= 2:
        passed_tests += 1
    if apple_mobile_capable and apple_mobile_capable.get('content') == 'yes':
        passed_tests += 1
    if theme_color:
        passed_tests += 1
    
    print(f"\nSEO Test Results: {passed_tests}/{total_tests} tests passed")
    
    return passed_tests >= 7  # Consider success if at least 7/9 tests pass

if __name__ == '__main__':
    success = test_seo_improvements()
    if success:
        print("\n🎉 SUCCESS: SEO improvements are working well!")
    else:
        print("\n⚠️  WARNING: Some SEO improvements may need attention")