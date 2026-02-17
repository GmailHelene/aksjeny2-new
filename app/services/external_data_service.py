"""
Comprehensive External Data Sources Service for Aksjeradar
Integrates with multiple financial data providers and APIs
"""

import requests
try:
    import yfinance as yf
except ImportError:
    yf = None
# import pandas as pd
from datetime import datetime, timedelta
import logging
from typing import Dict, List, Optional, Any
import time
from functools import lru_cache
from .safe_yfinance import safe_ticker, get_fallback_stock_info
from functools import lru_cache
import json
import os

logger = logging.getLogger(__name__)

class ExternalDataService:
    """
    Comprehensive external data integration service
    Inspired by major competitors like:
    - E24 Børs
    - DN Børs 
    - Nordnet
    - Yahoo Finance
    - Morningstar
    - Bloomberg
    - TradingView
    """
    
    def __init__(self):
        self.cache = {}
        self.cache_duration = 300  # 5 minutes
        
        # API endpoints and configurations
        self.endpoints = {
            'oslo_bors': 'https://www.oslobors.no/ob/servlets/components/statistics/download',
            'ssb_statistics': 'https://data.ssb.no/api/v0/no/table/',
            'norges_bank': 'https://data.norges-bank.no/api/data/',
            'ecb_rates': 'https://api.exchangerate.host/latest',
            'fred_economic': 'https://api.stlouisfed.org/fred/series/observations',
            'tradingview': 'https://scanner.tradingview.com/norway/scan',
            'investing_com': 'https://api.investing.com/api/financialdata/',
            'morningstar': 'https://api.morningstar.com/proxies/markets/',
            'financial_modeling': 'https://financialmodelingprep.com/api/v3/',
            'alpha_vantage': 'https://www.alphavantage.co/query'
        }
        
        # API keys (to be set via environment variables)
        self.api_keys = {
            'alpha_vantage': os.getenv('ALPHA_VANTAGE_API_KEY'),
            'financial_modeling': os.getenv('FMP_API_KEY'),
            'fred': os.getenv('FRED_API_KEY'),
            'morningstar': os.getenv('MORNINGSTAR_API_KEY')
        }
    
    def _cache_key(self, service: str, params: str) -> str:
        """Generate cache key"""
        return f"{service}_{params}_{int(time.time() // self.cache_duration)}"
    
    def _get_cached_or_fetch(self, cache_key: str, fetch_func, *args, **kwargs):
        """Get cached data or fetch new"""
        if cache_key in self.cache:
            return self.cache[cache_key]
        
        try:
            data = fetch_func(*args, **kwargs)
            self.cache[cache_key] = data
            return data
        except Exception as e:
            logger.error(f"Error fetching data: {e}")
            return None
    
    # =================== OSLO BØRS DATA ===================
    
    def get_oslo_bors_real_time(self) -> Dict[str, Any]:
        """
        Get real-time Oslo Børs data
        Similar to E24 Børs and DN Børs functionality
        """
        cache_key = self._cache_key('oslo_bors', 'realtime')
        
        def fetch_data():
            try:
                # Use yfinance for Norwegian stocks
                tickers = ['EQNR.OL', 'DNB.OL', 'TEL.OL', 'MOWI.OL', 'NHY.OL', 'ORK.OL', 'YAR.OL', 'STL.OL']
                data = {}
                
                for ticker in tickers:
                    try:
                        stock = safe_ticker(ticker)
                        if stock is not None:
                            info = stock.info
                            hist = stock.history(period='2d')
                            
                            if not hist.empty:
                                current_price = hist['Close'].iloc[-1]
                                prev_close = hist['Close'].iloc[-2] if len(hist) > 1 else current_price
                                change = current_price - prev_close
                                change_pct = (change / prev_close) * 100 if prev_close else 0
                        else:
                            # Use fallback data when yfinance is not available
                            current_price = 100.0 + (hash(ticker) % 100)
                            prev_close = current_price * 0.99
                            change = current_price - prev_close
                            change_pct = (change / prev_close) * 100
                            info = get_fallback_stock_info(ticker)
                            
                            data[ticker] = {
                                'symbol': ticker,
                                'name': info.get('longName', ticker),
                                'price': round(current_price, 2),
                                'change': round(change, 2),
                                'change_percent': round(change_pct, 2),
                                'volume': info.get('volume', 0),
                                'market_cap': info.get('marketCap', 0),
                                'sector': info.get('sector', 'Unknown'),
                                'industry': info.get('industry', 'Unknown')
                            }
                    except Exception as e:
                        logger.warning(f"Error fetching {ticker}: {e}")
                
                return data
                
            except Exception as e:
                logger.error(f"Error fetching Oslo Børs data: {e}")
                return {}
        
        return self._get_cached_or_fetch(cache_key, fetch_data)
    
    def get_oslo_bors_indices(self) -> Dict[str, Any]:
        """Get Oslo Børs indices (OSEBX, OBX, etc.)"""
        cache_key = self._cache_key('oslo_indices', 'main')
        
        def fetch_data():
            indices = {
                '^OSEAX': 'OSEBX',  # Main index
                '^OBX': 'OBX',      # Top 25 companies
            }
            
            data = {}
            for symbol, name in indices.items():
                try:
                    ticker = safe_ticker(symbol)
                    if ticker is not None:
                        hist = ticker.history(period='2d')
                        
                        if not hist.empty:
                            current = hist['Close'].iloc[-1]
                            prev = hist['Close'].iloc[-2] if len(hist) > 1 else current
                            change = current - prev
                            change_pct = (change / prev) * 100 if prev else 0
                            
                            data[name] = {
                                'value': round(current, 2),
                            'change': round(change, 2),
                            'change_percent': round(change_pct, 2)
                        }
                except Exception as e:
                    logger.warning(f"Error fetching {symbol}: {e}")
            
            return data
        
        return self._get_cached_or_fetch(cache_key, fetch_data)
    
    # =================== GLOBAL MARKETS ===================
    
    def get_global_markets_overview(self) -> Dict[str, Any]:
        """
        Get global markets overview
        Similar to TradingView, Yahoo Finance functionality
        """
        cache_key = self._cache_key('global_markets', 'overview')
        
        def fetch_data():
            markets = {
                '^GSPC': 'S&P 500',
                '^DJI': 'Dow Jones',
                '^IXIC': 'NASDAQ',
                '^FTSE': 'FTSE 100',
                '^GDAXI': 'DAX',
                '^FCHI': 'CAC 40',
                '^N225': 'Nikkei 225',
                '^HSI': 'Hang Seng'
            }
            
            data = {}
            for symbol, name in markets.items():
                try:
                    ticker = yf.Ticker(symbol)
                    hist = ticker.history(period='2d')
                    
                    if not hist.empty:
                        current = hist['Close'].iloc[-1]
                        prev = hist['Close'].iloc[-2] if len(hist) > 1 else current
                        change = current - prev
                        change_pct = (change / prev) * 100 if prev else 0
                        
                        data[name] = {
                            'value': round(current, 2),
                            'change': round(change, 2),
                            'change_percent': round(change_pct, 2)
                        }
                except Exception as e:
                    logger.warning(f"Error fetching {symbol}: {e}")
            
            return data
        
        return self._get_cached_or_fetch(cache_key, fetch_data)
    
    # =================== CRYPTOCURRENCY ===================
    
    def get_crypto_overview(self) -> Dict[str, Any]:
        """
        Get cryptocurrency overview
        Similar to CoinMarketCap, CoinGecko functionality
        """
        cache_key = self._cache_key('crypto', 'overview')
        
        def fetch_data():
            cryptos = {
                'BTC-USD': 'Bitcoin',
                'ETH-USD': 'Ethereum',
                'BNB-USD': 'Binance Coin',
                'ADA-USD': 'Cardano',
                'DOT-USD': 'Polkadot',
                'MATIC-USD': 'Polygon',
                'AVAX-USD': 'Avalanche',
                'SOL-USD': 'Solana'
            }
            
            data = {}
            for symbol, name in cryptos.items():
                try:
                    ticker = yf.Ticker(symbol)
                    hist = ticker.history(period='2d')
                    
                    if not hist.empty:
                        current = hist['Close'].iloc[-1]
                        prev = hist['Close'].iloc[-2] if len(hist) > 1 else current
                        change = current - prev
                        change_pct = (change / prev) * 100 if prev else 0
                        
                        data[name] = {
                            'symbol': symbol,
                            'price': round(current, 2),
                            'change': round(change, 2),
                            'change_percent': round(change_pct, 2)
                        }
                except Exception as e:
                    logger.warning(f"Error fetching {symbol}: {e}")
            
            return data
        
        return self._get_cached_or_fetch(cache_key, fetch_data)
    
    # =================== CURRENCIES ===================
    
    def get_currency_rates(self) -> Dict[str, Any]:
        """
        Get currency exchange rates
        Similar to XE.com, Norges Bank functionality
        """
        cache_key = self._cache_key('currencies', 'rates')
        
        def fetch_data():
            try:
                # Primary: Try exchange rate API
                response = requests.get(
                    'https://api.exchangerate.host/latest?base=NOK',
                    timeout=10
                )
                
                if response.status_code == 200:
                    data = response.json()
                    rates = data.get('rates', {})
                    
                    return {
                        'USD/NOK': round(1 / rates.get('USD', 1), 4),
                        'EUR/NOK': round(1 / rates.get('EUR', 1), 4),
                        'GBP/NOK': round(1 / rates.get('GBP', 1), 4),
                        'SEK/NOK': round(1 / rates.get('SEK', 1), 4),
                        'DKK/NOK': round(1 / rates.get('DKK', 1), 4),
                        'CHF/NOK': round(1 / rates.get('CHF', 1), 4)
                    }
                
            except Exception as e:
                logger.warning(f"Primary currency API failed: {e}")
                
            # Fallback: Use yfinance
            try:
                currencies = {
                    'USDNOK=X': 'USD/NOK',
                    'EURNOK=X': 'EUR/NOK',
                    'GBPNOK=X': 'GBP/NOK',
                    'SEKNOK=X': 'SEK/NOK'
                }
                
                data = {}
                for symbol, name in currencies.items():
                    try:
                        ticker = yf.Ticker(symbol)
                        hist = ticker.history(period='1d')
                        
                        if not hist.empty:
                            data[name] = round(hist['Close'].iloc[-1], 4)
                    except Exception as e:
                        logger.warning(f"Error fetching {symbol}: {e}")
                
                return data
                
            except Exception as e:
                logger.error(f"Currency fallback failed: {e}")
                return {}
        
        return self._get_cached_or_fetch(cache_key, fetch_data)
    
    # =================== ECONOMIC INDICATORS ===================
    
    def get_economic_indicators(self) -> Dict[str, Any]:
        """
        Get Norwegian and global economic indicators
        Similar to SSB, Statistics Norway, FRED functionality
        """
        cache_key = self._cache_key('economic', 'indicators')
        
        def fetch_data():
            indicators = {}
            
            try:
                # Norwegian Government Bond 10Y
                bond_ticker = safe_ticker('TNX')  # US 10Y as proxy
                if bond_ticker is not None:
                    bond_hist = bond_ticker.history(period='2d')
                    
                    if not bond_hist.empty:
                        indicators['10Y_Bond_Yield'] = {
                            'value': round(bond_hist['Close'].iloc[-1], 2),
                            'unit': '%'
                        }
                
                # Oil price (Brent) - crucial for Norwegian economy
                oil_ticker = safe_ticker('BZ=F')
                if oil_ticker is not None:
                    oil_hist = oil_ticker.history(period='2d')
                    
                    if not oil_hist.empty:
                        current = oil_hist['Close'].iloc[-1]
                        prev = oil_hist['Close'].iloc[-2] if len(oil_hist) > 1 else current
                        change_pct = ((current - prev) / prev) * 100 if prev else 0
                    
                    indicators['Brent_Oil'] = {
                        'value': round(current, 2),
                        'change_percent': round(change_pct, 2),
                        'unit': 'USD/barrel'
                    }
                
                # VIX (Fear index)
                vix_ticker = safe_ticker('^VIX')
                if vix_ticker is not None:
                    vix_hist = vix_ticker.history(period='2d')
                    
                    if not vix_hist.empty:
                        indicators['VIX'] = {
                            'value': round(vix_hist['Close'].iloc[-1], 2),
                        'unit': 'points'
                    }
                
            except Exception as e:
                logger.error(f"Error fetching economic indicators: {e}")
            
            return indicators
        
        return self._get_cached_or_fetch(cache_key, fetch_data)
    
    # =================== NEWS & SENTIMENT ===================
    
    def get_financial_news(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get financial news aggregated from multiple sources
        Similar to Bloomberg, Reuters, E24 functionality
        """
        cache_key = self._cache_key('news', f'limit_{limit}')
        
        def fetch_data():
            # This would integrate with news APIs like:
            # - NewsAPI
            # - E24 RSS
            # - DN RSS
            # - Bloomberg API
            # - Reuters API
            
            # For now, return sample news structure
            sample_news = [
                {
                    'title': 'Oslo Børs åpner høyere etter sterke USA-tall',
                    'summary': 'Hovedindeksen stiger 0.8% i åpningen etter positive signaler fra amerikansk økonomi.',
                    'source': 'E24',
                    'published': datetime.now() - timedelta(hours=1),
                    'category': 'market',
                    'relevance': 'high'
                },
                {
                    'title': 'Equinor rapporterer rekordresultat',
                    'summary': 'Oljeselskapet overrasker positivt med kvartalstall som overgår forventningene.',
                    'source': 'DN',
                    'published': datetime.now() - timedelta(hours=2),
                    'category': 'earnings',
                    'relevance': 'high'
                }
            ]
            
            return sample_news[:limit]
        
        return self._get_cached_or_fetch(cache_key, fetch_data)
    
    # =================== COMPREHENSIVE DATA ===================
    
    def get_comprehensive_market_data(self) -> Dict[str, Any]:
        """
        Get comprehensive market data combining all sources
        This is the main method competitors would use for dashboard
        """
        return {
            'oslo_bors': self.get_oslo_bors_real_time(),
            'oslo_indices': self.get_oslo_bors_indices(),
            'global_markets': self.get_global_markets_overview(),
            'cryptocurrencies': self.get_crypto_overview(),
            'currencies': self.get_currency_rates(),
            'economic_indicators': self.get_economic_indicators(),
            'financial_news': self.get_financial_news(5),
            'last_updated': datetime.now().isoformat()
        }
    
    # =================== COMPETITOR-INSPIRED FEATURES ===================
    
    def get_sector_performance(self) -> Dict[str, Any]:
        """
        Sector performance analysis inspired by Morningstar, Yahoo Finance
        """
        sectors = {
            'Technology': ['AAPL', 'MSFT', 'GOOGL'],
            'Energy': ['EQNR.OL', 'XOM', 'CVX'],
            'Healthcare': ['JNJ', 'PFE', 'UNH'],
            'Finance': ['DNB.OL', 'JPM', 'BAC']
        }
        
        sector_data = {}
        
        for sector, tickers in sectors.items():
            try:
                performances = []
                for ticker in tickers:
                    stock = yf.Ticker(ticker)
                    hist = stock.history(period='5d')
                    
                    if len(hist) >= 2:
                        change_pct = ((hist['Close'].iloc[-1] - hist['Close'].iloc[0]) / hist['Close'].iloc[0]) * 100
                        performances.append(change_pct)
                
                if performances:
                    avg_performance = sum(performances) / len(performances)
                    sector_data[sector] = round(avg_performance, 2)
                    
            except Exception as e:
                logger.warning(f"Error calculating sector {sector}: {e}")
        
        return sector_data
    
    def get_market_sentiment(self) -> Dict[str, Any]:
        """
        Market sentiment analysis inspired by TradingView, Investing.com
        """
        try:
            # Simple sentiment based on major indices performance
            indices = ['^GSPC', '^IXIC', '^DJI']
            positive_count = 0
            total_count = 0
            
            for index in indices:
                try:
                    ticker = yf.Ticker(index)
                    hist = ticker.history(period='2d')
                    
                    if len(hist) >= 2:
                        change = hist['Close'].iloc[-1] - hist['Close'].iloc[-2]
                        if change > 0:
                            positive_count += 1
                        total_count += 1
                except:
                    continue
            
            if total_count > 0:
                sentiment_score = positive_count / total_count
                
                if sentiment_score >= 0.67:
                    sentiment = 'Bullish'
                elif sentiment_score <= 0.33:
                    sentiment = 'Bearish'
                else:
                    sentiment = 'Neutral'
                
                return {
                    'sentiment': sentiment,
                    'score': round(sentiment_score, 2),
                    'confidence': 'Medium'
                }
            
        except Exception as e:
            logger.error(f"Error calculating sentiment: {e}")
        
        return {
            'sentiment': 'Neutral',
            'score': 0.5,
            'confidence': 'Low'
        }
    
    def get_social_sentiment(self, ticker):
        """
        Get social sentiment data for a stock ticker
        This method should integrate with real social media APIs
        Currently returns None to indicate real-time data is needed
        """
        # TODO: Integrate with real APIs:
        # - Twitter API v2 for tweet sentiment
        # - Reddit API for r/stocks, r/investing mentions
        # - Financial forums like Yahoo Finance, SeekingAlpha
        # - News sentiment from financial news sources
        
        # For now, return None to indicate no real data available
        return None

# Global instance
external_data_service = ExternalDataService()
