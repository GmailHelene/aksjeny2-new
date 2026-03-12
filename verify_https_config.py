#!/usr/bin/env python3
"""
Verify HTTPS Configuration for aksjeradar.trade
This script tests that all HTTPS security headers and configurations are properly set
"""
import os
import sys
import json
from urllib.parse import urljoin

try:
    import requests
except ImportError:
    print("❌ requests library not installed. Run: pip install requests")
    sys.exit(1)


def test_https_headers(url):
    """Test HTTPS security headers"""
    print(f"\n🔍 Testing HTTPS Configuration for {url}")
    print("=" * 70)
    
    try:
        # Set a reasonable timeout
        response = requests.head(url, timeout=10, allow_redirects=True)
        
        print(f"\n✅ Connected successfully")
        print(f"Status Code: {response.status_code}")
        print(f"Final URL: {response.url}")
        print(f"Scheme: {response.url.split('://')[0]}")
        
        # Check critical headers
        print("\n🔐 Security Headers Check:")
        print("-" * 70)
        
        required_headers = {
            'Strict-Transport-Security': 'HSTS (forces HTTPS)',
            'X-Content-Type-Options': 'MIME type sniffing protection',
            'X-Frame-Options': 'Clickjacking protection',
            'X-XSS-Protection': 'XSS protection',
            'Referrer-Policy': 'Referrer policy control',
            'Content-Security-Policy': 'Content Security Policy',
        }
        
        all_headers_present = True
        for header, description in required_headers.items():
            if header in response.headers:
                value = response.headers[header]
                timestamp = response.headers.get('Date', 'N/A')
                print(f"  ✅ {header}")
                print(f"     └─ Value: {value[:80]}")
                print(f"     └─ Purpose: {description}")
            else:
                print(f"  ❌ {header} - MISSING")
                all_headers_present = False
        
        # Check protocol
        print("\n🔒 Protocol Check:")
        print("-" * 70)
        if response.url.startswith('https://'):
            print(f"  ✅ Using HTTPS")
        else:
            print(f"  ❌ NOT using HTTPS - URL: {response.url}")
        
        # Check redirect
        if response.history:
            print(f"\n📍 Redirects:")
            print("-" * 70)
            for i, redirect in enumerate(response.history, 1):
                print(f"  {i}. {redirect.status_code} → {redirect.url}")
        
        # HSTS preload check
        print(f"\n📋 HSTS Details:")
        print("-" * 70)
        hsts = response.headers.get('Strict-Transport-Security', 'NOT SET')
        if 'max-age' in hsts:
            print(f"  ✅ HSTS is configured")
            print(f"     └─ Header: {hsts}")
            if 'preload' in hsts:
                print(f"     └─ Preload: ENABLED (can be added to HSTS preload list)")
            else:
                print(f"     └─ Preload: disabled")
        else:
            print(f"  ❌ HSTS header missing or misconfigured")
        
        # Certificate info (for HTTPS)
        if response.url.startswith('https://'):
            print(f"\n🔐 SSL/TLS Check:")
            print("-" * 70)
            try:
                conn = response.raw._connection.sock
                cert = conn.getpeercert()
                if cert:
                    print(f"  ✅ SSL Certificate valid")
                    subject = dict(x[0] for x in cert['subject'])
                    print(f"     └─ Subject: {subject.get('commonName', 'N/A')}")
                    print(f"     └─ Issuer: {cert.get('issuer', 'N/A')}")
                else:
                    print(f"  ⚠️  Could not retrieve certificate details")
            except Exception as cert_err:
                print(f"  ⚠️  Certificate check: {cert_err}")
        
        # Summary
        print(f"\n📊 Summary:")
        print("-" * 70)
        if all_headers_present and response.url.startswith('https://'):
            print(f"  ✅ HTTPS is properly configured!")
            print(f"  ✅ All security headers are in place!")
            return True
        else:
            issues = []
            if not response.url.startswith('https://'):
                issues.append("Not using HTTPS")
            if not all_headers_present:
                issues.append("Some security headers missing")
            print(f"  ⚠️  Issues found: {', '.join(issues)}")
            return False
            
    except requests.exceptions.ConnectionError as e:
        print(f"❌ Connection error: {e}")
        print(f"   Make sure the URL is accessible and HTTPS is working")
        return False
    except requests.exceptions.Timeout:
        print(f"❌ Connection timeout")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def main():
    """Main function"""
    print("\n" + "=" * 70)
    print("HTTPS Configuration Verification for Aksjeradar")
    print("=" * 70)
    
    # Test URLs
    test_urls = [
        'https://aksjeradar.trade',
        'https://www.aksjeradar.trade',
    ]
    
    results = {}
    for url in test_urls:
        try:
            results[url] = test_https_headers(url)
        except KeyboardInterrupt:
            print("\n\n⚠️  Test interrupted by user")
            break
        except Exception as e:
            print(f"\n❌ Unexpected error testing {url}: {e}")
            results[url] = False
    
    # Final summary
    print("\n" + "=" * 70)
    print("FINAL RESULTS")
    print("=" * 70)
    
    all_passed = True
    for url, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} - {url}")
        if not passed:
            all_passed = False
    
    print("=" * 70)
    
    if all_passed:
        print("\n✅ All HTTPS checks passed! aksjeradar.trade is properly configured.")
        return 0
    else:
        print("\n❌ Some HTTPS checks failed. Please review the configuration.")
        return 1


if __name__ == '__main__':
    sys.exit(main())
