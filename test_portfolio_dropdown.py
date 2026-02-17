#!/usr/bin/env python3
"""
Test script for portfolio dropdown functionality
"""
import sys
import os
sys.path.append('/workspaces/aksjeny2')

from app import create_app
from app.models import User, Portfolio, db
from flask import url_for
import requests

def test_portfolio_dropdown():
    """Test if portfolio dropdown switching works"""
    app = create_app()
    
    with app.app_context():
        # Check if we have any test users with multiple portfolios
        users_with_portfolios = db.session.query(User).join(Portfolio).group_by(User.id).all()
        
        print("=== Portfolio Dropdown Test ===")
        
        if not users_with_portfolios:
            print("❌ No users with portfolios found")
            return False
            
        # Find user with multiple portfolios
        test_user = None
        for user in users_with_portfolios:
            portfolio_count = Portfolio.query.filter_by(user_id=user.id).count()
            if portfolio_count > 1:
                test_user = user
                break
                
        if not test_user:
            print("❌ No users with multiple portfolios found")
            return False
            
        user_portfolios = Portfolio.query.filter_by(user_id=test_user.id).all()
        print(f"✓ Found user {test_user.username} with {len(user_portfolios)} portfolios:")
        
        for portfolio in user_portfolios:
            print(f"  - Portfolio ID: {portfolio.id}, Name: {portfolio.name or 'Unnamed'}")
            
        # Test portfolio URLs
        print("\n=== Testing Portfolio URLs ===")
        
        with app.test_client() as client:
            # First, login as the test user (simulate authenticated session)
            with client.session_transaction() as sess:
                sess['_user_id'] = str(test_user.id)
                sess['_fresh'] = True
                
            # Test default portfolio page
            response = client.get('/portfolio/')
            print(f"Default portfolio page: {response.status_code}")
            
            # Test each portfolio selection
            for portfolio in user_portfolios:
                response = client.get(f'/portfolio/?selected={portfolio.id}')
                print(f"Portfolio {portfolio.id} selection: {response.status_code}")
                
                if response.status_code != 200:
                    print(f"❌ Error accessing portfolio {portfolio.id}")
                    print(f"Response: {response.data.decode()[:200]}...")
                else:
                    print(f"✓ Successfully accessed portfolio {portfolio.id}")
                    
        return True

if __name__ == "__main__":
    test_portfolio_dropdown()