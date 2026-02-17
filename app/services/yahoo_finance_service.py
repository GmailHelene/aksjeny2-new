"""
Yahoo Finance integration service with proper error handling and caching
"""
try:
    import yfinance as yf
except ImportError:
    yf = None
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
try:
    import pandas as pd  # type: ignore
except Exception:
    pd = None  # type: ignore
from flask import current_app
from ..services.cache_service import get_cache_service
from ..services.rate_limiter import rate_limiter

logger = logging.getLogger(__name__)

class YahooFinanceService:
    """Service for fetching data from Yahoo Finance"""
    
    # Cache durations in seconds
    CACHE_DURATIONS = {
        'stock_info': 300,      # 5 minutes
        'stock_data': 60,       # 1 minute for price data
        'historical': 3600,     # 1 hour for historical data
        'financials': 86400,    # 24 hours for financial statements
    }
    
    @staticmethod
    def get_stock_info(ticker: str) -> Dict[str, Any]:
        """Get comprehensive stock information"""
        cache_key = f"yf:info:{ticker}"
        cached = get_cache_service().get(cache_key)
        if cached:
            return cached
        
        try:
            # Rate limiting
            rate_limiter.wait_if_needed('yahoo_finance')
            
            stock = yf.Ticker(ticker)
            info = stock.info
            
            # Process and clean the data
            processed_info = {
                'ticker': ticker,
                'longName': info.get('longName', ticker),
                'shortName': info.get('shortName', ticker),
                'sector': info.get('sector', 'Unknown'),
                'industry': info.get('industry', 'Unknown'),
                'currency': info.get('currency', 'NOK' if ticker.endswith('.OL') else 'USD'),
                'regularMarketPrice': info.get('currentPrice') or info.get('regularMarketPrice'),
                'regularMarketChange': info.get('regularMarketChange'),
                'regularMarketChangePercent': info.get('regularMarketChangePercent'),
                'regularMarketVolume': info.get('regularMarketVolume') or info.get('volume'),
                'marketCap': info.get('marketCap'),
                'trailingPE': info.get('trailingPE'),
                'forwardPE': info.get('forwardPE'),
                'priceToBook': info.get('priceToBook'),
                'dividendYield': info.get('dividendYield'),
                'beta': info.get('beta'),
                'fiftyTwoWeekLow': info.get('fiftyTwoWeekLow'),
                'fiftyTwoWeekHigh': info.get('fiftyTwoWeekHigh'),
                'dayLow': info.get('dayLow'),
                'dayHigh': info.get('dayHigh'),
                'volume': info.get('volume'),
                'averageVolume': info.get('averageVolume'),
                'bid': info.get('bid'),
                'ask': info.get('ask'),
                'bidSize': info.get('bidSize'),
                'askSize': info.get('askSize'),
                'previousClose': info.get('previousClose'),
                'open': info.get('open'),
                'earningsPerShare': info.get('trailingEps'),
                'bookValue': info.get('bookValue'),
                'priceToSalesTrailing12Months': info.get('priceToSalesTrailing12Months'),
                'profitMargins': info.get('profitMargins'),
                'operatingMargins': info.get('operatingMargins'),
                'returnOnAssets': info.get('returnOnAssets'),
                'returnOnEquity': info.get('returnOnEquity'),
                'revenueGrowth': info.get('revenueGrowth'),
                'earningsGrowth': info.get('earningsGrowth'),
                'currentRatio': info.get('currentRatio'),
                'debtToEquity': info.get('debtToEquity'),
                'totalRevenue': info.get('totalRevenue'),
                'revenuePerShare': info.get('revenuePerShare'),
                'totalCash': info.get('totalCash'),
                'totalDebt': info.get('totalDebt'),
                'description': info.get('longBusinessSummary', ''),
                'website': info.get('website', ''),
                'employees': info.get('fullTimeEmployees'),
                'country': info.get('country', 'Norway' if ticker.endswith('.OL') else 'USA'),
                'exchange': info.get('exchange', 'OSL' if ticker.endswith('.OL') else 'Unknown')
            }
            
            # Cache the result
            get_cache_service().set(cache_key, processed_info, YahooFinanceService.CACHE_DURATIONS['stock_info'])
            
            return processed_info
            
        except Exception as e:
            logger.error(f"Error fetching stock info for {ticker}: {str(e)}")
            return YahooFinanceService._get_fallback_info(ticker)
    
    @staticmethod
    def get_stock_data(ticker: str, period: str = "1d", interval: str = "1m"):
        """Get stock price data"""
        cache_key = f"yf:data:{ticker}:{period}:{interval}"
        cached = get_cache_service().get(cache_key)
        if cached and pd is not None:
            return pd.DataFrame(cached)  # type: ignore
        if cached and pd is None:
            return cached
        
        try:
            rate_limiter.wait_if_needed('yahoo_finance')
            
            stock = yf.Ticker(ticker)
            data = stock.history(period=period, interval=interval)
            
            if not data.empty:
                # Convert to dict for caching
                data_dict = data.reset_index().to_dict('records')
                get_cache_service().set(cache_key, data_dict, YahooFinanceService.CACHE_DURATIONS['stock_data'])
                
            return data
            
        except Exception as e:
            logger.error(f"Error fetching stock data for {ticker}: {str(e)}")
            return pd.DataFrame() if pd is not None else []
    
    @staticmethod
    def get_multiple_stocks_info(tickers: List[str]) -> Dict[str, Dict[str, Any]]:
        """Get info for multiple stocks efficiently"""
        result = {}
        
        for ticker in tickers:
            try:
                info = YahooFinanceService.get_stock_info(ticker)
                result[ticker] = info
            except Exception as e:
                logger.error(f"Error fetching info for {ticker}: {str(e)}")
                result[ticker] = YahooFinanceService._get_fallback_info(ticker)
        
        return result
    
    @staticmethod
    def get_historical_data(ticker: str, start_date: str, end_date: str):
        """Get historical price data"""
        cache_key = f"yf:hist:{ticker}:{start_date}:{end_date}"
        cached = get_cache_service().get(cache_key)
        if cached and pd is not None:
            return pd.DataFrame(cached)  # type: ignore
        if cached and pd is None:
            return cached
        
        try:
            rate_limiter.wait_if_needed('yahoo_finance')
            
            stock = yf.Ticker(ticker)
            data = stock.history(start=start_date, end=end_date)
            
            if not data.empty:
                # Convert to dict for caching
                data_dict = data.reset_index().to_dict('records')
                get_cache_service().set(cache_key, data_dict, YahooFinanceService.CACHE_DURATIONS['historical'])
            
            return data
            
        except Exception as e:
            logger.error(f"Error fetching historical data for {ticker}: {str(e)}")
            return pd.DataFrame() if pd is not None else []
    
    @staticmethod
    def get_financials(ticker: str) -> Dict[str, Any]:
        """Get financial statements"""
        cache_key = f"yf:financials:{ticker}"
        cached = get_cache_service().get(cache_key)
        if cached:
            return cached
        
        try:
            rate_limiter.wait_if_needed('yahoo_finance')
            
            stock = yf.Ticker(ticker)
            
            financials = {
                'income_statement': stock.financials.to_dict() if hasattr(stock, 'financials') else {},
                'balance_sheet': stock.balance_sheet.to_dict() if hasattr(stock, 'balance_sheet') else {},
                'cash_flow': stock.cashflow.to_dict() if hasattr(stock, 'cashflow') else {},
                'quarterly_income': stock.quarterly_financials.to_dict() if hasattr(stock, 'quarterly_financials') else {},
                'quarterly_balance': stock.quarterly_balance_sheet.to_dict() if hasattr(stock, 'quarterly_balance_sheet') else {},
                'quarterly_cashflow': stock.quarterly_cashflow.to_dict() if hasattr(stock, 'quarterly_cashflow') else {}
            }
            
            # Cache the result
            get_cache_service().set(cache_key, financials, YahooFinanceService.CACHE_DURATIONS['financials'])
            
            return financials
            
        except Exception as e:
            logger.error(f"Error fetching financials for {ticker}: {str(e)}")
            return {}
    
    @staticmethod
    def _get_fallback_info(ticker: str) -> Dict[str, Any]:
        """Return fallback data when API fails"""
        # Import fallback data from DataService
        from ..services.data_service import FALLBACK_OSLO_DATA, FALLBACK_GLOBAL_DATA
        
        # Check if we have fallback data
        if ticker in FALLBACK_OSLO_DATA:
            data = FALLBACK_OSLO_DATA[ticker]
        elif ticker in FALLBACK_GLOBAL_DATA:
            data = FALLBACK_GLOBAL_DATA[ticker]
        else:
            # Generic fallback
            data = {
                'ticker': ticker,
                'name': ticker,
                'last_price': 0,
                'change': 0,
                'change_percent': 0,
                'volume': 0
            }
        
        # Convert to Yahoo Finance format
        return {
            'ticker': ticker,
            'longName': data.get('name', ticker),
            'shortName': data.get('name', ticker),
            'currency': 'NOK' if ticker.endswith('.OL') else 'USD',
            'regularMarketPrice': data.get('last_price', 0),
            'regularMarketChange': data.get('change', 0),
            'regularMarketChangePercent': data.get('change_percent', 0),
            'regularMarketVolume': data.get('volume', 0),
            'sector': data.get('sector', 'Unknown'),
            '_fallback': True
        }
    
    @staticmethod
    def search_stocks(query: str) -> List[Dict[str, Any]]:
        """Search for stocks by name or ticker"""
        try:
            # For now, return a curated list of Norwegian stocks
            norwegian_stocks = [
                {'symbol': 'EQNR.OL', 'name': 'Equinor ASA', 'exchange': 'Oslo'},
                {'symbol': 'DNB.OL', 'name': 'DNB Bank ASA', 'exchange': 'Oslo'},
                {'symbol': 'TEL.OL', 'name': 'Telenor ASA', 'exchange': 'Oslo'},
                {'symbol': 'YAR.OL', 'name': 'Yara International ASA', 'exchange': 'Oslo'},
                {'symbol': 'NHY.OL', 'name': 'Norsk Hydro ASA', 'exchange': 'Oslo'},
                {'symbol': 'MOWI.OL', 'name': 'Mowi ASA', 'exchange': 'Oslo'},
                {'symbol': 'AKERBP.OL', 'name': 'Aker BP ASA', 'exchange': 'Oslo'},
                {'symbol': 'AKER.OL', 'name': 'Aker ASA', 'exchange': 'Oslo'},
                {'symbol': 'SUBC.OL', 'name': 'Subsea 7 SA', 'exchange': 'Oslo'},
                {'symbol': 'SCATC.OL', 'name': 'Scatec ASA', 'exchange': 'Oslo'}
            ]
            
            # Filter based on query
            query_lower = query.lower()
            results = [
                stock for stock in norwegian_stocks
                if query_lower in stock['symbol'].lower() or query_lower in stock['name'].lower()
            ]
            
            return results[:10]  # Limit to 10 results
            
        except Exception as e:
            logger.error(f"Error searching stocks: {str(e)}")
            return []

# Global instance
yahoo_finance_service = YahooFinanceService()
