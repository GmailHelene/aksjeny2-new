"""
SEO Sitemap Generator for Aksjeradar
Generates dynamic sitemap.xml for optimal search engine indexing
"""

from flask import Blueprint, render_template_string, url_for
from datetime import datetime

seo_sitemap = Blueprint('seo_sitemap', __name__)

@seo_sitemap.route('/sitemap.xml')
def sitemap():
    """Generate dynamic sitemap.xml for SEO"""
    
    # Static pages with priorities
    static_pages = [
        # Core pages - highest priority
        {'url': '/', 'priority': '1.0', 'changefreq': 'daily'},
        {'url': '/demo', 'priority': '1.0', 'changefreq': 'weekly'},
        {'url': '/stocks/', 'priority': '1.0', 'changefreq': 'daily'},
        {'url': '/analysis/', 'priority': '1.0', 'changefreq': 'daily'},
        
        # High-value landing pages
        {'url': '/stocks/list/oslo', 'priority': '0.9', 'changefreq': 'daily'},
        {'url': '/stocks/list/global', 'priority': '0.9', 'changefreq': 'daily'},
        {'url': '/stocks/list/crypto', 'priority': '0.9', 'changefreq': 'daily'},
        {'url': '/stocks/list/currency', 'priority': '0.9', 'changefreq': 'daily'},
        {'url': '/stocks/compare', 'priority': '0.9', 'changefreq': 'weekly'},
        
        # Analysis pages - high search volume
        {'url': '/analysis/technical/', 'priority': '0.9', 'changefreq': 'daily'},
        {'url': '/analysis/fundamental/', 'priority': '0.9', 'changefreq': 'daily'},
        {'url': '/analysis/ai', 'priority': '0.9', 'changefreq': 'daily'},
        {'url': '/analysis/screener', 'priority': '0.9', 'changefreq': 'daily'},
        {'url': '/analysis/warren-buffett', 'priority': '0.8', 'changefreq': 'weekly'},
        {'url': '/analysis/benjamin-graham', 'priority': '0.8', 'changefreq': 'weekly'},
        {'url': '/analysis/market-overview', 'priority': '0.8', 'changefreq': 'daily'},
        {'url': '/analysis/sentiment', 'priority': '0.8', 'changefreq': 'daily'},
        {'url': '/analysis/recommendations', 'priority': '0.8', 'changefreq': 'daily'},
        
        # News and content
        {'url': '/news/', 'priority': '0.8', 'changefreq': 'hourly'},
        {'url': '/news/category/økonomi', 'priority': '0.7', 'changefreq': 'daily'},
        {'url': '/news/category/aksjer', 'priority': '0.7', 'changefreq': 'daily'},
        {'url': '/news/category/teknologi', 'priority': '0.7', 'changefreq': 'daily'},
        
        # Portfolio tools
        {'url': '/portfolio/', 'priority': '0.7', 'changefreq': 'weekly'},
        {'url': '/portfolio/watchlist', 'priority': '0.7', 'changefreq': 'daily'},
        
        # Education and guides
        {'url': '/investment-guides/', 'priority': '0.6', 'changefreq': 'monthly'},
        {'url': '/investment-guides/index', 'priority': '0.6', 'changefreq': 'monthly'},
        
        # Business pages
        {'url': '/pricing/pricing/', 'priority': '0.6', 'changefreq': 'monthly'},
    {'url': '/investor/', 'priority': '0.7', 'changefreq': 'monthly'},
        {'url': '/about', 'priority': '0.5', 'changefreq': 'monthly'},
        {'url': '/contact', 'priority': '0.5', 'changefreq': 'monthly'},
        {'url': '/privacy', 'priority': '0.3', 'changefreq': 'yearly'},
        {'url': '/terms', 'priority': '0.3', 'changefreq': 'yearly'},
    ]
    
    # Generate URLs with full domain
    current_date = datetime.now().strftime('%Y-%m-%d')
    
    sitemap_xml = '''<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"
        xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
        xsi:schemaLocation="http://www.sitemaps.org/schemas/sitemap/0.9
        http://www.sitemaps.org/schemas/sitemap/0.9/sitemap.xsd">
'''
    
    for page in static_pages:
        full_url = f"https://aksjeradar.trade{page['url']}"
        sitemap_xml += f'''
    <url>
        <loc>{full_url}</loc>
        <lastmod>{current_date}</lastmod>
        <changefreq>{page['changefreq']}</changefreq>
        <priority>{page['priority']}</priority>
    </url>'''
    
    sitemap_xml += '\n</urlset>'
    
    from flask import Response
    return Response(sitemap_xml, mimetype='application/xml')

@seo_sitemap.route('/robots.txt')
def robots():
    """Serve robots.txt dynamically"""
    robots_txt = """User-agent: *
Allow: /

# Allow all crawlers
Disallow: /admin/
Disallow: /api/
Disallow: /restricted_access
Disallow: /payment_success
Disallow: /payment_cancel
Disallow: /_debug_toolbar/
Disallow: /logout
Disallow: /login

# Sitemap location
Sitemap: https://aksjeradar.trade/sitemap.xml

# Crawl-delay (polite crawling)
Crawl-delay: 1
"""
    
    from flask import Response
    return Response(robots_txt, mimetype='text/plain')
