from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, current_app
from flask_login import login_required, current_user
from ..models.user import User
from ..models.portfolio import Portfolio, PortfolioStock
from ..extensions import db
from datetime import datetime, timedelta
try:
    import yfinance as yf
except ImportError:
    yf = None
# import pandas as pd
# import numpy as np
from scipy.optimize import minimize
import json

# Safe optional numerical imports (prevents NameError if missing)
try:  # pragma: no cover - environment dependent
    import pandas as pd  # type: ignore
except Exception:  # pragma: no cover
    pd = None  # type: ignore
try:  # pragma: no cover
    import numpy as np  # type: ignore
except Exception:  # pragma: no cover
    np = None  # type: ignore

portfolio_advanced = Blueprint('portfolio_advanced', __name__)

class PortfolioOptimizer:
    """AI-basert porteføljeoptimalisering"""
    
    def __init__(self):
        self.risk_free_rate = 0.02  # 2% risikoløs rente
        
    def get_stock_data(self, symbols, period="1y"):
        """Hent historiske data for aksjer"""
        try:
            data = {}
            for symbol in symbols:
                if yf is not None:
                    ticker = yf.Ticker(symbol)
                    hist = ticker.history(period=period)
                    if not hist.empty:
                        data[symbol] = hist['Close']
            if data:
                df = pd.DataFrame(data)
                return df.dropna()
            return None
        except Exception as e:
            current_app.logger.error(f"Feil ved henting av aksjedata: {e}")
            return None
    
    def calculate_portfolio_metrics(self, returns, weights):
        """Beregn porteføljemålinger"""
        portfolio_return = np.sum(returns.mean() * weights) * 252
        portfolio_std = np.sqrt(np.dot(weights.T, np.dot(returns.cov() * 252, weights)))
        sharpe_ratio = (portfolio_return - self.risk_free_rate) / portfolio_std
        
        return {
            'return': portfolio_return,
            'volatility': portfolio_std,
            'sharpe_ratio': sharpe_ratio
        }
    
    def optimize_portfolio(self, symbols, optimization_type='sharpe'):
        """Optimaliser portefølje basert på ulike kriterier"""
        try:
            price_data = self.get_stock_data(symbols)
            if price_data is None or price_data.empty:
                return None
            
            returns = price_data.pct_change().dropna()
            n_assets = len(symbols)
            
            # Begrensninger
            constraints = ({'type': 'eq', 'fun': lambda x: np.sum(x) - 1})
            bounds = tuple((0, 1) for _ in range(n_assets))
            
            # Initial guess - like vekting
            x0 = np.array([1/n_assets] * n_assets)
            
            if optimization_type == 'sharpe':
                # Maksimer Sharpe ratio
                def objective(weights):
                    metrics = self.calculate_portfolio_metrics(returns, weights)
                    return -metrics['sharpe_ratio']  # Negativ fordi vi minimerer
            
            elif optimization_type == 'min_volatility':
                # Minimer volatilitet
                def objective(weights):
                    metrics = self.calculate_portfolio_metrics(returns, weights)
                    return metrics['volatility']
            
            elif optimization_type == 'max_return':
                # Maksimer avkastning
                def objective(weights):
                    metrics = self.calculate_portfolio_metrics(returns, weights)
                    return -metrics['return']
            
            result = minimize(objective, x0, method='SLSQP', bounds=bounds, constraints=constraints)
            
            if result.success:
                optimal_weights = result.x
                metrics = self.calculate_portfolio_metrics(returns, optimal_weights)
                
                return {
                    'symbols': symbols,
                    'weights': optimal_weights.tolist(),
                    'expected_return': metrics['return'],
                    'volatility': metrics['volatility'],
                    'sharpe_ratio': metrics['sharpe_ratio'],
                    'optimization_type': optimization_type
                }
            
            return None
            
        except Exception as e:
            current_app.logger.error(f"Feil ved porteføljeoptimalisering: {e}")
            return None
    
    def generate_ai_insights(self, portfolio_data, current_holdings=None):
        """Generer AI-innsikt for porteføljen"""
        insights = []
        
        if portfolio_data:
            # Analyser diversifisering
            weights = portfolio_data['weights']
            max_weight = max(weights)
            min_weight = min(weights)
            
            if max_weight > 0.4:
                insights.append({
                    'type': 'warning',
                    'title': 'Konsentrasjonsrisiko',
                    'message': f'En aksje utgjør {max_weight:.1%} av porteføljen. Vurder å diversifisere mer.',
                    'severity': 'medium'
                })
            
            if portfolio_data['volatility'] > 0.25:
                insights.append({
                    'type': 'warning',
                    'title': 'Høy volatilitet',
                    'message': f'Porteføljen har høy volatilitet ({portfolio_data["volatility"]:.1%}). Vurder å legge til mer stabile aksjer.',
                    'severity': 'high'
                })
            
            if portfolio_data['sharpe_ratio'] > 1.0:
                insights.append({
                    'type': 'success',
                    'title': 'Utmerket risikojustert avkastning',
                    'message': f'Sharpe ratio på {portfolio_data["sharpe_ratio"]:.2f} indikerer god balanse mellom risiko og avkastning.',
                    'severity': 'low'
                })
            
            # Sektoranalyse (forenklet)
            if len(portfolio_data['symbols']) < 5:
                insights.append({
                    'type': 'info',
                    'title': 'Lav diversifisering',
                    'message': 'Vurder å legge til flere aksjer fra ulike sektorer for bedre risikospredning.',
                    'severity': 'medium'
                })
        
        return insights

@portfolio_advanced.route('/advanced/')
@login_required
def advanced_portfolio():
    """Avansert porteføljeanalyse"""
    return render_template('portfolio/advanced.html')

@portfolio_advanced.route('/optimize', methods=['POST'])
@login_required
def optimize_portfolio():
    """Optimaliser portefølje"""
    try:
        data = request.get_json()
        symbols = data.get('symbols', [])
        optimization_type = data.get('type', 'sharpe')
        
        if not symbols:
            return jsonify({'error': 'Ingen aksjer spesifisert'}), 400
        
        optimizer = PortfolioOptimizer()
        result = optimizer.optimize_portfolio(symbols, optimization_type)
        
        if result:
            insights = optimizer.generate_ai_insights(result)
            result['insights'] = insights
            return jsonify(result)
        else:
            return jsonify({'error': 'Kunne ikke optimalisere portefølje'}), 500
            
    except Exception as e:
        current_app.logger.error(f"Feil ved porteføljeoptimalisering: {e}")
        return jsonify({'error': 'Intern serverfeil'}), 500

@portfolio_advanced.route('/backtest', methods=['POST'])
@login_required
def backtest_portfolio():
    """Backtesting av porteføljestrategi"""
    try:
        data = request.get_json()
        symbols = data.get('symbols', [])
        weights = data.get('weights', [])
        start_date = data.get('start_date', '2022-01-01')
        end_date = data.get('end_date', datetime.now().strftime('%Y-%m-%d'))
        
        if len(symbols) != len(weights):
            return jsonify({'error': 'Antall aksjer og vekter må være like'}), 400
        
        # Normaliser vekter
        weights = np.array(weights)
        weights = weights / np.sum(weights)
        
        optimizer = PortfolioOptimizer()
        
        # Hent historiske data
        price_data = optimizer.get_stock_data(symbols, period="2y")
        if price_data is None:
            return jsonify({'error': 'Kunne ikke hente historiske data'}), 500
        
        # Filtrer datoer
        start = pd.to_datetime(start_date)
        end = pd.to_datetime(end_date)
        price_data = price_data[(price_data.index >= start) & (price_data.index <= end)]
        
        if price_data.empty:
            return jsonify({'error': 'Ingen data i spesifisert periode'}), 400
        
        # Beregn porteføljeavkastning
        returns = price_data.pct_change().dropna()
        portfolio_returns = (returns * weights).sum(axis=1)
        
        # Beregn kumulativ avkastning
        cumulative_returns = (1 + portfolio_returns).cumprod()
        
        # Beregn nøkkeltall
        total_return = cumulative_returns.iloc[-1] - 1
        annual_return = (1 + total_return) ** (252 / len(portfolio_returns)) - 1
        volatility = portfolio_returns.std() * np.sqrt(252)
        sharpe_ratio = (annual_return - optimizer.risk_free_rate) / volatility
        
        # Maksimal drawdown
        running_max = cumulative_returns.cummax()
        drawdown = (cumulative_returns - running_max) / running_max
        max_drawdown = drawdown.min()
        
        result = {
            'symbols': symbols,
            'weights': weights.tolist(),
            'start_date': start_date,
            'end_date': end_date,
            'total_return': total_return,
            'annual_return': annual_return,
            'volatility': volatility,
            'sharpe_ratio': sharpe_ratio,
            'max_drawdown': max_drawdown,
            'cumulative_returns': cumulative_returns.tolist(),
            'dates': [d.strftime('%Y-%m-%d') for d in cumulative_returns.index],
            'portfolio_returns': portfolio_returns.tolist()
        }
        
        return jsonify(result)
        
    except Exception as e:
        current_app.logger.error(f"Feil ved backtesting: {e}")
        return jsonify({'error': 'Intern serverfeil'}), 500

@portfolio_advanced.route('/monte_carlo', methods=['POST'])
@login_required
def monte_carlo_simulation():
    """Monte Carlo-simulering av portefølje"""
    try:
        data = request.get_json()
        symbols = data.get('symbols', [])
        weights = data.get('weights', [])
        time_horizon = data.get('time_horizon', 252)  # 1 år
        n_simulations = data.get('n_simulations', 1000)
        
        if len(symbols) != len(weights):
            return jsonify({'error': 'Antall aksjer og vekter må være like'}), 400
        
        weights = np.array(weights)
        weights = weights / np.sum(weights)
        
        optimizer = PortfolioOptimizer()
        price_data = optimizer.get_stock_data(symbols)
        
        if price_data is None:
            return jsonify({'error': 'Kunne ikke hente aksjedata'}), 500
        
        returns = price_data.pct_change().dropna()
        mean_returns = returns.mean()
        cov_matrix = returns.cov()
        
        # Monte Carlo-simulering
        np.random.seed(42)  # For repeterbare resultater
        
        simulations = []
        for _ in range(n_simulations):
            # Generer tilfeldige avkastninger
            random_returns = np.random.multivariate_normal(mean_returns, cov_matrix, time_horizon)
            portfolio_returns = np.dot(random_returns, weights)
            
            # Beregn kumulativ avkastning
            cumulative_return = np.prod(1 + portfolio_returns) - 1
            simulations.append(cumulative_return)
        
        simulations = np.array(simulations)
        
        # Beregn statistikk
        percentiles = [5, 25, 50, 75, 95]
        percentile_values = np.percentile(simulations, percentiles)
        
        result = {
            'simulations': simulations.tolist(),
            'percentiles': dict(zip(percentiles, percentile_values.tolist())),
            'mean': np.mean(simulations),
            'std': np.std(simulations),
            'time_horizon_days': time_horizon,
            'n_simulations': n_simulations,
            'probability_positive': (simulations > 0).mean(),
            'worst_case_5': percentile_values[0],
            'best_case_5': percentile_values[4]
        }
        
        return jsonify(result)
        
    except Exception as e:
        current_app.logger.error(f"Feil ved Monte Carlo-simulering: {e}")
        return jsonify({'error': 'Intern serverfeil'}), 500
