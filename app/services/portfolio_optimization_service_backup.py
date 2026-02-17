"""
Advanced Portfolio Optimization Service
=====================================

AI-powered portfolio management with modern portfolio theory,
risk analytics, and dynamic rebalancing recommendations.
"""

# import numpy as np
# import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
import logging
# from scipy.optimize import minimize
# from scipy.stats import norm
import json

logger = logging.getLogger(__name__)

class PortfolioOptimizationService:
    """Advanced portfolio optimization using AI and modern portfolio theory"""
    
    @staticmethod
    def optimize_portfolio(holdings: List[Dict], risk_tolerance: str = 'moderate', 
                          target_return: Optional[float] = None) -> Dict:
        """
        Optimize portfolio allocation using Modern Portfolio Theory
        
        Args:
            holdings: List of current portfolio holdings
            risk_tolerance: 'conservative', 'moderate', 'aggressive'
            target_return: Target annual return (optional)
            
        Returns:
            Optimized portfolio allocation with metrics
        """
        try:
            # Generate synthetic market data for optimization
            symbols = [holding['symbol'] for holding in holdings]
            price_data = PortfolioOptimizationService._generate_price_data(symbols)
            
            # Calculate returns and covariance matrix
            returns = price_data.pct_change().dropna()
            mean_returns = returns.mean() * 252  # Annualized
            cov_matrix = returns.cov() * 252  # Annualized
            
            # Risk tolerance mapping
            risk_params = {
                'conservative': {'risk_penalty': 10, 'max_weight': 0.15},
                'moderate': {'risk_penalty': 5, 'max_weight': 0.25},
                'aggressive': {'risk_penalty': 1, 'max_weight': 0.40}
            }
            
            params = risk_params.get(risk_tolerance, risk_params['moderate'])
            
            # Optimization constraints
            n_assets = len(symbols)
            constraints = [
                {'type': 'eq', 'fun': lambda x: np.sum(x) - 1},  # Weights sum to 1
            ]
            
            # Bounds for individual weights
            bounds = tuple((0.02, params['max_weight']) for _ in range(n_assets))
            
            # Objective function (maximize Sharpe ratio or minimize risk)
            if target_return:
                # Risk minimization for target return
                def objective(weights):
                    portfolio_return = np.sum(weights * mean_returns)
                    portfolio_risk = np.sqrt(np.dot(weights.T, np.dot(cov_matrix, weights)))
                    return portfolio_risk
                
                constraints.append({
                    'type': 'eq', 
                    'fun': lambda x: np.sum(x * mean_returns) - target_return
                })
            else:
                # Sharpe ratio maximization with risk penalty
                def objective(weights):
                    portfolio_return = np.sum(weights * mean_returns)
                    portfolio_risk = np.sqrt(np.dot(weights.T, np.dot(cov_matrix, weights)))
                    risk_free_rate = 0.02  # 2% risk-free rate
                    
                    if portfolio_risk == 0:
                        return -float('inf')
                    
                    sharpe_ratio = (portfolio_return - risk_free_rate) / portfolio_risk
                    risk_penalty = params['risk_penalty'] * portfolio_risk
                    
                    return -(sharpe_ratio - risk_penalty)  # Negative for minimization
            
            # Initial guess (equal weights)
            x0 = np.array([1/n_assets] * n_assets)
            
            # Optimize
            result = minimize(
                objective, x0, method='SLSQP',
                bounds=bounds, constraints=constraints,
                options={'maxiter': 1000, 'ftol': 1e-6}
            )
            
            # If SLSQP fails, try alternative method
            if not result.success:
                result = minimize(
                    objective, x0, method='L-BFGS-B',
                    bounds=bounds,
                    options={'maxiter': 1000}
                )
                
                # Check constraints manually for L-BFGS-B
                weights_sum = np.sum(result.x)
                if abs(weights_sum - 1.0) > 0.01:  # Normalize if needed
                    result.x = result.x / weights_sum
            
            if result.success:
                optimal_weights = result.x
                
                # Calculate portfolio metrics
                portfolio_return = np.sum(optimal_weights * mean_returns)
                portfolio_risk = np.sqrt(np.dot(optimal_weights.T, np.dot(cov_matrix, optimal_weights)))
                sharpe_ratio = (portfolio_return - 0.02) / portfolio_risk if portfolio_risk > 0 else 0
                
                # Create optimized allocation
                optimized_allocation = []
                for i, symbol in enumerate(symbols):
                    optimized_allocation.append({
                        'symbol': symbol,
                        'current_weight': holdings[i].get('weight', 0),
                        'optimal_weight': round(optimal_weights[i], 4),
                        'difference': round(optimal_weights[i] - holdings[i].get('weight', 0), 4),
                        'action': 'increase' if optimal_weights[i] > holdings[i].get('weight', 0) else 'decrease'
                    })
                
                return {
                    'success': True,
                    'optimization_type': 'target_return' if target_return else 'sharpe_maximization',
                    'risk_tolerance': risk_tolerance,
                    'portfolio_metrics': {
                        'expected_return': round(portfolio_return, 4),
                        'volatility': round(portfolio_risk, 4),
                        'sharpe_ratio': round(sharpe_ratio, 4),
                        'max_drawdown': PortfolioOptimizationService._calculate_max_drawdown(
                            price_data, optimal_weights
                        )
                    },
                    'optimized_allocation': optimized_allocation,
                    'rebalancing_needed': any(
                        abs(alloc['difference']) > 0.05 for alloc in optimized_allocation
                    ),
                    'timestamp': datetime.utcnow().isoformat()
                }
            else:
                raise Exception(f"Optimization failed: {result.message}")
                
        except Exception as e:
            logger.error(f"Portfolio optimization error: {e}")
            return {
                'success': False,
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat()
            }
    
    @staticmethod
    def calculate_risk_metrics(holdings: List[Dict], timeframe_days: int = 252) -> Dict:
        """Calculate comprehensive risk metrics for portfolio"""
        try:
            symbols = [holding['symbol'] for holding in holdings]
            weights = np.array([holding.get('weight', 0) for holding in holdings])
            
            # Generate price data
            price_data = PortfolioOptimizationService._generate_price_data(symbols, timeframe_days)
            returns = price_data.pct_change().dropna()
            
            # Portfolio returns
            portfolio_returns = np.dot(returns, weights)
            
            # Value at Risk (VaR)
            var_95 = np.percentile(portfolio_returns, 5)
            var_99 = np.percentile(portfolio_returns, 1)
            
            # Conditional VaR (Expected Shortfall)
            cvar_95 = portfolio_returns[portfolio_returns <= var_95].mean()
            cvar_99 = portfolio_returns[portfolio_returns <= var_99].mean()
            
            # Other risk metrics
            volatility = portfolio_returns.std() * np.sqrt(252)
            
            # Convert to pandas Series for skew and kurtosis
            portfolio_series = pd.Series(portfolio_returns)
            skewness = portfolio_series.skew()
            kurtosis = portfolio_series.kurtosis()
            
            # Maximum Drawdown
            cumulative_returns = (1 + portfolio_returns).cumprod()
            cumulative_series = pd.Series(cumulative_returns)
            rolling_max = cumulative_series.expanding().max()
            drawdown = (cumulative_series - rolling_max) / rolling_max
            max_drawdown = drawdown.min()
            
            # Beta calculation (vs market proxy)
            market_returns = PortfolioOptimizationService._generate_market_returns(len(returns))
            beta = np.cov(portfolio_returns, market_returns)[0, 1] / np.var(market_returns)
            
            # Tracking error
            excess_returns = portfolio_returns - market_returns
            tracking_error = excess_returns.std() * np.sqrt(252)
            
            # Information ratio
            information_ratio = excess_returns.mean() / excess_returns.std() * np.sqrt(252)
            
            return {
                'success': True,
                'risk_metrics': {
                    'volatility': round(volatility, 4),
                    'var_95': round(var_95, 6),
                    'var_99': round(var_99, 6),
                    'cvar_95': round(cvar_95, 6),
                    'cvar_99': round(cvar_99, 6),
                    'max_drawdown': round(max_drawdown, 4),
                    'skewness': round(skewness, 4),
                    'kurtosis': round(kurtosis, 4),
                    'beta': round(beta, 4),
                    'tracking_error': round(tracking_error, 4),
                    'information_ratio': round(information_ratio, 4)
                },
                'risk_classification': PortfolioOptimizationService._classify_risk_level(volatility),
                'risk_warnings': PortfolioOptimizationService._generate_risk_warnings(
                    volatility, max_drawdown, var_95
                ),
                'timestamp': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Risk metrics calculation error: {e}")
            return {
                'success': False,
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat()
            }
    
    @staticmethod
    def generate_scenario_analysis(holdings: List[Dict], scenarios: List[str] = None) -> Dict:
        """Generate Monte Carlo scenario analysis for portfolio"""
        try:
            if scenarios is None:
                scenarios = ['market_crash', 'recession', 'inflation_spike', 'bull_market', 'base_case']
            
            symbols = [holding['symbol'] for holding in holdings]
            weights = np.array([holding.get('weight', 0) for holding in holdings])
            
            # Scenario parameters
            scenario_params = {
                'market_crash': {'return_factor': -0.3, 'volatility_factor': 2.0},
                'recession': {'return_factor': -0.15, 'volatility_factor': 1.5},
                'inflation_spike': {'return_factor': -0.05, 'volatility_factor': 1.2},
                'bull_market': {'return_factor': 0.25, 'volatility_factor': 0.8},
                'base_case': {'return_factor': 0.08, 'volatility_factor': 1.0}
            }
            
            scenario_results = {}
            
            for scenario in scenarios:
                params = scenario_params.get(scenario, scenario_params['base_case'])
                
                # Monte Carlo simulation
                n_simulations = 1000
                n_days = 252
                
                results = []
                for _ in range(n_simulations):
                    # Generate random returns for each asset
                    daily_returns = np.random.multivariate_normal(
                        [params['return_factor'] / 252] * len(symbols),
                        np.eye(len(symbols)) * (0.16 * params['volatility_factor'] / np.sqrt(252))**2,
                        n_days
                    )
                    
                    # Calculate portfolio returns
                    portfolio_returns = np.dot(daily_returns, weights)
                    cumulative_return = np.prod(1 + portfolio_returns) - 1
                    results.append(cumulative_return)
                
                results = np.array(results)
                
                scenario_results[scenario] = {
                    'mean_return': round(np.mean(results), 4),
                    'std_return': round(np.std(results), 4),
                    'var_95': round(np.percentile(results, 5), 4),
                    'var_99': round(np.percentile(results, 1), 4),
                    'best_case': round(np.percentile(results, 95), 4),
                    'worst_case': round(np.percentile(results, 5), 4),
                    'probability_positive': round(np.mean(results > 0), 4),
                    'probability_loss_10': round(np.mean(results < -0.1), 4)
                }
            
            return {
                'success': True,
                'scenario_analysis': scenario_results,
                'recommendations': PortfolioOptimizationService._generate_scenario_recommendations(
                    scenario_results
                ),
                'timestamp': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Scenario analysis error: {e}")
            return {
                'success': False,
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat()
            }
    
    @staticmethod
    def _generate_price_data(symbols: List[str], days: int = 252) -> Dict:
        """Generate synthetic price data for optimization"""
        # dates = pd.date_range(end=datetime.now(), periods=days, freq='D')
        
        # Temporary simple implementation without pandas
        return {}
        for symbol in symbols:
            # Generate realistic price movements
            np.random.seed(hash(symbol) % 2**32)  # Consistent seed for symbol
            returns = np.random.normal(0.0008, 0.016, days)  # Daily returns
            prices = 100 * np.cumprod(1 + returns)  # Starting at 100
            data[symbol] = prices
        
        return pd.DataFrame(data, index=dates)
    
    @staticmethod
    def _generate_market_returns(length: int) -> np.ndarray:
        """Generate synthetic market returns for beta calculation"""
        return np.random.normal(0.0006, 0.014, length)
    
    @staticmethod
    def _calculate_max_drawdown(price_data: pd.DataFrame, weights: np.ndarray) -> float:
        """Calculate maximum drawdown for optimized portfolio"""
        portfolio_prices = np.dot(price_data, weights)
        cumulative = pd.Series(portfolio_prices).cumprod()
        rolling_max = cumulative.expanding().max()
        drawdown = (cumulative - rolling_max) / rolling_max
        return round(drawdown.min(), 4)
    
    @staticmethod
    def _classify_risk_level(volatility: float) -> str:
        """Classify portfolio risk level based on volatility"""
        if volatility < 0.10:
            return 'Low Risk'
        elif volatility < 0.20:
            return 'Moderate Risk'
        elif volatility < 0.30:
            return 'High Risk'
        else:
            return 'Very High Risk'
    
    @staticmethod
    def _generate_risk_warnings(volatility: float, max_drawdown: float, var_95: float) -> List[str]:
        """Generate risk warnings based on metrics"""
        warnings = []
        
        if volatility > 0.25:
            warnings.append("Portfolio has high volatility - consider diversification")
        
        if max_drawdown < -0.20:
            warnings.append("Portfolio experienced significant drawdowns historically")
        
        if var_95 < -0.05:
            warnings.append("Portfolio has high 1-day Value at Risk")
        
        if not warnings:
            warnings.append("Portfolio risk metrics are within acceptable ranges")
        
        return warnings
    
    @staticmethod
    def _generate_scenario_recommendations(scenario_results: Dict) -> List[str]:
        """Generate recommendations based on scenario analysis"""
        recommendations = []
        
        # Check market crash scenario
        crash_loss = scenario_results.get('market_crash', {}).get('var_95', 0)
        if crash_loss < -0.25:
            recommendations.append("Consider adding defensive assets for crash protection")
        
        # Check inflation scenario
        inflation_return = scenario_results.get('inflation_spike', {}).get('mean_return', 0)
        if inflation_return < 0:
            recommendations.append("Portfolio may need inflation hedges (commodities, REITs)")
        
        # Check overall resilience
        base_case_positive = scenario_results.get('base_case', {}).get('probability_positive', 0)
        if base_case_positive < 0.6:
            recommendations.append("Portfolio shows low probability of positive returns")
        
        return recommendations if recommendations else ["Portfolio shows good resilience across scenarios"]
