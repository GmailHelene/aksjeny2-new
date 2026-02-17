#!/usr/bin/env python3
"""
Comprehensive Endpoint Testing for Aksjeradar
Tests all endpoints, error handling, and access control
"""

import requests
import sys
import json
import time
from urllib.parse import urljoin, urlparse
from typing import List, Dict, Tuple, Optional
import re
from datetime import datetime
import pytest
from flask import url_for
from app import create_app

class EndpointTester:
    def __init__(self, base_url: str = "http://localhost:5002"):
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Aksjeradar-Endpoint-Tester/1.0'
        })
        self.results = []
        self.errors = []
        self.redirects = []
        
    def get_all_endpoints(self) -> List[Dict]:
        """Get all endpoints from the application"""
        # Main routes
        main_endpoints = [
            {'url': '/', 'name': 'Homepage', 'auth_required': False},
            {'url': '/register', 'name': 'Register', 'auth_required': False},
            {'url': '/login', 'name': 'Login', 'auth_required': False},
            {'url': '/logout', 'name': 'Logout', 'auth_required': True},
            {'url': '/demo', 'name': 'Demo', 'auth_required': False},
            {'url': '/profile', 'name': 'Profile', 'auth_required': True},
            {'url': '/portfolio', 'name': 'Portfolio', 'auth_required': True},
            {'url': '/subscription', 'name': 'Subscription', 'auth_required': False},
            {'url': '/privacy', 'name': 'Privacy Policy', 'auth_required': False},
            {'url': '/terms', 'name': 'Terms of Service', 'auth_required': False},
            {'url': '/contact', 'name': 'Contact', 'auth_required': False},
            {'url': '/forgot-password', 'name': 'Forgot Password', 'auth_required': False},
            {'url': '/reset-password', 'name': 'Reset Password', 'auth_required': False},
        ]
        
        # Analysis routes
        analysis_endpoints = [
            {'url': '/analysis', 'name': 'Analysis Index', 'auth_required': True},
            {'url': '/analysis/technical/AAPL', 'name': 'Technical Analysis (AAPL)', 'auth_required': True},
            {'url': '/analysis/ai', 'name': 'AI Analysis', 'auth_required': True},
            {'url': '/analysis/warren-buffett', 'name': 'Warren Buffett Analysis', 'auth_required': True},
            {'url': '/analysis/benjamin-graham', 'name': 'Benjamin Graham Analysis', 'auth_required': True},
            {'url': '/analysis/short-analysis', 'name': 'Short Analysis', 'auth_required': True},
            {'url': '/analysis/market-overview', 'name': 'Market Overview', 'auth_required': True},
        ]
        
        # Stock routes
        stock_endpoints = [
            {'url': '/stocks', 'name': 'Stock List', 'auth_required': True},
            {'url': '/stocks/AAPL', 'name': 'Stock Details (AAPL)', 'auth_required': True},
            {'url': '/stocks/search?q=apple', 'name': 'Stock Search', 'auth_required': True},
        ]
        
        # Market Intel routes
        market_intel_endpoints = [
            {'url': '/market-intel', 'name': 'Market Intel Index', 'auth_required': True},
            {'url': '/market-intel/insider-trading', 'name': 'Insider Trading', 'auth_required': True},
            {'url': '/market-intel/earnings-calendar', 'name': 'Earnings Calendar', 'auth_required': True},
            {'url': '/market-intel/sector-analysis', 'name': 'Sector Analysis', 'auth_required': True},
            {'url': '/market-intel/economic-indicators', 'name': 'Economic Indicators', 'auth_required': True},
        ]
        
        # API endpoints
        api_endpoints = [
            {'url': '/api/stock/AAPL', 'name': 'API: Stock Data', 'auth_required': True},
            {'url': '/api/portfolio', 'name': 'API: Portfolio', 'auth_required': True},
            {'url': '/api/search?q=apple', 'name': 'API: Search', 'auth_required': True},
            {'url': '/api/technical-indicators/AAPL', 'name': 'API: Technical Indicators', 'auth_required': True},
            {'url': '/api/news/AAPL', 'name': 'API: Stock News', 'auth_required': True},
            {'url': '/api/feedback', 'name': 'API: Feedback', 'auth_required': False, 'method': 'POST'},
        ]
        
        # Pricing routes
        pricing_endpoints = [
            {'url': '/pricing', 'name': 'Pricing Page', 'auth_required': False},
            {'url': '/pricing/checkout/starter', 'name': 'Checkout Starter', 'auth_required': True},
            {'url': '/pricing/checkout/professional', 'name': 'Checkout Professional', 'auth_required': True},
            {'url': '/pricing/checkout/enterprise', 'name': 'Checkout Enterprise', 'auth_required': True},
        ]
        
        # Feature routes
        feature_endpoints = [
            {'url': '/features/analyst-recommendations', 'name': 'Analyst Recommendations', 'auth_required': True},
            {'url': '/features/social-sentiment', 'name': 'Social Sentiment', 'auth_required': True},
            # {'url': '/features/ai-predictions', 'name': 'AI Predictions', 'auth_required': True},  # deprecated
        ]
        
        # Admin routes (if exists)
        admin_endpoints = [
            {'url': '/admin', 'name': 'Admin Dashboard', 'auth_required': True, 'admin_only': True},
            {'url': '/admin/users', 'name': 'Admin Users', 'auth_required': True, 'admin_only': True},
        ]
        
        # Combine all endpoints
        all_endpoints = (
            main_endpoints + 
            analysis_endpoints + 
            stock_endpoints + 
            market_intel_endpoints + 
            api_endpoints + 
            pricing_endpoints + 
            feature_endpoints + 
            admin_endpoints
        )
        
        return all_endpoints
    
    def test_endpoint(self, endpoint: Dict, user_type: str = 'anonymous') -> Dict:
        """Test a single endpoint"""
        url = urljoin(self.base_url, endpoint['url'])
        method = endpoint.get('method', 'GET')
        
        try:
            # Prepare request based on method
            if method == 'GET':
                response = self.session.get(url, allow_redirects=False, timeout=10)
            elif method == 'POST':
                # Add dummy data for POST requests
                data = {'test': 'data'}
                response = self.session.post(url, json=data, allow_redirects=False, timeout=10)
            else:
                response = self.session.request(method, url, allow_redirects=False, timeout=10)
            
            # Check for redirects
            is_redirect = response.status_code in [301, 302, 303, 307, 308]
            redirect_location = response.headers.get('Location', '')
            
            # Follow redirect to get final response
            if is_redirect:
                final_response = self.session.get(
                    urljoin(self.base_url, redirect_location), 
                    allow_redirects=True,
                    timeout=10
                )
            else:
                final_response = response
            
            # Check for errors in response
            errors_found = self.check_for_errors(final_response)
            
            # Check for demo redirect
            is_demo_redirect = '/demo' in redirect_location.lower()
            
            # Check for login redirect
            is_login_redirect = '/login' in redirect_location.lower()
            
            result = {
                'endpoint': endpoint['url'],
                'name': endpoint['name'],
                'method': method,
                'user_type': user_type,
                'status_code': response.status_code,
                'is_redirect': is_redirect,
                'redirect_location': redirect_location,
                'is_demo_redirect': is_demo_redirect,
                'is_login_redirect': is_login_redirect,
                'final_status_code': final_response.status_code,
                'final_url': final_response.url,
                'errors_found': errors_found,
                'response_time': final_response.elapsed.total_seconds(),
                'content_length': len(final_response.content),
                'success': True,
                'error_message': None
            }
            
            # Track redirects
            if is_redirect:
                self.redirects.append({
                    'from': endpoint['url'],
                    'to': redirect_location,
                    'type': 'demo' if is_demo_redirect else 'login' if is_login_redirect else 'other'
                })
            
            # Track errors
            if errors_found:
                self.errors.append({
                    'endpoint': endpoint['url'],
                    'errors': errors_found
                })
            
            return result
            
        except Exception as e:
            error_result = {
                'endpoint': endpoint['url'],
                'name': endpoint['name'],
                'method': method,
                'user_type': user_type,
                'status_code': None,
                'success': False,
                'error_message': str(e)
            }
            
            self.errors.append({
                'endpoint': endpoint['url'],
                'error': str(e)
            })
            
            return error_result
    
    def check_for_errors(self, response) -> List[str]:
        """Check response for error messages"""
        errors = []
        
        if not response.text:
            return errors
        
        # Common error patterns
        error_patterns = [
            r'error',
            r'Error',
            r'ERROR',
            r'exception',
            r'Exception',
            r'traceback',
            r'Traceback',
            r'500\s*-?\s*Internal\s*Server\s*Error',
            r'404\s*-?\s*Not\s*Found',
            r'403\s*-?\s*Forbidden',
            r'401\s*-?\s*Unauthorized',
            r'400\s*-?\s*Bad\s*Request',
            r'Beklager.*gikk.*galt',
            r'Sorry.*went.*wrong',
            r'Noe\s*gikk\s*galt',
            r'Something\s*went\s*wrong',
            r'En\s*feil\s*oppstod',
            r'An\s*error\s*occurred',
            r'Kunne\s*ikke',
            r'Could\s*not',
            r'Failed\s*to',
            r'Feilet',
            r'Internal\s*Server\s*Error'
        ]
        
        # Check for error patterns
        for pattern in error_patterns:
            if re.search(pattern, response.text, re.IGNORECASE):
                # Try to extract context
                matches = re.finditer(pattern, response.text, re.IGNORECASE)
                for match in matches:
                    start = max(0, match.start() - 50)
                    end = min(len(response.text), match.end() + 50)
                    context = response.text[start:end].strip()
                    
                    # Skip false positives
                    false_positives = [
                        'error-free',
                        'no errors',
                        'error handling',
                        'error message',
                        'class="error"',
                        'id="error"',
                        '.error {',
                        'error:',
                        'Error:'
                    ]
                    
                    if not any(fp in context.lower() for fp in false_positives):
                        errors.append(f"Pattern '{pattern}' found: ...{context}...")
        
        # Check for Python traceback
        if 'Traceback (most recent call last)' in response.text:
            errors.append("Python traceback found in response")
        
        # Check for common framework errors
        if 'werkzeug.exceptions' in response.text:
            errors.append("Werkzeug exception found")
        
        if 'jinja2.exceptions' in response.text:
            errors.append("Jinja2 template error found")
        
        if 'sqlalchemy.exc' in response.text:
            errors.append("SQLAlchemy database error found")
        
        return errors
    
    def test_user_scenarios(self) -> Dict:
        """Test different user scenarios"""
        scenarios = {
            'anonymous': self.test_anonymous_user(),
            'expired_trial': self.test_expired_trial_user(),
            'active_trial': self.test_active_trial_user(),
            'premium': self.test_premium_user()
        }
        
        return scenarios
    
    def test_anonymous_user(self) -> List[Dict]:
        """Test endpoints as anonymous user"""
        print("\n🚫 Testing as Anonymous User...")
        results = []
        
        # Clear any existing session
        self.session = requests.Session()
        
        endpoints = self.get_all_endpoints()
        for endpoint in endpoints:
            result = self.test_endpoint(endpoint, 'anonymous')
            results.append(result)
            
            # Print progress
            status_icon = "✅" if result['success'] else "❌"
            redirect_info = ""
            if result.get('is_redirect'):
                if result.get('is_demo_redirect'):
                    redirect_info = " → /demo"
                elif result.get('is_login_redirect'):
                    redirect_info = " → /login"
                else:
                    redirect_info = f" → {result.get('redirect_location', '?')}"
            
            print(f"  {status_icon} {endpoint['name']}: {result.get('status_code', 'ERROR')}{redirect_info}")
        
        return results
    
    def test_expired_trial_user(self) -> List[Dict]:
        """Test endpoints as expired trial user"""
        print("\n⏰ Testing as Expired Trial User...")
        results = []
        
        # Simulate expired trial user
        self.session.cookies.set('trial_expired', 'true')
        self.session.cookies.set('user_type', 'expired_trial')
        
        # Test only authenticated endpoints
        endpoints = [e for e in self.get_all_endpoints() if e.get('auth_required')]
        
        for endpoint in endpoints:
            result = self.test_endpoint(endpoint, 'expired_trial')
            results.append(result)
            
            # Check if properly redirected to demo
            if result.get('is_demo_redirect'):
                print(f"  ✅ {endpoint['name']}: Correctly redirected to /demo")
            elif result.get('status_code') == 200 and not result.get('errors_found'):
                print(f"  ⚠️  {endpoint['name']}: Accessible (should redirect to /demo?)")
            else:
                print(f"  ✓ {endpoint['name']}: {result.get('status_code', 'ERROR')}")
        
        return results
    
    def test_active_trial_user(self) -> List[Dict]:
        """Test endpoints as active trial user"""
        print("\n⏱️  Testing as Active Trial User...")
        results = []
        
        # Simulate active trial user
        self.session.cookies.set('trial_active', 'true')
        self.session.cookies.set('user_type', 'trial')
        self.session.cookies.set('trial_start', str(int(time.time())))
        
        endpoints = self.get_all_endpoints()
        
        for endpoint in endpoints:
            result = self.test_endpoint(endpoint, 'active_trial')
            results.append(result)
            
            if result['success'] and result.get('status_code') == 200:
                print(f"  ✅ {endpoint['name']}: Accessible")
            else:
                print(f"  ❌ {endpoint['name']}: {result.get('status_code', 'ERROR')}")
        
        return results
    
    def test_premium_user(self) -> List[Dict]:
        """Test endpoints as premium user"""
        print("\n💎 Testing as Premium User...")
        results = []
        
        # Simulate premium user
        self.session.cookies.set('premium_user', 'true')
        self.session.cookies.set('user_type', 'premium')
        self.session.cookies.set('subscription', 'active')
        
        endpoints = self.get_all_endpoints()
        
        for endpoint in endpoints:
            result = self.test_endpoint(endpoint, 'premium')
            results.append(result)
            
            if result['success'] and result.get('status_code') == 200:
                print(f"  ✅ {endpoint['name']}: Full access")
            else:
                print(f"  ⚠️  {endpoint['name']}: {result.get('status_code', 'ERROR')}")
        
        return results
    
    def analyze_results(self) -> Dict:
        """Analyze all test results"""
        analysis = {
            'total_endpoints': len(self.results),
            'successful_tests': len([r for r in self.results if r.get('success', False)]),
            'failed_tests': len([r for r in self.results if not r.get('success', False)]),
            'endpoints_with_errors': len(self.errors),
            'total_redirects': len(self.redirects),
            'demo_redirects': len([r for r in self.redirects if r['type'] == 'demo']),
            'login_redirects': len([r for r in self.redirects if r['type'] == 'login']),
            'average_response_time': sum(r.get('response_time', 0) for r in self.results if r.get('response_time')) / len([r for r in self.results if r.get('response_time')]) if self.results else 0,
            'error_details': self.errors,
            'redirect_details': self.redirects
        }
        
        return analysis
    
    def generate_report(self) -> str:
        """Generate comprehensive test report"""
        report = []
        report.append("=" * 80)
        report.append("AKSJERADAR ENDPOINT TEST REPORT")
        report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append(f"Base URL: {self.base_url}")
        report.append("=" * 80)
        
        # Test all scenarios
        scenarios = self.test_user_scenarios()
        
        # Analyze results
        analysis = self.analyze_results()
        
        # Summary
        report.append("\n📊 SUMMARY")
        report.append("-" * 40)
        report.append(f"Total Endpoints Tested: {analysis['total_endpoints']}")
        report.append(f"Successful Tests: {analysis['successful_tests']}")
        report.append(f"Failed Tests: {analysis['failed_tests']}")
        report.append(f"Endpoints with Errors: {analysis['endpoints_with_errors']}")
        report.append(f"Total Redirects: {analysis['total_redirects']}")
        report.append(f"  - Demo Redirects: {analysis['demo_redirects']}")
        report.append(f"  - Login Redirects: {analysis['login_redirects']}")
        report.append(f"Average Response Time: {analysis['average_response_time']:.3f}s")
        
        # Error Details
        if self.errors:
            report.append("\n❌ ERRORS FOUND")
            report.append("-" * 40)
            for error in self.errors[:10]:  # Show first 10 errors
                report.append(f"Endpoint: {error.get('endpoint', error.get('url', 'Unknown'))}")
                if 'errors' in error:
                    for err in error['errors']:
                        report.append(f"  - {err}")
                elif 'error' in error:
                    report.append(f"  - {error['error']}")
                report.append("")
        
        # Redirect Analysis
        report.append("\n🔀 REDIRECT ANALYSIS")
        report.append("-" * 40)
        demo_redirects = [r for r in self.redirects if r['type'] == 'demo']
        if demo_redirects:
            report.append("Demo Redirects (Expired Trial):")
            for redirect in demo_redirects[:5]:
                report.append(f"  {redirect['from']} → {redirect['to']}")
        
        # Demo Functionality Check
        report.append("\n🎭 DEMO FUNCTIONALITY")
        report.append("-" * 40)
        expired_trial_results = scenarios.get('expired_trial', [])
        demo_working = all(
            r.get('is_demo_redirect') or r.get('is_login_redirect') 
            for r in expired_trial_results 
            if r.get('success') and r['endpoint'] not in ['/demo', '/login', '/register', '/subscription', '/privacy']
        )
        
        if demo_working:
            report.append("✅ Demo redirect for expired trial users: WORKING")
        else:
            report.append("❌ Demo redirect for expired trial users: NOT WORKING PROPERLY")
            non_redirected = [
                r['endpoint'] for r in expired_trial_results 
                if r.get('success') and not r.get('is_demo_redirect') and not r.get('is_login_redirect')
                and r['endpoint'] not in ['/demo', '/login', '/register', '/subscription', '/privacy']
            ]
            if non_redirected:
                report.append("  Endpoints not redirecting to demo:")
                for endpoint in non_redirected[:5]:
                    report.append(f"    - {endpoint}")
        
        # Recommendations
        report.append("\n💡 RECOMMENDATIONS")
        report.append("-" * 40)
        
        if analysis['failed_tests'] > 0:
            report.append(f"- Fix {analysis['failed_tests']} failing endpoints")
        
        if analysis['endpoints_with_errors'] > 0:
            report.append(f"- Investigate {analysis['endpoints_with_errors']} endpoints showing error messages")
        
        if not demo_working:
            report.append("- Fix demo redirect logic for expired trial users")
        
        if analysis['average_response_time'] > 1.0:
            report.append(f"- Improve performance (avg response time: {analysis['average_response_time']:.3f}s)")
        
        report.append("\n" + "=" * 80)
        
        return "\n".join(report)
    
    def save_detailed_results(self, filename: str = "endpoint_test_results.json"):
        """Save detailed results to JSON file"""
        detailed_results = {
            'timestamp': datetime.now().isoformat(),
            'base_url': self.base_url,
            'summary': self.analyze_results(),
            'all_results': self.results,
            'errors': self.errors,
            'redirects': self.redirects
        }
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(detailed_results, f, indent=2, ensure_ascii=False)
        
        print(f"\n📄 Detailed results saved to: {filename}")


def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Test all Aksjeradar endpoints')
    parser.add_argument('--url', default='http://localhost:5002', 
                       help='Base URL to test (default: http://localhost:5002)')
    parser.add_argument('--output', default='endpoint_test_results.json',
                       help='Output file for detailed results')
    
    args = parser.parse_args()
    
    print("🧪 AKSJERADAR COMPREHENSIVE ENDPOINT TESTING")
    print("=" * 60)
    
    # Create tester and run tests
    tester = EndpointTester(args.url)
    
    try:
        # Generate and print report
        report = tester.generate_report()
        print(report)
        
        # Save detailed results
        tester.save_detailed_results(args.output)
        
        # Exit with appropriate code
        analysis = tester.analyze_results()
        if analysis['failed_tests'] > 0 or analysis['endpoints_with_errors'] > 0:
            sys.exit(1)
        else:
            sys.exit(0)
            
    except KeyboardInterrupt:
        print("\n🛑 Testing interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


# Testing all endpoints and URLs for errors and redirects

import pytest
from flask import url_for
from app import create_app

@pytest.fixture
def client():
    app = create_app('testing')
    app.config['TESTING'] = True
    ctx = app.app_context()
    ctx.push()
    with app.test_client() as client:
        yield client
    ctx.pop()

def build_url(client, endpoint, **values):
    """Safely build a URL for an endpoint inside a request context."""
    with client.application.test_request_context():
        return url_for(endpoint, **values)


def test_homepage(client):
    response = client.get(build_url(client, 'main.index'))
    assert response.status_code == 200


def test_language_switch(client):
    response = client.get(build_url(client, 'main.set_app_language', language='no'))
    assert response.status_code == 302  # Check for redirect


def test_invalid_language(client):
    response = client.get(build_url(client, 'main.set_app_language', language='invalid'))
    assert b'Invalid language selected' in response.data


def test_referrals(client):
    response = client.get(build_url(client, 'main.referrals'))
    assert response.status_code == 200


def test_send_referral(client):
    response = client.post(build_url(client, 'main.send_referral'), data={})  # Add necessary data
    assert response.status_code == 302  # Check for redirect


def test_stock_details(client):
    # Use legacy redirect endpoint which forwards to stocks.details
    response = client.get(build_url(client, 'main.stock_details_legacy_redirect', ticker='AAPL'), follow_redirects=True)
    assert response.status_code == 200


def test_market_overview(client):
    response = client.get(build_url(client, 'main.market_overview'))
    assert response.status_code == 200


def test_demo_ping(client):
    response = client.get(build_url(client, 'main.demo_ping'))
    assert response.status_code == 200
    assert response.json['status'] == 'ok'


def test_demo_echo(client):
    response = client.post(build_url(client, 'main.demo_echo'), data={'message': 'Hello'})
    assert response.status_code == 200


def test_auth(client):
    response = client.get(build_url(client, 'main.auth'))
    assert response.status_code == 200


def test_profile(client):
    response = client.get(build_url(client, 'main.profile'))
    assert response.status_code == 200


def test_debug_status(client):
    response = client.get(url_for('main.debug_status'))
    assert response.status_code == 200


def test_feedback(client):
    response = client.post(url_for('main.get_user_referral_code'), data={})  # Add necessary data
    assert response.status_code == 200


if __name__ == "__main__":
    main()