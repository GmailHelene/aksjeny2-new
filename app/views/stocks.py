from flask import render_template, request, jsonify, current_app
from app.utils.stocks_utils import get_comparison_data, generate_demo_comparison

def init_stocks_routes(app):
    """Initialize stock routes with app instance"""
    
    @app.route('/stocks/compare')
    def stocks_compare():
        """Compare multiple stocks"""
        try:
            tickers = request.args.getlist('tickers')
            # Remove empty strings
            tickers = [t for t in tickers if t]
            
            if not tickers:
                tickers = ['EQNR.OL', 'DNB.OL']
            comparison_data = get_comparison_data(tickers)
            if not comparison_data:
                comparison_data = generate_demo_comparison(tickers)
            return render_template('stocks/compare.html',
                                 tickers=tickers,
                                 error=False,
                                 **comparison_data)
                                 
        except Exception as e:
            current_app.logger.error(f"Compare error: {str(e)}")
            return render_template('stocks/compare.html',
                                 error=True,
                                 message="Kunne ikke sammenligne aksjer")

    # /stocks/details/<symbol> now served exclusively by blueprint in app/routes/stocks.py (unified logic)
