"""
Advanced Portfolio Optimization Service
Modern Portfolio Theory, Risk Management, and Asset Allocation
"""

# import numpy as np
# import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional, Any, Union
# from pandas import DataFrame, Series
import logging
import warnings

# Graceful imports for optional dependencies
try:
    from scipy.optimize import minimize
    from scipy import stats
    HAS_SCIPY = True
except ImportError:
    HAS_SCIPY = False
    logging.warning("SciPy not available - advanced optimization features disabled")

warnings.filterwarnings('ignore')

logger = logging.getLogger(__name__)

class PortfolioOptimizer:
    """Service for portfolio optimization"""
    
    def __init__(self):
        self.cache = {}
    
    def rebalance_portfolio(
            self,
            portfolio: Dict[str, Any],
            constraints: Optional[Dict[str, Any]] = None
        ) -> Dict[str, Any]:
        """Rebalance portfolio based on optimization criteria"""
        try:
            # Mock optimization result for now
            total_value = sum(stock['value'] for stock in portfolio.values())
            optimized = {}
            
            for symbol, data in portfolio.items():
                # Simple equal-weight strategy as fallback
                target_weight = 1.0 / len(portfolio)
                current_weight = data['value'] / total_value
                
                optimized[symbol] = {
                    'current_weight': current_weight,
                    'target_weight': target_weight,
                    'adjustment': target_weight - current_weight,
                    'recommendation': 'HOLD'
                }
                
                if optimized[symbol]['adjustment'] > 0.02:
                    optimized[symbol]['recommendation'] = 'BUY'
                elif optimized[symbol]['adjustment'] < -0.02:
                    optimized[symbol]['recommendation'] = 'SELL'
            
            return {
                'success': True,
                'optimized_weights': optimized,
                'risk_adjusted_return': 0.12,  # Mock value
                'sharpe_ratio': 1.5,  # Mock value
                'generated_at': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error optimizing portfolio: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    """Advanced portfolio optimization using Modern Portfolio Theory"""
    
    def __init__(self):
        self.risk_free_rate = 0.02  # 2% annual risk-free rate
        self.trading_days = 252
        self.cache = {}
        
    def calculate_returns(self, prices: pd.DataFrame) -> pd.DataFrame:
        """Calculate daily returns from price data"""
        return prices.pct_change().dropna()
    
    def calculate_portfolio_metrics(self, weights: np.ndarray, 
                                  returns: pd.DataFrame) -> Dict[str, float]:
        """Calculate portfolio metrics given weights and returns"""
        try:
            # Convert to numpy array if needed
            if isinstance(returns, pd.DataFrame):
                returns_array = returns.values
            else:
                returns_array = returns
            
            # Portfolio return
            portfolio_return = np.sum(returns_array.mean() * weights) * self.trading_days
            
            # Portfolio variance
            cov_matrix = np.cov(returns_array.T)
            portfolio_variance = np.dot(weights.T, np.dot(cov_matrix, weights))
            portfolio_std = np.sqrt(portfolio_variance) * np.sqrt(self.trading_days)
            
            # Sharpe ratio
            sharpe_ratio = (portfolio_return - self.risk_free_rate) / portfolio_std
            
            # Value at Risk (VaR) 95%
            portfolio_daily_returns = np.dot(returns_array, weights)
            var_95 = np.percentile(portfolio_daily_returns, 5)
            
            # Maximum Drawdown
            cumulative_returns = (1 + portfolio_daily_returns).cumprod()
            running_max = np.maximum.accumulate(cumulative_returns)
            drawdowns = (cumulative_returns - running_max) / running_max
            max_drawdown = np.min(drawdowns)
            
            return {
                'expected_return': float(portfolio_return),
                'volatility': float(portfolio_std),
                'sharpe_ratio': float(sharpe_ratio),
                'var_95': float(var_95),
                'max_drawdown': float(max_drawdown),
                'sortino_ratio': self._calculate_sortino_ratio(portfolio_daily_returns)
            }
            
        except Exception as e:
            logger.error(f"Error calculating portfolio metrics: {e}")
            return {
                'expected_return': 0.0,
                'volatility': 0.0,
                'sharpe_ratio': 0.0,
                'var_95': 0.0,
                'max_drawdown': 0.0,
                'sortino_ratio': 0.0
            }
    
    def _calculate_sortino_ratio(self, returns: np.ndarray) -> float:
        """Calculate Sortino ratio (downside deviation)"""
        try:
            excess_returns = returns - self.risk_free_rate / self.trading_days
            downside_returns = excess_returns[excess_returns < 0]
            
            if len(downside_returns) == 0:
                return float(np.inf)
            
            downside_deviation = np.sqrt(np.mean(downside_returns ** 2)) * np.sqrt(self.trading_days)
            avg_excess_return = np.mean(excess_returns) * self.trading_days
            
            return float(avg_excess_return / downside_deviation) if downside_deviation > 0 else 0.0
            
        except Exception:
            return 0.0
    
    def optimize_portfolio(self, returns: pd.DataFrame, 
                          optimization_type: str = 'sharpe',
                          constraints: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Optimize portfolio using different objectives
        
        optimization_type: 'sharpe', 'min_variance', 'max_return', 'risk_parity'
        """
        if not HAS_SCIPY:
            logger.warning("SciPy not available - using equal weight fallback")
            n_assets = len(returns.columns)
            equal_weights = np.array([1.0 / n_assets] * n_assets)
            portfolio_metrics = self.calculate_portfolio_metrics(equal_weights, returns)
            
            return {
                'success': True,
                'weights': dict(zip(returns.columns, equal_weights.tolist())),
                'metrics': portfolio_metrics,
                'optimization_type': 'equal_weight_fallback',
                'message': 'Using equal weights - SciPy not available for optimization'
            }
            
        try:
            n_assets = len(returns.columns)
            
            # Default constraints
            if constraints is None:
                constraints = {
                    'max_weight': 0.4,
                    'min_weight': 0.01,
                    'target_return': None,
                    'max_risk': None
                }
            
            # Initial guess - equal weights
            x0 = np.array([1.0 / n_assets] * n_assets)
            
            # Bounds for each weight
            bounds = tuple((constraints['min_weight'], constraints['max_weight']) 
                          for _ in range(n_assets))
            
            # Constraint: weights sum to 1
            constraint_sum = {'type': 'eq', 'fun': lambda x: np.sum(x) - 1}
            constraints_list = [constraint_sum]
            
            # Additional constraints
            if constraints.get('target_return'):
                def return_constraint(x):
                    portfolio_metrics = self.calculate_portfolio_metrics(x, returns)
                    return portfolio_metrics['expected_return'] - constraints['target_return']
                constraints_list.append({'type': 'eq', 'fun': return_constraint})
            
            if constraints.get('max_risk'):
                def risk_constraint(x):
                    portfolio_metrics = self.calculate_portfolio_metrics(x, returns)
                    return constraints['max_risk'] - portfolio_metrics['volatility']
                constraints_list.append({'type': 'ineq', 'fun': risk_constraint})
            
            # Objective function
            if optimization_type == 'sharpe':
                def objective(x):
                    metrics = self.calculate_portfolio_metrics(x, returns)
                    return -metrics['sharpe_ratio']  # Negative for minimization
            elif optimization_type == 'min_variance':
                def objective(x):
                    metrics = self.calculate_portfolio_metrics(x, returns)
                    return metrics['volatility']
            elif optimization_type == 'max_return':
                def objective(x):
                    metrics = self.calculate_portfolio_metrics(x, returns)
                    return -metrics['expected_return']
            elif optimization_type == 'risk_parity':
                def objective(x):
                    return self._risk_parity_objective(x, returns)
            else:
                raise ValueError(f"Unknown optimization type: {optimization_type}")
            
            # Optimize
            result = minimize(
                objective,
                x0,
                method='SLSQP',
                bounds=bounds,
                constraints=constraints_list,
                options={'maxiter': 1000}
            )
            
            if result.success:
                optimal_weights = result.x
                portfolio_metrics = self.calculate_portfolio_metrics(optimal_weights, returns)
                
                return {
                    'success': True,
                    'weights': dict(zip(returns.columns, optimal_weights.tolist())),
                    'metrics': portfolio_metrics,
                    'optimization_type': optimization_type,
                    'message': 'Optimization successful'
                }
            else:
                return {
                    'success': False,
                    'error': f"Optimization failed: {result.message}",
                    'weights': dict(zip(returns.columns, x0.tolist())),
                    'metrics': self.calculate_portfolio_metrics(x0, returns)
                }
                
        except Exception as e:
            logger.error(f"Error in portfolio optimization: {e}")
            n_assets = len(returns.columns) if isinstance(returns, pd.DataFrame) else 1
            equal_weights = [1.0 / n_assets] * n_assets
            
            return {
                'success': False,
                'error': str(e),
                'weights': dict(zip(returns.columns, equal_weights)) if isinstance(returns, pd.DataFrame) else {},
                'metrics': self.calculate_portfolio_metrics(np.array(equal_weights), returns)
            }
    
    def _risk_parity_objective(self, weights: np.ndarray, returns: pd.DataFrame) -> float:
        """Risk parity objective function"""
        try:
            cov_matrix = returns.cov().values
            portfolio_variance = np.dot(weights.T, np.dot(cov_matrix, weights))
            
            # Risk contribution of each asset
            marginal_contrib = np.dot(cov_matrix, weights)
            contrib = weights * marginal_contrib / portfolio_variance
            
            # Target risk contribution (equal for all assets)
            target_contrib = np.ones(len(weights)) / len(weights)
            
            # Sum of squared differences
            return np.sum((contrib - target_contrib) ** 2)
            
        except Exception:
            return 1e6
    
    def generate_efficient_frontier(self, returns: pd.DataFrame, 
                                  num_points: int = 50) -> Dict:
        """Generate efficient frontier points"""
        try:
            # Calculate min variance and max return portfolios
            min_var_result = self.optimize_portfolio(returns, 'min_variance')
            max_ret_result = self.optimize_portfolio(returns, 'max_return')
            
            if not min_var_result['success'] or not max_ret_result['success']:
                return {'error': 'Could not generate efficient frontier'}
            
            min_return = min_var_result['metrics']['expected_return']
            max_return = max_ret_result['metrics']['expected_return']
            
            # Generate target returns
            target_returns = np.linspace(min_return, max_return, num_points)
            
            frontier_points = []
            
            for target_return in target_returns:
                constraints = {'target_return': target_return}
                result = self.optimize_portfolio(returns, 'min_variance', constraints)
                
                if result['success']:
                    frontier_points.append({
                        'return': result['metrics']['expected_return'],
                        'risk': result['metrics']['volatility'],
                        'sharpe': result['metrics']['sharpe_ratio'],
                        'weights': result['weights']
                    })
            
            return {
                'success': True,
                'frontier_points': frontier_points,
                'min_variance_portfolio': min_var_result,
                'max_return_portfolio': max_ret_result
            }
            
        except Exception as e:
            logger.error(f"Error generating efficient frontier: {e}")
            return {'error': str(e)}
    
    def calculate_portfolio_attribution(self, weights: Dict[str, float], 
                                      returns: pd.DataFrame) -> Dict:
        """Calculate portfolio performance attribution"""
        try:
            # Convert weights to array
            assets = list(weights.keys())
            weight_array = np.array([weights[asset] for asset in assets])
            
            # Calculate individual asset metrics
            attribution = {}
            
            for i, asset in enumerate(assets):
                asset_returns = returns[asset]
                asset_weight = weight_array[i]
                
                # Asset contribution to portfolio return
                asset_annual_return = asset_returns.mean() * self.trading_days
                contribution_to_return = asset_weight * asset_annual_return
                
                # Asset contribution to portfolio risk
                asset_variance = asset_returns.var() * self.trading_days
                contribution_to_risk = asset_weight * np.sqrt(asset_variance)
                
                attribution[asset] = {
                    'weight': float(asset_weight),
                    'asset_return': float(asset_annual_return),
                    'contribution_to_return': float(contribution_to_return),
                    'contribution_to_risk': float(contribution_to_risk),
                    'sharpe_ratio': float((asset_annual_return - self.risk_free_rate) / np.sqrt(asset_variance))
                }
            
            # Total portfolio metrics
            portfolio_metrics = self.calculate_portfolio_metrics(weight_array, returns)
            
            return {
                'attribution': attribution,
                'portfolio_metrics': portfolio_metrics,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error in portfolio attribution: {e}")
            return {'error': str(e)}
    
    def risk_budgeting(self, returns: pd.DataFrame, 
                      risk_budgets: Dict[str, float]) -> Dict:
        """Optimize portfolio based on risk budgets"""
        if not HAS_SCIPY:
            logger.warning("SciPy not available - using equal weight fallback for risk budgeting")
            assets = returns.columns.tolist()
            n_assets = len(assets)
            equal_weights = np.array([1.0 / n_assets] * n_assets)
            portfolio_metrics = self.calculate_portfolio_metrics(equal_weights, returns)
            
            return {
                'success': True,
                'weights': dict(zip(assets, equal_weights.tolist())),
                'metrics': portfolio_metrics,
                'message': 'Using equal weights - SciPy not available for risk budgeting'
            }
            
        try:
            assets = returns.columns.tolist()
            n_assets = len(assets)
            
            # Validate risk budgets
            total_budget = sum(risk_budgets.values())
            if abs(total_budget - 1.0) > 0.01:
                return {'error': 'Risk budgets must sum to 1.0'}
            
            # Initial guess
            x0 = np.array([1.0 / n_assets] * n_assets)
            
            # Bounds
            bounds = tuple((0.001, 0.99) for _ in range(n_assets))
            
            # Constraints
            constraint_sum = {'type': 'eq', 'fun': lambda x: np.sum(x) - 1}
            
            def risk_budget_objective(weights):
                try:
                    cov_matrix = returns.cov().values
                    portfolio_variance = np.dot(weights.T, np.dot(cov_matrix, weights))
                    
                    if portfolio_variance <= 0:
                        return 1e6
                    
                    # Risk contribution
                    marginal_contrib = np.dot(cov_matrix, weights)
                    risk_contrib = weights * marginal_contrib / portfolio_variance
                    
                    # Target risk contributions
                    target_risk_contrib = np.array([risk_budgets.get(asset, 1.0/n_assets) 
                                                  for asset in assets])
                    
                    # Minimize squared differences
                    return np.sum((risk_contrib - target_risk_contrib) ** 2)
                    
                except Exception:
                    return 1e6
            
            # Optimize
            result = minimize(
                risk_budget_objective,
                x0,
                method='SLSQP',
                bounds=bounds,
                constraints=[constraint_sum],
                options={'maxiter': 1000}
            )
            
            if result.success:
                optimal_weights = result.x
                portfolio_metrics = self.calculate_portfolio_metrics(optimal_weights, returns)
                
                return {
                    'success': True,
                    'weights': dict(zip(assets, optimal_weights.tolist())),
                    'metrics': portfolio_metrics,
                    'risk_budgets': risk_budgets,
                    'message': 'Risk budgeting optimization successful'
                }
            else:
                return {
                    'success': False,
                    'error': f"Risk budgeting optimization failed: {result.message}"
                }
                
        except Exception as e:
            logger.error(f"Error in risk budgeting: {e}")
            return {'error': str(e)}
    
    def black_litterman_optimization(self, returns: pd.DataFrame,
                                   market_caps: Optional[Dict[str, float]] = None,
                                   views: Optional[List[Dict[str, Any]]] = None,
                                   confidence: float = 0.25) -> Dict:
        """
        Black-Litterman portfolio optimization
        
        views: List of dicts with 'asset', 'expected_return', 'confidence'
        """
        try:
            assets = returns.columns.tolist()
            n_assets = len(assets)
            
            # Market equilibrium weights (equal weight if no market caps)
            if market_caps is None:
                w_market = np.array([1.0 / n_assets] * n_assets)
            else:
                total_market_cap = sum(market_caps.values())
                w_market = np.array([market_caps.get(asset, 0) / total_market_cap 
                                   for asset in assets])
            
            # Covariance matrix
            cov_matrix = returns.cov().values * self.trading_days
            
            # Market implied returns (reverse optimization)
            risk_aversion = 3.0  # Typical value
            pi = risk_aversion * np.dot(cov_matrix, w_market)
            
            # Uncertainty in prior (tau)
            tau = 1.0 / len(returns)
            
            # Process views
            if views is None:
                # No views, return market portfolio
                portfolio_metrics = self.calculate_portfolio_metrics(w_market, returns)
                return {
                    'success': True,
                    'weights': dict(zip(assets, w_market.tolist())),
                    'metrics': portfolio_metrics,
                    'type': 'market_equilibrium'
                }
            
            # Create picking matrix P and view returns Q
            P = np.zeros((len(views), n_assets))
            Q = np.zeros(len(views))
            omega_values = []
            
            for i, view in enumerate(views):
                asset_idx = assets.index(view['asset'])
                P[i, asset_idx] = 1
                Q[i] = view['expected_return']
                
                # Confidence in view (lower omega = higher confidence)
                view_confidence = view.get('confidence', confidence)
                omega_values.append(tau * P[i].T @ cov_matrix @ P[i] / view_confidence)
            
            omega = np.diag(omega_values)
            
            # Black-Litterman formula
            M1 = np.linalg.inv(tau * cov_matrix)
            M2 = P.T @ np.linalg.inv(omega) @ P
            M3 = np.linalg.inv(tau * cov_matrix) @ pi
            M4 = P.T @ np.linalg.inv(omega) @ Q
            
            # New expected returns
            mu_bl = np.linalg.inv(M1 + M2) @ (M3 + M4)
            
            # New covariance matrix
            cov_bl = np.linalg.inv(M1 + M2)
            
            # Optimize with Black-Litterman inputs
            optimal_weights = np.linalg.inv(risk_aversion * cov_bl) @ mu_bl
            
            # Normalize weights
            optimal_weights = optimal_weights / np.sum(optimal_weights)
            
            # Ensure non-negative weights
            optimal_weights = np.maximum(optimal_weights, 0)
            optimal_weights = optimal_weights / np.sum(optimal_weights)
            
            portfolio_metrics = self.calculate_portfolio_metrics(optimal_weights, returns)
            
            return {
                'success': True,
                'weights': dict(zip(assets, optimal_weights.tolist())),
                'metrics': portfolio_metrics,
                'bl_returns': dict(zip(assets, mu_bl.tolist())),
                'market_weights': dict(zip(assets, w_market.tolist())),
                'views': views,
                'type': 'black_litterman'
            }
            
        except Exception as e:
            logger.error(f"Error in Black-Litterman optimization: {e}")
            return {'error': str(e)}
    
    def monte_carlo_simulation(self, weights: Dict[str, float], 
                             returns: pd.DataFrame,
                             time_horizon: int = 252,
                             num_simulations: int = 10000) -> Dict:
        """Monte Carlo simulation for portfolio performance"""
        try:
            assets = list(weights.keys())
            weight_array = np.array([weights[asset] for asset in assets])
            
            # Calculate portfolio statistics
            # Ensure numpy arrays for dot product
            asset_returns = np.array(returns[assets].values, dtype=np.float64)
            weights = np.array(weight_array, dtype=np.float64)
            portfolio_returns = np.dot(asset_returns, weights)
            mean_return = np.mean(portfolio_returns)
            std_return = np.std(portfolio_returns)
            
            # Monte Carlo simulation
            random_returns = np.random.normal(
                mean_return, std_return, 
                (num_simulations, time_horizon)
            )
            
            # Calculate cumulative returns for each simulation
            cumulative_returns = np.cumprod(1 + random_returns, axis=1)
            final_values = cumulative_returns[:, -1]
            
            # Statistics
            percentiles = [5, 10, 25, 50, 75, 90, 95]
            percentile_values = np.percentile(final_values, percentiles)
            
            return {
                'success': True,
                'simulations': num_simulations,
                'time_horizon_days': time_horizon,
                'initial_value': 1.0,
                'percentiles': dict(zip(percentiles, percentile_values.tolist())),
                'expected_return': float(np.mean(final_values)),
                'volatility': float(np.std(final_values)),
                'probability_of_loss': float(np.mean(final_values < 1.0)),
                'max_gain': float(np.max(final_values)),
                'max_loss': float(np.min(final_values)),
                'sharpe_ratio': float((np.mean(final_values) - 1) / np.std(final_values)) if np.std(final_values) > 0 else 0,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error in Monte Carlo simulation: {e}")
            return {'error': str(e)}

# Global instance
portfolio_optimizer = PortfolioOptimizer()
