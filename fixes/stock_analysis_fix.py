from flask import Blueprint, render_template, request, jsonify
import yfinance as yf
import pandas as pd
import numpy as np

stock_analysis_bp = Blueprint('stock_analysis', __name__)

@stock_analysis_bp.route('/stocks/details/<ticker>')
def stock_details(ticker):
    try:
        stock = yf.Ticker(ticker)
        hist = stock.history(period="6mo")
        
        # Beregn RSI
        delta = hist['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        
        # Beregn MACD
        exp1 = hist['Close'].ewm(span=12, adjust=False).mean()
        exp2 = hist['Close'].ewm(span=26, adjust=False).mean()
        macd = exp1 - exp2
        signal = macd.ewm(span=9, adjust=False).mean()
        
        chart_data = {
            'dates': hist.index.strftime('%Y-%m-%d').tolist(),
            'prices': hist['Close'].tolist(),
            'volume': hist['Volume'].tolist(),
            'rsi': rsi.fillna(50).tolist(),
            'macd': macd.fillna(0).tolist(),
            'signal': signal.fillna(0).tolist()
        }
        
        return render_template('stocks/details.html', 
                             ticker=ticker, 
                             data=stock.info,
                             chart_data=chart_data)
    except Exception as e:
        return render_template('error.html', error=str(e)), 500

@stock_analysis_bp.route('/stocks/compare')
def compare_stocks():
    tickers = request.args.getlist('tickers')
    period = request.args.get('period', '6mo')
    interval = request.args.get('interval', '1d')
    
    comparison_data = []
    
    for ticker in tickers:
        if ticker:  # Sjekk at ticker ikke er tom
            try:
                stock = yf.Ticker(ticker)
                hist = stock.history(period=period, interval=interval)
                
                if not hist.empty:
                    comparison_data.append({
                        'ticker': ticker,
                        'dates': hist.index.strftime('%Y-%m-%d').tolist(),
                        'prices': hist['Close'].tolist(),
                        'volume': hist['Volume'].tolist()
                    })
            except Exception as e:
                print(f"Error fetching {ticker}: {e}")
    
    return render_template('stocks/compare.html', data=comparison_data)

@stock_analysis_bp.route('/analysis/warren-buffett')
def warren_buffett():
    ticker = request.args.get('ticker', '')
    search_result = None
    
    if ticker:
        try:
            stock = yf.Ticker(ticker)
            info = stock.info
            
            # Warren Buffett-stil analyse
            search_result = {
                'ticker': ticker,
                'name': info.get('longName', ticker),
                'pe_ratio': info.get('trailingPE', 'N/A'),
                'pb_ratio': info.get('priceToBook', 'N/A'),
                'roe': info.get('returnOnEquity', 'N/A'),
                'debt_to_equity': info.get('debtToEquity', 'N/A'),
                'profit_margin': info.get('profitMargins', 'N/A'),
                'recommendation': info.get('recommendationKey', 'N/A')
            }
        except Exception as e:
            search_result = {'error': str(e)}
    
    return render_template('analysis/warren_buffett.html', result=search_result)

@stock_analysis_bp.route('/analysis/short-analysis')
def short_analysis():
    # Inkluder analysemeny
    return render_template('analysis/short_analysis.html', include_menu=True)
