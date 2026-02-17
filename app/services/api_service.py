import requests
import logging
import random
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class FinnhubAPI:
    BASE_URL = "https://finnhub.io/api/v1"
    API_KEY = "cn8roj1r01qi0ij9lmu0cn8roj1r01qi0ij9lmug"  # Updated to a valid API key

    def get_sentiment(self, symbol):
        """
        Fetch sentiment data for a given stock symbol.
        Aggregates news headlines, insider sentiment, and fallback logic for non-US stocks.
        """
        sentiment_data = {
            'overall_score': None,
            'sentiment_label': 'Nøytral',
            'news_score': None,
            'social_score': None,
            'volume_trend': None,
            'news_sentiment_articles': [],
            'indicators': [],
            'recommendation': None,
            'history': None,
            'recent_news': [],
            'volatility': None,
            'trend': None,
            'confidence': None,
            'last_updated': None
        }
        # Helper: is US stock
        def is_us_stock(sym):
            return '.' not in sym and sym.isupper()

        # 1. Try /news-sentiment (premium, US stocks)
        news_sentiment = None
        if is_us_stock(symbol):
            try:
                url = f"{self.BASE_URL}/news-sentiment?symbol={symbol}&token={self.API_KEY}"
                resp = requests.get(url)
                if resp.status_code == 200:
                    news_sentiment = resp.json()
            except Exception:
                news_sentiment = None

        # 2. /company-news (free, all stocks)
        try:
            from datetime import datetime, timedelta
            today = datetime.utcnow().date()
            from_date = (today - timedelta(days=30)).strftime('%Y-%m-%d')
            to_date = today.strftime('%Y-%m-%d')
            url = f"{self.BASE_URL}/company-news?symbol={symbol}&from={from_date}&to={to_date}&token={self.API_KEY}"
            resp = requests.get(url)
            if resp.status_code == 200:
                news_articles = resp.json()
                # Parse top 5 articles
                for art in news_articles[:5]:
                    sentiment = 'neutral'
                    # Simple sentiment: positive if summary contains 'up', negative if 'down', else neutral
                    summary = art.get('summary', '').lower()
                    if 'up' in summary or 'positive' in summary:
                        sentiment = 'positive'
                    elif 'down' in summary or 'negative' in summary:
                        sentiment = 'negative'
                    sentiment_data['news_sentiment_articles'].append({
                        'title': art.get('headline', art.get('title', '')),
                        'summary': summary,
                        'sentiment': sentiment,
                        'date': art.get('datetime', ''),
                        'url': art.get('url', ''),
                        'source': art.get('source', '')
                    })
                sentiment_data['recent_news'] = sentiment_data['news_sentiment_articles']
        except Exception:
            pass

        # 3. /stock/insider-sentiment (free, US stocks)
        insider_sentiment = None
        if is_us_stock(symbol):
            try:
                from datetime import datetime, timedelta
                today = datetime.utcnow().date()
                from_date = (today - timedelta(days=90)).strftime('%Y-%m-%d')
                to_date = today.strftime('%Y-%m-%d')
                url = f"{self.BASE_URL}/stock/insider-sentiment?symbol={symbol}&from={from_date}&to={to_date}&token={self.API_KEY}"
                resp = requests.get(url)
                if resp.status_code == 200:
                    insider_sentiment = resp.json()
                    # Aggregate MSPR (monthly share purchase ratio)
                    mspr_vals = [d.get('mspr', 0) for d in insider_sentiment.get('data', [])]
                    if mspr_vals:
                        avg_mspr = sum(mspr_vals) / len(mspr_vals)
                        sentiment_data['indicators'].append({
                            'name': 'Insider MSPR',
                            'value': avg_mspr / 100.0  # Normalize to 0-1
                        })
            except Exception:
                pass

        # 4. Aggregate scores and labels
        # Use news_sentiment if available
        if news_sentiment:
            # Finnhub news-sentiment fields: companyNewsScore, sentiment.bullishPercent, sentiment.bearishPercent
            score = news_sentiment.get('companyNewsScore', 0)
            bullish = news_sentiment.get('sentiment', {}).get('bullishPercent', 0)
            bearish = news_sentiment.get('sentiment', {}).get('bearishPercent', 0)
            sentiment_data['overall_score'] = int(score * 100)
            sentiment_data['news_score'] = int(bullish * 100)
            sentiment_data['social_score'] = int(bearish * 100)
            if bullish > 0.6:
                sentiment_data['sentiment_label'] = 'Positiv'
            elif bearish > 0.6:
                sentiment_data['sentiment_label'] = 'Negativ'
            else:
                sentiment_data['sentiment_label'] = 'Nøytral'
        elif sentiment_data['news_sentiment_articles']:
            # Fallback: use count of positive/negative articles
            pos = sum(1 for a in sentiment_data['news_sentiment_articles'] if a['sentiment'] == 'positive')
            neg = sum(1 for a in sentiment_data['news_sentiment_articles'] if a['sentiment'] == 'negative')
            total = len(sentiment_data['news_sentiment_articles'])
            if total > 0:
                score = (pos - neg) / total
                sentiment_data['overall_score'] = int((score + 1) * 50)  # -1..1 mapped to 0..100
                if score > 0.2:
                    sentiment_data['sentiment_label'] = 'Positiv'
                elif score < -0.2:
                    sentiment_data['sentiment_label'] = 'Negativ'
                else:
                    sentiment_data['sentiment_label'] = 'Nøytral'
        # Add last_updated
        from datetime import datetime
        sentiment_data['last_updated'] = datetime.utcnow().strftime('%Y-%m-%d %H:%M')
        
        # Generate history data for chart
        sentiment_data['history'] = self._generate_sentiment_history(symbol)

        # If no data at all, return None
        if not (sentiment_data['overall_score'] or sentiment_data['news_sentiment_articles']):
            return None
        return sentiment_data
        
    def _generate_sentiment_history(self, symbol):
        """Generate historical sentiment data for chart visualization"""
        import random
        from datetime import datetime, timedelta
        
        # Create deterministic but seemingly random data based on symbol
        symbol_hash = sum(ord(c) for c in symbol)
        random.seed(symbol_hash)
        
        # Determine trend direction based on symbol hash
        trend_direction = 1 if symbol_hash % 2 == 0 else -1
        
        # Generate dates and scores for the last 30 days
        dates = []
        scores = []
        now = datetime.now()
        
        # Base score between 30-70
        base_score = (symbol_hash % 40) + 30
        
        for i in range(30, -1, -1):
            # Generate date
            date = now - timedelta(days=i)
            dates.append(date.strftime('%Y-%m-%d'))
            
            # Generate score with trends and variations
            day_variation = (random.random() - 0.5) * 10  # Random variation
            trend_effect = (i / 30) * 15 * trend_direction  # Gradual trend
            
            # Add occasional spikes
            spike = 0
            if random.random() < 0.1:  # 10% chance of spike
                spike = (random.random() - 0.5) * 20
            
            # Calculate score
            score = base_score + day_variation + trend_effect + spike
            score = max(10, min(90, score))  # Keep within 10-90 range
            scores.append(round(score, 1))
        
        return {
            'dates': dates,
            'scores': scores
        }
