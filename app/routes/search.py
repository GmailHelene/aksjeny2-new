from flask import Blueprint, render_template, request, current_app
from ..utils.access_control import access_required

search = Blueprint('search', __name__)

@search.route('/search')
@access_required
def search_page():
    """Search page route"""
    try:
        query = request.args.get('q', '')
        
        if not query:
            return render_template('search/search.html', title='Søk', results=None, query='')
        
        # Mock search results with better error handling
        search_results = []
        
        # Handle known tickers with predefined data
        if query.lower() in ['eqnr', 'equinor']:
            search_results.append({
                'ticker': 'OSL:EQNR',
                'name': 'Equinor ASA',
                'exchange': 'Oslo Børs',
                'price': 290.25,
                'change': 1.2
            })
        elif query.lower() in ['dnb', 'dnb bank']:
            search_results.append({
                'ticker': 'OSL:DNB',
                'name': 'DNB Bank ASA',
                'exchange': 'Oslo Børs',
                'price': 212.80,
                'change': -0.56
            })
        elif query.lower() in ['apple', 'aapl']:
            search_results.append({
                'ticker': 'NASDAQ:AAPL',
                'name': 'Apple Inc.',
                'exchange': 'NASDAQ',
                'price': 185.70,
                'change': 0.67
            })
        elif query.lower() in ['microsoft', 'msft']:
            search_results.append({
                'ticker': 'NASDAQ:MSFT',
                'name': 'Microsoft Corporation',
                'exchange': 'NASDAQ',
                'price': 390.20,
                'change': 0.54
            })
        
        # If we don't have predefined data but it's still a valid query, show some results
        if not search_results and len(query) >= 2:
            # Create some generic results based on query
            if any(char.isdigit() for char in query):
                # Handle numeric queries
                search_results.append({
                    'ticker': 'DEMO-' + query.upper(),
                    'name': 'Demo Result ' + query,
                    'exchange': 'Demo Exchange',
                    'price': 100.00,
                    'change': 0.50
                })
            else:
                # Handle text queries for Norwegian stocks
                search_results.append({
                    'ticker': 'OSL:' + query.upper(),
                    'name': query.title() + ' ASA',
                    'exchange': 'Oslo Børs',
                    'price': 150.25,
                    'change': 1.25
                })
        
        return render_template('search/search.html', title='Søk - ' + query, 
                            query=query, results=search_results)
    except Exception as e:
        current_app.logger.error(f"Error in search: {str(e)}")
        return render_template('error.html', error="Det oppsto en feil under søket."), 200