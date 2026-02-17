"""
Advanced News Aggregation Service
===============================

Real-time news collection, processing, and intelligent categorization
with AI-powered relevance scoring and market impact analysis.
"""

try:
    import feedparser  # type: ignore
    FEEDPARSER_AVAILABLE = True
except Exception as e:  # pragma: no cover
    FEEDPARSER_AVAILABLE = False
    class _FeedparserFallback:
        def parse(self, *_, **__):
            return {'entries': []}
    feedparser = _FeedparserFallback()  # type: ignore
    import logging as _logging
    _logging.getLogger(__name__).warning(f"feedparser import failed ({e}); using fallback (no external RSS ingestion)")
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
import logging
import re
import json
from urllib.parse import urlparse
import hashlib
import time

logger = logging.getLogger(__name__)

class NewsAggregationService:
    """Advanced news aggregation with multi-source collection and intelligent processing"""
    
    # News sources configuration
    NEWS_SOURCES = {
        'financial_times': {
            'rss': 'https://www.ft.com/markets?format=rss',
            'category': 'financial',
            'weight': 0.9,
            'language': 'en'
        },
        'reuters_business': {
            'rss': 'https://feeds.reuters.com/reuters/businessNews',
            'category': 'business',
            'weight': 0.85,
            'language': 'en'
        },
        'bloomberg': {
            'rss': 'https://feeds.bloomberg.com/markets/news.rss',
            'category': 'markets',
            'weight': 0.9,
            'language': 'en'
        },
        'cnbc': {
            'rss': 'https://www.cnbc.com/id/10000664/device/rss/rss.html',
            'category': 'markets',
            'weight': 0.8,
            'language': 'en'
        },
        'e24': {
            'rss': 'https://e24.no/rss',
            'category': 'norwegian_business',
            'weight': 0.75,
            'language': 'no'
        },
        'dn': {
            'rss': 'https://www.dn.no/rss',
            'category': 'norwegian_business', 
            'weight': 0.8,
            'language': 'no'
        },
        'investtech': {
            'rss': 'https://www.investtech.com/main/rss.php?lang=no',
            'category': 'technical_analysis',
            'weight': 0.7,
            'language': 'no'
        }
    }
    
    @staticmethod
    def collect_all_news() -> Dict:
        """Collect news from all configured sources"""
        try:
            all_articles = []
            source_stats = {}
            
            for source_name, source_config in NewsAggregationService.NEWS_SOURCES.items():
                try:
                    articles = NewsAggregationService._collect_from_source(
                        source_name, source_config
                    )
                    
                    all_articles.extend(articles)
                    source_stats[source_name] = {
                        'articles_collected': len(articles),
                        'status': 'success',
                        'last_updated': datetime.utcnow().isoformat()
                    }
                    
                    # Rate limiting
                    time.sleep(0.5)
                    
                except Exception as e:
                    logger.error(f"Error collecting from {source_name}: {e}")
                    source_stats[source_name] = {
                        'articles_collected': 0,
                        'status': 'error',
                        'error': str(e),
                        'last_updated': datetime.utcnow().isoformat()
                    }
            
            # Remove duplicates and process articles
            unique_articles = NewsAggregationService._remove_duplicates(all_articles)
            processed_articles = NewsAggregationService._process_articles(unique_articles)
            
            # Categorize and score articles
            categorized_articles = NewsAggregationService._categorize_articles(processed_articles)
            
            return {
                'success': True,
                'total_articles': len(categorized_articles),
                'source_stats': source_stats,
                'articles': categorized_articles,
                'collection_time': datetime.utcnow().isoformat(),
                'next_update': (datetime.utcnow() + timedelta(minutes=15)).isoformat()
            }
            
        except Exception as e:
            logger.error(f"News collection error: {e}")
            return {
                'success': False,
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat()
            }
    
    @staticmethod
    def get_company_specific_news(company_symbol: str, company_name: str = None) -> Dict:
        """Get news specifically related to a company"""
        try:
            # Collect general news first
            all_news = NewsAggregationService.collect_all_news()
            
            if not all_news['success']:
                return all_news
            
            # Filter for company-specific news
            company_keywords = [company_symbol.upper()]
            if company_name:
                company_keywords.extend([
                    company_name.lower(),
                    company_name.upper(),
                    company_name.title()
                ])
            
            relevant_articles = []
            for article in all_news['articles']:
                relevance_score = NewsAggregationService._calculate_company_relevance(
                    article, company_keywords
                )
                
                if relevance_score > 0.3:  # Threshold for relevance
                    article['company_relevance_score'] = relevance_score
                    article['matched_keywords'] = NewsAggregationService._find_matched_keywords(
                        article, company_keywords
                    )
                    relevant_articles.append(article)
            
            # Sort by relevance and recency
            relevant_articles.sort(
                key=lambda x: (x['company_relevance_score'], x['published_timestamp']),
                reverse=True
            )
            
            return {
                'success': True,
                'company_symbol': company_symbol,
                'company_name': company_name,
                'total_relevant_articles': len(relevant_articles),
                'articles': relevant_articles[:20],  # Top 20 most relevant
                'search_keywords': company_keywords,
                'timestamp': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Company news collection error: {e}")
            return {
                'success': False,
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat()
            }
    
    @staticmethod
    def get_trending_topics() -> Dict:
        """Identify trending topics and themes in recent news"""
        try:
            # Collect recent news
            all_news = NewsAggregationService.collect_all_news()
            
            if not all_news['success']:
                return all_news
            
            # Extract keywords and topics
            keyword_frequency = {}
            topic_articles = {}
            
            for article in all_news['articles']:
                keywords = NewsAggregationService._extract_keywords(article)
                
                for keyword in keywords:
                    keyword_frequency[keyword] = keyword_frequency.get(keyword, 0) + 1
                    
                    if keyword not in topic_articles:
                        topic_articles[keyword] = []
                    topic_articles[keyword].append(article)
            
            # Identify trending topics (appearing in multiple articles)
            trending_topics = []
            for keyword, frequency in keyword_frequency.items():
                if frequency >= 3:  # Minimum frequency for trending
                    trending_topics.append({
                        'topic': keyword,
                        'frequency': frequency,
                        'trend_score': frequency * len(topic_articles[keyword]),
                        'related_articles': len(topic_articles[keyword]),
                        'sample_headlines': [
                            article['title'] for article in topic_articles[keyword][:3]
                        ]
                    })
            
            # Sort by trend score
            trending_topics.sort(key=lambda x: x['trend_score'], reverse=True)
            
            return {
                'success': True,
                'trending_topics': trending_topics[:10],  # Top 10 trending
                'total_articles_analyzed': len(all_news['articles']),
                'analysis_time': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Trending topics analysis error: {e}")
            return {
                'success': False,
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat()
            }
    
    @staticmethod
    def _collect_from_source(source_name: str, source_config: Dict) -> List[Dict]:
        """Collect articles from a single news source"""
        articles = []
        
        try:
            # Parse RSS feed
            if not FEEDPARSER_AVAILABLE:
                logger.debug(f"Skipping RSS fetch for {source_name} (feedparser unavailable)")
                return []
            feed = feedparser.parse(source_config['rss'])
            
            for entry in feed.entries:
                article = {
                    'source': source_name,
                    'source_weight': source_config['weight'],
                    'category': source_config['category'],
                    'language': source_config['language'],
                    'title': entry.get('title', ''),
                    'description': entry.get('description', ''),
                    'summary': entry.get('summary', ''),
                    'link': entry.get('link', ''),
                    'published': entry.get('published', ''),
                    'published_timestamp': NewsAggregationService._parse_timestamp(
                        entry.get('published', '')
                    ),
                    'content_hash': NewsAggregationService._generate_content_hash(
                        entry.get('title', '') + entry.get('description', '')
                    ),
                    'collected_at': datetime.utcnow().isoformat()
                }
                
                # Add additional metadata if available
                if hasattr(entry, 'tags'):
                    article['tags'] = [tag.term for tag in entry.tags]
                
                if hasattr(entry, 'author'):
                    article['author'] = entry.author
                
                articles.append(article)
                
        except Exception as e:
            logger.error(f"Error parsing RSS from {source_name}: {e}")
            # Try alternative parsing or API calls here
            
        return articles
    
    @staticmethod
    def _remove_duplicates(articles: List[Dict]) -> List[Dict]:
        """Remove duplicate articles based on content hash"""
        seen_hashes = set()
        unique_articles = []
        
        for article in articles:
            content_hash = article['content_hash']
            if content_hash not in seen_hashes:
                seen_hashes.add(content_hash)
                unique_articles.append(article)
        
        return unique_articles
    
    @staticmethod
    def _process_articles(articles: List[Dict]) -> List[Dict]:
        """Process and enrich articles with additional metadata"""
        processed = []
        
        for article in articles:
            # Clean and normalize text
            article['title'] = NewsAggregationService._clean_text(article['title'])
            article['description'] = NewsAggregationService._clean_text(article['description'])
            
            # Extract domain from link
            if article['link']:
                article['domain'] = urlparse(article['link']).netloc
            
            # Calculate article age
            if article['published_timestamp']:
                age_hours = (datetime.utcnow() - article['published_timestamp']).total_seconds() / 3600
                article['age_hours'] = round(age_hours, 2)
                article['age_category'] = NewsAggregationService._categorize_age(age_hours)
            
            # Initial relevance score
            article['relevance_score'] = NewsAggregationService._calculate_initial_relevance(article)
            
            processed.append(article)
        
        return processed
    
    @staticmethod
    def _categorize_articles(articles: List[Dict]) -> List[Dict]:
        """Categorize articles into market-relevant categories"""
        categorized = []
        
        market_keywords = {
            'earnings': ['earnings', 'quarterly', 'results', 'profit', 'revenue'],
            'mergers': ['merger', 'acquisition', 'takeover', 'deal', 'buyout'],
            'regulation': ['regulation', 'policy', 'government', 'law', 'compliance'],
            'technology': ['technology', 'innovation', 'AI', 'digital', 'tech'],
            'energy': ['oil', 'gas', 'energy', 'renewable', 'solar', 'wind'],
            'finance': ['bank', 'financial', 'credit', 'loan', 'interest rate'],
            'crypto': ['bitcoin', 'cryptocurrency', 'blockchain', 'crypto', 'digital currency']
        }
        
        for article in articles:
            article_text = (article['title'] + ' ' + article['description']).lower()
            
            # Determine market categories
            article['market_categories'] = []
            for category, keywords in market_keywords.items():
                if any(keyword in article_text for keyword in keywords):
                    article['market_categories'].append(category)
            
            # Market impact score
            article['market_impact_score'] = NewsAggregationService._calculate_market_impact(article)
            
            # Priority classification
            article['priority'] = NewsAggregationService._classify_priority(article)
            
            categorized.append(article)
        
        return categorized
    
    @staticmethod
    def _calculate_company_relevance(article: Dict, company_keywords: List[str]) -> float:
        """Calculate how relevant an article is to a specific company"""
        text = (article['title'] + ' ' + article['description']).lower()
        
        relevance_score = 0.0
        
        for keyword in company_keywords:
            keyword_lower = keyword.lower()
            
            # Title mentions (higher weight)
            if keyword_lower in article['title'].lower():
                relevance_score += 0.5
            
            # Description mentions
            if keyword_lower in article['description'].lower():
                relevance_score += 0.3
            
            # Exact matches get bonus
            if keyword_lower == keyword:
                relevance_score += 0.2
        
        # Source weight bonus
        relevance_score *= article.get('source_weight', 1.0)
        
        # Recency bonus (more recent = more relevant)
        age_hours = article.get('age_hours', 24)
        if age_hours < 1:
            relevance_score *= 1.5
        elif age_hours < 6:
            relevance_score *= 1.2
        elif age_hours < 24:
            relevance_score *= 1.0
        else:
            relevance_score *= 0.8
        
        return min(relevance_score, 1.0)  # Cap at 1.0
    
    @staticmethod
    def _find_matched_keywords(article: Dict, keywords: List[str]) -> List[str]:
        """Find which keywords were matched in the article"""
        text = (article['title'] + ' ' + article['description']).lower()
        matched = []
        
        for keyword in keywords:
            if keyword.lower() in text:
                matched.append(keyword)
        
        return matched
    
    @staticmethod
    def _extract_keywords(article: Dict) -> List[str]:
        """Extract key terms and topics from article"""
        text = (article['title'] + ' ' + article['description']).lower()
        
        # Common financial and market keywords
        important_keywords = [
            'earnings', 'revenue', 'profit', 'loss', 'merger', 'acquisition',
            'stock', 'share', 'market', 'trading', 'investment', 'dividend',
            'growth', 'decline', 'rise', 'fall', 'volatility', 'risk',
            'inflation', 'interest rate', 'federal reserve', 'central bank',
            'technology', 'energy', 'healthcare', 'finance', 'real estate'
        ]
        
        found_keywords = []
        for keyword in important_keywords:
            if keyword in text:
                found_keywords.append(keyword)
        
        return found_keywords
    
    @staticmethod
    def _calculate_initial_relevance(article: Dict) -> float:
        """Calculate initial relevance score for an article"""
        score = 0.5  # Base score
        
        # Source weight
        score *= article.get('source_weight', 1.0)
        
        # Age factor (newer is more relevant)
        age_hours = article.get('age_hours', 24)
        if age_hours < 2:
            score *= 1.3
        elif age_hours < 12:
            score *= 1.1
        elif age_hours > 48:
            score *= 0.7
        
        # Title length factor (reasonable length preferred)
        title_length = len(article['title'])
        if 30 <= title_length <= 100:
            score *= 1.1
        elif title_length < 10 or title_length > 150:
            score *= 0.8
        
        return min(score, 1.0)
    
    @staticmethod
    def _calculate_market_impact(article: Dict) -> float:
        """Calculate potential market impact of an article"""
        impact_score = 0.0
        
        title_text = article['title'].lower()
        desc_text = article['description'].lower()
        
        # High impact keywords
        high_impact_keywords = [
            'crash', 'collapse', 'surge', 'plummet', 'skyrocket',
            'bankruptcy', 'bailout', 'emergency', 'crisis', 'bubble'
        ]
        
        # Medium impact keywords
        medium_impact_keywords = [
            'earnings', 'merger', 'acquisition', 'dividend', 'split',
            'guidance', 'forecast', 'outlook', 'results', 'announcement'
        ]
        
        # Calculate impact based on keywords
        for keyword in high_impact_keywords:
            if keyword in title_text:
                impact_score += 0.8
            elif keyword in desc_text:
                impact_score += 0.5
        
        for keyword in medium_impact_keywords:
            if keyword in title_text:
                impact_score += 0.4
            elif keyword in desc_text:
                impact_score += 0.2
        
        # Source credibility factor
        impact_score *= article.get('source_weight', 1.0)
        
        return min(impact_score, 1.0)
    
    @staticmethod
    def _classify_priority(article: Dict) -> str:
        """Classify article priority level"""
        market_impact = article.get('market_impact_score', 0)
        age_hours = article.get('age_hours', 24)
        
        if market_impact > 0.7 and age_hours < 6:
            return 'urgent'
        elif market_impact > 0.5 and age_hours < 12:
            return 'high'
        elif market_impact > 0.3 or age_hours < 24:
            return 'medium'
        else:
            return 'low'
    
    @staticmethod
    def _parse_timestamp(timestamp_str: str) -> Optional[datetime]:
        """Parse various timestamp formats"""
        if not timestamp_str:
            return None
        
        try:
            # Try various formats
            formats = [
                '%a, %d %b %Y %H:%M:%S %z',
                '%a, %d %b %Y %H:%M:%S %Z',
                '%Y-%m-%dT%H:%M:%S%z',
                '%Y-%m-%d %H:%M:%S',
                '%d %b %Y %H:%M:%S'
            ]
            
            for fmt in formats:
                try:
                    return datetime.strptime(timestamp_str, fmt)
                except ValueError:
                    continue
            
            # If all fail, return current time
            return datetime.utcnow()
            
        except Exception:
            return datetime.utcnow()
    
    @staticmethod
    def _generate_content_hash(content: str) -> str:
        """Generate hash for duplicate detection"""
        return hashlib.md5(content.encode('utf-8')).hexdigest()
    
    @staticmethod
    def _clean_text(text: str) -> str:
        """Clean and normalize text content"""
        if not text:
            return ""
        
        # Remove HTML tags
        text = re.sub(r'<[^>]+>', '', text)
        
        # Remove extra whitespace
        text = ' '.join(text.split())
        
        # Remove special characters (keep basic punctuation)
        text = re.sub(r'[^\w\s\.\,\!\?\:\;\-]', '', text)
        
        return text.strip()
    
    @staticmethod
    def _categorize_age(age_hours: float) -> str:
        """Categorize article age"""
        if age_hours < 1:
            return 'breaking'
        elif age_hours < 6:
            return 'recent'
        elif age_hours < 24:
            return 'today'
        elif age_hours < 72:
            return 'this_week'
        else:
            return 'older'
