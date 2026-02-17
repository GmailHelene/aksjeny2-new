from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, current_app, Response
from flask_login import login_required, current_user
from flask_wtf.csrf import validate_csrf, ValidationError
from datetime import datetime, timedelta
from io import BytesIO
import logging
import json
import os
import traceback

from ..models import Portfolio, PortfolioStock, StockTip, Watchlist, WatchlistStock
from ..extensions import db
from ..utils.access_control import access_required, demo_access
from ..utils.access_control_unified import unified_access_required
from ..utils.error_handler import (
    handle_api_error, format_number_norwegian, format_currency_norwegian,
    format_percentage_norwegian, safe_api_call, validate_stock_symbol,
    validate_quantity, UserFriendlyError
)
# Temporarily comment out problematic imports
# from ..services.portfolio_optimization_service import PortfolioOptimizationService
# from ..services.performance_tracking_service import PerformanceTrackingService

logger = logging.getLogger(__name__)

# Lazy import for DataService to avoid circular import
def get_data_service():
    """Lazy import DataService to avoid circular imports"""
    from ..services.data_service import DataService
    return DataService

# Lazy import for AnalysisService to avoid circular import
def get_analysis_service():
    """Lazy import AnalysisService to avoid circular imports"""
    # from ..services.analysis_service import AnalysisService
    return None  # Disabled temporarily

# Lazy import for portfolio services
def get_portfolio_optimization_service():
    """Return Portfolio Optimization Service if available"""
    return None  # Disabled temporarily

def get_performance_tracking_service():
    """Return Performance Tracking Service if available"""
    return None  # Disabled temporarily

# Lazy import for reportlab to handle optional dependency
def get_reportlab():
    """Lazy import reportlab components for PDF generation"""
    try:
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle
        from reportlab.lib.pagesizes import A4
        from reportlab.lib import colors
        return {
            'SimpleDocTemplate': SimpleDocTemplate,
            'Table': Table, 
            'TableStyle': TableStyle,
            'A4': A4,
            'colors': colors
        }
    except ImportError:
        return None

portfolio = Blueprint('portfolio', __name__, url_prefix='/portfolio')
# Backwards compatibility alias for tests expecting 'portfolio_bp'
portfolio_bp = portfolio

@portfolio.route('/add_to_portfolio', methods=['POST'])
@access_required
def add_to_portfolio_quick():
    """Lightweight JSON endpoint for adding a symbol to the user's default portfolio.
    Expects JSON: {"symbol": "DNB.OL", "shares": optional float, "price": optional float}
    Returns JSON success state for toast messages.
    """
    try:
        if not request.is_json:
            return jsonify({'success': False, 'message': 'JSON body required'}), 400

        data = request.get_json() or {}
        ticker = (data.get('symbol') or data.get('ticker') or '').strip().upper()
        if not ticker:
            return jsonify({'success': False, 'message': 'Ticker mangler'}), 400

        # Basic validation (reuse validate_stock_symbol if available)
        try:
            validate_stock_symbol(ticker)
        except Exception:
            # Non-fatal; continue but mark invalid
            pass

        # Find or create a default portfolio
        portfolio_obj = None
        try:
            portfolio_obj = Portfolio.query.filter_by(user_id=current_user.id).first()
        except Exception as e:
            current_app.logger.error(f"Quick add portfolio query error: {e}")

        created_portfolio = False
        if not portfolio_obj:
            try:
                portfolio_obj = Portfolio(name='Min portefølje', user_id=current_user.id, description='Auto-opprettet')
                db.session.add(portfolio_obj)
                db.session.commit()
                created_portfolio = True
            except Exception as e:
                current_app.logger.error(f"Could not create default portfolio: {e}")
                db.session.rollback()
                return jsonify({'success': False, 'message': 'Kunne ikke opprette portefølje'}), 500

        # Determine shares and price (optional)
        shares = data.get('shares')
        price = data.get('price') or data.get('purchase_price')
        try:
            shares = float(shares) if shares is not None else 1.0
        except Exception:
            shares = 1.0
        try:
            price = float(price) if price is not None else 0.0
        except Exception:
            price = 0.0

        # Check if already present (avoid duplicates) - simple exact ticker match & not soft-deleted
        existing = None
        try:
            existing = PortfolioStock.query.filter_by(portfolio_id=portfolio_obj.id, ticker=ticker, deleted_at=None).first()
        except Exception as e:
            current_app.logger.warning(f"Duplicate check error for {ticker}: {e}")

        if existing:
            return jsonify({'success': True, 'message': f'{ticker} allerede i portefølje'}), 200

        # Insert new portfolio stock
        try:
            new_stock = PortfolioStock(
                portfolio_id=portfolio_obj.id,
                ticker=ticker,
                shares=shares,
                purchase_price=price,
                added_at=datetime.utcnow()
            )
            db.session.add(new_stock)
            db.session.commit()
        except Exception as e:
            current_app.logger.error(f"Insert portfolio stock error {ticker}: {e}")
            db.session.rollback()
            return jsonify({'success': False, 'message': 'Kunne ikke lagre aksje'}), 500

        msg = f'{ticker} lagt til i portefølje'
        if created_portfolio:
            msg += ' (ny portefølje opprettet)'
        return jsonify({'success': True, 'message': msg})
    except Exception as e:
        current_app.logger.error(f"Unhandled error in add_to_portfolio_quick: {e}")
        current_app.logger.error(traceback.format_exc())
        return jsonify({'success': False, 'message': 'Teknisk feil'}), 500

@portfolio.route('/overview')
@portfolio.route('/')  # Add this as an alias
@unified_access_required
def portfolio_overview():
    """Portfolio overview with enhanced error handling and fallback data"""
    try:
        current_app.logger.info(f"Loading portfolio overview for user {current_user.id}")
        
        # Get all portfolios for the current user
        user_portfolios = Portfolio.query.filter_by(user_id=current_user.id).all()
        
        if not user_portfolios:
            # No portfolios exist - show creation prompt
            context = {
                'total_value': 0,
                'total_profit_loss': 0,
                'active_alerts': 0,
                'stocks': {},
                'portfolio': None,
                'portfolios': [],
                'error': None
            }
            current_app.logger.info(f"No portfolios found for user {current_user.id}")
            return render_template('portfolio/index.html', **context)
        
        # Get the first portfolio to display (or could be selected portfolio)
        primary_portfolio = user_portfolios[0]
        current_app.logger.info(f"Using portfolio {primary_portfolio.id} as primary")
        
        # Get stocks in the primary portfolio
        try:
            # Exclude soft-deleted stocks
            portfolio_stocks = PortfolioStock.query.filter_by(portfolio_id=primary_portfolio.id, deleted_at=None).all()
            current_app.logger.info(f"Found {len(portfolio_stocks)} stocks in portfolio {primary_portfolio.id}")
        except Exception as db_error:
            current_app.logger.error(f"Database error retrieving portfolio stocks: {db_error}")
            portfolio_stocks = []
        
        # Calculate portfolio values with robust error handling
        total_value = 0
        total_profit_loss = 0
        stocks_data = {}
        
        for stock in portfolio_stocks:
            try:
                current_app.logger.debug(f"Processing stock {stock.ticker}")
                # Use simplified data access with multiple fallback layers
                try:
                    data_service = get_data_service()
                    stock_data = data_service.get_stock_info(stock.ticker)
                    
                    if stock_data and ('last_price' in stock_data or 'regularMarketPrice' in stock_data):
                        current_price = float(stock_data.get('last_price', stock_data.get('regularMarketPrice', stock.purchase_price)))
                        current_app.logger.debug(f"Got current price for {stock.ticker}: {current_price}")
                    else:
                        current_app.logger.warning(f"No price data found for {stock.ticker}, using purchase price")
                        current_price = stock.purchase_price
                except Exception as data_error:
                    current_app.logger.warning(f"Data service failed for {stock.ticker}: {data_error}")
                    # Use purchase price as fallback
                    current_price = stock.purchase_price
                
                # Safety check for invalid values
                if not current_price or not isinstance(current_price, (int, float)) or current_price <= 0:
                    current_price = stock.purchase_price if stock.purchase_price and stock.purchase_price > 0 else 1.0
                    current_app.logger.warning(f"Invalid price for {stock.ticker}, using fallback: {current_price}")
                
                # Safety check for purchase price
                if not stock.purchase_price or not isinstance(stock.purchase_price, (int, float)) or stock.purchase_price <= 0:
                    stock.purchase_price = current_price
                    current_app.logger.warning(f"Invalid purchase price for {stock.ticker}, using current price")
                
                purchase_value = stock.purchase_price * stock.shares
                current_value = current_price * stock.shares
                profit_loss = current_value - purchase_value
                
                # Safe calculation of percentage
                try:
                    profit_loss_percent = ((current_price / stock.purchase_price) - 1) * 100 if stock.purchase_price > 0 else 0
                except ZeroDivisionError:
                    profit_loss_percent = 0
                    current_app.logger.warning(f"Division by zero when calculating profit percent for {stock.ticker}")
                
                total_value += current_value
                total_profit_loss += profit_loss
                
                stocks_data[stock.ticker] = {
                    'shares': stock.shares,
                    'purchase_price': stock.purchase_price,
                    'last_price': current_price,
                    'profit_loss': profit_loss,
                    'profit_loss_percent': profit_loss_percent,
                    'stock_id': stock.id
                }
                
            except Exception as stock_error:
                current_app.logger.error(f"Error processing stock {stock.ticker}: {stock_error}")
                # Include stock with fallback data
                try:
                    purchase_value = stock.purchase_price * stock.shares
                    total_value += purchase_value
                    
                    stocks_data[stock.ticker] = {
                        'shares': stock.shares,
                        'purchase_price': stock.purchase_price,
                        'last_price': stock.purchase_price,  # Use purchase price as fallback
                        'profit_loss': 0,
                        'profit_loss_percent': 0,
                        'stock_id': stock.id
                    }
                except Exception as fallback_error:
                    current_app.logger.error(f"Critical error with fallback for {stock.ticker}: {fallback_error}")
                    # Skip this stock completely if it's causing serious issues
        
        # Prepare the context data for the template
        context = {
            'total_value': total_value,
            'total_profit_loss': total_profit_loss,
            'active_alerts': 0,  # Could be calculated from actual alerts
            'stocks': stocks_data,
            'portfolio': primary_portfolio,
            'portfolios': user_portfolios,
            'error': None
        }
        
        current_app.logger.info(f"Successfully loaded portfolio overview for user {current_user.id}")
        # Caching headers (weak ETag based on portfolio id + updated_at + stock count)
        try:
            import hashlib
            last_update = primary_portfolio.updated_at.isoformat() if primary_portfolio.updated_at else ''
            active_stock_count = len([s for s in portfolio_stocks])
            etag_base = f"overview:{primary_portfolio.id}:{last_update}:{active_stock_count}"
            etag = hashlib.sha1(etag_base.encode()).hexdigest()
            if request.headers.get('If-None-Match') == etag:
                return Response(status=304)
            response = Response(render_template('portfolio/index.html', **context))
            response.headers['ETag'] = etag
            if primary_portfolio.updated_at:
                response.headers['Last-Modified'] = primary_portfolio.updated_at.strftime('%a, %d %b %Y %H:%M:%S GMT')
            return response
        except Exception as cache_err:
            current_app.logger.debug(f"ETag generation failed: {cache_err}")
            return render_template('portfolio/index.html', **context)
        
    except Exception as e:
        current_app.logger.error(f"Critical error in portfolio overview: {str(e)}")
        import traceback
        current_app.logger.error(f"Traceback: {traceback.format_exc()}")
        flash('Det oppstod en feil ved lasting av porteføljer.', 'error')
        
        # Return safe fallback data
        fallback_context = {
            'portfolios': [],
            'total_value': 0,
            'total_profit_loss': 0,
            'active_alerts': 0,
            'stocks': {},
            'portfolio': None,
            'error': f"Teknisk feil: {str(e)}"
        }
        return render_template('portfolio/index.html', **fallback_context)

# Delete portfolio route
@portfolio.route('/delete/<int:id>', methods=['POST'])
@login_required
def delete_portfolio(id):
    """Delete a portfolio and all associated stocks"""
    try:
        portfolio_obj = Portfolio.query.filter_by(id=id, user_id=current_user.id).first()
        if not portfolio_obj:
            error_msg = 'Portefølje ikke funnet eller du har ikke tilgang.'
            if 'application/json' in request.headers.get('Accept', ''):
                return jsonify({'success': False, 'error': error_msg, 'portfolio_id': id}), 404
            flash(error_msg, 'danger')
            return redirect(url_for('portfolio.portfolio_overview'))

        # Delete all stocks in the portfolio (best-effort)
        try:
            PortfolioStock.query.filter_by(portfolio_id=id).delete()
        except Exception as stock_delete_error:
            current_app.logger.error(f"Error deleting stocks for portfolio {id}: {stock_delete_error}")

        # Delete the portfolio itself
        db.session.delete(portfolio_obj)
        db.session.commit()

        success_msg = 'Porteføljen ble slettet.'
        if 'application/json' in request.headers.get('Accept', ''):
            return jsonify({'success': True, 'message': success_msg, 'portfolio_id': id})
        flash(success_msg, 'success')
        return redirect(url_for('portfolio.portfolio_overview'))
    except Exception as e:
        current_app.logger.error(f"Error deleting portfolio {id}: {e}")
        db.session.rollback()
        error_msg = 'Kunne ikke slette porteføljen. Prøv igjen senere.'
        if 'application/json' in request.headers.get('Accept', ''):
            return jsonify({'success': False, 'error': error_msg, 'portfolio_id': id}), 500
        flash(error_msg, 'danger')
        return redirect(url_for('portfolio.portfolio_overview'))

"""Removed a large legacy block that executed at import time and referenced
undefined symbols (e.g. user_portfolios, total_value). That block caused
NameError during module import leading to 500 on /portfolio. The logic was
an older alternative overview implementation and is superseded by
portfolio_overview() which renders portfolio/index.html with safe fallbacks."""

@portfolio.route('/watchlist')
@unified_access_required
def watchlist():
    """User's watchlist with real data integration for paying users"""
    try:
        current_app.logger.info(f"Loading watchlist for user {current_user.id}")
        
        # Get user's watchlists and stocks
        user_watchlists = Watchlist.query.filter_by(user_id=current_user.id).all()
        
        # If no watchlists exist, create a default one
        if not user_watchlists:
            try:
                default_watchlist = Watchlist(
                    name='Min Watchlist',
                    description='Standard watchlist',
                    user_id=current_user.id
                )
                db.session.add(default_watchlist)
                db.session.commit()
                user_watchlists = [default_watchlist]
                current_app.logger.info(f"Created default watchlist for user {current_user.id}")
            except Exception as create_error:
                current_app.logger.error(f"Error creating default watchlist: {create_error}")
                db.session.rollback()
                # Use empty list if creation fails
                user_watchlists = []
        
        # Get primary watchlist (first one)
        primary_watchlist = user_watchlists[0] if user_watchlists else None
        watchlist_stocks = []
        
        if primary_watchlist:
            try:
                # Get all stocks in the primary watchlist
                watchlist_items = WatchlistStock.query.filter_by(watchlist_id=primary_watchlist.id).all()
                current_app.logger.info(f"Found {len(watchlist_items)} items in watchlist {primary_watchlist.id}")
                
                # Get current data for each stock
                DataService = get_data_service()
                
                for item in watchlist_items:
                    try:
                        # Get real-time stock data
                        stock_data = DataService.get_stock_info(item.symbol)
                        
                        if stock_data:
                            current_price = stock_data.get('last_price') or stock_data.get('regularMarketPrice', 0)
                            change = stock_data.get('regularMarketChange', 0)
                            change_percent = stock_data.get('regularMarketChangePercent', 0)
                            volume = stock_data.get('regularMarketVolume', 0)
                            company_name = stock_data.get('shortName') or stock_data.get('longName', item.symbol)
                        else:
                            # Fallback to default values
                            current_price = 0
                            change = 0
                            change_percent = 0
                            volume = 0
                            company_name = item.name or item.symbol
                        
                        watchlist_stocks.append({
                            'id': item.id,
                            'ticker': item.symbol,
                            'name': company_name,
                            'current_price': current_price,
                            'change': change,
                            'change_percent': change_percent,
                            'volume': volume,
                            'added_at': item.added_date.strftime('%d.%m.%Y') if item.added_date else None,
                            'error': False
                        })
                        
                    except Exception as stock_error:
                        current_app.logger.error(f"Error getting data for watchlist stock {item.symbol}: {stock_error}")
                        # Add stock with error state
                        watchlist_stocks.append({
                            'id': item.id,
                            'ticker': item.symbol,
                            'name': item.name or item.symbol,
                            'current_price': 0,
                            'change': 0,
                            'change_percent': 0,
                            'volume': 0,
                            'added_at': item.added_date.strftime('%d.%m.%Y') if item.added_date else None,
                            'error': True
                        })
                        
            except Exception as watchlist_error:
                current_app.logger.error(f"Error loading watchlist stocks: {watchlist_error}")
                watchlist_stocks = []
        
        # Add some sample Norwegian stocks if watchlist is empty (for demo purposes)
        if not watchlist_stocks and current_user.is_authenticated:
            sample_stocks = ['EQNR.OL', 'DNB.OL', 'TEL.OL', 'MOWI.OL', 'NHY.OL']
            DataService = get_data_service()
            
            for symbol in sample_stocks[:3]:  # Only add first 3 for demo
                try:
                    stock_data = DataService.get_stock_info(symbol)
                    if stock_data:
                        watchlist_stocks.append({
                            'id': f'demo_{symbol}',
                            'ticker': symbol,
                            'name': stock_data.get('shortName', symbol),
                            'current_price': stock_data.get('last_price', 0),
                            'change': stock_data.get('regularMarketChange', 0),
                            'change_percent': stock_data.get('regularMarketChangePercent', 0),
                            'volume': stock_data.get('regularMarketVolume', 0),
                            'added_at': None,
                            'error': False,
                            'is_demo': True
                        })
                except Exception as demo_error:
                    current_app.logger.error(f"Error loading demo stock {symbol}: {demo_error}")
        
        context = {
            'stocks': watchlist_stocks,
            'watchlists': user_watchlists,
            'primary_watchlist': primary_watchlist,
            'total_stocks': len(watchlist_stocks),
            'error': False
        }
        
        current_app.logger.info(f"Successfully loaded watchlist with {len(watchlist_stocks)} stocks")
        return render_template('portfolio/watchlist.html', **context)
        
    except Exception as e:
        current_app.logger.error(f"Critical error in watchlist route: {e}")
        import traceback
        current_app.logger.error(f"Traceback: {traceback.format_exc()}")
        
        # Return safe fallback
        return render_template('portfolio/watchlist.html', 
                             stocks=[], 
                             watchlists=[], 
                             primary_watchlist=None,
                             total_stocks=0,
                             error=True,
                             error_message="Kunne ikke laste watchlist. Prøv igjen senere.")

# Get user data for portfolio display
def get_user_data_for_portfolio():
    watchlist_items = []
    try:
        from ..models.favorites import Favorites
        favorites = Favorites.get_user_favorites(current_user.id)
        # Convert favorites to watchlist item format
        for fav in favorites:
            # Create a mock watchlist item object for favorites
            class MockWatchlistItem:
                def __init__(self, symbol, name=None):
                    self.symbol = symbol
                    self.ticker = symbol
                    self.name = name or symbol
                    
            watchlist_items.append(MockWatchlistItem(fav.symbol, fav.name))
    except Exception as e:
        current_app.logger.warning(f"Could not get favorites: {e}")
    
    # Get current prices for watchlist items
    watchlist_data = []
    for item in watchlist_items:
        try:
            symbol = getattr(item, 'symbol', getattr(item, 'ticker', 'UNKNOWN'))
            stock_data = get_data_service().get_stock_info(symbol)
            
            # KRITISK FIX: Sikre at alle verdier er numeriske
            current_price = float(stock_data.get('regularMarketPrice', 0)) if stock_data.get('regularMarketPrice') is not None else 0.0
            change = float(stock_data.get('regularMarketChange', 0)) if stock_data.get('regularMarketChange') is not None else 0.0
            change_percent = float(stock_data.get('regularMarketChangePercent', 0)) if stock_data.get('regularMarketChangePercent') is not None else 0.0;
            
            watchlist_data.append({
                'item': item,
                'ticker': symbol,
                'current_price': current_price,
                'change': change,
                'change_percent': change_percent,
                'name': stock_data.get('shortName', symbol) if stock_data else symbol
            })
        except Exception as e:
            current_app.logger.warning(f"Could not get data for watchlist item {symbol}: {e}")
            # KRITISK FIX: Alltid bruk numeriske fallback-verdier
            watchlist_data.append({
                'item': item,
                'ticker': symbol,
                'current_price': 0.0,
                'change': 0.0,
                'change_percent': 0.0,
                'name': symbol
            })
    
    # If no watchlist data, create sample data for demo
    if not watchlist_data:
        sample_stocks = [
            {'ticker': 'EQNR.OL', 'name': 'Equinor', 'last_price': 280.50, 'change_percent': 2.1},
            {'ticker': 'DNB.OL', 'name': 'DNB Bank', 'last_price': 220.30, 'change_percent': -0.8},
            {'ticker': 'AAPL', 'name': 'Apple Inc.', 'last_price': 175.40, 'change_percent': 1.2}
        ]
        return render_template('portfolio/watchlist.html', stocks=sample_stocks, watchlist=[])
    
    return render_template('portfolio/watchlist.html', watchlist=watchlist_data, stocks=watchlist_data)

# Removed duplicate index route - using portfolio_overview as main route
@portfolio.route('/tips', methods=['GET', 'POST'])
@unified_access_required
def stock_tips():
    """Stock tips page with enhanced error handling"""
    try:
        if request.method == 'POST':
            try:
                ticker = request.form.get('ticker', '').strip().upper()
                tip_type = request.form.get('tip_type', '').strip()
                confidence = request.form.get('confidence', '').strip()
                analysis = request.form.get('analysis', '').strip()

                # Validate inputs
                if not all([ticker, tip_type, confidence, analysis]):
                    flash('Alle felt må fylles ut.', 'warning')
                    return redirect(url_for('portfolio.stock_tips'))

                # Validate ticker format
                if not ticker or len(ticker) < 2:
                    flash('Ugyldig ticker-symbol.', 'warning')
                    return redirect(url_for('portfolio.stock_tips'))

                # Create new tip
                tip = StockTip(
                    ticker=ticker,
                    tip_type=tip_type,
                    confidence=confidence,
                    analysis=analysis,
                    user_id=current_user.id
                )
                
                db.session.add(tip)
                db.session.commit()
                flash('Aksjetips er lagt til!', 'success')
                return redirect(url_for('portfolio.stock_tips'))
                
            except Exception as post_error:
                current_app.logger.error(f"Error creating stock tip: {post_error}")
                db.session.rollback()
                flash('Feil ved lagring av tips. Prøv igjen.', 'error')
        
        # GET request - load tips
        try:
            tips = StockTip.query.order_by(StockTip.created_at.desc()).limit(10).all()
        except Exception as db_error:
            current_app.logger.error(f"Database error loading tips: {db_error}")
            tips = []
            flash('Kunne ikke laste aksjetips fra databasen.', 'warning')
        
        return render_template('portfolio/tips.html', tips=tips)
        
    except Exception as e:
        current_app.logger.error(f"Critical error in stock_tips route: {e}")
        flash('Siden kunne ikke lastes. Prøv igjen senere.', 'error')
        return render_template('portfolio/tips.html', tips=[], error="Feil ved lasting av siden")


@portfolio.route('/tips/feedback/<int:tip_id>', methods=['POST'])
@unified_access_required
def stock_tips_feedback(tip_id):
    """Handle feedback on stock tips"""
    try:
        # Get the tip
        tip = StockTip.query.get_or_404(tip_id)
        
        # Get feedback data
        rating = request.form.get('rating')
        comment = request.form.get('comment', '').strip()
        
        if rating:
            # Here you could save the feedback to a separate table if needed
            # For now, just flash a success message
            flash('Takk for tilbakemeldingen!', 'success')
        else:
            flash('Vennligst gi en vurdering.', 'warning')
            
    except Exception as e:
        logger.error(f"Error processing tip feedback: {e}")
        flash('Kunne ikke lagre tilbakemelding.', 'error')
    
    return redirect(url_for('portfolio.stock_tips'))


@portfolio.route('/create', methods=['GET', 'POST'])
@login_required
@unified_access_required
def create_portfolio():
    """Create a new portfolio with robust error handling"""
    try:
        if request.method == 'POST':
            # Validate CSRF token more robustly
            csrf_token = request.form.get('csrf_token')
            if csrf_token:  # Only validate if token was provided
                try:
                    validate_csrf(csrf_token)
                except ValidationError as csrf_error:
                    logger.warning(f"CSRF validation failed: {csrf_error}")
                    flash('Sikkerhetsfeil: Vennligst prøv igjen.', 'danger')
                    return render_template('portfolio/create.html')
            else:
                logger.info("No CSRF token provided, but allowing request to proceed")
            
            name = request.form.get('name', '').strip()
            description = request.form.get('description', '').strip()
            initial_value = request.form.get('initial_value', '0')
            currency = request.form.get('currency', 'NOK')
            
            if not name:
                flash('Du må gi porteføljen et navn.', 'danger')
                return render_template('portfolio/create.html')
            
            # Opprett og lagre portefølje
            try:
                # Ensure we have the Portfolio model
                if Portfolio is None:
                    flash('Portfolio-funksjonen er ikke tilgjengelig for øyeblikket.', 'warning')
                    return render_template('portfolio/create.html', error="Portfolio-tjeneste ikke tilgjengelig")
                    
                new_portfolio = Portfolio(
                    name=name, 
                    description=description, 
                    user_id=current_user.id
                )
                db.session.add(new_portfolio)
                db.session.commit()
                
                # Track achievement for creating portfolio (moved after success flash)
                try:
                    from ..models.achievements import UserStats, check_user_achievements
                    user_stats = UserStats.query.filter_by(user_id=current_user.id).first()
                    if not user_stats:
                        user_stats = UserStats(user_id=current_user.id)
                        db.session.add(user_stats)
                    user_stats.portfolios_created += 1
                    db.session.commit()
                    
                    # Check for new achievements
                    check_user_achievements(current_user.id, 'portfolios', user_stats.portfolios_created)
                except Exception as achievement_error:
                    logger.warning(f"Achievement tracking failed but portfolio created: {achievement_error}")
                    # Don't fail portfolio creation if achievement tracking fails
                
                flash(f'Porteføljen "{name}" ble opprettet!', 'success')
                return redirect(url_for('portfolio.view_portfolio', id=new_portfolio.id))
                
            except Exception as db_error:
                logger.error(f"Database error creating portfolio: {db_error}")
                db.session.rollback()
                flash('Kunne ikke opprette portefølje i databasen. Prøv igjen.', 'danger')
                return render_template('portfolio/create.html')
                
        # GET request - show form
        return render_template('portfolio/create.html')
        
    except Exception as e:
        logger.error(f"Critical error in create_portfolio: {e}")
        flash('En teknisk feil oppstod ved opprettelse av portefølje. Prøv igjen senere.', 'error')
        return render_template('portfolio/create.html')

@portfolio.route('/api/portfolio/<int:id>', methods=['GET'])
@unified_access_required
def get_portfolio_data(id):
    """API endpoint to get portfolio data as JSON for AJAX loading"""
    try:
        portfolio_obj = Portfolio.query.filter_by(id=id, user_id=current_user.id).first()
        if not portfolio_obj:
            return jsonify({'success': False, 'error': 'Portefølje ikke funnet'}), 404
        
        # Get active (non soft-deleted) portfolio stocks
        portfolio_stocks = PortfolioStock.query.filter_by(portfolio_id=id, deleted_at=None).all()
        
        # Calculate portfolio metrics
        total_value = 0
        total_cost = 0
        holdings = []

        # Lazy import DataService to avoid circular imports
        DataService = get_data_service()

        for stock in portfolio_stocks:
            try:
                # Get current stock data
                current_data = DataService.get_stock_data(stock.ticker)
                if current_data:
                    current_price = current_data.get('last_price', stock.purchase_price)
                    current_value = current_price * stock.shares
                    cost_value = stock.purchase_price * stock.shares
                    gain_loss = current_value - cost_value
                    gain_loss_percent = (gain_loss / cost_value * 100) if cost_value > 0 else 0

                    holdings.append({
                        'id': stock.id,
                        'symbol': stock.ticker,
                        'company_name': current_data.get('name', stock.ticker),
                        'quantity': stock.shares,
                        'average_price': stock.purchase_price,
                        'current_price': current_price,
                        'market_value': current_value,
                        'unrealized_gain': gain_loss,
                        'unrealized_gain_percent': gain_loss_percent
                    })

                    total_value += current_value
                    total_cost += cost_value
            except Exception as e:
                current_app.logger.error(f"Error getting data for {stock.ticker}: {e}")
                # Use stored values as fallback
                cost_value = stock.purchase_price * stock.shares
                holdings.append({
                    'id': stock.id,
                    'symbol': stock.ticker,
                    'company_name': stock.ticker,
                    'quantity': stock.shares,
                    'average_price': stock.purchase_price,
                    'current_price': stock.purchase_price,
                    'market_value': cost_value,
                    'unrealized_gain': 0,
                    'unrealized_gain_percent': 0
                })
                total_value += cost_value
                total_cost += cost_value

        # Calculate total metrics
        total_gain_loss = total_value - total_cost
        total_gain_loss_percent = (total_gain_loss / total_cost * 100) if total_cost > 0 else 0

        return jsonify({
            'success': True,
            'portfolio': {
                'id': portfolio_obj.id,
                'name': portfolio_obj.name,
                'description': portfolio_obj.description or 'Ingen beskrivelse',
                'currency': getattr(portfolio_obj, 'currency', 'NOK')
            },
            'holdings': holdings,
            'summary': {
                'total_value': total_value,
                'total_cost': total_cost,
                'total_gain_loss': total_gain_loss,
                'total_gain_loss_percent': total_gain_loss_percent
            }
        })
                             
    except Exception as e:
        current_app.logger.error(f"Error getting portfolio data {id}: {e}")
        return jsonify({'success': False, 'error': 'Feil ved lasting av portefølje'}), 500

@portfolio.route('/view/<int:id>')
@login_required
def view_portfolio(id):
    """View a specific portfolio - primary function"""
    try:
        portfolio_obj = Portfolio.query.filter_by(id=id, user_id=current_user.id).first()
        if not portfolio_obj:
            flash('Portefølje ikke funnet', 'error')
            return redirect(url_for('portfolio.portfolio_overview'))
        
        # Get active (non soft-deleted) portfolio stocks
        portfolio_stocks = PortfolioStock.query.filter_by(portfolio_id=id, deleted_at=None).all()
        
        # Calculate portfolio metrics
        total_value = 0
        total_cost = 0
        portfolio_data = []
        holdings = []  # list of dicts for template

        # Lazy import DataService to avoid circular imports
        DataService = get_data_service()

        for stock in portfolio_stocks:
            try:
                # Get current stock data
                current_data = DataService.get_stock_data(stock.ticker)
                if current_data:
                    current_price = current_data.get('last_price', stock.purchase_price)
                    current_value = current_price * stock.shares
                    cost_value = stock.purchase_price * stock.shares
                    gain_loss = current_value - cost_value
                    gain_loss_percent = (gain_loss / cost_value * 100) if cost_value > 0 else 0

                    portfolio_data.append({
                        'stock': stock,
                        'current_price': current_price,
                        'current_value': current_value,
                        'cost_value': cost_value,
                        'gain_loss': gain_loss,
                        'gain_loss_percent': gain_loss_percent
                    })
                    holdings.append({
                        'id': stock.id,
                        'symbol': stock.ticker,
                        'company_name': current_data.get('name', stock.ticker),
                        'quantity': stock.shares,
                        'average_price': stock.purchase_price,
                        'current_price': current_price,
                        'market_value': current_value,
                        'unrealized_gain': gain_loss,
                        'unrealized_gain_percent': gain_loss_percent
                    })

                    total_value += current_value
                    total_cost += cost_value
            except Exception as e:
                current_app.logger.error(f"Error getting data for {stock.ticker}: {e}")
                # Use stored values as fallback
                cost_value = stock.purchase_price * stock.shares
                portfolio_data.append({
                    'stock': stock,
                    'current_price': stock.purchase_price,
                    'current_value': cost_value,
                    'cost_value': cost_value,
                    'gain_loss': 0,
                    'gain_loss_percent': 0
                })
                total_value += cost_value
                total_cost += cost_value
                holdings.append({
                    'id': stock.id,
                    'symbol': stock.ticker,
                    'company_name': stock.ticker,
                    'quantity': stock.shares,
                    'average_price': stock.purchase_price,
                    'current_price': stock.purchase_price,
                    'market_value': cost_value,
                    'unrealized_gain': 0,
                    'unrealized_gain_percent': 0
                })

        # Calculate total metrics
        total_gain_loss = total_value - total_cost
        total_gain_loss_percent = (total_gain_loss / total_cost * 100) if total_cost > 0 else 0

        # Prepare template context
        template_context = dict(
            portfolio=portfolio_obj,
            portfolio_data=portfolio_data,
            holdings=holdings,
            total_value=total_value,
            total_cost=total_cost,
            total_gain_loss=total_gain_loss,
            total_gain_loss_percent=total_gain_loss_percent
        )
        # ETag/Last-Modified caching logic
        try:
            import hashlib
            last_update = portfolio_obj.updated_at.isoformat() if portfolio_obj.updated_at else ''
            active_stock_count = len(portfolio_stocks)
            etag_base = f"view:{portfolio_obj.id}:{last_update}:{active_stock_count}:{total_value:.2f}:{total_cost:.2f}"
            etag = hashlib.sha1(etag_base.encode()).hexdigest()
            if request.headers.get('If-None-Match') == etag:
                return Response(status=304)
            response = Response(render_template('portfolio/view.html', **template_context))
            response.headers['ETag'] = etag
            if portfolio_obj.updated_at:
                response.headers['Last-Modified'] = portfolio_obj.updated_at.strftime('%a, %d %b %Y %H:%M:%S GMT')
            return response
        except Exception as cache_err:
            current_app.logger.debug(f"ETag generation failed view_portfolio: {cache_err}")
            return render_template('portfolio/view.html', **template_context)
                             
    except Exception as e:
        current_app.logger.error(f"Error viewing portfolio {id}: {e}")
        flash('Feil ved lasting av portefølje', 'error')
        return redirect(url_for('portfolio.portfolio_overview'))

@portfolio.route('/<int:id>/add', methods=['GET', 'POST'])
@login_required
def add_stock_to_portfolio(id):
    """Add a stock to a specific portfolio with enhanced error handling"""
    try:
        # Import required models at function level to avoid circular imports
        from ..models.portfolio import Portfolio, PortfolioStock
        
        # Get portfolio with improved error handling
        try:
            portfolio_obj = Portfolio.query.filter_by(id=id, user_id=current_user.id).first()
            if not portfolio_obj:
                flash('Portefølje ikke funnet eller du har ikke tilgang.', 'danger')
                return redirect(url_for('portfolio.portfolio_overview'))
                
        except Exception as e:
            logger.error(f"Error getting portfolio {id}: {e}")
            flash('Det oppstod en teknisk feil ved lasting av portefølje.', 'danger')
            return redirect(url_for('portfolio.portfolio_overview'))
        
        if request.method == 'POST':
            try:
                # Get form data with validation
                ticker = request.form.get('ticker', '').strip().upper()
                quantity_str = request.form.get('quantity', '0').strip()
                price_str = request.form.get('price', '0').strip()

                # Validate required fields
                if not ticker or not quantity_str or not price_str:
                    flash('Alle felt er påkrevd', 'danger')
                    return render_template('portfolio/add_stock_to_portfolio.html', 
                                         portfolio=portfolio_obj,
                                         page_title="Legg til aksje")

                try: 
                    quantity = float(quantity_str.replace(',', '.'))
                    price = float(price_str.replace(',', '.'))
                    if quantity <= 0 or price <= 0:
                        raise ValueError("Must be positive numbers")
                except ValueError:
                    flash('Antall og pris må være positive tall', 'danger')
                    return render_template('portfolio/add_stock_to_portfolio.html', 
                                         portfolio=portfolio_obj,
                                         page_title="Legg til aksje")

                # Check if stock exists in portfolio
                existing_stock = PortfolioStock.query.filter_by(portfolio_id=id, ticker=ticker).first()

                if existing_stock:
                    # Update existing stock with weighted average price
                    total_value = (existing_stock.shares * existing_stock.purchase_price) + (quantity * price)
                    total_quantity = existing_stock.shares + quantity
                    existing_stock.purchase_price = total_value / total_quantity if total_quantity > 0 else price
                    existing_stock.shares = total_quantity
                    logger.info(f"Updated existing stock {ticker} in portfolio {id}")
                else:
                    # Add new stock
                    stock = PortfolioStock(
                        portfolio_id=id,
                        ticker=ticker,
                        shares=quantity,
                        purchase_price=price
                    )
                    db.session.add(stock)
                    logger.info(f"Added new stock {ticker} to portfolio {id}")
            
                db.session.commit()
                # Audit log after successful add/update
                try:
                    from ..models.portfolio_audit import PortfolioAuditLog
                    action = 'update_stock' if existing_stock else 'add_stock'
                    after_state = {
                        'shares': float(existing_stock.shares if existing_stock else stock.shares),
                        'purchase_price': float(existing_stock.purchase_price if existing_stock else stock.purchase_price)
                    }
                    audit = PortfolioAuditLog(
                        user_id=current_user.id,
                        portfolio_id=id,
                        stock_id=(existing_stock.id if existing_stock else stock.id),
                        ticker=ticker,
                        action=action,
                        before_state=None if not existing_stock else {
                            'shares': float(total_quantity - quantity),
                            'purchase_price': float((total_value - (quantity * price)) / (total_quantity - quantity) if (total_quantity - quantity) > 0 else price)
                        },
                        after_state=after_state,
                        ip_address=request.remote_addr,
                        user_agent=request.headers.get('User-Agent', '')[:256]
                    )
                    db.session.add(audit)
                    db.session.commit()
                except Exception as audit_err:
                    current_app.logger.warning(f"Failed to persist audit log for add/update stock {ticker}: {audit_err}")
                flash(f'✅ {ticker} lagt til i porteføljen!', 'success')
                return redirect(url_for('portfolio.view_portfolio', id=id))
                
            except Exception as db_error:
                logger.error(f"Database error adding stock: {db_error}")
                db.session.rollback()
                flash('❌ Kunne ikke lagre aksjen. Prøv igjen.', 'danger')
                return render_template('portfolio/add_stock_to_portfolio.html', 
                                     portfolio=portfolio_obj,
                                     page_title="Legg til aksje")

        # GET request - show add form
        return render_template('portfolio/add_stock_to_portfolio.html', 
                             portfolio=portfolio_obj,
                             page_title="Legg til aksje")
                             
    except Exception as e:
        logger.error(f"Critical error in add_stock_to_portfolio: {e}")
        flash('❌ En kritisk feil oppstod. Kontakt support hvis problemet vedvarer.', 'danger')
        return redirect(url_for('portfolio.portfolio_overview'))
        logger.error(f"Traceback: {traceback.format_exc()}")
        
        # Test database connectivity
        try:
            db.session.execute('SELECT 1')
            error_msg = 'En teknisk feil oppstod ved tillegging av aksje. Prøv igjen senere.'
        except Exception as db_error:
            logger.error(f"Database connectivity issue: {db_error}")
            error_msg = 'Det oppstod en feil ved lasting av porteføljer. Database ikke tilgjengelig.'
        
        if request.is_json:
            return jsonify({'success': False, 'error': error_msg}), 500
        flash(error_msg, 'error')
        return redirect(url_for('portfolio.portfolio_overview'))

@portfolio.route('/<int:id>/edit/<int:stock_id>', methods=['POST'])
@unified_access_required
def edit_stock_in_portfolio(id, stock_id):
    """Edit a stock holding in a specific portfolio"""
    try:
        # CSRF validation
        csrf_token_form = request.form.get('csrf_token') if request.form else None
        csrf_token_header = request.headers.get('X-CSRFToken') or request.headers.get('X-CSRF-Token')
        if not csrf_token_form and not csrf_token_header:
            return jsonify({'success': False, 'error': 'CSRF token mangler'}), 403

        # Get portfolio and verify ownership
        portfolio_obj = Portfolio.query.get_or_404(id)
        if portfolio_obj.user_id != current_user.id:
            return jsonify({'success': False, 'error': 'Du har ikke tilgang til denne porteføljen'}), 403

        # Get the stock holding
        stock = PortfolioStock.query.get_or_404(stock_id)
        if stock.portfolio_id != id or stock.deleted_at is not None:
            return jsonify({'success': False, 'error': 'Beholdning ikke funnet eller slettet'}), 404

        # Get form data
        quantity_str = request.form.get('quantity', '0').strip()
        price_str = request.form.get('price', '0').strip()

        # Validate inputs
        try:
            quantity = float(quantity_str.replace(',', '.'))
            price = float(price_str.replace(',', '.'))
            if quantity <= 0 or price <= 0:
                raise ValueError("Must be positive numbers")
        except ValueError:
            return jsonify({'success': False, 'error': 'Antall og pris må være positive tall'}), 400

        # Store original values for audit
        before_state = {
            'shares': float(stock.shares),
            'purchase_price': float(stock.purchase_price or 0)
        }

        # Update the stock holding
        stock.shares = quantity
        stock.purchase_price = price
        stock.updated_at = datetime.utcnow()

        try:
            db.session.commit()
            
            # Create audit log (best effort)
            try:
                from ..models.portfolio_audit import PortfolioAuditLog
                audit = PortfolioAuditLog(
                    user_id=current_user.id,
                    portfolio_id=id,
                    stock_id=stock.id,
                    ticker=stock.ticker,
                    action='edit_stock',
                    before_state=before_state,
                    after_state={'shares': quantity, 'purchase_price': price},
                    ip_address=request.remote_addr,
                    user_agent=request.headers.get('User-Agent', '')[:256]
                )
                db.session.add(audit)
                db.session.commit()
            except Exception as audit_err:
                current_app.logger.warning(f"Failed to create audit log for edit holding {stock_id}: {audit_err}")

            return jsonify({
                'success': True, 
                'message': f'{stock.ticker} oppdatert i porteføljen',
                'holding': {
                    'id': stock.id,
                    'ticker': stock.ticker,
                    'quantity': quantity,
                    'average_price': price
                }
            })

        except Exception as commit_err:
            current_app.logger.error(f"Database error updating holding {stock_id}: {commit_err}")
            db.session.rollback()
            return jsonify({'success': False, 'error': 'Kunne ikke lagre endringer i databasen'}), 500

    except Exception as e:
        current_app.logger.error(f"Error editing holding {stock_id} in portfolio {id}: {e}")
        db.session.rollback()
        return jsonify({'success': False, 'error': 'Teknisk feil ved redigering av beholdning'}), 500

@portfolio.route('/<int:id>/remove/<int:stock_id>', methods=['POST'])
@unified_access_required
def remove_stock_from_portfolio(id, stock_id):
    """Soft-delete a stock from a specific portfolio by setting deleted_at."""
    try:
        # CSRF validation: accept either form field or header token (to support JS fetch)
        csrf_token_form = request.form.get('csrf_token') if request.form else None
        csrf_token_header = request.headers.get('X-CSRFToken') or request.headers.get('X-CSRF-Token')
        if not csrf_token_form and not csrf_token_header:
            if 'application/json' in request.headers.get('Accept', ''):
                return jsonify({'success': False, 'error': 'CSRF token mangler'}), 403
            flash('CSRF token mangler.', 'danger')
            return redirect(url_for('portfolio.portfolio_overview'))
        portfolio = Portfolio.query.get_or_404(id)

        # Ownership check
        if portfolio.user_id != current_user.id:
            error_msg = 'Du har ikke tilgang til denne porteføljen'
            if request.headers.get('Accept') == 'application/json':
                return jsonify({'success': False, 'error': error_msg}), 403
            flash(error_msg, 'danger')
            return redirect(url_for('portfolio.portfolio_overview'))

        stock = PortfolioStock.query.get_or_404(stock_id)

        if stock.portfolio_id != id:
            error_msg = 'Aksjen tilhører ikke denne porteføljen'
            if request.headers.get('Accept') == 'application/json':
                return jsonify({'success': False, 'error': error_msg}), 400
            flash(error_msg, 'danger')
            return redirect(url_for('portfolio.view_portfolio', id=id))

        # If already soft-deleted, treat as idempotent success
        if stock.deleted_at is not None:
            success_msg = 'Aksje allerede fjernet.'
            if request.headers.get('Accept') == 'application/json':
                return jsonify({'success': True, 'message': success_msg})
            flash(success_msg, 'info')
            return redirect(url_for('portfolio.view_portfolio', id=id))

        from datetime import datetime as _dt
        stock.deleted_at = _dt.utcnow()
        before_state = {
            'shares': float(stock.shares),
            'purchase_price': float(stock.purchase_price or 0)
        }
        try:
            db.session.commit()
            # Persist audit
            try:
                from ..models.portfolio_audit import PortfolioAuditLog
                audit = PortfolioAuditLog(
                    user_id=current_user.id,
                    portfolio_id=id,
                    stock_id=stock.id,
                    ticker=stock.ticker,
                    action='delete_stock',
                    before_state=before_state,
                    after_state={'deleted_at': stock.deleted_at.isoformat()},
                    ip_address=request.remote_addr,
                    user_agent=request.headers.get('User-Agent', '')[:256]
                )
                db.session.add(audit)
                db.session.commit()
            except Exception as audit_err:
                current_app.logger.warning(f"Failed to persist audit log for delete_stock {stock_id}: {audit_err}")
        except Exception as commit_err:
            current_app.logger.error(f"Commit error during soft-delete stock {stock_id}: {commit_err}")
            db.session.rollback()
            raise

        success_msg = 'Aksje fjernet fra porteføljen'
        if 'application/json' in request.headers.get('Accept', ''):
            return jsonify({'success': True, 'message': success_msg, 'stock_id': stock_id, 'portfolio_id': id})
        flash(success_msg, 'success')
        return redirect(url_for('portfolio.view_portfolio', id=id))

    except Exception as e:
        current_app.logger.error(f"Error soft-deleting stock {stock_id} from portfolio {id}: {e}")
        db.session.rollback()
        error_msg = 'Kunne ikke fjerne aksjen. Prøv igjen senere.'
        if 'application/json' in request.headers.get('Accept', ''):
            # Use 500 to better signal failure to client JS
            return jsonify({'success': False, 'error': error_msg, 'stock_id': stock_id, 'portfolio_id': id}), 500
        flash(error_msg, 'danger')
        return redirect(url_for('portfolio.view_portfolio', id=id))

@portfolio.route('/watchlist/create', methods=['GET', 'POST'])
@unified_access_required
def create_watchlist():
    """Create a new watchlist"""
    if request.method == 'POST':
        name = request.form.get('name')
        user_id = current_user.id
        watchlist = Watchlist(name=name, user_id=user_id)
        db.session.add(watchlist)
        db.session.commit()
        flash('Favorittliste opprettet!', 'success')
        return redirect(url_for('portfolio.watchlist'))
    return render_template('portfolio/create_watchlist.html')

@portfolio.route('/watchlist/<int:id>/add', methods=['GET', 'POST'])
@access_required
def add_to_watchlist(id):
    """Add a stock to a watchlist"""
    try:
        # For POST requests, handle both JSON and form data
        if request.method == 'POST':
            # Get ticker/symbol from JSON or form data
            if request.is_json:
                data = request.get_json()
                ticker = data.get('symbol') or data.get('ticker')
            else:
                ticker = request.form.get('ticker') or request.form.get('symbol')

            if not ticker:
                if request.is_json:
                    return jsonify({'success': False, 'message': 'Ticker/symbol er påkrevd'}), 400
                flash('Ticker er påkrevd', 'danger')
                return redirect(url_for('portfolio.add_to_watchlist', id=id))

            # Clean ticker symbol
            ticker = ticker.strip().upper()

            # Get or create watchlist
            watchlist_obj = None
            if current_user.is_authenticated:
                try:
                    watchlist_obj = Watchlist.query.filter_by(id=id, user_id=current_user.id).first()
                except Exception as e:
                    current_app.logger.error(f"Error finding watchlist {id}: {e}")

            # If no specific watchlist found, try to find any user watchlist
            if not watchlist_obj and current_user.is_authenticated:
                try:
                    watchlist_obj = Watchlist.query.filter_by(user_id=current_user.id).first()
                    if watchlist_obj:
                        current_app.logger.info(f"Using alternative watchlist {watchlist_obj.id} for user {current_user.id}")
                except Exception as e:
                    current_app.logger.error(f"Error finding alternative watchlist: {e}")

            if not watchlist_obj:
                # Create a new watchlist for the user
                try:
                    watchlist_obj = Watchlist(
                        name=f"Min Watchlist",
                        description="Automatisk opprettet watchlist",
                        user_id=current_user.id
                    )
                    db.session.add(watchlist_obj)
                    db.session.commit()
                    current_app.logger.info(f"Created new watchlist {watchlist_obj.id} for user {current_user.id}")
                except Exception as create_error:
                    current_app.logger.error(f"Error creating watchlist: {create_error}")
                    if request.is_json:
                        return jsonify({'success': False, 'message': 'Kunne ikke opprette watchlist'}), 500
                    flash('Kunne ikke opprette watchlist', 'danger')
                    return redirect(url_for('portfolio.watchlist'))

            # Check if stock already exists in watchlist
            try:
                existing = WatchlistStock.query.filter_by(
                    watchlist_id=watchlist_obj.id, 
                    symbol=ticker
                ).first()

                if existing:
                    message = f'Aksjen {ticker} er allerede i watchlist'
                    if request.is_json:
                        return jsonify({'success': True, 'message': message})
                    flash(message, 'warning')
                else:
                    # Add stock to watchlist
                    stock = WatchlistStock(
                        watchlist_id=watchlist_obj.id, 
                        symbol=ticker,
                        name=ticker,  # Will be updated when stock info is fetched
                        added_date=datetime.now()
                    )
                    db.session.add(stock)
                    db.session.commit()
                    
                    message = f'Aksje {ticker} lagt til i watchlist!'
                    current_app.logger.info(f"Added {ticker} to watchlist {watchlist_obj.id}")
                    
                    if request.is_json:
                        return jsonify({'success': True, 'message': message})
                    flash(message, 'success')

            except Exception as stock_error:
                current_app.logger.error(f"Error handling stock {ticker}: {stock_error}")
                if request.is_json:
                    return jsonify({'success': False, 'message': 'Teknisk feil ved tillegging av aksje'}), 500
                flash('Teknisk feil ved tillegging av aksje', 'danger')

            # Redirect based on request type
            if request.is_json:
                return jsonify({'success': True, 'message': f'{ticker} behandlet'})
            
            # Redirect to internal portfolio watchlist page (original target blueprint not present)
            return redirect(url_for('portfolio.watchlist'))

        # GET request - show add form
        watchlist_obj = None
        if current_user.is_authenticated:
            try:
                watchlist_obj = Watchlist.query.filter_by(id=id, user_id=current_user.id).first()
            except Exception as e:
                current_app.logger.error(f"Error getting watchlist for form: {e}")

        if not watchlist_obj:
            flash('Watchlist ikke funnet', 'danger')
            return redirect(url_for('portfolio.watchlist'))

        return render_template('portfolio/add_to_watchlist.html', watchlist=watchlist_obj)

    except Exception as e:
        current_app.logger.error(f"Error in add_to_watchlist: {e}")
        import traceback
        current_app.logger.error(traceback.format_exc())
        
        if request.is_json:
            return jsonify({'success': False, 'message': 'Teknisk feil'}), 500
        flash('Teknisk feil oppstod', 'danger')
        return redirect(url_for('portfolio.watchlist'))

@portfolio.route('/watchlist/remove', methods=['POST'])
@unified_access_required  
def remove_from_watchlist():
    """Remove a stock from user's watchlist"""
    try:
        # Handle both JSON and form data
        if request.is_json:
            data = request.get_json()
            ticker = data.get('ticker')
        else:
            ticker = request.form.get('ticker')
            
        if not ticker:
            return jsonify({'success': False, 'error': 'Ticker er påkrevd'}), 400
            
        ticker = ticker.strip().upper()
        
        # Find the user's watchlist and the stock
        user_watchlist = Watchlist.query.filter_by(user_id=current_user.id).first()
        if not user_watchlist:
            return jsonify({'success': False, 'error': 'Ingen watchlist funnet'}), 404
            
        # Find and remove the stock
        stock_to_remove = WatchlistStock.query.filter_by(
            watchlist_id=user_watchlist.id,
            symbol=ticker
        ).first()
        
        if stock_to_remove:
            db.session.delete(stock_to_remove)
            db.session.commit()
            return jsonify({'success': True, 'message': f'{ticker} fjernet fra watchlist'})
        else:
            return jsonify({'success': False, 'error': f'{ticker} ikke funnet i watchlist'}), 404
            
    except Exception as e:
        current_app.logger.error(f"Error removing {ticker} from watchlist: {e}")
        db.session.rollback()
        return jsonify({'success': False, 'error': 'Teknisk feil ved fjerning'}), 500

@portfolio.route('/add_to_watchlist', methods=['POST'])
@access_required
def add_to_watchlist_quick():
    """Lightweight JSON endpoint to add a symbol to the user's default watchlist.
    This matches the frontend fetch('/add_to_watchlist') call on stock details pages.
    Always returns JSON (never redirects) so UI can toast the result.
    """
    try:
        if not request.is_json:
            return jsonify({'success': False, 'message': 'JSON body required'}), 400

        data = request.get_json() or {}
        ticker = (data.get('symbol') or data.get('ticker') or '').strip().upper()
        if not ticker:
            return jsonify({'success': False, 'message': 'Ticker mangler'}), 400

        # Find existing default/simple watchlist or create one
        watchlist_obj = None
        try:
            watchlist_obj = Watchlist.query.filter_by(user_id=current_user.id).first()
        except Exception as e:
            current_app.logger.error(f"Quick add watchlist query error: {e}")

        if not watchlist_obj:
            try:
                watchlist_obj = Watchlist(
                    name='Min Watchlist',
                    description='Automatisk opprettet watchlist',
                    user_id=current_user.id
                )
                db.session.add(watchlist_obj)
                db.session.commit()
            except Exception as e:
                current_app.logger.error(f"Could not create watchlist: {e}")
                db.session.rollback()
                return jsonify({'success': False, 'message': 'Kunne ikke opprette watchlist'}), 500

        # Check if already present
        try:
            existing = WatchlistStock.query.filter_by(
                watchlist_id=watchlist_obj.id,
                symbol=ticker
            ).first()
        except Exception as e:
            current_app.logger.error(f"Watchlist existing query error: {e}")
            existing = None

        if existing:
            return jsonify({'success': True, 'message': f'{ticker} er allerede i favoritter'}), 200

        # Insert new
        try:
            stock = WatchlistStock(
                watchlist_id=watchlist_obj.id,
                symbol=ticker,
                name=ticker,
                added_date=datetime.now()
            )
            db.session.add(stock)
            db.session.commit()
            return jsonify({'success': True, 'message': f'{ticker} lagt til i favoritter'}), 201
        except Exception as e:
            current_app.logger.error(f"Failed adding {ticker} to watchlist: {e}")
            db.session.rollback()
            return jsonify({'success': False, 'message': 'Teknisk feil – kunne ikke lagre'}), 500
    except Exception as e:
        current_app.logger.error(f"Unhandled quick watchlist add error: {e}")
        return jsonify({'success': False, 'message': 'Uventet feil'}), 500

@portfolio.route('/tips/add', methods=['GET', 'POST'])
@access_required
def add_tip():
    """Add a stock tip"""
    if request.method == 'POST':
        ticker = request.form.get('ticker')
        tip_type = request.form.get('tip_type')
        confidence = request.form.get('confidence')
        analysis = request.form.get('analysis')
        tip = StockTip(
            ticker=ticker,
            tip_type=tip_type,
            confidence=confidence,
            analysis=analysis,
            user_id=current_user.id
        )
        db.session.add(tip)
        db.session.commit()
        flash('Aksjetips lagt til', 'success')
        return redirect(url_for('portfolio.stock_tips'))
    ticker = request.args.get('ticker', '')
    return render_template('portfolio/add_tip.html', ticker=ticker)

@portfolio.route('/tips/feedback/<int:tip_id>', methods=['POST'])
@access_required
def tip_feedback(tip_id):
    """Submit feedback for a stock tip"""
    tip = StockTip.query.get_or_404(tip_id)
    feedback = request.form.get('feedback')
    tip.feedback = feedback
    db.session.commit()
    flash('Tilbakemelding lagret!', 'success')
    return redirect(url_for('portfolio.stock_tips'))

@portfolio.route('/add/<ticker>')
@access_required
def quick_add_stock(ticker):
    """Quickly add a stock to the user's portfolio"""
    # Check if user is authenticated
    if not current_user.is_authenticated:
        flash("Du må logge inn for å legge til aksjer i porteføljen.", "warning")
        return redirect(url_for('main.login'))
    
    stock_info = get_data_service().get_stock_info(ticker)
    if not stock_info:
        flash(f"Aksje {ticker} ble ikke funnet.", "danger")
        return redirect(url_for('main.index'))

    # Finn eller opprett brukerens første portefølje
    portfolio = Portfolio.query.filter_by(user_id=current_user.id).first()
    if not portfolio:
        portfolio = Portfolio(name="Min portefølje", user_id=current_user.id)
        db.session.add(portfolio)
        db.session.commit()

    # Sjekk om aksjen allerede finnes i porteføljen
    existing_stock = PortfolioStock.query.filter_by(portfolio_id=portfolio.id, ticker=ticker).first()
    if existing_stock:
        # Øk antall aksjer med 1
        existing_stock.shares += 1
    else:
        # Legg til ny aksje med 1 aksje og dagens pris som snittpris
        avg_price = stock_info.get('last_price') or stock_info.get('regularMarketPrice') or 100.0
        stock = PortfolioStock(
            portfolio_id=portfolio.id,
            ticker=ticker,
            shares=1,
            purchase_price=avg_price
        )
        db.session.add(stock)

    db.session.commit()
    flash(f"Aksje {ticker} lagt til i din portefølje!", "success")
    return redirect(url_for('portfolio.portfolio_overview'))

@portfolio.route('/add', methods=['GET', 'POST'])
@access_required
def add_stock():
    """Add a stock to the user's default portfolio, supporting JSON requests for AJAX"""
    if request.method == 'POST':
        # Handle both JSON (AJAX) and form data
        if request.is_json:
            data = request.get_json()
            ticker = data.get('ticker')
            quantity = float(data.get('quantity', 1))
            purchase_price = float(data.get('purchase_price', 0))
        else:
            ticker = request.form.get('ticker')
            quantity = float(request.form.get('quantity', 0))
            purchase_price = float(request.form.get('purchase_price', 0))
        
        MAX_SHARES = 10_000_000  # arbitrary upper safety cap
        MAX_PRICE = 1_000_000    # cap per share
        if not ticker or quantity <= 0 or purchase_price <= 0:
            error_msg = 'Alle felt må fylles ut korrekt.'
            if request.is_json:
                return jsonify({'success': False, 'error': error_msg}), 400
            flash(error_msg, 'danger')
            return redirect(url_for('portfolio.add_stock'))

        # Additional validation for unrealistic values
        if quantity > MAX_SHARES or purchase_price > MAX_PRICE:
            error_msg = 'Urealistisk verdi for antall eller pris.'
            if request.is_json:
                return jsonify({'success': False, 'error': error_msg}), 400
            flash(error_msg, 'danger')
            return redirect(url_for('portfolio.add_stock'))
        
        try:
            # Hent brukerens portefølje
            user_portfolio = Portfolio.query.filter_by(user_id=current_user.id).first()
            if not user_portfolio:
                user_portfolio = Portfolio(name="Min portefølje", user_id=current_user.id)
                db.session.add(user_portfolio)
                db.session.commit()
            
            # Sjekk om aksjen allerede finnes i porteføljen
            existing_stock = PortfolioStock.query.filter_by(portfolio_id=user_portfolio.id, ticker=ticker).first()
            if existing_stock:
                # Beregn ny gjennomsnittspris
                total_value = (existing_stock.shares * existing_stock.purchase_price) + (quantity * purchase_price)
                total_quantity = existing_stock.shares + quantity
                existing_stock.purchase_price = total_value / total_quantity
                existing_stock.shares = total_quantity
            else:
                # Legg til ny aksje
                portfolio_stock = PortfolioStock(
                    portfolio_id=user_portfolio.id,
                    ticker=ticker,
                    shares=quantity,
                    purchase_price=purchase_price
                )
                db.session.add(portfolio_stock)
            
            db.session.commit()
            current_app.logger.info(f"AUDIT: add_stock user={current_user.id} ticker={ticker} quantity={quantity} price={purchase_price}")
            success_msg = f'{ticker} lagt til i porteføljen.'
            
            if request.is_json:
                return jsonify({'success': True, 'message': success_msg})
            flash(success_msg, 'success')
            return redirect(url_for('portfolio.portfolio_overview'))
            
        except Exception as e:
            db.session.rollback()
            error_msg = f'Kunne ikke legge til aksje: {str(e)}'
            if request.is_json:
                return jsonify({'success': False, 'error': error_msg}), 500
            flash(error_msg, 'error')
            return redirect(url_for('portfolio.add_stock'))
    
    # GET: support pre-filling ticker from ?symbol= param
    prefill_ticker = request.args.get('symbol', '')
    return render_template('portfolio/add_stock.html', prefill_ticker=prefill_ticker)

@portfolio.route('/edit/<ticker>', methods=['GET', 'POST'])
@access_required
def edit_stock(ticker):
    """Edit a stock in the user's portfolio"""
    # Hent brukerens portefølje
    user_portfolio = Portfolio.query.filter_by(user_id=current_user.id).first()
    if not user_portfolio:
        msg = 'Du har ingen portefølje ennå.'
        if request.is_json:
            return jsonify({'success': False, 'error': msg}), 404
        flash(msg, 'warning')
        return redirect(url_for('portfolio.portfolio_overview'))
    
    # Finn aksjen (utelukk soft-deleted)
    portfolio_stock = PortfolioStock.query.filter_by(
        portfolio_id=user_portfolio.id,
        ticker=ticker,
        deleted_at=None
    ).first()
    if not portfolio_stock:
        msg = f'Aksjen {ticker} ble ikke funnet i din portefølje.'
        if request.is_json:
            return jsonify({'success': False, 'error': msg}), 404
        flash(msg, 'warning')
        return redirect(url_for('portfolio.portfolio_overview'))
    
    if request.method == 'POST':
        # En enkel CSRF-tilstedeværelsessjekk (om Flask-WTF ikke allerede fanger)
        if 'csrf_token' not in request.form and not request.is_json:
            msg = 'CSRF token mangler.'
            if request.is_json:
                return jsonify({'success': False, 'error': msg}), 403
            flash(msg, 'danger')
            return redirect(url_for('portfolio.edit_stock', ticker=ticker))
        # Aksepter både 'quantity' (nytt felt) og fallback 'shares' for bakoverkompatibilitet
        raw_quantity = request.form.get('quantity') or request.form.get('shares') or '0'
        raw_price = request.form.get('purchase_price') or '0'
        purchase_date_str = request.form.get('purchase_date')

        try:
            quantity = float(raw_quantity)
            purchase_price = float(raw_price)
        except ValueError:
            msg = 'Ugyldige numeriske verdier.'
            if request.is_json:
                return jsonify({'success': False, 'error': msg}), 400
            flash(msg, 'danger')
            return redirect(url_for('portfolio.edit_stock', ticker=ticker))

        MAX_SHARES = 10_000_000
        MAX_PRICE = 1_000_000
        if quantity <= 0 or purchase_price <= 0:
            msg = 'Alle felt må fylles ut korrekt.'
            if request.is_json:
                return jsonify({'success': False, 'error': msg}), 400
            flash(msg, 'danger')
            return redirect(url_for('portfolio.edit_stock', ticker=ticker))
        if quantity > MAX_SHARES or purchase_price > MAX_PRICE:
            msg = 'Urealistisk verdi for antall eller pris.'
            if request.is_json:
                return jsonify({'success': False, 'error': msg}), 400
            flash(msg, 'danger')
            return redirect(url_for('portfolio.edit_stock', ticker=ticker))

        before_state = {'shares': float(portfolio_stock.shares), 'purchase_price': float(portfolio_stock.purchase_price or 0)}
        portfolio_stock.shares = quantity
        portfolio_stock.purchase_price = purchase_price

        # Oppdater kjøpsdato hvis sendt inn (tillat blank for å la eksisterende stå)
        if purchase_date_str:
            try:
                from datetime import datetime
                portfolio_stock.purchase_date = datetime.strptime(purchase_date_str, '%Y-%m-%d').date()
            except ValueError:
                # Ignorer feil format, men informer bruker
                flash('Kjøpsdato hadde feil format (YYYY-MM-DD).', 'warning')

        try:
            db.session.commit()
        except Exception as commit_err:
            db.session.rollback()
            msg = f'Kunne ikke lagre endringer: {commit_err}'
            if request.is_json:
                return jsonify({'success': False, 'error': msg}), 500
            flash(msg, 'danger')
            return redirect(url_for('portfolio.edit_stock', ticker=ticker))

        # Audit log er best-effort
        try:
            from ..models.portfolio_audit import PortfolioAuditLog
            audit = PortfolioAuditLog(
                user_id=current_user.id,
                portfolio_id=portfolio_stock.portfolio_id,
                stock_id=portfolio_stock.id,
                ticker=ticker,
                action='edit_stock',
                before_state=before_state,
                after_state={'shares': quantity, 'purchase_price': purchase_price},
                ip_address=request.remote_addr,
                user_agent=request.headers.get('User-Agent', '')[:256]
            )
            db.session.add(audit)
            db.session.commit()
        except Exception as audit_err:
            current_app.logger.warning(f"Failed to persist audit log for edit_stock {ticker}: {audit_err}")

        success_msg = f'{ticker} oppdatert i porteføljen.'
        if request.is_json:
            return jsonify({'success': True, 'message': success_msg, 'ticker': ticker, 'shares': quantity, 'purchase_price': purchase_price})
        flash(success_msg, 'success')
        return redirect(url_for('portfolio.portfolio_overview'))
    
    # GET
    if request.is_json:
        return jsonify({
            'ticker': portfolio_stock.ticker,
            'shares': float(portfolio_stock.shares),
            'purchase_price': float(portfolio_stock.purchase_price or 0),
            'purchase_date': portfolio_stock.purchase_date.isoformat() if portfolio_stock.purchase_date else None
        })
    return render_template('portfolio/edit_stock.html', stock=portfolio_stock)

@portfolio.route('/remove/<ticker>', methods=['POST'])
@access_required
def remove_stock(ticker):
    """Remove a stock from the user's portfolio (POST only, CSRF protected)."""
    try:
        # Basic CSRF presence check (Flask-WTF normally validates; here we ensure field exists)
        if 'csrf_token' not in request.form:
            # Return 403 to be explicit for tests/clients
            if request.headers.get('Accept') == 'application/json':
                return jsonify({'success': False, 'error': 'CSRF token mangler'}), 403
            flash('CSRF token mangler.', 'danger')
            return redirect(url_for('portfolio.portfolio_overview'))

        user_portfolio = Portfolio.query.filter_by(user_id=current_user.id).first()
        if not user_portfolio:
            flash('Du har ingen portefølje ennå.', 'warning')
            return redirect(url_for('portfolio.portfolio_overview'))

        portfolio_stock = PortfolioStock.query.filter_by(
            portfolio_id=user_portfolio.id,
            ticker=ticker,
            deleted_at=None
        ).first_or_404()

        # Capture before state
        before_state = {
            'shares': float(portfolio_stock.shares),
            'purchase_price': float(portfolio_stock.purchase_price or 0)
        }
        # Soft delete instead of hard delete
        from datetime import datetime as _dt
        portfolio_stock.deleted_at = _dt.utcnow()
        db.session.commit()
        # Persist audit log
        try:
            from ..models.portfolio_audit import PortfolioAuditLog
            audit = PortfolioAuditLog(
                user_id=current_user.id,
                portfolio_id=user_portfolio.id,
                stock_id=portfolio_stock.id,
                ticker=ticker,
                action='delete_stock',
                before_state=before_state,
                after_state={'deleted_at': portfolio_stock.deleted_at.isoformat()},
                ip_address=request.remote_addr,
                user_agent=request.headers.get('User-Agent', '')[:256]
            )
            db.session.add(audit)
            db.session.commit()
        except Exception as audit_err:
            current_app.logger.warning(f"Failed to persist audit log for delete_stock {ticker}: {audit_err}")

        flash(f'{ticker} fjernet (soft-delete) fra porteføljen.', 'success')
        return redirect(url_for('portfolio.portfolio_overview'))
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Feil ved sletting av aksje {ticker}: {e}")
        flash('Kunne ikke fjerne aksjen. Prøv igjen senere.', 'danger')
        return redirect(url_for('portfolio.portfolio_overview'))

@portfolio.route('/transactions')
@access_required
def transactions():
    """Show transaction history"""
    return render_template('main/coming_soon.html', message="Kommer senere")

@portfolio.route('/advanced')
@portfolio.route('/advanced/')
@access_required
def advanced():
    """Advanced portfolio analysis page"""
    try:
        # Get user's portfolio stocks if they have any
        user_stocks = []
        try:
            # Try to get user's actual portfolio
            user = current_user if hasattr(current_user, 'id') else None
            if user:
                # Query user's portfolio holdings
                user_stocks = ['EQNR.OL', 'DNB.OL', 'TEL.OL']  # Fallback sample
        except:
            # Use sample Norwegian stocks as fallback
            user_stocks = ['EQNR.OL', 'DNB.OL', 'TEL.OL', 'NHY.OL', 'MOWI.OL']
            
        # Provide sample data for the advanced portfolio page
        sample_data = {
            'expected_return': 8.5,
            'volatility': 12.3,
            'sharpe_ratio': 0.69,
            'max_drawdown': -15.2,
            'portfolio_value': 500000,
            'total_return': 12.4,
            'selected_stocks': user_stocks
        }
        return render_template('portfolio/advanced.html', **sample_data)
    except Exception as e:
        current_app.logger.error(f"Error loading advanced portfolio page: {e}")
        # Provide a basic fallback instead of redirect to avoid loops
        return render_template('portfolio/advanced.html', 
                             error=True, 
                             error_message="Avansert analyse midlertidig utilgjengelig",
                             selected_stocks=['EQNR.OL', 'DNB.OL', 'TEL.OL'])

# Helper method to get stock data
def get_single_stock_data(ticker):
    """Get data for a single stock"""
    try:
        # Hent gjeldende data
        stock_data = get_data_service().get_stock_data(ticker, period='1d')
        if stock_data.empty:
            return None
            
        # Teknisk analyse
        AnalysisService = get_analysis_service()
        ta_data = AnalysisService.get_technical_analysis(ticker) if AnalysisService else None
        
        # Sett sammen data
        last_price = stock_data['Close'].iloc[-1]
        change = 0
        change_percent = 0
        
        if len(stock_data) > 1:
            prev_price = stock_data['Close'].iloc[-2]
            change = last_price - prev_price
            change_percent = (change / prev_price) * 100 if prev_price > 0 else 0
        
        return {
            'ticker': ticker,
            'last_price': round(last_price, 2),
            'change': round(change, 2),
            'change_percent': round(change_percent, 2),
            'signal': ta_data.get('signal', 'Hold') if ta_data else 'Hold',
            'rsi': ta_data.get('rsi', 50) if ta_data else 50,
            'volume': ta_data.get('volume', 100000) if ta_data else 100000
        }
    except Exception as e:
        print(f"Error getting data for {ticker}: {str(e)}")
        return None

@portfolio.route('/api/export', methods=['GET'])
@login_required
@access_required
def export_portfolio():
    """Eksporter portefølje til CSV eller PDF"""
    try:
        # import pandas as pd
        from flask import Response
        format = request.args.get('format', 'csv')
        
        # Hent porteføljedata for bruker
        portfolios = Portfolio.query.filter_by(user_id=current_user.id).all()
        data = []
        
        for p in portfolios:
            for stock in p.stocks:
                data.append({
                    'Portefølje': p.name,
                    'Ticker': stock.ticker,
                    'Antall': format_number_norwegian(stock.shares),
                    'Kjøpspris': format_currency_norwegian(stock.purchase_price),
                    'Nåverdi': format_currency_norwegian(stock.current_value),
                    'Kjøpsdato': stock.purchase_date.strftime('%d.%m.%Y') if stock.purchase_date else ''
                })
        
        if not data:
            raise UserFriendlyError('portfolio_not_found')
        
        # Temporary placeholder - pandas not available
        # df = pd.DataFrame(data)
        df_data = data
        
        if format == 'csv':
            # Simple CSV creation without pandas
            import csv
            import io
            
            output = io.StringIO()
            if df_data:
                fieldnames = df_data[0].keys()
                writer = csv.DictWriter(output, fieldnames=fieldnames, delimiter=';')
                writer.writeheader()
                writer.writerows(df_data)
            
            csv_data = output.getvalue()
            output.close()
            
            return Response(
                csv_data,
                mimetype='text/csv',
                headers={'Content-Disposition': 'attachment;filename=portefolje.csv'}
            )
        elif format == 'pdf':
            # Try to use reportlab for PDF generation
            reportlab_components = get_reportlab()
            if not reportlab_components:
                # Fallback to CSV if reportlab is not available
                import csv
                import io
                
                output = io.StringIO()
                if df_data:
                    fieldnames = df_data[0].keys()
                    writer = csv.DictWriter(output, fieldnames=fieldnames, delimiter=';')
                    writer.writeheader()
                    writer.writerows(df_data)
                
                csv_data = output.getvalue()
                output.close()
                
                return Response(
                    csv_data,
                    mimetype='text/csv',
                    headers={'Content-Disposition': 'attachment;filename=portefolje.csv'}
                )
            
            try:
                buffer = BytesIO()
                doc = reportlab_components['SimpleDocTemplate'](buffer, pagesize=reportlab_components['A4'])
                
                # Create table data without pandas
                if df_data:
                    headers = list(df_data[0].keys())
                    rows = [list(row.values()) for row in df_data]
                    table_data = [headers] + rows
                else:
                    table_data = [['No data available']]
                
                table = reportlab_components['Table'](table_data)
                table.setStyle(reportlab_components['TableStyle']([
                    ('BACKGROUND', (0, 0), (-1, 0), reportlab_components['colors'].lightgrey),
                    ('GRID', (0, 0), (-1, -1), 0.5, reportlab_components['colors'].grey),
                ]))
                doc.build([table])
                
                buffer.seek(0)
                return Response(
                    buffer.read(),
                    mimetype='application/pdf',
                    headers={'Content-Disposition': 'attachment;filename=portefolje.pdf'}
                )
            except Exception:
                # Fallback to CSV if PDF generation fails
                csv_data = df.to_csv(index=False, sep=';', decimal=',')
                return Response(
                    csv_data,
                    mimetype='text/csv',
                    headers={'Content-Disposition': 'attachment;filename=portefolje.csv'}
                )
        else:
            raise UserFriendlyError('invalid_file_type')
            
    except UserFriendlyError as e:
        return handle_api_error(e, 'export_portfolio')
    except Exception as e:
        current_app.logger.error(f"Export error: {e}")
        return handle_api_error(
            UserFriendlyError('export_failed'), 
            'export_portfolio'
        )

# =============================================================================
# ADVANCED PORTFOLIO OPTIMIZATION AND ANALYTICS API ENDPOINTS
# =============================================================================

@portfolio.route('/optimization')
@access_required  
def optimization_page():
    """Portfolio optimization interface"""
    try:
        return render_template('portfolio/optimization.html',
                             title='Portfolio Optimization')
    except Exception as e:
        logger.error(f"Optimization page error: {e}")
        # Return simple error page instead of 500
        return render_template('error.html', 
                             error='Portfolio optimization er midlertidig utilgjengelig. Prøv igjen senere.'), 200

@portfolio.route('/performance-analytics')
@access_required
def performance_page():
    """Performance analytics interface"""
    try:
        # Get user's portfolios for selection
        user_portfolios = Portfolio.query.filter_by(user_id=current_user.id).all()
        default_portfolio = user_portfolios[0] if user_portfolios else None
        
        return render_template('portfolio_analytics/dashboard.html',
                             page_title='Portfolio Performance Analytics',
                             portfolios=user_portfolios,
                             default_portfolio=default_portfolio)
    except Exception as e:
        logger.error(f"Performance page error: {e}")
        # Return simple error page instead of 500
        return render_template('error.html', 
                             error='Portfolio analytics er midlertidig utilgjengelig. Prøv igjen senere.'), 200

@portfolio.route('/api/optimization', methods=['POST'])
@access_required
def api_portfolio_optimization():
    """API endpoint for portfolio optimization"""
    try:
        data = request.get_json()
        
        # Extract parameters
        holdings = data.get('holdings', [])
        risk_tolerance = data.get('risk_tolerance', 'moderate')
        target_return = data.get('target_return')
        
        # Validate holdings data
        if not holdings:
            return jsonify({
                'success': False,
                'error': 'Holdings data is required'
            }), 400
        
        # Perform optimization
        optimization_service = get_portfolio_optimization_service()
        if optimization_service:
            optimization_result = optimization_service.optimize_portfolio(
                holdings=holdings,
                risk_tolerance=risk_tolerance,
                target_return=target_return
            )
        else:
            # Fallback when service not available
            optimization_result = {
                'success': True,
                'optimal_weights': {},
                'expected_return': 0.08,
                'volatility': 0.15,
                'sharpe_ratio': 0.53,
                'message': 'Optimization service temporarily unavailable - showing sample data'
            }
        
        return jsonify(optimization_result)
        
    except Exception as e:
        logger.error(f"Portfolio optimization API error: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@portfolio.route('/api/risk-metrics', methods=['POST'])
@access_required
def api_risk_metrics():
    """API endpoint for comprehensive risk analysis"""
    try:
        data = request.get_json()
        
        holdings = data.get('holdings', [])
        timeframe_days = data.get('timeframe_days', 252)
        
        if not holdings:
            return jsonify({
                'success': False,
                'error': 'Holdings data is required'
            }), 400
        
        # Calculate risk metrics
        optimization_service = get_portfolio_optimization_service()
        if optimization_service:
            risk_analysis = optimization_service.calculate_risk_metrics(
                holdings=holdings,
                timeframe_days=timeframe_days
            )
        else:
            # Fallback when service not available
            risk_analysis = {
                'success': True,
                'var_95': 0.02,
                'cvar_95': 0.035,
                'max_drawdown': 0.15,
                'beta': 1.05,
                'alpha': 0.02,
                'message': 'Risk analysis service temporarily unavailable - showing sample data'
            }
        
        return jsonify(risk_analysis)
        
    except Exception as e:
        logger.error(f"Risk metrics API error: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@portfolio.route('/api/scenario-analysis', methods=['POST'])
@access_required
def api_scenario_analysis():
    """API endpoint for Monte Carlo scenario analysis"""
    try:
        data = request.get_json()
        
        holdings = data.get('holdings', [])
        scenarios = data.get('scenarios', None)
        
        if not holdings:
            return jsonify({
                'success': False,
                'error': 'Holdings data is required'
            }), 400
        
        # Generate scenario analysis
        optimization_service = get_portfolio_optimization_service()
        if optimization_service:
            scenario_results = optimization_service.generate_scenario_analysis(
                holdings=holdings,
                scenarios=scenarios
            )
        else:
            # Fallback when service not available
            scenario_results = {
                'success': True,
                'scenarios': {
                    'bull_market': {'return': 0.15, 'probability': 0.3},
                    'bear_market': {'return': -0.20, 'probability': 0.2},
                    'normal_market': {'return': 0.08, 'probability': 0.5}
                },
                'message': 'Scenario analysis service temporarily unavailable - showing sample data'
            }
        
        return jsonify(scenario_results)
        
    except Exception as e:
        logger.error(f"Scenario analysis API error: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@portfolio.route('/api/performance-attribution', methods=['POST'])
@access_required
def api_performance_attribution():
    """API endpoint for performance attribution analysis"""
    try:
        data = request.get_json()
        
        holdings = data.get('holdings', [])
        benchmark = data.get('benchmark', 'OSEBX')
        periods = data.get('periods', None)
        
        if not holdings:
            return jsonify({
                'success': False,
                'error': 'Holdings data is required'
            }), 400
        
        # Calculate performance attribution
        performance_service = get_performance_tracking_service()
        if performance_service:
            attribution_results = performance_service.calculate_performance_attribution(
                holdings=holdings,
                benchmark=benchmark,
                periods=periods
            )
        else:
            # Fallback when service not available
            attribution_results = {
                'success': True,
                'stock_selection': 0.02,
                'asset_allocation': 0.01,
                'interaction': 0.003,
                'total_attribution': 0.033,
                'message': 'Performance attribution service temporarily unavailable - showing sample data'
            }
        
        return jsonify(attribution_results)
        
    except Exception as e:
        logger.error(f"Performance attribution API error: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@portfolio.route('/api/benchmark-comparison', methods=['POST'])
@access_required
def api_benchmark_comparison():
    """API endpoint for benchmark comparison analysis"""
    try:
        data = request.get_json()
        
        holdings = data.get('holdings', [])
        benchmarks = data.get('benchmarks', None)
        
        if not holdings:
            return jsonify({
                'success': False,
                'error': 'Holdings data is required'
            }), 400
        
        # Generate benchmark comparison
        performance_service = get_performance_tracking_service()
        if performance_service:
            comparison_results = performance_service.generate_benchmark_comparison(
                holdings=holdings,
                benchmarks=benchmarks
            )
        else:
            # Fallback when service not available
            comparison_results = {
                'success': True,
                'vs_sp500': {'excess_return': 0.02, 'tracking_error': 0.05},
                'vs_nasdaq': {'excess_return': -0.01, 'tracking_error': 0.08},
                'message': 'Benchmark comparison service temporarily unavailable - showing sample data'
            }
        
        return jsonify(comparison_results)
        
    except Exception as e:
        logger.error(f"Benchmark comparison API error: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@portfolio.route('/api/factor-exposure', methods=['POST'])
@access_required
def api_factor_exposure():
    """API endpoint for factor exposure analysis"""
    try:
        data = request.get_json()
        
        holdings = data.get('holdings', [])
        
        if not holdings:
            return jsonify({
                'success': False,
                'error': 'Holdings data is required'
            }), 400
        
        # Calculate factor exposures
        performance_service = get_performance_tracking_service()
        if performance_service:
            factor_results = performance_service.calculate_factor_exposure(
                holdings=holdings
            )
        else:
            # Fallback when service not available
            factor_results = {
                'success': True,
                'value_factor': 0.15,
                'growth_factor': 0.25,
                'size_factor': -0.05,
                'momentum_factor': 0.10,
                'message': 'Factor exposure service temporarily unavailable - showing sample data'
            }
        
        return jsonify(factor_results)
        
    except Exception as e:
        logger.error(f"Factor exposure API error: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@portfolio.route('/api/portfolio-health', methods=['POST'])
@access_required
def api_portfolio_health():
    """API endpoint for comprehensive portfolio health check"""
    try:
        data = request.get_json()
        
        holdings = data.get('holdings', [])
        
        if not holdings:
            return jsonify({
                'success': False,
                'error': 'Holdings data is required'
            }), 400
        
        # Comprehensive health analysis
        health_analysis = _generate_portfolio_health_analysis(holdings)
        
        return jsonify(health_analysis)
        
    except Exception as e:
        logger.error(f"Portfolio health API error: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

def _generate_portfolio_health_analysis(holdings):
    """Generate comprehensive portfolio health analysis"""
    try:
        # Basic portfolio statistics
        total_positions = len(holdings)
        total_value = sum(holding.get('value', 0) for holding in holdings)
        
        # Concentration analysis
        largest_position = max(holding.get('weight', 0) for holding in holdings) if holdings else 0
        top_5_concentration = sum(sorted([h.get('weight', 0) for h in holdings], reverse=True)[:5])
        
        # Diversification metrics
        hhi_index = sum(h.get('weight', 0)**2 for h in holdings)  # Herfindahl-Hirschman Index
        effective_positions = 1 / hhi_index if hhi_index > 0 else 0
        
        # Risk indicators
        risk_indicators = []
        if largest_position > 0.20:
            risk_indicators.append("High concentration in single position")
        if top_5_concentration > 0.60:
            risk_indicators.append("High concentration in top 5 positions")
        if total_positions < 10:
            risk_indicators.append("Limited diversification - consider more positions")
        if effective_positions < 5:
            risk_indicators.append("Low effective diversification")
        
        # Health score calculation
        health_score = 100
        health_score -= min(largest_position * 200, 40)  # Concentration penalty
        health_score -= max(0, (0.60 - top_5_concentration) * -50)  # Diversification bonus
        health_score -= max(0, (10 - total_positions) * 2)  # Position count penalty
        health_score = max(0, min(100, health_score))
        
        # Health grade
        if health_score >= 80:
            health_grade = 'Excellent'
        elif health_score >= 65:
            health_grade = 'Good'
        elif health_score >= 50:
            health_grade = 'Fair'
        else:
            health_grade = 'Poor'
        
        # Recommendations
        recommendations = []
        if largest_position > 0.15:
            recommendations.append("Consider reducing largest position concentration")
        if total_positions < 15:
            recommendations.append("Add more positions for better diversification")
        if len(risk_indicators) == 0:
            recommendations.append("Portfolio shows good diversification characteristics")
        
        return {
            'success': True,
            'health_metrics': {
                'total_positions': total_positions,
                'total_value': round(total_value, 2),
                'largest_position_weight': round(largest_position, 4),
                'top_5_concentration': round(top_5_concentration, 4),
                'hhi_index': round(hhi_index, 4),
                'effective_positions': round(effective_positions, 2),
                'health_score': round(health_score, 1),
                'health_grade': health_grade
            },
            'risk_indicators': risk_indicators,
            'recommendations': recommendations,
            'diversification_analysis': {
                'concentration_risk': 'High' if largest_position > 0.20 else 'Low',
                'diversification_level': 'Good' if effective_positions > 10 else 'Needs Improvement',
                'position_sizing': 'Balanced' if largest_position < 0.15 else 'Concentrated'
            },
            'timestamp': 'datetime.utcnow().isoformat()'
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }
        return jsonify({'error': 'Ugyldig format'}), 400


@portfolio.route('/optimization')
@login_required 
def optimization():
    """Modern Portfolio Theory optimization"""
    try:
        # Sample portfolio data
        current_portfolio = [
            {'symbol': 'EQUI.OL', 'name': 'Equinor ASA', 'weight': 30.0, 'expected_return': 12.5, 'risk': 18.2},
            {'symbol': 'DNB.OL', 'name': 'DNB Bank ASA', 'weight': 25.0, 'expected_return': 10.8, 'risk': 15.4},
            {'symbol': 'TEL.OL', 'name': 'Telenor ASA', 'weight': 20.0, 'expected_return': 8.2, 'risk': 12.1},
            {'symbol': 'MOWI.OL', 'name': 'Mowi ASA', 'weight': 15.0, 'expected_return': 14.2, 'risk': 22.3},
            {'symbol': 'YAR.OL', 'name': 'Yara International', 'weight': 10.0, 'expected_return': 11.5, 'risk': 19.8}
        ]
        
        # Optimization scenarios
        scenarios = [
            {
                'name': 'Conservative',
                'target_risk': 12.0,
                'expected_return': 9.5,
                'description': 'Lav risiko, stabil avkastning'
            },
            {
                'name': 'Balanced',
                'target_risk': 15.0,
                'expected_return': 11.2,
                'description': 'Balansert risiko og avkastning'
            },
            {
                'name': 'Aggressive',
                'target_risk': 20.0,
                'expected_return': 14.8,
                'description': 'Høy risiko, høy potensial avkastning'
            }
        ]
        
        # Risk metrics
        risk_metrics = {
            'portfolio_var_95': 8.5,  # Value at Risk 95%
            'portfolio_var_99': 12.3,  # Value at Risk 99%
            'expected_shortfall': 15.7,
            'beta': 1.12,
            'alpha': 0.8,
            'correlation_to_market': 0.78
        }
        
        return render_template('portfolio/optimization.html',
                             current_portfolio=current_portfolio,
                             scenarios=scenarios,
                             risk_metrics=risk_metrics)
    
    except Exception as e:
        logger.error(f"Error in portfolio optimization: {e}")
        return render_template('portfolio/optimization.html',
                             current_portfolio=[],
                             scenarios=[],
                             risk_metrics={})


@portfolio.route('/api/optimize', methods=['POST'])
@login_required
def optimize_portfolio():
    """Run portfolio optimization"""
    try:
        data = request.get_json()
        target_risk = data.get('target_risk', 15.0)
        target_return = data.get('target_return', 10.0)
        
        # Simulate optimization (would use real MPT in production)
        import random
        optimized_weights = [
            {'symbol': 'EQUI.OL', 'weight': round(random.uniform(15, 35), 1)},
            {'symbol': 'DNB.OL', 'weight': round(random.uniform(20, 30), 1)},
            {'symbol': 'TEL.OL', 'weight': round(random.uniform(15, 25), 1)},
            {'symbol': 'MOWI.OL', 'weight': round(random.uniform(10, 20), 1)},
            {'symbol': 'YAR.OL', 'weight': round(random.uniform(5, 15), 1)}
        ]
        
        # Normalize weights to sum to 100%
        total_weight = sum(w['weight'] for w in optimized_weights)
        for weight in optimized_weights:
            weight['weight'] = round((weight['weight'] / total_weight) * 100, 1)
        
        results = {
            'optimized_weights': optimized_weights,
            'expected_return': round(target_return + random.uniform(-1, 1), 2),
            'expected_risk': round(target_risk + random.uniform(-0.5, 0.5), 2),
            'sharpe_ratio': round(random.uniform(0.8, 1.5), 2),
            'improvement': {
                'return_improvement': round(random.uniform(0.5, 2.0), 2),
                'risk_reduction': round(random.uniform(1.0, 3.0), 2)
            }
        }
        
        return jsonify({
            'success': True,
            'results': results
        })
    
    except Exception as e:
        logger.error(f"Error optimizing portfolio: {e}")
        return jsonify({
            'success': False,
            'error': 'Feil ved optimalisering av portefølje'
        })

@portfolio.route('/audit-history')
@login_required
def audit_history():
    """Display portfolio audit log with simple filtering & pagination.
    Restricted to viewing own entries unless user is admin (is_admin attr)."""
    from ..models.portfolio_audit import PortfolioAuditLog
    q = PortfolioAuditLog.query
    # Non-admins only see their own
    if not getattr(current_user, 'is_admin', False):
        q = q.filter_by(user_id=current_user.id)
    # Filters
    portfolio_id = request.args.get('portfolio_id', type=int)
    if portfolio_id:
        q = q.filter_by(portfolio_id=portfolio_id)
    ticker = request.args.get('ticker', type=str)
    if ticker:
        q = q.filter(PortfolioAuditLog.ticker.ilike(f"%{ticker}%"))
    action = request.args.get('action', type=str)
    if action:
        q = q.filter_by(action=action)
    # Date range filtering
    from datetime import datetime
    start_date = request.args.get('start_date', type=str)
    end_date = request.args.get('end_date', type=str)
    if start_date:
        try:
            dt_start = datetime.strptime(start_date, "%Y-%m-%d")
            q = q.filter(PortfolioAuditLog.created_at >= dt_start)
        except Exception:
            pass
    if end_date:
        try:
            dt_end = datetime.strptime(end_date, "%Y-%m-%d")
            # To include the full end date, add one day and filter less than next day
            from datetime import timedelta
            dt_end_next = dt_end + timedelta(days=1)
            q = q.filter(PortfolioAuditLog.created_at < dt_end_next)
        except Exception:
            pass
    # Pagination
    page = request.args.get('page', 1, type=int)
    per_page = 50
    total = q.count()
    total_pages = max(1, (total + per_page - 1)//per_page)
    rows = q.order_by(PortfolioAuditLog.created_at.desc()).offset((page-1)*per_page).limit(per_page).all()
    return render_template('portfolio_audit_history.html', rows=rows, page=page, total_pages=total_pages)

@portfolio.route('/admin/prune-soft-deleted')
@login_required
def prune_soft_deleted():
    if not getattr(current_user, 'is_admin', False):
        return jsonify({'error':'forbidden'}), 403
    days = request.args.get('days', 90, type=int)
    dry_run = request.args.get('dry_run', 'true').lower() in ('true','1','yes')
    cutoff = datetime.utcnow() - timedelta(days=days)
    q = PortfolioStock.query.filter(PortfolioStock.deleted_at != None, PortfolioStock.deleted_at < cutoff)
    count = q.count()
    deleted_ids = []
    if not dry_run:
        for s in q.all():
            deleted_ids.append(s.id)
            db.session.delete(s)
        db.session.commit()
    return jsonify({'pruned': 0 if dry_run else len(deleted_ids), 'candidates': count, 'dry_run': dry_run, 'cutoff': cutoff.isoformat()})
