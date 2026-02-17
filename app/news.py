from flask import Blueprint, render_template, request, jsonify, abort
from datetime import datetime, timedelta
from app.services.news_service import (
    news_service, 
    get_latest_news_sync, 
    get_company_news_sync,
    search_news_sync,
    get_article_by_id
)
from app.utils.access_control import access_required
import logging

logger = logging.getLogger(__name__)

news_bp = Blueprint('news', __name__, url_prefix='/news')

@news_bp.route('/')
@access_required
def news_index():
    """Main news page with real data"""
    try:
        category = request.args.get('category', 'all')
        limit = min(int(request.args.get('limit', 20)), 50)  # Cap at 50 for performance
        page = max(int(request.args.get('page', 1)), 1)
        
        # Calculate offset for pagination
        offset = (page - 1) * limit
        
        # Get latest news with error handling
        news_articles = get_latest_news_sync(limit=limit + offset, category=category)
        
        # Apply pagination
        if offset > 0:
            news_articles = news_articles[offset:offset + limit]
        else:
            news_articles = news_articles[:limit]
        
        # Ensure we have data
        if not news_articles:
            logger.warning(f"No news articles found for category: {category}")
            news_articles = []
        
        # Get available categories for filter
        categories = [
            {'id': 'all', 'name': 'Alle nyheter'},
            {'id': 'norwegian', 'name': 'Norske nyheter'},
            {'id': 'international', 'name': 'Internasjonale nyheter'},
            {'id': 'oslo_bors', 'name': 'Oslo Børs'},
            {'id': 'energy', 'name': 'Energi'},
            {'id': 'tech', 'name': 'Teknologi'},
            {'id': 'crypto', 'name': 'Kryptovaluta'},
            {'id': 'banking', 'name': 'Bank og finans'},
            {'id': 'shipping', 'name': 'Shipping'},
            {'id': 'salmon', 'name': 'Laks og sjømat'}
        ]
        
        return render_template('news/index.html', 
                             news_articles=news_articles,
                             category=category,
                             categories=categories,
                             page=page,
                             has_more=len(news_articles) == limit)
    except ValueError as ve:
        logger.error(f"Invalid parameter in news index: {ve}")
        return render_template('news/index.html', 
                             news_articles=[],
                             category='all',
                             categories=[],
                             error="Ugyldig parameter")
    except Exception as e:
        logger.error(f"Error in news index: {e}")
        return render_template('news/index.html', 
                             news_articles=[],
                             category='all',
                             categories=[],
                             error="Kunne ikke laste nyheter")

@news_bp.route('/api/latest')
def api_latest_news():
    """API endpoint for latest news (JSON)"""
    try:
        category = request.args.get('category', 'all')
        limit = min(int(request.args.get('limit', 10)), 50)
        
        news_articles = get_latest_news_sync(limit=limit, category=category)
        
        # Convert to JSON-serializable format
        articles_data = []
        for article in news_articles:
            articles_data.append({
                'title': article.title,
                'summary': article.summary,
                'link': article.link,
                'source': article.source,
                'published': article.published.isoformat() if article.published else None,
                'image_url': article.image_url,
                'relevance_score': article.relevance_score,
                'categories': article.categories
            })
        
        return jsonify({
            'success': True,
            'count': len(articles_data),
            'articles': articles_data
        })
    except Exception as e:
        logger.error(f"Error in API latest news: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@news_bp.route('/category/<category_name>')
@access_required
def news_category(category_name):
    """News filtered by specific category"""
    try:
        limit = min(int(request.args.get('limit', 20)), 50)
        page = max(int(request.args.get('page', 1)), 1)
        
        # Get news for specific category
        news_articles = get_latest_news_sync(limit=limit * page, category=category_name)
        
        # Apply pagination
        offset = (page - 1) * limit
        if offset > 0:
            news_articles = news_articles[offset:offset + limit]
        else:
            news_articles = news_articles[:limit]
        
        category_names = {
            'norwegian': 'Norske nyheter',
            'international': 'Internasjonale nyheter',
            'oslo_bors': 'Oslo Børs',
            'energy': 'Energi',
            'tech': 'Teknologi',
            'crypto': 'Kryptovaluta',
            'banking': 'Bank og finans',
            'shipping': 'Shipping',
            'salmon': 'Laks og sjømat'
        }
        
        category_display_name = category_names.get(category_name, category_name.title())
        
        return render_template('news/category.html',
                             news_articles=news_articles,
                             category=category_name,
                             category_name=category_display_name,
                             page=page,
                             has_more=len(news_articles) == limit)
    except Exception as e:
        logger.error(f"Error in news category {category_name}: {e}")
        return render_template('news/category.html',
                             news_articles=[],
                             category=category_name,
                             category_name=category_name.title(),
                             error="Kunne ikke laste kategorinyheter")

@news_bp.route('/search')
@access_required
def news_search():
    """Search news articles"""
    try:
        query = request.args.get('q', '').strip()
        limit = min(int(request.args.get('limit', 20)), 50)
        
        if not query:
            return render_template('news/search.html',
                                 articles=[],
                                 query='',
                                 message="Skriv inn et søkeord")
        
        # Search articles
        articles = search_news_sync(query, limit)
        
        return render_template('news/search.html',
                             articles=articles,
                             query=query,
                             count=len(articles))
    except Exception as e:
        logger.error(f"Error in news search: {e}")
        return render_template('news/search.html',
                             articles=[],
                             query=request.args.get('q', ''),
                             error="Søket feilet")

@news_bp.route('/company/<company_symbol>')
@access_required
def company_news(company_symbol):
    """News for specific company"""
    try:
        limit = min(int(request.args.get('limit', 10)), 30)
        
        # Get company-specific news
        news_articles = get_company_news_sync(company_symbol, limit)
        
        # Company name mapping for display
        company_names = {
            'EQNR.OL': 'Equinor ASA',
            'DNB.OL': 'DNB Bank ASA',
            'TEL.OL': 'Telenor ASA',
            'AKERBP.OL': 'Aker BP ASA',
            'YAR.OL': 'Yara International ASA',
            'NHY.OL': 'Norsk Hydro ASA',
            'MOWI.OL': 'Mowi ASA'
        }
        
        company_name = company_names.get(company_symbol, company_symbol)
        
        return render_template('news/company.html',
                             news_articles=news_articles,
                             company_symbol=company_symbol,
                             company_name=company_name)
    except Exception as e:
        logger.error(f"Error getting company news for {company_symbol}: {e}")
        return render_template('news/company.html',
                             news_articles=[],
                             company_symbol=company_symbol,
                             company_name=company_symbol,
                             error="Kunne ikke laste selskapsnyheter")

@news_bp.route('/article/<article_id>')
@access_required
def news_article(article_id):
    """Display individual news article"""
    try:
        article = get_article_by_id(article_id)
        
        if not article:
            abort(404)
        
        return render_template('news/article.html', article=article)
    except Exception as e:
        logger.error(f"Error getting article {article_id}: {e}")
        abort(500)

@news_bp.route('/widget')
def news_widget():
    """Lightweight news widget for embedding"""
    try:
        limit = min(int(request.args.get('limit', 5)), 10)
        category = request.args.get('category', 'all')
        
        news_articles = get_latest_news_sync(limit=limit, category=category)
        
        return render_template('news/widget.html',
                             news_articles=news_articles,
                             category=category)
    except Exception as e:
        logger.error(f"Error in news widget: {e}")
        return render_template('news/widget.html',
                             news_articles=[],
                             category='all')

@news_bp.route('/embed')
def news_embed():
    """Embeddable news feed"""
    try:
        limit = min(int(request.args.get('limit', 8)), 15)
        category = request.args.get('category', 'norwegian')
        
        news_articles = get_latest_news_sync(limit=limit, category=category)
        
        return render_template('news/embed.html',
                             news_articles=news_articles,
                             category=category)
    except Exception as e:
        logger.error(f"Error in news embed: {e}")
        return render_template('news/embed.html',
                             news_articles=[],
                             category='norwegian')

@news_bp.route('/api/company/<company_symbol>')
def api_company_news(company_symbol):
    """API endpoint for company news"""
    try:
        limit = min(int(request.args.get('limit', 5)), 20)
        
        articles = get_company_news_sync(company_symbol, limit)
        
        articles_data = []
        for article in articles:
            articles_data.append({
                'title': article.title,
                'summary': article.summary,
                'link': article.link,
                'source': article.source,
                'published': article.published.isoformat() if article.published else None,
                'relevance_score': article.relevance_score
            })
        
        return jsonify({
            'success': True,
            'company': company_symbol,
            'count': len(articles_data),
            'articles': articles_data
        })
    except Exception as e:
        logger.error(f"Error in API company news for {company_symbol}: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

# Error handlers for news blueprint
@news_bp.errorhandler(404)
def news_not_found(error):
    return render_template('news/404.html'), 404

@news_bp.errorhandler(500)
def news_server_error(error):
    return render_template('news/500.html'), 500