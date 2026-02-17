"""
AI-Powered Sentiment Analysis Service
===================================

Advanced natural language processing for financial news sentiment,
market impact scoring, and predictive sentiment analytics.
"""

import re
import json
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
import logging
# import numpy as np

logger = logging.getLogger(__name__)

class SentimentAnalysisService:
    """AI-powered sentiment analysis for financial news and market intelligence"""
    
    # Financial sentiment lexicon
    POSITIVE_FINANCIAL_TERMS = {
        'strong': 0.8, 'growth': 0.7, 'profit': 0.8, 'gain': 0.7, 'up': 0.6,
        'rise': 0.7, 'increase': 0.6, 'surge': 0.9, 'boost': 0.7, 'positive': 0.6,
        'bullish': 0.8, 'optimistic': 0.7, 'confident': 0.6, 'success': 0.8,
        'beat': 0.7, 'exceed': 0.7, 'outperform': 0.8, 'rally': 0.8,
        'breakthrough': 0.9, 'milestone': 0.7, 'record': 0.8, 'expansion': 0.7
    }
    
    NEGATIVE_FINANCIAL_TERMS = {
        'weak': -0.7, 'decline': -0.7, 'loss': -0.8, 'fall': -0.7, 'down': -0.6,
        'drop': -0.7, 'decrease': -0.6, 'plunge': -0.9, 'crash': -0.9, 'negative': -0.6,
        'bearish': -0.8, 'pessimistic': -0.7, 'concern': -0.6, 'worry': -0.6,
        'miss': -0.7, 'underperform': -0.8, 'sell-off': -0.8, 'correction': -0.7,
        'volatility': -0.5, 'uncertainty': -0.6, 'risk': -0.5, 'trouble': -0.7,
        'crisis': -0.9, 'bankruptcy': -0.9, 'deficit': -0.7, 'recession': -0.9
    }
    
    # Market impact modifiers
    IMPACT_MODIFIERS = {
        'significantly': 1.3, 'substantially': 1.3, 'dramatically': 1.4,
        'slightly': 0.7, 'marginally': 0.6, 'moderately': 0.8,
        'extremely': 1.5, 'very': 1.2, 'quite': 1.1, 'somewhat': 0.8
    }
    
    # Context-aware sentiment patterns
    SENTIMENT_PATTERNS = {
        'earnings_beat': {'pattern': r'(beat|exceed|outperform).*(estimate|expectation|forecast)', 'sentiment': 0.8},
        'earnings_miss': {'pattern': r'(miss|below|under).*(estimate|expectation|forecast)', 'sentiment': -0.7},
        'guidance_raised': {'pattern': r'(raise|increase|upgrade).*(guidance|outlook|forecast)', 'sentiment': 0.7},
        'guidance_lowered': {'pattern': r'(lower|reduce|cut).*(guidance|outlook|forecast)', 'sentiment': -0.7},
        'analyst_upgrade': {'pattern': r'(upgrade|raise).*(rating|target|price)', 'sentiment': 0.6},
        'analyst_downgrade': {'pattern': r'(downgrade|lower|cut).*(rating|target|price)', 'sentiment': -0.6},
        'dividend_increase': {'pattern': r'(increase|raise|boost).*(dividend)', 'sentiment': 0.6},
        'dividend_cut': {'pattern': r'(cut|reduce|suspend).*(dividend)', 'sentiment': -0.8},
        'stock_buyback': {'pattern': r'(buyback|repurchase).*(program|shares)', 'sentiment': 0.5},
        'merger_announced': {'pattern': r'(merger|acquisition|takeover).*(announced|agreed)', 'sentiment': 0.7}
    }
    
    @staticmethod
    def analyze_article_sentiment(article: Dict) -> Dict:
        """Perform comprehensive sentiment analysis on a news article"""
        try:
            text = (article.get('title', '') + ' ' + article.get('description', '')).lower()
            
            # Basic sentiment scoring
            basic_sentiment = SentimentAnalysisService._calculate_basic_sentiment(text)
            
            # Pattern-based sentiment
            pattern_sentiment = SentimentAnalysisService._analyze_sentiment_patterns(text)
            
            # Context-aware adjustments
            context_score = SentimentAnalysisService._apply_context_adjustments(text, article)
            
            # Combined sentiment score
            final_sentiment = SentimentAnalysisService._combine_sentiment_scores(
                basic_sentiment, pattern_sentiment, context_score
            )
            
            # Market impact assessment
            market_impact = SentimentAnalysisService._assess_market_impact(article, final_sentiment)
            
            # Confidence level
            confidence = SentimentAnalysisService._calculate_confidence(
                basic_sentiment, pattern_sentiment, context_score
            )
            
            # Entity extraction (companies, sectors mentioned)
            entities = SentimentAnalysisService._extract_entities(text)
            
            return {
                'success': True,
                'sentiment_score': round(final_sentiment, 4),
                'sentiment_label': SentimentAnalysisService._get_sentiment_label(final_sentiment),
                'confidence': round(confidence, 4),
                'market_impact_score': round(market_impact, 4),
                'market_impact_label': SentimentAnalysisService._get_impact_label(market_impact),
                'sentiment_breakdown': {
                    'basic_sentiment': round(basic_sentiment, 4),
                    'pattern_sentiment': round(pattern_sentiment, 4),
                    'context_adjustment': round(context_score, 4)
                },
                'entities': entities,
                'analysis_timestamp': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Sentiment analysis error: {e}")
            return {
                'success': False,
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat()
            }
    
    @staticmethod
    def analyze_batch_sentiment(articles: List[Dict]) -> Dict:
        """Analyze sentiment for multiple articles"""
        try:
            results = []
            sentiment_trends = {
                'positive': 0,
                'negative': 0,
                'neutral': 0
            }
            
            total_sentiment = 0
            weighted_sentiment = 0
            total_weight = 0
            
            for article in articles:
                analysis = SentimentAnalysisService.analyze_article_sentiment(article)
                
                if analysis['success']:
                    results.append({
                        'article_id': article.get('content_hash', ''),
                        'title': article.get('title', ''),
                        'sentiment_analysis': analysis
                    })
                    
                    sentiment_raw = analysis['sentiment_score']
                    
                    # Ensure sentiment is a number, not a list
                    if isinstance(sentiment_raw, list):
                        sentiment = sentiment_raw[0] if sentiment_raw else 0
                    else:
                        sentiment = sentiment_raw
                    
                    # Ensure sentiment is numeric
                    try:
                        sentiment = float(sentiment)
                    except (ValueError, TypeError):
                        sentiment = 0
                    
                    total_sentiment += sentiment
                    
                    # Weight by source credibility and market impact
                    weight = article.get('source_weight', 1.0) * analysis.get('market_impact_score', 0.5)
                    weighted_sentiment += sentiment * weight
                    total_weight += weight
                    
                    # Count sentiment categories
                    if sentiment > 0.1:
                        sentiment_trends['positive'] += 1
                    elif sentiment < -0.1:
                        sentiment_trends['negative'] += 1
                    else:
                        sentiment_trends['neutral'] += 1
            
            # Calculate aggregate metrics
            avg_sentiment = total_sentiment / len(results) if results else 0
            weighted_avg_sentiment = weighted_sentiment / total_weight if total_weight > 0 else 0
            
            # Market mood assessment
            market_mood = SentimentAnalysisService._assess_market_mood(sentiment_trends, avg_sentiment)
            
            return {
                'success': True,
                'total_articles_analyzed': len(results),
                'sentiment_summary': {
                    'average_sentiment': round(avg_sentiment, 4),
                    'weighted_average_sentiment': round(weighted_avg_sentiment, 4),
                    'overall_mood': market_mood,
                    'sentiment_distribution': sentiment_trends
                },
                'individual_results': results,
                'analysis_timestamp': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Batch sentiment analysis error: {e}")
            return {
                'success': False,
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat()
            }
    
    @staticmethod
    def get_sentiment_trends(timeframe_hours: int = 24) -> Dict:
        """Analyze sentiment trends over time"""
        try:
            # This would typically fetch historical sentiment data
            # For demonstration, we'll generate representative trend data
            
            time_periods = []
            current_time = datetime.utcnow()
            
            # Generate hourly sentiment data
            for i in range(timeframe_hours):
                period_time = current_time - timedelta(hours=i)
                
                # Simulate sentiment trend (would be real data in production)
                base_sentiment = 0.1  # Slightly positive base
                noise = np.random.normal(0, 0.3)
                time_factor = np.sin(i * 0.1) * 0.2  # Some cyclical component
                
                sentiment = base_sentiment + noise + time_factor
                sentiment = max(-1, min(1, sentiment))  # Clamp to [-1, 1]
                
                time_periods.append({
                    'timestamp': period_time.isoformat(),
                    'hour': period_time.hour,
                    'sentiment_score': round(sentiment, 4),
                    'sentiment_label': SentimentAnalysisService._get_sentiment_label(sentiment),
                    'volume_indicator': max(10, int(50 + np.random.normal(0, 20)))  # Simulated volume
                })
            
            # Reverse to get chronological order
            time_periods.reverse()
            
            # Calculate trend metrics
            recent_sentiments = [p['sentiment_score'] for p in time_periods[-6:]]  # Last 6 hours
            earlier_sentiments = [p['sentiment_score'] for p in time_periods[:6]]   # First 6 hours
            
            trend_direction = np.mean(recent_sentiments) - np.mean(earlier_sentiments)
            trend_strength = abs(trend_direction)
            
            return {
                'success': True,
                'timeframe_hours': timeframe_hours,
                'sentiment_trend': {
                    'direction': 'improving' if trend_direction > 0.05 else 'declining' if trend_direction < -0.05 else 'stable',
                    'strength': 'strong' if trend_strength > 0.2 else 'moderate' if trend_strength > 0.1 else 'weak',
                    'trend_score': round(trend_direction, 4)
                },
                'current_sentiment': time_periods[-1]['sentiment_score'],
                'hourly_data': time_periods,
                'analysis_timestamp': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Sentiment trends analysis error: {e}")
            return {
                'success': False,
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat()
            }
    
    @staticmethod
    def get_company_sentiment(company_symbol: str, articles: List[Dict]) -> Dict:
        """Analyze sentiment specifically for a company"""
        try:
            company_articles = []
            
            # Filter articles mentioning the company
            for article in articles:
                text = (article.get('title', '') + ' ' + article.get('description', '')).lower()
                if company_symbol.lower() in text:
                    company_articles.append(article)
            
            if not company_articles:
                return {
                    'success': True,
                    'company_symbol': company_symbol,
                    'articles_found': 0,
                    'sentiment_summary': 'No recent news found',
                    'timestamp': datetime.utcnow().isoformat()
                }
            
            # Analyze sentiment for company-specific articles
            batch_analysis = SentimentAnalysisService.analyze_batch_sentiment(company_articles)
            
            if not batch_analysis['success']:
                return batch_analysis
            
            # Additional company-specific analysis
            company_specific_score = SentimentAnalysisService._calculate_company_specific_sentiment(
                company_articles, company_symbol
            )
            
            return {
                'success': True,
                'company_symbol': company_symbol,
                'articles_analyzed': len(company_articles),
                'sentiment_summary': batch_analysis['sentiment_summary'],
                'company_specific_score': round(company_specific_score, 4),
                'company_sentiment_label': SentimentAnalysisService._get_sentiment_label(company_specific_score),
                'recent_articles': [
                    {
                        'title': article.get('title', ''),
                        'sentiment': result['sentiment_analysis']['sentiment_score'],
                        'impact': result['sentiment_analysis']['market_impact_score']
                    }
                    for article, result in zip(company_articles[:5], batch_analysis['individual_results'][:5])
                ],
                'analysis_timestamp': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Company sentiment analysis error: {e}")
            return {
                'success': False,
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat()
            }
    
    @staticmethod
    def _calculate_basic_sentiment(text: str) -> float:
        """Calculate basic sentiment using financial lexicon"""
        words = re.findall(r'\b\w+\b', text.lower())
        
        sentiment_score = 0.0
        word_count = 0
        
        for word in words:
            if word in SentimentAnalysisService.POSITIVE_FINANCIAL_TERMS:
                sentiment_score += SentimentAnalysisService.POSITIVE_FINANCIAL_TERMS[word]
                word_count += 1
            elif word in SentimentAnalysisService.NEGATIVE_FINANCIAL_TERMS:
                sentiment_score += SentimentAnalysisService.NEGATIVE_FINANCIAL_TERMS[word]
                word_count += 1
        
        # Normalize by word count
        if word_count > 0:
            sentiment_score /= word_count
        
        # Apply modifiers
        for modifier, factor in SentimentAnalysisService.IMPACT_MODIFIERS.items():
            if modifier in text:
                sentiment_score *= factor
                break
        
        return max(-1, min(1, sentiment_score))
    
    @staticmethod
    def _analyze_sentiment_patterns(text: str) -> float:
        """Analyze sentiment using predefined patterns"""
        pattern_score = 0.0
        matches_found = 0
        
        for pattern_name, pattern_data in SentimentAnalysisService.SENTIMENT_PATTERNS.items():
            if re.search(pattern_data['pattern'], text, re.IGNORECASE):
                pattern_score += pattern_data['sentiment']
                matches_found += 1
        
        if matches_found > 0:
            pattern_score /= matches_found
        
        return max(-1, min(1, pattern_score))
    
    @staticmethod
    def _apply_context_adjustments(text: str, article: Dict) -> float:
        """Apply context-specific sentiment adjustments"""
        context_score = 0.0
        
        # Source credibility adjustment
        source_weight = article.get('source_weight', 1.0)
        if source_weight > 0.8:
            context_score += 0.1  # Bonus for credible sources
        
        # Article age adjustment
        age_hours = article.get('age_hours', 24)
        if age_hours < 2:
            context_score += 0.05  # Bonus for breaking news
        
        # Market category adjustments
        market_categories = article.get('market_categories', [])
        if 'earnings' in market_categories:
            context_score += 0.05  # Earnings news is more impactful
        if 'regulation' in market_categories:
            context_score -= 0.05  # Regulatory news tends to be negative
        
        return max(-0.3, min(0.3, context_score))  # Limit context adjustment
    
    @staticmethod
    def _combine_sentiment_scores(basic: float, pattern: float, context: float) -> float:
        """Combine different sentiment scores intelligently"""
        # Weighted combination
        if pattern != 0.0:  # Pattern match found - give it higher weight
            combined = (basic * 0.4) + (pattern * 0.5) + (context * 0.1)
        else:  # No pattern match - rely more on basic sentiment
            combined = (basic * 0.7) + (context * 0.3)
        
        return max(-1, min(1, combined))
    
    @staticmethod
    def _assess_market_impact(article: Dict, sentiment: float) -> float:
        """Assess potential market impact of the sentiment"""
        base_impact = abs(sentiment) * 0.5  # Base impact from sentiment magnitude
        
        # Source credibility factor
        source_weight = article.get('source_weight', 1.0)
        base_impact *= source_weight
        
        # Article freshness factor
        age_hours = article.get('age_hours', 24)
        if age_hours < 1:
            base_impact *= 1.5
        elif age_hours < 6:
            base_impact *= 1.2
        elif age_hours > 48:
            base_impact *= 0.6
        
        # Market category multipliers
        market_categories = article.get('market_categories', [])
        category_multipliers = {
            'earnings': 1.3,
            'mergers': 1.4,
            'regulation': 1.2,
            'crypto': 1.1
        }
        
        for category in market_categories:
            if category in category_multipliers:
                base_impact *= category_multipliers[category]
        
        return min(base_impact, 1.0)
    
    @staticmethod
    def _calculate_confidence(basic: float, pattern: float, context: float) -> float:
        """Calculate confidence level in the sentiment analysis"""
        confidence = 0.5  # Base confidence
        
        # Higher confidence if multiple methods agree
        if abs(basic) > 0.3:
            confidence += 0.2
        if abs(pattern) > 0.3:
            confidence += 0.3
        if basic * pattern > 0:  # Same direction
            confidence += 0.2
        
        return min(confidence, 1.0)
    
    @staticmethod
    def _extract_entities(text: str) -> Dict:
        """Extract companies, sectors, and other entities"""
        # Simple entity extraction (would use NER models in production)
        entities = {
            'companies': [],
            'sectors': [],
            'currencies': [],
            'commodities': []
        }
        
        # Common company patterns
        company_patterns = [
            r'\b[A-Z]{2,5}\b',  # Stock symbols
            r'\b\w+\s+(Inc|Corp|Ltd|LLC|Group|Holdings)\b'
        ]
        
        # Sector keywords
        sectors = ['technology', 'finance', 'healthcare', 'energy', 'retail', 'automotive']
        
        # Currency mentions
        currencies = ['USD', 'EUR', 'NOK', 'GBP', 'JPY', 'bitcoin', 'ethereum']
        
        # Extract entities
        for pattern in company_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            entities['companies'].extend(matches)
        
        for sector in sectors:
            if sector in text.lower():
                entities['sectors'].append(sector)
        
        for currency in currencies:
            if currency.lower() in text.lower():
                entities['currencies'].append(currency)
        
        # Remove duplicates
        for key in entities:
            entities[key] = list(set(entities[key]))
        
        return entities
    
    @staticmethod
    def _get_sentiment_label(sentiment: float) -> str:
        """Convert sentiment score to human-readable label"""
        if sentiment > 0.3:
            return 'Very Positive'
        elif sentiment > 0.1:
            return 'Positive'
        elif sentiment > -0.1:
            return 'Neutral'
        elif sentiment > -0.3:
            return 'Negative'
        else:
            return 'Very Negative'
    
    @staticmethod
    def _get_impact_label(impact: float) -> str:
        """Convert impact score to human-readable label"""
        if impact > 0.7:
            return 'High Impact'
        elif impact > 0.4:
            return 'Medium Impact'
        elif impact > 0.2:
            return 'Low Impact'
        else:
            return 'Minimal Impact'
    
    @staticmethod
    def _assess_market_mood(sentiment_trends: Dict, avg_sentiment: float) -> str:
        """Assess overall market mood"""
        total_articles = sum(sentiment_trends.values())
        
        if total_articles == 0:
            return 'Unknown'
        
        positive_ratio = sentiment_trends['positive'] / total_articles
        negative_ratio = sentiment_trends['negative'] / total_articles
        
        if positive_ratio > 0.6 and avg_sentiment > 0.2:
            return 'Very Bullish'
        elif positive_ratio > 0.4 and avg_sentiment > 0.1:
            return 'Bullish'
        elif negative_ratio > 0.6 and avg_sentiment < -0.2:
            return 'Very Bearish'
        elif negative_ratio > 0.4 and avg_sentiment < -0.1:
            return 'Bearish'
        else:
            return 'Mixed/Neutral'
    
    @staticmethod
    def _calculate_company_specific_sentiment(articles: List[Dict], company_symbol: str) -> float:
        """Calculate sentiment specifically focused on company mentions"""
        total_sentiment = 0.0
        weighted_sum = 0.0
        
        for article in articles:
            text = (article.get('title', '') + ' ' + article.get('description', '')).lower()
            
            # Count mentions of company
            mention_count = text.count(company_symbol.lower())
            
            # Weight by mention frequency and article credibility
            weight = mention_count * article.get('source_weight', 1.0)
            
            # Simple sentiment extraction around company mentions
            company_context_sentiment = 0.0
            for word in SentimentAnalysisService.POSITIVE_FINANCIAL_TERMS:
                if word in text:
                    company_context_sentiment += SentimentAnalysisService.POSITIVE_FINANCIAL_TERMS[word] * 0.5
            
            for word in SentimentAnalysisService.NEGATIVE_FINANCIAL_TERMS:
                if word in text:
                    company_context_sentiment += SentimentAnalysisService.NEGATIVE_FINANCIAL_TERMS[word] * 0.5
            
            total_sentiment += company_context_sentiment * weight
            weighted_sum += weight
        
        return total_sentiment / weighted_sum if weighted_sum > 0 else 0.0
