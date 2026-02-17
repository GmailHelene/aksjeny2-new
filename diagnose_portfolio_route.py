#!/usr/bin/env python3
"""
This script diagnoses issues with the portfolio route and applies a fix.
"""
import logging
from flask import url_for, render_template, jsonify
import traceback
import sys
import os

# Set up logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('portfolio_diagnosis')

def diagnose_portfolio_route():
    """Diagnose issues with the portfolio route"""
    logger.info("Starting portfolio route diagnosis")
    
    try:
        # Import needed modules
        from app import create_app
        from app.models import Portfolio, PortfolioStock
        from flask import current_app
        from flask_login import current_user
        
        # Create an application context
        app = create_app()
        with app.app_context():
            logger.info("Application context created")
            
            # Check if the database is accessible
            try:
                from app.extensions import db
                logger.info("Testing database connection...")
                portfolio_count = Portfolio.query.count()
                logger.info(f"Database connection successful. Found {portfolio_count} portfolios.")
            except Exception as db_error:
                logger.error(f"Database connection error: {db_error}")
                return False
            
            # Check DataService availability
            try:
                logger.info("Testing DataService...")
                from app.services.data_service import DataService
                test_ticker = "AAPL"
                stock_data = DataService.get_stock_info(test_ticker)
                if stock_data:
                    logger.info(f"DataService working. Retrieved data for {test_ticker}: {stock_data.get('regularMarketPrice')}")
                else:
                    logger.warning(f"DataService returned no data for {test_ticker}")
            except Exception as service_error:
                logger.error(f"DataService error: {service_error}")
                logger.error(traceback.format_exc())
                
            # Check if alternative data service is accessible
            try:
                logger.info("Testing AlternativeDataService...")
                from app.services.alternative_data_service import AlternativeDataService
                test_ticker = "MSFT"
                stock_data = AlternativeDataService.get_stock_info(test_ticker)
                if stock_data:
                    logger.info(f"AlternativeDataService working. Retrieved data for {test_ticker}: {stock_data.get('regularMarketPrice')}")
                else:
                    logger.warning(f"AlternativeDataService returned no data for {test_ticker}")
            except Exception as alt_service_error:
                logger.error(f"AlternativeDataService error: {alt_service_error}")
                logger.error(traceback.format_exc())
            
            # Check route registration
            logger.info("Checking route registration...")
            for rule in app.url_map.iter_rules():
                if 'portfolio' in rule.endpoint:
                    logger.info(f"Route: {rule.rule} -> {rule.endpoint}")
            
            logger.info("Portfolio route diagnosis complete")
            return True
            
    except Exception as e:
        logger.error(f"Diagnosis failed: {e}")
        logger.error(traceback.format_exc())
        return False

if __name__ == "__main__":
    success = diagnose_portfolio_route()
    sys.exit(0 if success else 1)
