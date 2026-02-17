from flask import Blueprint, make_response, url_for, current_app
from datetime import datetime

sitemap_bp = Blueprint('sitemap', __name__)

@sitemap_bp.route('/sitemap.xml')
def sitemap():
    """Generate XML sitemap for SEO"""
    try:
        # Define all public URLs for sitemap
        pages = []
        
        # Static pages - only include existing routes
        static_pages = [
            {'url': url_for('main.index', _external=True), 'lastmod': '2025-07-14', 'changefreq': 'daily', 'priority': '1.0'},
        ]
        
        # Try to add auth routes if they exist
        try:
            static_pages.append({'url': url_for('auth.register', _external=True), 'lastmod': '2025-07-14', 'changefreq': 'monthly', 'priority': '0.9'})
        except:
            pass
            
        try:
            static_pages.append({'url': url_for('auth.login', _external=True), 'lastmod': '2025-07-14', 'changefreq': 'monthly', 'priority': '0.9'})
        except:
            pass
        
        # Stock pages for popular tickers
        popular_tickers = [
            'EQNR.OL', 'DNB.OL', 'TEL.OL', 'MOWI.OL', 'YAR.OL', 'AKERBP.OL',
            'AAPL', 'GOOGL', 'MSFT', 'TSLA', 'AMZN', 'NVDA', 'META'
        ]
        
        stock_pages = []
        for ticker in popular_tickers:
            try:
                stock_url = url_for('stocks.details', ticker=ticker, _external=True)
                stock_pages.append({
                    'url': stock_url,
                    'lastmod': '2025-07-14',
                    'changefreq': 'hourly',
                    'priority': '0.9'
                })
            except Exception:
                continue
        
        # Analysis pages
        analysis_pages = []
        try:
            analysis_pages = [
                {'url': url_for('analysis.technical', _external=True), 'lastmod': '2025-07-14', 'changefreq': 'daily', 'priority': '0.8'},
                {'url': url_for('analysis.market_sentiment', _external=True), 'lastmod': '2025-07-14', 'changefreq': 'daily', 'priority': '0.8'},
            ]
        except Exception:
            # Skip analysis pages if routes don't exist
            pass
        
        # Combine all pages
        pages.extend(static_pages)
        pages.extend(stock_pages)
        pages.extend(analysis_pages)
        
        # Generate XML
        xml_content = '''<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"
        xmlns:news="http://www.google.com/schemas/sitemap-news/0.9"
        xmlns:xhtml="http://www.w3.org/1999/xhtml"
        xmlns:mobile="http://www.google.com/schemas/sitemap-mobile/1.0">
'''
        
        for page in pages:
            xml_content += f'''
    <url>
        <loc>{page['url']}</loc>
        <lastmod>{page['lastmod']}</lastmod>
        <changefreq>{page['changefreq']}</changefreq>
        <priority>{page['priority']}</priority>
        <mobile:mobile/>
    </url>'''
        
        xml_content += '\n</urlset>'
        
        response = make_response(xml_content)
        response.headers['Content-Type'] = 'application/xml; charset=utf-8'
        return response
        
    except Exception as e:
        current_app.logger.error(f"Error generating sitemap: {e}")
        # Return a basic sitemap
        basic_xml = '''<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
    <url>
        <loc>https://aksjeradar.trade/</loc>
        <lastmod>2025-07-14</lastmod>
        <changefreq>daily</changefreq>
        <priority>1.0</priority>
    </url>
</urlset>'''
        
        response = make_response(basic_xml)
        response.headers['Content-Type'] = 'application/xml; charset=utf-8'
        return response

@sitemap_bp.route('/robots.txt')
def robots():
    """Generate robots.txt for SEO"""
    robots_content = f"""User-agent: *
Allow: /
Disallow: /admin/
Disallow: /auth/reset-password*
Disallow: /profile/
Disallow: /portfolio/
Disallow: /watchlist/
Disallow: /api/

Sitemap: {url_for('sitemap.sitemap', _external=True)}

# Norwegian specific
User-agent: Googlebot
Allow: /

# Bing
User-agent: bingbot
Allow: /

# Yandex
User-agent: YandexBot
Allow: /
"""
    
    response = make_response(robots_content)
    response.headers['Content-Type'] = 'text/plain; charset=utf-8'
    return response
