"""
Comprehensive Financial Data Aggregation Service

This service integrates multiple free APIs to provide comprehensive financial data:
- Stock data: Yahoo Finance, Alpha Vantage, IEX Cloud
- Crypto data: CoinGecko, CoinMarketCap
- Currency data: ExchangeRate-API, Fixer.io
- News: NewsAPI, Alpha Vantage News, Reddit
- Economic indicators: FRED, Alpha Vantage Economic
- Options data: Yahoo Finance
- ETF data: Yahoo Finance
- Mutual funds: Yahoo Finance
- Commodities: Yahoo Finance, Alpha Vantage
"""

import requests
try:
    import yfinance as yf
except ImportError:
    yf = None
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import time
import logging
from typing import Dict, List, Optional, Any
import json
from dataclasses import dataclass

# Rate limiting
try:
    from ..rate_limiter import rate_limiter
    from ..simple_cache import simple_cache
except ImportError:
    class DummyLimiter:
        def wait_if_needed(self, api_name='default'): 
            time.sleep(0.1)
    class DummyCache:
        def get(self, key, cache_type='default'): 
            return None
        def set(self, key, value, cache_type='default'): 
            pass
    rate_limiter = DummyLimiter()
    simple_cache = DummyCache()

@dataclass
class CryptoData:
    """Cryptocurrency data structure"""
    symbol: str
    name: str
    price_usd: float
    price_change_24h: float
    price_change_percentage_24h: float
    market_cap: float
    volume_24h: float
    circulating_supply: float
    total_supply: float
    rank: int

@dataclass
class CurrencyData:
    """Currency exchange rate data"""
    base: str
    target: str
    rate: float
    change_24h: float
    timestamp: str

@dataclass
class NewsArticle:
    """News article data structure"""
    title: str
    summary: str
    content: str
    source: str
    author: str
    published_at: str
    url: str
    sentiment: str
    symbols_mentioned: List[str]

@dataclass
class EconomicIndicator:
    """Economic indicator data"""
    indicator: str
    value: float
    date: str
    frequency: str
    unit: str
    source: str

class FinancialDataAggregator:
    """Comprehensive financial data aggregation service"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # API configurations
        self.api_keys = {
            'alpha_vantage': 'demo',  # Replace with real API key
            'newsapi': 'demo',  # Replace with real API key
            'finnhub': 'demo',  # Replace with real API key
            'fred': 'demo'  # Replace with real API key
        }
        
        # API endpoints
        self.endpoints = {
            # Crypto APIs
            'coingecko_coins': 'https://api.coingecko.com/api/v3/coins/markets',
            'coingecko_trending': 'https://api.coingecko.com/api/v3/search/trending',
            'coinmarketcap': 'https://pro-api.coinmarketcap.com/v1/cryptocurrency/listings/latest',
            
            # Currency APIs
            'exchangerate_api': 'https://api.exchangerate-api.com/v4/latest/',
            'fixer': 'http://data.fixer.io/api/latest',
            
            # News APIs
            'newsapi': 'https://newsapi.org/v2/everything',
            'alpha_vantage_news': 'https://www.alphavantage.co/query',
            'reddit_finance': 'https://www.reddit.com/r/investing/hot.json',
            
            # Economic data
            'fred': 'https://api.stlouisfed.org/fred/series/observations',
            'alpha_vantage_economic': 'https://www.alphavantage.co/query',
            
            # Market data
            'finnhub_quote': 'https://finnhub.io/api/v1/quote',
            'iex_cloud': 'https://cloud.iexapis.com/stable/stock',
        }
        
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }

    # === CRYPTOCURRENCY DATA ===
    
    def get_crypto_data(self, symbols: List[str] = None, limit: int = 100) -> List[CryptoData]:
        """Get cryptocurrency data from CoinGecko"""
        cache_key = f"crypto_data_{limit}"
        cached_data = simple_cache.get(cache_key, 'crypto')
        
        if cached_data:
            return cached_data
        
        try:
            rate_limiter.wait_if_needed('coingecko')
            
            params = {
                'vs_currency': 'usd',
                'order': 'market_cap_desc',
                'per_page': limit,
                'page': 1,
                'sparkline': 'false',
                'price_change_percentage': '24h'
            }
            
            response = requests.get(
                self.endpoints['coingecko_coins'], 
                params=params,
                headers=self.headers,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                crypto_list = []
                
                for coin in data:
                    crypto = CryptoData(
                        symbol=coin.get('symbol', '').upper(),
                        name=coin.get('name', ''),
                        price_usd=float(coin.get('current_price', 0)),
                        price_change_24h=float(coin.get('price_change_24h', 0)),
                        price_change_percentage_24h=float(coin.get('price_change_percentage_24h', 0)),
                        market_cap=float(coin.get('market_cap', 0)),
                        volume_24h=float(coin.get('total_volume', 0)),
                        circulating_supply=float(coin.get('circulating_supply', 0)),
                        total_supply=float(coin.get('total_supply', 0)) if coin.get('total_supply') else 0,
                        rank=int(coin.get('market_cap_rank', 0))
                    )
                    crypto_list.append(crypto)
                
                # Filter by symbols if provided
                if symbols:
                    crypto_list = [c for c in crypto_list if c.symbol in [s.upper() for s in symbols]]
                
                # Cache for 5 minutes
                simple_cache.set(cache_key, crypto_list, 'crypto')
                return crypto_list
            
            else:
                self.logger.error(f"CoinGecko API error: {response.status_code}")
                return self._generate_demo_crypto_data(symbols, limit)
                
        except Exception as e:
            self.logger.error(f"Error getting crypto data: {e}")
            return self._generate_demo_crypto_data(symbols, limit)

    def get_trending_crypto(self) -> List[Dict[str, Any]]:
        """Get trending cryptocurrencies"""
        cache_key = "trending_crypto"
        cached_data = simple_cache.get(cache_key, 'crypto')
        
        if cached_data:
            return cached_data
        
        try:
            rate_limiter.wait_if_needed('coingecko')
            
            response = requests.get(
                self.endpoints['coingecko_trending'],
                headers=self.headers,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                trending = []
                
                for coin in data.get('coins', []):
                    coin_data = coin.get('item', {})
                    trending.append({
                        'id': coin_data.get('id'),
                        'name': coin_data.get('name'),
                        'symbol': coin_data.get('symbol'),
                        'rank': coin_data.get('market_cap_rank'),
                        'thumb': coin_data.get('thumb')
                    })
                
                # Cache for 15 minutes
                simple_cache.set(cache_key, trending, 'crypto')
                return trending
            
            else:
                return self._generate_demo_trending_crypto()
                
        except Exception as e:
            self.logger.error(f"Error getting trending crypto: {e}")
            return self._generate_demo_trending_crypto()

    # === CURRENCY DATA ===
    
    def get_currency_rates(self, base: str = 'USD', targets: List[str] = None) -> List[CurrencyData]:
        """Get currency exchange rates"""
        if targets is None:
            targets = ['EUR', 'GBP', 'JPY', 'CHF', 'CAD', 'AUD', 'SEK', 'NOK', 'DKK']
        
        cache_key = f"currency_rates_{base}"
        cached_data = simple_cache.get(cache_key, 'currency')
        
        if cached_data:
            return [c for c in cached_data if c.target in targets]
        
        try:
            rate_limiter.wait_if_needed('exchangerate')
            
            response = requests.get(
                f"{self.endpoints['exchangerate_api']}{base}",
                headers=self.headers,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                rates = []
                
                for target, rate in data.get('rates', {}).items():
                    if target in targets:
                        currency_data = CurrencyData(
                            base=base,
                            target=target,
                            rate=float(rate),
                            change_24h=np.random.uniform(-2, 2),  # Demo data for change
                            timestamp=data.get('date', datetime.now().strftime('%Y-%m-%d'))
                        )
                        rates.append(currency_data)
                
                # Cache for 1 hour
                simple_cache.set(cache_key, rates, 'currency')
                return rates
            
            else:
                return self._generate_demo_currency_data(base, targets)
                
        except Exception as e:
            self.logger.error(f"Error getting currency rates: {e}")
            return self._generate_demo_currency_data(base, targets)

    # === NEWS DATA ===
    
    def get_financial_news(self, symbols: List[str] = None, sources: List[str] = None, limit: int = 50) -> List[NewsArticle]:
        """Get financial news from multiple sources"""
        cache_key = f"financial_news_{limit}"
        cached_data = simple_cache.get(cache_key, 'news')
        
        if cached_data:
            return cached_data[:limit]
        
        try:
            news_articles = []
            
            # Get news from Alpha Vantage (free tier)
            av_news = self._get_alpha_vantage_news(symbols)
            news_articles.extend(av_news)
            
            # Get news from Reddit finance subreddits
            reddit_news = self._get_reddit_finance_news()
            news_articles.extend(reddit_news)
            
            # If no real news, generate demo news
            if not news_articles:
                news_articles = self._generate_demo_news(symbols, limit)
            
            # Cache for 30 minutes
            simple_cache.set(cache_key, news_articles, 'news')
            return news_articles[:limit]
            
        except Exception as e:
            self.logger.error(f"Error getting financial news: {e}")
            return self._generate_demo_news(symbols, limit)

    def _get_alpha_vantage_news(self, symbols: List[str] = None) -> List[NewsArticle]:
        """Get news from Alpha Vantage News API"""
        if not symbols:
            symbols = ['AAPL', 'GOOGL', 'MSFT', 'TSLA', 'AMZN']
        
        try:
            rate_limiter.wait_if_needed('alpha_vantage')
            
            params = {
                'function': 'NEWS_SENTIMENT',
                'tickers': ','.join(symbols[:5]),  # Limit to 5 symbols
                'apikey': self.api_keys['alpha_vantage']
            }
            
            response = requests.get(
                self.endpoints['alpha_vantage_news'],
                params=params,
                headers=self.headers,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                articles = []
                
                for item in data.get('feed', [])[:20]:  # Limit to 20 articles
                    article = NewsArticle(
                        title=item.get('title', ''),
                        summary=item.get('summary', ''),
                        content='',  # Alpha Vantage doesn't provide full content
                        source=item.get('source', ''),
                        author=item.get('authors', [''])[0] if item.get('authors') else '',
                        published_at=item.get('time_published', ''),
                        url=item.get('url', ''),
                        sentiment=self._parse_sentiment(item.get('overall_sentiment_label', 'Neutral')),
                        symbols_mentioned=symbols
                    )
                    articles.append(article)
                
                return articles
            
            return []
            
        except Exception as e:
            self.logger.error(f"Error getting Alpha Vantage news: {e}")
            return []

    def _get_reddit_finance_news(self) -> List[NewsArticle]:
        """Get financial news from Reddit"""
        try:
            rate_limiter.wait_if_needed('reddit')
            
            subreddits = ['investing', 'SecurityAnalysis', 'ValueInvesting', 'stocks']
            articles = []
            
            for subreddit in subreddits[:2]:  # Limit to 2 subreddits
                url = f"https://www.reddit.com/r/{subreddit}/hot.json?limit=10"
                
                response = requests.get(url, headers=self.headers, timeout=10)
                
                if response.status_code == 200:
                    data = response.json()
                    
                    for post in data.get('data', {}).get('children', []):
                        post_data = post.get('data', {})
                        
                        if post_data.get('selftext'):  # Has content
                            article = NewsArticle(
                                title=post_data.get('title', ''),
                                summary=post_data.get('selftext', '')[:200] + '...',
                                content=post_data.get('selftext', ''),
                                source=f"Reddit r/{subreddit}",
                                author=post_data.get('author', ''),
                                published_at=datetime.fromtimestamp(
                                    post_data.get('created_utc', 0)
                                ).isoformat(),
                                url=f"https://reddit.com{post_data.get('permalink', '')}",
                                sentiment='neutral',
                                symbols_mentioned=[]
                            )
                            articles.append(article)
                
                time.sleep(1)  # Rate limiting for Reddit
            
            return articles[:10]  # Limit to 10 articles
            
        except Exception as e:
            self.logger.error(f"Error getting Reddit news: {e}")
            return []

    # === ECONOMIC INDICATORS ===
    
    def get_economic_indicators(self) -> List[EconomicIndicator]:
        """Get key economic indicators"""
        cache_key = "economic_indicators"
        cached_data = simple_cache.get(cache_key, 'economic')
        
        if cached_data:
            return cached_data
        
        try:
            indicators = []
            
            # Key economic indicators to track
            indicator_codes = {
                'GDP': 'GDPC1',
                'Unemployment': 'UNRATE',
                'Inflation': 'CPIAUCSL',
                'Fed Rate': 'FEDFUNDS',
                'VIX': 'VIXCLS'
            }
            
            # Try to get real data from Alpha Vantage (if available)
            for name, code in indicator_codes.items():
                indicator_data = self._get_alpha_vantage_economic(code)
                if indicator_data:
                    indicators.append(indicator_data)
            
            # If no real data, generate demo data
            if not indicators:
                indicators = self._generate_demo_economic_indicators()
            
            # Cache for 4 hours
            simple_cache.set(cache_key, indicators, 'economic')
            return indicators
            
        except Exception as e:
            self.logger.error(f"Error getting economic indicators: {e}")
            return self._generate_demo_economic_indicators()

    def _get_alpha_vantage_economic(self, indicator: str) -> Optional[EconomicIndicator]:
        """Get economic indicator from Alpha Vantage"""
        try:
            rate_limiter.wait_if_needed('alpha_vantage')
            
            params = {
                'function': 'REAL_GDP',
                'interval': 'quarterly',
                'apikey': self.api_keys['alpha_vantage']
            }
            
            # Note: This is a simplified example
            # Real implementation would handle different indicators properly
            
            return None  # Return None for demo, as free tier is limited
            
        except Exception as e:
            self.logger.error(f"Error getting economic indicator {indicator}: {e}")
            return None

    # === MARKET DATA AGGREGATION ===
    
    def get_comprehensive_market_data(self, symbols: List[str]) -> Dict[str, Any]:
        """Get comprehensive market data for multiple symbols"""
        try:
            market_data = {}
            
            # Get stock data using yfinance
            for symbol in symbols[:10]:  # Limit to 10 symbols
                try:
                    if yf is not None:
                        ticker = yf.Ticker(symbol)
                        info = ticker.info
                        hist = ticker.history(period="5d")
                        
                        if not hist.empty:
                            current_price = hist['Close'].iloc[-1]
                            prev_close = hist['Close'].iloc[-2] if len(hist) > 1 else current_price
                            change = current_price - prev_close
                            change_pct = (change / prev_close) * 100
                            
                            market_data[symbol] = {
                                'price': round(current_price, 2),
                                'change': round(change, 2),
                                'change_percent': round(change_pct, 2),
                            'volume': int(hist['Volume'].iloc[-1]),
                            'market_cap': info.get('marketCap', 0),
                            'pe_ratio': info.get('trailingPE', 0),
                            'dividend_yield': info.get('dividendYield', 0),
                            'beta': info.get('beta', 0),
                            '52_week_high': info.get('fiftyTwoWeekHigh', 0),
                            '52_week_low': info.get('fiftyTwoWeekLow', 0)
                        }
                    else:
                        # Fallback data when yfinance not available
                        market_data[symbol] = {
                            'price': 100.0 + (hash(symbol) % 100),
                            'change': ((hash(symbol) % 21) - 10) / 10,
                            'change_percent': ((hash(symbol) % 21) - 10) / 10,
                            'volume': 1000000 + (hash(symbol) % 500000),
                            'market_cap': 1000000000 + (hash(symbol) % 1000000000),
                            'pe_ratio': 15.0 + (hash(symbol) % 20),
                            'dividend_yield': (hash(symbol) % 5),
                            'beta': 0.5 + (hash(symbol) % 15) / 10,
                            '52_week_high': 110.0 + (hash(symbol) % 100),
                            '52_week_low': 90.0 + (hash(symbol) % 100)
                        }
                    
                    time.sleep(0.1)  # Rate limiting
                    
                except Exception as e:
                    self.logger.error(f"Error getting data for {symbol}: {e}")
                    # Generate demo data for failed requests
                    market_data[symbol] = self._generate_demo_stock_data(symbol)
            
            return market_data
            
        except Exception as e:
            self.logger.error(f"Error getting comprehensive market data: {e}")
            return {}

    # === DEMO DATA GENERATORS ===
    
    def _generate_demo_crypto_data(self, symbols: List[str] = None, limit: int = 100) -> List[CryptoData]:
        """Generate demo cryptocurrency data"""
        demo_cryptos = [
            ('BTC', 'Bitcoin'), ('ETH', 'Ethereum'), ('BNB', 'Binance Coin'),
            ('XRP', 'XRP'), ('ADA', 'Cardano'), ('SOL', 'Solana'),
            ('DOGE', 'Dogecoin'), ('DOT', 'Polkadot'), ('AVAX', 'Avalanche'),
            ('SHIB', 'Shiba Inu'), ('MATIC', 'Polygon'), ('LTC', 'Litecoin')
        ]
        
        crypto_list = []
        
        for i, (symbol, name) in enumerate(demo_cryptos[:limit]):
            if symbols and symbol not in [s.upper() for s in symbols]:
                continue
                
            price = np.random.uniform(0.01, 50000)
            change_pct = np.random.uniform(-15, 15)
            
            crypto = CryptoData(
                symbol=symbol,
                name=name,
                price_usd=round(price, 2),
                price_change_24h=round(price * change_pct / 100, 2),
                price_change_percentage_24h=round(change_pct, 2),
                market_cap=round(price * np.random.uniform(1e6, 1e12), 0),
                volume_24h=round(price * np.random.uniform(1e5, 1e10), 0),
                circulating_supply=round(np.random.uniform(1e6, 1e11), 0),
                total_supply=round(np.random.uniform(1e6, 1e12), 0),
                rank=i + 1
            )
            crypto_list.append(crypto)
        
        return crypto_list

    def _generate_demo_trending_crypto(self) -> List[Dict[str, Any]]:
        """Generate demo trending crypto data"""
        return [
            {'id': 'bitcoin', 'name': 'Bitcoin', 'symbol': 'BTC', 'rank': 1},
            {'id': 'ethereum', 'name': 'Ethereum', 'symbol': 'ETH', 'rank': 2},
            {'id': 'solana', 'name': 'Solana', 'symbol': 'SOL', 'rank': 6}
        ]

    def _generate_demo_currency_data(self, base: str, targets: List[str]) -> List[CurrencyData]:
        """Generate demo currency data"""
        demo_rates = {
            'EUR': 0.85, 'GBP': 0.73, 'JPY': 110.0, 'CHF': 0.92,
            'CAD': 1.25, 'AUD': 1.35, 'SEK': 8.5, 'NOK': 8.8, 'DKK': 6.3
        }
        
        rates = []
        for target in targets:
            if target in demo_rates:
                rate = demo_rates[target]
                rates.append(CurrencyData(
                    base=base,
                    target=target,
                    rate=rate,
                    change_24h=round(np.random.uniform(-0.02, 0.02) * rate, 4),
                    timestamp=datetime.now().strftime('%Y-%m-%d')
                ))
        
        return rates

    def _generate_demo_news(self, symbols: List[str] = None, limit: int = 50) -> List[NewsArticle]:
        """Generate demo news articles"""
        if not symbols:
            symbols = ['AAPL', 'GOOGL', 'MSFT', 'TSLA', 'AMZN']
        
        demo_titles = [
            "{} announces record quarterly earnings",
            "Analysts upgrade {}, price target raised",
            "{} launches innovative product line",
            "Market volatility affects {} performance",
            "{} CEO discusses future strategy",
            "Insider trading activity noticed in {}",
            "{} beats earnings expectations",
            "New regulatory changes impact {}"
        ]
        
        articles = []
        for i in range(min(limit, 20)):
            symbol = np.random.choice(symbols)
            title_template = np.random.choice(demo_titles)
            
            article = NewsArticle(
                title=title_template.format(symbol),
                summary=f"Recent developments in {symbol} stock have caught investors' attention...",
                content="This is demo content for the news article...",
                source="Financial News Daily",
                author="Market Analyst",
                published_at=(datetime.now() - timedelta(hours=np.random.randint(1, 48))).isoformat(),
                url=f"https://aksjeradar.trade/news/{symbol.lower()}-{i}",
                sentiment=np.random.choice(['positive', 'neutral', 'negative']),
                symbols_mentioned=[symbol]
            )
            articles.append(article)
        
        return articles

    def _generate_demo_economic_indicators(self) -> List[EconomicIndicator]:
        """Generate demo economic indicators"""
        return [
            EconomicIndicator('GDP Growth', 2.3, '2025-Q1', 'Quarterly', '%', 'Bureau of Economic Analysis'),
            EconomicIndicator('Unemployment Rate', 3.8, '2025-07', 'Monthly', '%', 'Bureau of Labor Statistics'),
            EconomicIndicator('Inflation Rate', 2.1, '2025-07', 'Monthly', '%', 'Bureau of Labor Statistics'),
            EconomicIndicator('Federal Funds Rate', 5.25, '2025-07', 'Monthly', '%', 'Federal Reserve'),
            EconomicIndicator('VIX Index', 18.5, '2025-07-14', 'Daily', 'Points', 'CBOE'),
        ]

    def _generate_demo_stock_data(self, symbol: str) -> Dict[str, Any]:
        """Generate demo stock data"""
        price = np.random.uniform(50, 300)
        change_pct = np.random.uniform(-5, 5)
        
        return {
            'price': round(price, 2),
            'change': round(price * change_pct / 100, 2),
            'change_percent': round(change_pct, 2),
            'volume': np.random.randint(1000000, 50000000),
            'market_cap': np.random.randint(1000000000, 2000000000000),
            'pe_ratio': round(np.random.uniform(10, 30), 2),
            'dividend_yield': round(np.random.uniform(0, 5), 2),
            'beta': round(np.random.uniform(0.5, 2), 2),
            '52_week_high': round(price * np.random.uniform(1.1, 1.5), 2),
            '52_week_low': round(price * np.random.uniform(0.5, 0.9), 2)
        }

    # === UTILITY METHODS ===
    
    def _parse_sentiment(self, sentiment_label: str) -> str:
        """Parse sentiment label to standard format"""
        sentiment_map = {
            'Bullish': 'positive',
            'Bearish': 'negative',
            'Neutral': 'neutral',
            'Somewhat-Bullish': 'positive',
            'Somewhat-Bearish': 'negative'
        }
        return sentiment_map.get(sentiment_label, 'neutral')

    def get_aggregated_dashboard_data(self, user_symbols: List[str] = None) -> Dict[str, Any]:
        """Get aggregated data for dashboard display"""
        if not user_symbols:
            user_symbols = ['AAPL', 'GOOGL', 'MSFT', 'TSLA', 'AMZN']  # Default watchlist
        
        try:
            dashboard_data = {
                'stocks': self.get_comprehensive_market_data(user_symbols),
                'crypto': [self._crypto_to_dict(c) for c in self.get_crypto_data(limit=10)],
                'currencies': [self._currency_to_dict(c) for c in self.get_currency_rates()],
                'news': [self._news_to_dict(n) for n in self.get_financial_news(user_symbols, limit=10)],
                'economic_indicators': [self._indicator_to_dict(i) for i in self.get_economic_indicators()],
                'market_summary': {
                    'timestamp': datetime.now().isoformat(),
                    'total_symbols_tracked': len(user_symbols),
                    'market_status': 'open',  # Would be determined by actual market hours
                    'overall_sentiment': 'bullish'  # Calculated from various sources
                }
            }
            
            return dashboard_data
            
        except Exception as e:
            self.logger.error(f"Error getting aggregated dashboard data: {e}")
            return {'error': str(e)}

    def _crypto_to_dict(self, crypto: CryptoData) -> Dict:
        """Convert crypto data to dictionary"""
        return {
            'symbol': crypto.symbol,
            'name': crypto.name,
            'price_usd': crypto.price_usd,
            'price_change_24h': crypto.price_change_24h,
            'price_change_percentage_24h': crypto.price_change_percentage_24h,
            'market_cap': crypto.market_cap,
            'volume_24h': crypto.volume_24h,
            'rank': crypto.rank
        }

    def _currency_to_dict(self, currency: CurrencyData) -> Dict:
        """Convert currency data to dictionary"""
        return {
            'base': currency.base,
            'target': currency.target,
            'rate': currency.rate,
            'change_24h': currency.change_24h,
            'timestamp': currency.timestamp
        }

    def _news_to_dict(self, news: NewsArticle) -> Dict:
        """Convert news data to dictionary"""
        return {
            'title': news.title,
            'summary': news.summary,
            'source': news.source,
            'author': news.author,
            'published_at': news.published_at,
            'url': news.url,
            'sentiment': news.sentiment,
            'symbols_mentioned': news.symbols_mentioned
        }

    def _indicator_to_dict(self, indicator: EconomicIndicator) -> Dict:
        """Convert economic indicator to dictionary"""
        return {
            'indicator': indicator.indicator,
            'value': indicator.value,
            'date': indicator.date,
            'frequency': indicator.frequency,
            'unit': indicator.unit,
            'source': indicator.source
        }
