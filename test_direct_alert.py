#!/usr/bin/env python3
"""
Direct test for test alert endpoint
"""
import sys
import os
sys.path.append('/workspaces/aksjeny2')

from app import create_app

def test_alert_endpoint_direct():
    """Direct test of test alert endpoint"""
    app = create_app()
    
    with app.test_client() as client:
        # First test without auth
        response = client.post('/watchlist/test-alert')
        print(f"Without auth: {response.status_code}")
        print(f"Headers: {dict(response.headers)}")
        print(f"Data: {response.data.decode()[:200]}")
        
        # Test with basic session
        with client.session_transaction() as sess:
            sess['_user_id'] = '1'
            sess['_fresh'] = True
            
        response = client.post('/watchlist/test-alert')
        print(f"\nWith session: {response.status_code}")
        print(f"Headers: {dict(response.headers)}")
        print(f"Data: {response.data.decode()[:200]}")

if __name__ == "__main__":
    test_alert_endpoint_direct()