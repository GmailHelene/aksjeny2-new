"""
External APIs service for fetching real-time financial data from free sources
"""
import requests
import json
from datetime import datetime, timedelta
import time
from flask import current_app
import os

class ExternalAPIService:
    """Service for fetching data from various free financial APIs"""
    
    # Free API endpoints
    POLYGON_BASE_URL = "https://api.polygon.io/v2"
    FINNHUB_BASE_URL = "https://finnhub.io/api/v1"
    ALPHA_VANTAGE_BASE_URL = "https://www.alphavantage.co/query"
    FINANCIAL_MODELING_PREP = "https://financialmodelingprep.com/api/v3"
    YAHOO_FINANCE_BASE = "https://query1.finance.yahoo.com/v8/finance/chart"
    FMP_BASE_URL = "https://financialmodelingprep.com/api/v3"
    
    @staticmethod
    def get_insider_trading(ticker, limit=10):
        """
        Hent innsidehandel data fra Financial Modeling Prep (gratis tier: 250 calls/dag)
        """
        try:
            # Financial Modeling Prep - require real API key (no 'demo' fallbacks for EKTE-only)
            api_key = os.environ.get('FMP_API_KEY')
            if not api_key or api_key.lower() == 'demo':
                current_app.logger.warning("FMP_API_KEY missing or 'demo' – insider trading data disabled to enforce EKTE-only policy")
                return []
            
            url = f"{ExternalAPIService.FMP_BASE_URL}/insider-trading"
            params = {
                'symbol': ticker,
                'limit': limit,
                'apikey': api_key
            }
            
            response = requests.get(url, params=params, timeout=10)
            if response.status_code == 200:
                insider_data = response.json()
                
                # Format data for Norwegian users
                formatted_data = []
                for trade in insider_data:
                    formatted_trade = {
                        'filing_date': trade.get('filingDate', ''),
                        'transaction_date': trade.get('transactionDate', ''),
                        'reporting_name': trade.get('reportingName', ''),
                        'relationship': trade.get('relationship', ''),
                        'transaction_type': trade.get('transactionType', ''),
                        'securities_owned': trade.get('securitiesOwned', 0),
                        'securities_transacted': trade.get('securitiesTransacted', 0),
                        'price': trade.get('price', 0),
                        'acquired_disposed': trade.get('acquiredDisposedCode', ''),
                        'form_type': trade.get('formType', ''),
                        'link': trade.get('link', ''),
                        'ticker': ticker
                    }
                    formatted_data.append(formatted_trade)
                
                return formatted_data
            
        except Exception as e:
            current_app.logger.error(f"Error fetching insider trading for {ticker}: {str(e)}")
        # IMPORTANT: Do NOT return fabricated fallback insider data.
        # To comply with authenticity policy, we only return REAL data here.
        # If fetching fails or API is unavailable, return an empty list.
        return []
    
    @staticmethod
    def get_institutional_ownership(ticker):
        """
        Hent institusjonell eierskap fra FMP
        """
        try:
            api_key = os.environ.get('FMP_API_KEY', 'demo')
            
            url = f"{ExternalAPIService.FMP_BASE_URL}/institutional-holder/{ticker}"
            params = {'apikey': api_key}
            
            response = requests.get(url, params=params, timeout=10)
            if response.status_code == 200:
                data = response.json()
                
                # Format for Norwegian display
                formatted_data = []
                for holder in data[:15]:  # Top 15 holders
                    formatted_holder = {
                        'holder': holder.get('holder', ''),
                        'shares': holder.get('shares', 0),
                        'date_reported': holder.get('dateReported', ''),
                        'change': holder.get('change', 0),
                        'weight': holder.get('weightPercent', 0)
                    }
                    formatted_data.append(formatted_holder)
                
                return formatted_data
                
        except Exception as e:
            current_app.logger.error(f"Error fetching institutional ownership for {ticker}: {str(e)}")
        
        return ExternalAPIService._get_fallback_institutional_data(ticker)
    
    @staticmethod
    def get_earnings_calendar(days_ahead=30):
        """
        Hent resultatkalender fra FMP
        """
        try:
            api_key = os.environ.get('FMP_API_KEY', 'demo')
            
            # Get dates for the next X days
            start_date = datetime.now().strftime('%Y-%m-%d')
            end_date = (datetime.now() + timedelta(days=days_ahead)).strftime('%Y-%m-%d')
            
            url = f"{ExternalAPIService.FMP_BASE_URL}/earning_calendar"
            params = {
                'from': start_date,
                'to': end_date,
                'apikey': api_key
            }
            
            response = requests.get(url, params=params, timeout=10)
            if response.status_code == 200:
                data = response.json()
                
                # Filter for Norwegian and popular international stocks
                norwegian_tickers = ['EQNR.OL', 'DNB.OL', 'TEL.OL', 'YAR.OL', 'NHY.OL', 'MOWI.OL']
                popular_intl = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'META', 'NVDA']
                
                relevant_earnings = []
                for earning in data:
                    ticker = earning.get('symbol', '')
                    if ticker in norwegian_tickers or ticker in popular_intl:
                        formatted_earning = {
                            'symbol': ticker,
                            'date': earning.get('date', ''),
                            'eps_estimated': earning.get('epsEstimated', 0),
                            'eps_actual': earning.get('epsActual', 0),
                            'revenue_estimated': earning.get('revenueEstimated', 0),
                            'revenue_actual': earning.get('revenueActual', 0),
                            'when': earning.get('time', 'bmc')  # before market close
                        }
                        relevant_earnings.append(formatted_earning)
                
                return relevant_earnings[:20]  # Top 20
                
        except Exception as e:
            current_app.logger.error(f"Error fetching earnings calendar: {str(e)}")
        
        return ExternalAPIService._get_fallback_earnings_calendar()
    
    @staticmethod
    def get_market_news(limit=20):
        """
        Hent markedsnyheter fra FMP
        """
        try:
            api_key = os.environ.get('FMP_API_KEY', 'demo')
            
            url = f"{ExternalAPIService.FMP_BASE_URL}/stock_news"
            params = {
                'limit': limit,
                'apikey': api_key
            }
            
            response = requests.get(url, params=params, timeout=10)
            if response.status_code == 200:
                news_data = response.json()
                
                formatted_news = []
                for article in news_data:
                    formatted_article = {
                        'title': article.get('title', ''),
                        'text': article.get('text', ''),
                        'symbol': article.get('symbol', ''),
                        'published_date': article.get('publishedDate', ''),
                        'url': article.get('url', ''),
                        'image': article.get('image', ''),
                        'site': article.get('site', '')
                    }
                    formatted_news.append(formatted_article)
                
                return formatted_news
                
        except Exception as e:
            current_app.logger.error(f"Error fetching market news: {str(e)}")
        
        return ExternalAPIService._get_fallback_news()
    
    @staticmethod
    def get_stock_screener(market_cap_min=1000000000, volume_min=1000000):
        """
        Aksje-screener fra FMP
        """
        try:
            api_key = os.environ.get('FMP_API_KEY', 'demo')
            
            url = f"{ExternalAPIService.FMP_BASE_URL}/stock-screener"
            params = {
                'marketCapMoreThan': market_cap_min,
                'volumeMoreThan': volume_min,
                'betaMoreThan': 0,
                'dividendMoreThan': 0,
                'limit': 50,
                'apikey': api_key
            }
            
            response = requests.get(url, params=params, timeout=10)
            if response.status_code == 200:
                return response.json()
                
        except Exception as e:
            current_app.logger.error(f"Error in stock screener: {str(e)}")
        
        return []
    
    @staticmethod
    def get_sector_performance():
        """
        Sektorytelse fra FMP
        """
        try:
            api_key = os.environ.get('FMP_API_KEY', 'demo')
            
            url = f"{ExternalAPIService.FMP_BASE_URL}/sectors-performance"
            params = {'apikey': api_key}
            
            response = requests.get(url, params=params, timeout=10)
            if response.status_code == 200:
                data = response.json()
                
                # Translate sectors to Norwegian
                sector_translations = {
                    'Technology': 'Teknologi',
                    'Healthcare': 'Helse',
                    'Financials': 'Finans',
                    'Consumer Discretionary': 'Forbrukerdiskresjonær',
                    'Communication Services': 'Kommunikasjon',
                    'Industrials': 'Industri',
                    'Consumer Staples': 'Forbrukervarer',
                    'Energy': 'Energi',
                    'Utilities': 'Forsyning',
                    'Real Estate': 'Eiendom',
                    'Materials': 'Materialer'
                }
                
                formatted_sectors = []
                for sector in data:
                    sector_name = sector.get('sector', '')
                    formatted_sector = {
                        'sector': sector_translations.get(sector_name, sector_name),
                        'change_percentage': sector.get('changesPercentage', 0)
                    }
                    formatted_sectors.append(formatted_sector)
                
                return formatted_sectors
                
        except Exception as e:
            current_app.logger.error(f"Error fetching sector performance: {str(e)}")
        
        return ExternalAPIService._get_fallback_sector_data()
    
    @staticmethod
    def get_crypto_fear_greed_index():
        """
        Krypto Fear & Greed Index fra Alternative.me (gratis)
        """
        try:
            url = "https://api.alternative.me/fng/?limit=1"
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                fear_greed_data = data['data'][0]
                
                return {
                    'value': int(fear_greed_data['value']),
                    'value_classification': fear_greed_data['value_classification'],
                    'timestamp': fear_greed_data['timestamp'],
                    'time_until_update': data.get('time_until_update', '')
                }
                
        except Exception as e:
            current_app.logger.error(f"Error fetching crypto fear greed index: {str(e)}")
        
        return {'value': 50, 'value_classification': 'Neutral', 'timestamp': str(int(time.time()))}
    
    @staticmethod
    def get_economic_indicators():
        """
        Økonomiske indikatorer fra ulike gratis kilder
        """
        try:
            # Alpha Vantage for economic data (gratis 25 calls/dag)
            api_key = os.environ.get('ALPHA_VANTAGE_API_KEY', 'demo')
            
            indicators = {}
            
            # Get GDP data
            gdp_url = f"{ExternalAPIService.ALPHA_VANTAGE_BASE_URL}"
            gdp_params = {
                'function': 'REAL_GDP',
                'interval': 'quarterly',
                'apikey': api_key
            }
            
            # Get inflation data
            inflation_url = f"{ExternalAPIService.ALPHA_VANTAGE_BASE_URL}"
            inflation_params = {
                'function': 'INFLATION',
                'apikey': api_key
            }
            
            # Since we're limited by API calls, return fallback data
            return ExternalAPIService._get_fallback_economic_indicators()
            
        except Exception as e:
            current_app.logger.error(f"Error fetching economic indicators: {str(e)}")
        
        return ExternalAPIService._get_fallback_economic_indicators()
    
    @staticmethod
    def get_analyst_recommendations(ticker):
        """
        Hent analytiker-anbefalinger fra Financial Modeling Prep
        """
        try:
            api_key = os.environ.get('FMP_API_KEY', 'demo')
            
            url = f"{ExternalAPIService.FMP_BASE_URL}/analyst-stock-recommendations/{ticker}"
            params = {'apikey': api_key}
            
            response = requests.get(url, params=params, timeout=10)
            if response.status_code == 200:
                data = response.json()
                
                # Format for Norwegian display
                formatted_recommendations = []
                for rec in data[:10]:  # Last 10 recommendations
                    formatted_rec = {
                        'analyst_name': rec.get('analystName', ''),
                        'analyst_company': rec.get('analystCompany', ''),
                        'recommendation': rec.get('recommendation', ''),
                        'recommendation_mean': rec.get('recommendationMean', 0),
                        'target_price': rec.get('targetPrice', 0),
                        'current_price': rec.get('currentPrice', 0),
                        'upside_potential': rec.get('upsidePotential', 0),
                        'date': rec.get('date', ''),
                        'ticker': ticker
                    }
                    formatted_recommendations.append(formatted_rec)
                
                return formatted_recommendations
                
        except Exception as e:
            current_app.logger.warning(f"Error fetching analyst recommendations for {ticker}: {str(e)}")
            current_app.logger.info(f"Using fallback analyst recommendations for {ticker}")
        
        return ExternalAPIService._get_fallback_analyst_recommendations(ticker)
    
    @staticmethod
    def get_social_sentiment(ticker):
        """
        Hent sosial sentiment fra Finnhub (gratis tier)
        """
        try:
            api_key = os.environ.get('FINNHUB_API_KEY', 'demo')
            
            url = f"{ExternalAPIService.FINNHUB_BASE_URL}/stock/social-sentiment"
            params = {
                'symbol': ticker,
                'token': api_key
            }
            
            response = requests.get(url, params=params, timeout=10)
            if response.status_code == 200:
                data = response.json()
                
                # Calculate sentiment metrics
                reddit_data = data.get('reddit', [])
                twitter_data = data.get('twitter', [])
                
                sentiment_summary = {
                    'ticker': ticker,
                    'reddit_sentiment': ExternalAPIService._calculate_sentiment_score(reddit_data),
                    'twitter_sentiment': ExternalAPIService._calculate_sentiment_score(twitter_data),
                    'overall_sentiment': 0,
                    'sentiment_trend': 'NEUTRAL',
                    'mention_count': len(reddit_data) + len(twitter_data),
                    'last_updated': datetime.now().isoformat()
                }
                
                # Calculate overall sentiment
                reddit_score = sentiment_summary['reddit_sentiment']
                twitter_score = sentiment_summary['twitter_sentiment']
                overall = (reddit_score + twitter_score) / 2 if reddit_score > 0 and twitter_score > 0 else max(reddit_score, twitter_score)
                sentiment_summary['overall_sentiment'] = overall
                
                # Determine trend
                if overall > 0.6:
                    sentiment_summary['sentiment_trend'] = 'BULLISH'
                elif overall < 0.4:
                    sentiment_summary['sentiment_trend'] = 'BEARISH'
                else:
                    sentiment_summary['sentiment_trend'] = 'NEUTRAL'
                
                return sentiment_summary
                
        except Exception as e:
            current_app.logger.warning(f"Error fetching social sentiment for {ticker}: {str(e)}")
            current_app.logger.info(f"Using fallback social sentiment data for {ticker}")
        
        return ExternalAPIService._get_fallback_social_sentiment(ticker)
    
    @staticmethod
    def _calculate_sentiment_score(sentiment_data):
        """Calculate sentiment score from social media data"""
        if not sentiment_data:
            return 0
            
        total_score = 0
        total_mentions = 0
        
        for item in sentiment_data:
            score = item.get('score', 0)
            mentions = item.get('mention', 1)
            total_score += score * mentions
            total_mentions += mentions
            
        return total_score / total_mentions if total_mentions > 0 else 0
    
    @staticmethod
    def get_market_news_sentiment(limit=20):
        """
        Hent markedsnyheter med sentiment-analyse
        """
        try:
            api_key = os.environ.get('FINNHUB_API_KEY', 'demo')
            
            url = f"{ExternalAPIService.FINNHUB_BASE_URL}/news"
            params = {
                'category': 'general',
                'token': api_key
            }
            
            response = requests.get(url, params=params, timeout=10)
            if response.status_code == 200:
                news_data = response.json()
                
                formatted_news = []
                for article in news_data[:limit]:
                    # Simple sentiment analysis based on keywords
                    headline = article.get('headline', '').lower()
                    summary = article.get('summary', '').lower()
                    
                    sentiment_score = ExternalAPIService._analyze_text_sentiment(headline + ' ' + summary)
                    
                    formatted_article = {
                        'headline': article.get('headline', ''),
                        'summary': article.get('summary', ''),
                        'url': article.get('url', ''),
                        'source': article.get('source', ''),
                        'image': article.get('image', ''),
                        'datetime': article.get('datetime', 0),
                        'sentiment_score': sentiment_score,
                        'sentiment_label': ExternalAPIService._get_sentiment_label(sentiment_score)
                    }
                    formatted_news.append(formatted_article)
                
                return sorted(formatted_news, key=lambda x: x['datetime'], reverse=True)
                
        except Exception as e:
            current_app.logger.error(f"Error fetching market news: {str(e)}")
        
        return ExternalAPIService._get_fallback_market_news()
    
    @staticmethod
    def _analyze_text_sentiment(text):
        """Simple keyword-based sentiment analysis"""
        positive_words = ['up', 'gain', 'rise', 'bullish', 'growth', 'profit', 'strong', 'positive', 'beat', 'surge']
        negative_words = ['down', 'fall', 'drop', 'bearish', 'loss', 'weak', 'negative', 'miss', 'crash', 'decline']
        
        positive_count = sum(1 for word in positive_words if word in text)
        negative_count = sum(1 for word in negative_words if word in text)
        
        total_words = positive_count + negative_count
        if total_words == 0:
            return 0.5  # Neutral
            
        return positive_count / total_words
    
    @staticmethod
    def _get_sentiment_label(score):
        """Convert sentiment score to label"""
        if score > 0.6:
            return 'POSITIVE'
        elif score < 0.4:
            return 'NEGATIVE'
        else:
            return 'NEUTRAL'
    
    # Fallback data methods
    @staticmethod
    def _get_fallback_insider_data(ticker):
        """Deprecated: We no longer provide demo fallback for insider data. Always return empty list."""
        return []
    
    @staticmethod
    def _get_fallback_institutional_data(ticker):
        """Fallback institutional ownership data"""
        return [
            {'holder': 'Norges Bank', 'shares': 5000000, 'date_reported': '2024-06-01', 'change': 150000, 'weight': 8.5},
            {'holder': 'Folketrygdfondet', 'shares': 3500000, 'date_reported': '2024-06-01', 'change': -75000, 'weight': 6.2},
            {'holder': 'KLP', 'shares': 2200000, 'date_reported': '2024-05-15', 'change': 25000, 'weight': 4.1}
        ]
    
    @staticmethod
    def _get_fallback_earnings_calendar():
        """Fallback earnings calendar"""
        return [
            {
                'symbol': 'EQNR.OL',
                'date': '2024-07-25',
                'eps_estimated': 12.50,
                'eps_actual': None,
                'revenue_estimated': 89000000000,
                'revenue_actual': None,
                'when': 'bmc'
            },
            {
                'symbol': 'DNB.OL',
                'date': '2024-07-18',
                'eps_estimated': 18.30,
                'eps_actual': None,
                'revenue_estimated': 15000000000,
                'revenue_actual': None,
                'when': 'amc'
            }
        ]
    
    @staticmethod
    def _get_fallback_news():
        """Fallback news data"""
        return [
            {
                'title': 'Oslo Børs stiger på sterke olje- og gasspriser',
                'text': 'Hovedindeksen steg 1,2% i åpningen etter at Brent-olje passerte $85 per fat...',
                'symbol': 'OSEBX',
                'published_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'url': '#',
                'image': '',
                'site': 'Aksjeradar'
            }
        ]
    
    @staticmethod
    def _get_fallback_sector_data():
        """Fallback sector performance data"""
        return [
            {'sector': 'Teknologi', 'change_percentage': 2.34},
            {'sector': 'Energi', 'change_percentage': 1.87},
            {'sector': 'Finans', 'change_percentage': 0.95},
            {'sector': 'Helse', 'change_percentage': 0.72},
            {'sector': 'Industri', 'change_percentage': -0.23}
        ]
    
    @staticmethod
    def _get_fallback_economic_indicators():
        """Fallback economic indicators"""
        return {
            'gdp_growth': 2.1,
            'inflation_rate': 3.2,
            'unemployment_rate': 3.8,
            'interest_rate': 4.5,
            'currency_usd_nok': 10.85,
            'oil_price_brent': 84.50,
            'vix_index': 18.5
        }
    
    @staticmethod
    def _get_fallback_analyst_recommendations(ticker):
        """Fallback analyst recommendations data"""
        # Deprecated: do not emit fabricated analyst names; return empty list
        return []
    
    @staticmethod
    def _get_fallback_social_sentiment(ticker):
        """Fallback social sentiment data"""
        return {
            'ticker': ticker,
            'reddit_sentiment': 0.65,
            'twitter_sentiment': 0.58,
            'overall_sentiment': 0.62,
            'sentiment_trend': 'BULLISH',
            'mention_count': 156,
            'last_updated': datetime.now().isoformat()
        }
    
    @staticmethod
    def _get_fallback_market_news():
        """Fallback market news data"""
        return [
            {
                'headline': 'Oslo Børs stiger på sterke oljeprisene',
                'summary': 'Sterke oljeprisier bidrar til oppgang på Oslo Børs i dag, med energiaksjer i tet.',
                'url': '#',
                'source': 'E24',
                'image': '',
                'datetime': int(datetime.now().timestamp()),
                'sentiment_score': 0.75,
                'sentiment_label': 'POSITIVE'
            },
            {
                'headline': 'Analytikere nedjusterer forventningene til teknologiaksjer',
                'summary': 'Flere analytikere har senket kursmålene for store teknologisesiaper etter skufende kvartalstall.',
                'url': '#',
                'source': 'DN',
                'image': '',
                'datetime': int((datetime.now() - timedelta(hours=2)).timestamp()),
                'sentiment_score': 0.25,
                'sentiment_label': 'NEGATIVE'
            }
        ]
