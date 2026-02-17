"""
Advanced Risk Management Service
Comprehensive risk assessment, stress testing, and scenario analysis
"""

# import numpy as np
# import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional, Union, Any
import logging
from scipy import stats
from scipy.optimize import minimize
import warnings
warnings.filterwarnings('ignore')

logger = logging.getLogger(__name__)

class RiskManager:
    """Advanced risk management and analysis"""
    
    def __init__(self):
        self.confidence_levels = [0.95, 0.99, 0.999]
        self.trading_days = 252
        self.cache = {}
        
        # Risk-free rate (Norwegian 10-year government bond)
        self.risk_free_rate = 0.025
        
        # Market stress scenarios
        self.stress_scenarios = {
            'market_crash': {
                'description': '2008-style market crash',
                'equity_shock': -0.40,
                'bond_shock': -0.10,
                'commodity_shock': -0.30,
                'currency_shock': 0.15
            },
            'covid_shock': {
                'description': 'COVID-19 style shock',
                'equity_shock': -0.35,
                'bond_shock': 0.05,
                'commodity_shock': -0.25,
                'currency_shock': 0.10
            },
            'inflation_spike': {
                'description': 'High inflation scenario',
                'equity_shock': -0.15,
                'bond_shock': -0.20,
                'commodity_shock': 0.25,
                'currency_shock': -0.05
            },
            'rate_shock': {
                'description': 'Interest rate shock',
                'equity_shock': -0.20,
                'bond_shock': -0.25,
                'commodity_shock': -0.10,
                'currency_shock': 0.08
            }
        }
    
    def calculate_var(self, returns: Union[pd.Series, np.ndarray], 
                     confidence_level: float = 0.95,
                     method: str = 'historical') -> Dict[str, Union[float, str, int]]:
        """
        Calculate Value at Risk using different methods
        
        methods: 'historical', 'parametric', 'monte_carlo'
        """
        try:
            if isinstance(returns, pd.Series):
                returns_array = returns.dropna().to_numpy(dtype=np.float64)
            else:
                returns_array = np.asarray(returns[~np.isnan(returns)], dtype=np.float64)
            
            if len(returns_array) == 0:
                return {'var': 0.0, 'expected_shortfall': 0.0, 'method': method}
            
            if method == 'historical':
                var = np.percentile(returns_array, (1 - confidence_level) * 100)
                # Expected Shortfall (Conditional VaR)
                es_returns = returns_array[returns_array <= var]
                expected_shortfall = np.mean(es_returns) if len(es_returns) > 0 else var
                
            elif method == 'parametric':
                mean_return = np.mean(returns_array)
                std_return = np.std(returns_array)
                var = mean_return + stats.norm.ppf(1 - confidence_level) * std_return
                
                # Expected Shortfall for normal distribution
                phi = stats.norm.pdf(stats.norm.ppf(1 - confidence_level))
                expected_shortfall = mean_return - std_return * phi / (1 - confidence_level)
                
            elif method == 'monte_carlo':
                # Monte Carlo simulation
                mean_return = np.mean(returns_array)
                std_return = np.std(returns_array)
                
                simulated_returns = np.random.normal(mean_return, std_return, 10000)
                var = np.percentile(simulated_returns, (1 - confidence_level) * 100)
                
                es_returns = simulated_returns[simulated_returns <= var]
                expected_shortfall = np.mean(es_returns) if len(es_returns) > 0 else var
                
            else:
                raise ValueError(f"Unknown VaR method: {method}")
            
            return {
                'var': float(var),
                'expected_shortfall': float(expected_shortfall),
                'confidence_level': confidence_level,
                'method': method,
                'observations': len(returns_array)
            }
            
        except Exception as e:
            logger.error(f"Error calculating VaR: {e}")
            return {
                'var': 0.0,
                'expected_shortfall': 0.0,
                'confidence_level': confidence_level,
                'method': method,
                'error': str(e)
            }
    
    def calculate_portfolio_var(self, weights: Dict[str, float],
                              returns: pd.DataFrame,
                              confidence_level: float = 0.95,
                              time_horizon: int = 1) -> Dict:
        """Calculate portfolio VaR considering correlations"""
        try:
            assets = list(weights.keys())
            weight_array = np.array([weights[asset] for asset in assets])
            
            # Portfolio returns
            asset_returns = returns[assets].to_numpy(dtype=np.float64)
            portfolio_returns = np.dot(asset_returns, weight_array)
            
            # Scale to time horizon
            if time_horizon > 1:
                # Assuming returns are i.i.d., scale by sqrt(time)
                portfolio_returns = portfolio_returns * np.sqrt(time_horizon)
            
            # Calculate VaR using different methods
            var_results = {}
            for method in ['historical', 'parametric', 'monte_carlo']:
                var_result = self.calculate_var(portfolio_returns, confidence_level, method)
                var_results[method] = var_result
            
            # Component VaR (marginal contribution to portfolio VaR)
            component_var = self._calculate_component_var(weights, returns, confidence_level)
            
            return {
                'portfolio_var': var_results,
                'component_var': component_var,
                'time_horizon': time_horizon,
                'confidence_level': confidence_level,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error calculating portfolio VaR: {e}")
            return {'error': str(e)}
    
    def _calculate_component_var(self, weights: Dict[str, float],
                               returns: pd.DataFrame,
                               confidence_level: float) -> Dict[str, float]:
        """Calculate component VaR for each asset"""
        try:
            assets = list(weights.keys())
            weight_array = np.array([weights[asset] for asset in assets])
            
            # Portfolio returns
            portfolio_returns = np.dot(returns[assets].values, weight_array)
            
            # Portfolio VaR
            portfolio_var = self.calculate_var(portfolio_returns, confidence_level, 'historical')['var']
            
            component_vars = {}
            
            for i, asset in enumerate(assets):
                # Small perturbation
                epsilon = 0.001
                
                # Increase weight slightly
                perturbed_weights = weight_array.copy()
                perturbed_weights[i] += epsilon
                perturbed_weights = perturbed_weights / np.sum(perturbed_weights)  # Renormalize
                
                # Calculate new portfolio VaR
                perturbed_returns = np.dot(returns[assets].values, perturbed_weights)
                perturbed_var = self.calculate_var(perturbed_returns, confidence_level, 'historical')['var']
                
                # Marginal VaR
                marginal_var = (perturbed_var - portfolio_var) / epsilon
                
                # Component VaR
                component_var = weights[asset] * marginal_var
                component_vars[asset] = float(component_var)
            
            return component_vars
            
        except Exception as e:
            logger.error(f"Error calculating component VaR: {e}")
            return {}
    
    def stress_test_portfolio(self, weights: Dict[str, float],
                            returns: pd.DataFrame,
                            scenarios: Optional[List[str]] = None) -> Dict:
        """Stress test portfolio against predefined scenarios"""
        try:
            if scenarios is None:
                scenarios = list(self.stress_scenarios.keys())
            
            results = {}
            
            for scenario_name in scenarios:
                if scenario_name not in self.stress_scenarios:
                    continue
                
                scenario = self.stress_scenarios[scenario_name]
                scenario_results = self._apply_stress_scenario(weights, returns, scenario)
                results[scenario_name] = scenario_results
            
            # Custom scenarios based on historical worst periods
            historical_stress = self._historical_stress_test(weights, returns)
            results['historical_worst'] = historical_stress
            
            return {
                'stress_test_results': results,
                'portfolio_weights': weights,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error in stress testing: {e}")
            return {'error': str(e)}
    
    def _apply_stress_scenario(self, weights: Dict[str, float],
                             returns: pd.DataFrame,
                             scenario: Dict) -> Dict:
        """Apply stress scenario to portfolio"""
        try:
            stressed_returns = {}
            
            for asset in weights.keys():
                # Classify asset type (simplified)
                asset_type = self._classify_asset_type(asset)
                
                # Apply appropriate shock
                shock = 0.0
                if asset_type == 'equity':
                    shock = scenario.get('equity_shock', 0.0)
                elif asset_type == 'bond':
                    shock = scenario.get('bond_shock', 0.0)
                elif asset_type == 'commodity':
                    shock = scenario.get('commodity_shock', 0.0)
                elif asset_type == 'currency':
                    shock = scenario.get('currency_shock', 0.0)
                
                stressed_returns[asset] = shock
            
            # Calculate portfolio impact
            portfolio_impact = sum(weights[asset] * stressed_returns[asset] 
                                 for asset in weights.keys())
            
            return {
                'portfolio_impact': float(portfolio_impact),
                'asset_impacts': stressed_returns,
                'description': scenario.get('description', 'Custom scenario')
            }
            
        except Exception as e:
            logger.error(f"Error applying stress scenario: {e}")
            return {'portfolio_impact': 0.0, 'error': str(e)}
    
    def _classify_asset_type(self, asset: str) -> str:
        """Classify asset type for stress testing"""
        asset_upper = asset.upper()
        
        # Norwegian stocks
        if '.OL' in asset_upper:
            return 'equity'
        
        # Common equity symbols
        equity_symbols = ['AAPL', 'GOOGL', 'MSFT', 'TSLA', 'AMZN', 'META', 'NVDA']
        if any(symbol in asset_upper for symbol in equity_symbols):
            return 'equity'
        
        # Bond-related
        if any(term in asset_upper for term in ['BOND', 'TREASURY', 'GILT']):
            return 'bond'
        
        # Commodities
        if any(term in asset_upper for term in ['GOLD', 'OIL', 'SILVER', 'COPPER']):
            return 'commodity'
        
        # Currencies
        if any(term in asset_upper for term in ['USD', 'EUR', 'NOK', 'GBP', 'JPY']):
            return 'currency'
        
        # Default to equity
        return 'equity'
    
    def _historical_stress_test(self, weights: Dict[str, float],
                              returns: pd.DataFrame) -> Dict:
        """Find and apply historical worst-case scenario"""
        try:
            assets = list(weights.keys())
            weight_array = np.array([weights[asset] for asset in assets])
            
            # Calculate portfolio returns
            portfolio_returns = np.dot(returns[assets].to_numpy(dtype=np.float64), weight_array)
            
            # Find worst historical periods
            worst_day = np.min(portfolio_returns)
            worst_week = np.min(pd.Series(portfolio_returns).rolling(5).sum())
            worst_month = np.min(pd.Series(portfolio_returns).rolling(20).sum())
            
            return {
                'worst_day': float(worst_day),
                'worst_week': float(worst_week),
                'worst_month': float(worst_month),
                'description': 'Historical worst-case scenario'
            }
            
        except Exception as e:
            logger.error(f"Error in historical stress test: {e}")
            return {'error': str(e)}
    
    def calculate_risk_metrics(self, returns: Union[pd.Series, np.ndarray]) -> Dict[str, Union[float, str, Dict[str, Union[float, str]]]]:
        """Calculate comprehensive risk metrics"""
        try:
            if isinstance(returns, pd.Series):
                returns_array = returns.dropna().to_numpy(dtype=np.float64)
            else:
                returns_array = np.asarray(returns[~np.isnan(returns)], dtype=np.float64)
            
            if len(returns_array) == 0:
                return {'error': 'No valid returns data'}
            
            # Basic statistics
            returns_np = np.asarray(returns_array, dtype=np.float64)
            mean_return = np.mean(returns_np)
            std_return = np.std(returns_np)
            skewness = stats.skew(returns_array)
            kurtosis = stats.kurtosis(returns_array)
            
            # Annualized metrics
            annual_return = mean_return * self.trading_days
            annual_volatility = std_return * np.sqrt(self.trading_days)
            
            # Risk-adjusted returns
            sharpe_ratio = (annual_return - self.risk_free_rate) / annual_volatility if annual_volatility > 0 else 0
            
            # Downside risk
            returns_np = np.asarray(returns_array, dtype=np.float64)
            downside_returns = returns_np[returns_np < 0]
            downside_deviation = np.sqrt(np.mean(downside_returns ** 2)) * np.sqrt(self.trading_days) if len(downside_returns) > 0 else 0
            sortino_ratio = (annual_return - self.risk_free_rate) / downside_deviation if downside_deviation > 0 else 0
            
            # Maximum drawdown
            cumulative_returns = np.cumprod(1 + returns_np)
            running_max = np.maximum.accumulate(cumulative_returns)
            drawdowns = (cumulative_returns - running_max) / running_max
            max_drawdown = np.min(drawdowns)
            
            # Calmar ratio
            calmar_ratio = annual_return / abs(max_drawdown) if max_drawdown != 0 else 0
            
            # VaR calculations
            var_95 = self.calculate_var(returns_array, 0.95, 'historical')
            var_99 = self.calculate_var(returns_array, 0.99, 'historical')
            
            # Tail ratio
            gains = returns_array[returns_array > 0]
            losses = returns_array[returns_array < 0]
            
            avg_gain = np.mean(gains) if len(gains) > 0 else 0
            avg_loss = np.mean(losses) if len(losses) > 0 else 0
            tail_ratio = abs(avg_gain / avg_loss) if avg_loss != 0 else 0
            
            # Hit ratio
            hit_ratio = len(gains) / len(returns_array) if len(returns_array) > 0 else 0
            
            return {
                'annual_return': float(annual_return),
                'annual_volatility': float(annual_volatility),
                'sharpe_ratio': float(sharpe_ratio),
                'sortino_ratio': float(sortino_ratio),
                'calmar_ratio': float(calmar_ratio),
                'max_drawdown': float(max_drawdown),
                'skewness': float(skewness),
                'kurtosis': float(kurtosis),
                'var_95': var_95,
                'var_99': var_99,
                'tail_ratio': float(tail_ratio),
                'hit_ratio': float(hit_ratio),
                'downside_deviation': float(downside_deviation),
                'observations': len(returns_array),
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error calculating risk metrics: {e}")
            return {'error': str(e)}
    
    def portfolio_risk_decomposition(self, weights: Dict[str, float],
                                   returns: pd.DataFrame) -> Dict:
        """Decompose portfolio risk into various components"""
        try:
            assets = list(weights.keys())
            weight_array = np.array([weights[asset] for asset in assets])
            cov_matrix = returns[assets].cov().to_numpy(dtype=np.float64) * self.trading_days
            # Covariance matrix
            cov_matrix = returns[assets].cov().values * self.trading_days
            
            # Portfolio variance
            portfolio_variance = np.dot(weight_array.T, np.dot(cov_matrix, weight_array))
            portfolio_volatility = np.sqrt(portfolio_variance)
            
            # Risk decomposition
            risk_decomposition = {}
            
            for i, asset in enumerate(assets):
                # Marginal contribution to risk
                marginal_contrib = np.dot(cov_matrix[i], weight_array) / portfolio_volatility
                
                # Component contribution to risk
                component_contrib = weights[asset] * marginal_contrib
                
                # Percentage contribution
                percent_contrib = component_contrib / portfolio_volatility
                
                risk_decomposition[asset] = {
                    'weight': float(weights[asset]),
                    'marginal_contrib': float(marginal_contrib),
                    'component_contrib': float(component_contrib),
                    'percent_contrib': float(percent_contrib),
                    'asset_volatility': float(np.sqrt(cov_matrix[i, i]))
                }
            
            # Diversification ratio
            weighted_avg_vol = sum(weights[asset] * np.sqrt(cov_matrix[i, i]) 
                                 for i, asset in enumerate(assets))
            diversification_ratio = weighted_avg_vol / portfolio_volatility
            
            return {
                'portfolio_volatility': float(portfolio_volatility),
                'risk_decomposition': risk_decomposition,
                'diversification_ratio': float(diversification_ratio),
                'concentration_risk': self._calculate_concentration_risk(weights),
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error in risk decomposition: {e}")
            return {'error': str(e)}
    
    def _calculate_concentration_risk(self, weights: Dict[str, float]) -> Dict:
        """Calculate concentration risk metrics"""
        try:
            weight_values = list(weights.values())
            
            # Herfindahl-Hirschman Index
            hhi = sum(w ** 2 for w in weight_values)
            
            # Effective number of positions
            effective_positions = 1 / hhi if hhi > 0 else 0
            
            # Maximum weight
            max_weight = max(weight_values) if weight_values else 0
            
            # Weight concentration in top positions
            sorted_weights = sorted(weight_values, reverse=True)
            top_3_concentration = sum(sorted_weights[:3]) if len(sorted_weights) >= 3 else sum(sorted_weights)
            top_5_concentration = sum(sorted_weights[:5]) if len(sorted_weights) >= 5 else sum(sorted_weights)
            
            return {
                'hhi': float(hhi),
                'effective_positions': float(effective_positions),
                'max_weight': float(max_weight),
                'top_3_concentration': float(top_3_concentration),
                'top_5_concentration': float(top_5_concentration),
                'total_positions': len(weights)
            }
            
        except Exception as e:
            logger.error(f"Error calculating concentration risk: {e}")
            return {}
    
    def scenario_analysis(self, weights: Dict[str, float],
                         returns: pd.DataFrame,
                         custom_scenarios: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
        """Comprehensive scenario analysis"""
        try:
            results = {}
            
            # Base case (current portfolio)
            portfolio_returns = np.dot(returns[list(weights.keys())].values, 
                                     np.array(list(weights.values())))
            base_metrics = self.calculate_risk_metrics(portfolio_returns)
            results['base_case'] = base_metrics
            
            # Stress scenarios
            stress_results = self.stress_test_portfolio(weights, returns)
            results['stress_scenarios'] = stress_results.get('stress_test_results', {})
            
            # Custom scenarios
            if custom_scenarios:
                custom_results = {}
                for scenario in custom_scenarios:
                    scenario_result = self._apply_custom_scenario(weights, returns, scenario)
                    custom_results[scenario.get('name', 'custom')] = scenario_result
                results['custom_scenarios'] = custom_results
            
            # Monte Carlo scenarios
            mc_scenarios = self._monte_carlo_scenarios(weights, returns)
            results['monte_carlo'] = mc_scenarios
            
            return {
                'scenario_analysis': results,
                'summary': self._summarize_scenarios(results),
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error in scenario analysis: {e}")
            return {'error': str(e)}
    
    def _apply_custom_scenario(self, weights: Dict[str, float],
                             returns: pd.DataFrame,
                             scenario: Dict) -> Dict:
        """Apply custom scenario"""
        try:
            # Scenario should have 'shocks' dict with asset: shock_percent
            shocks = scenario.get('shocks', {})
            
            portfolio_impact = sum(weights.get(asset, 0) * shocks.get(asset, 0) 
                                 for asset in weights.keys())
            
            return {
                'portfolio_impact': float(portfolio_impact),
                'description': scenario.get('description', 'Custom scenario'),
                'shocks': shocks
            }
            
        except Exception as e:
            logger.error(f"Error applying custom scenario: {e}")
            return {'error': str(e)}
    
    def _monte_carlo_scenarios(self, weights: Dict[str, float],
                             returns: pd.DataFrame,
                             num_scenarios: int = 1000) -> Dict:
        """Generate Monte Carlo scenarios"""
        try:
            assets = list(weights.keys())
            weight_array = np.array([weights[asset] for asset in assets])
            mean_returns = returns[assets].mean().to_numpy(dtype=np.float64)
            # Calculate historical means and covariance
            mean_returns = returns[assets].mean().values
            cov_matrix = returns[assets].cov().values
            
            # Generate random scenarios
            scenario_returns = np.random.multivariate_normal(
                mean_returns, cov_matrix, num_scenarios
            )
            
            # Calculate portfolio returns for each scenario
            portfolio_scenarios = np.dot(scenario_returns, weight_array)
            
            # Statistics
            percentiles = [1, 5, 10, 25, 50, 75, 90, 95, 99]
            scenario_percentiles = np.percentile(portfolio_scenarios, percentiles)
            
            return {
                'num_scenarios': num_scenarios,
                'percentiles': dict(zip(percentiles, scenario_percentiles.tolist())),
                'mean': float(np.mean(portfolio_scenarios)),
                'std': float(np.std(portfolio_scenarios)),
                'min': float(np.min(portfolio_scenarios)),
                'max': float(np.max(portfolio_scenarios))
            }
            
        except Exception as e:
            logger.error(f"Error in Monte Carlo scenarios: {e}")
            return {'error': str(e)}
    
    def _summarize_scenarios(self, results: Dict) -> Dict:
        """Summarize scenario analysis results"""
        try:
            summary = {
                'worst_case': {'scenario': 'Unknown', 'impact': 0.0},
                'best_case': {'scenario': 'Unknown', 'impact': 0.0},
                'risk_level': 'Medium'
            }
            
            # Find worst and best scenarios
            all_impacts = []
            
            # Stress scenarios
            for scenario_name, scenario_data in results.get('stress_scenarios', {}).items():
                impact = scenario_data.get('portfolio_impact', 0.0)
                all_impacts.append((scenario_name, impact))
            
            if all_impacts:
                worst = min(all_impacts, key=lambda x: x[1])
                best = max(all_impacts, key=lambda x: x[1])
                
                summary['worst_case'] = {'scenario': worst[0], 'impact': worst[1]}
                summary['best_case'] = {'scenario': best[0], 'impact': best[1]}
                
                # Risk level assessment
                if worst[1] < -0.30:
                    summary['risk_level'] = 'High'
                elif worst[1] < -0.15:
                    summary['risk_level'] = 'Medium'
                else:
                    summary['risk_level'] = 'Low'
            
            return summary
            
        except Exception as e:
            logger.error(f"Error summarizing scenarios: {e}")
            return {'error': str(e)}

# Global instance
risk_manager = RiskManager()
