"""
Professional Risk Management Calculator for CMC Markets-style MT4 functionality
Advanced position sizing, risk metrics, and portfolio risk management
"""

import math
from typing import Dict, List, Tuple, Optional, Any
from datetime import datetime, timedelta
import numpy as np
from dataclasses import dataclass

@dataclass
class RiskProfile:
    """Risk profile configuration"""
    max_risk_per_trade: float = 2.0  # % of account
    max_portfolio_risk: float = 20.0  # % of account
    max_correlation_exposure: float = 10.0  # % to correlated assets
    max_sector_exposure: float = 15.0  # % to single sector
    risk_free_rate: float = 2.5  # % annual risk-free rate

class RiskCalculator:
    """Professional risk management calculator"""
    
    def __init__(self, account_balance: float, risk_profile: RiskProfile = None):
        self.account_balance = account_balance
        self.risk_profile = risk_profile or RiskProfile()
        self.positions = []
        self.historical_returns = {}
        
    def calculate_position_size(self, entry_price: float, stop_loss_price: float,
                               risk_percentage: float = None) -> Dict[str, Any]:
        """Calculate optimal position size based on risk parameters"""
        
        if risk_percentage is None:
            risk_percentage = self.risk_profile.max_risk_per_trade
            
        risk_amount = self.account_balance * (risk_percentage / 100)
        price_risk = abs(entry_price - stop_loss_price)
        
        if price_risk == 0:
            return {
                'position_size': 0,
                'error': 'Stop loss cannot equal entry price'
            }
            
        position_size = math.floor(risk_amount / price_risk)
        actual_risk_amount = position_size * price_risk
        actual_risk_percentage = (actual_risk_amount / self.account_balance) * 100
        
        return {
            'position_size': position_size,
            'position_value': position_size * entry_price,
            'risk_amount': actual_risk_amount,
            'risk_percentage': actual_risk_percentage,
            'price_risk_per_share': price_risk,
            'shares_per_percent_risk': risk_amount / price_risk,
            'recommendation': self._get_position_recommendation(actual_risk_percentage)
        }
        
    def calculate_stop_loss_levels(self, entry_price: float, volatility: float = None,
                                  atr: float = None, support_resistance: List[float] = None) -> Dict[str, float]:
        """Calculate multiple stop loss levels using different methods"""
        
        stop_levels = {}
        
        # Percentage-based stop loss (2-5% typical)
        stop_levels['percentage_2pct'] = entry_price * 0.98
        stop_levels['percentage_3pct'] = entry_price * 0.97
        stop_levels['percentage_5pct'] = entry_price * 0.95
        
        # ATR-based stop loss
        if atr:
            stop_levels['atr_1x'] = entry_price - atr
            stop_levels['atr_1_5x'] = entry_price - (atr * 1.5)
            stop_levels['atr_2x'] = entry_price - (atr * 2.0)
            
        # Volatility-based stop loss
        if volatility:
            stop_levels['volatility_1std'] = entry_price - volatility
            stop_levels['volatility_2std'] = entry_price - (volatility * 2)
            
        # Support/resistance based
        if support_resistance:
            nearest_support = max([level for level in support_resistance if level < entry_price], default=None)
            if nearest_support:
                stop_levels['support_level'] = nearest_support * 0.99  # Slightly below support
                
        return stop_levels
        
    def calculate_take_profit_levels(self, entry_price: float, stop_loss_price: float,
                                   risk_reward_ratios: List[float] = None) -> Dict[str, float]:
        """Calculate take profit levels based on risk/reward ratios"""
        
        if risk_reward_ratios is None:
            risk_reward_ratios = [1.0, 1.5, 2.0, 3.0]
            
        risk_amount = abs(entry_price - stop_loss_price)
        take_profit_levels = {}
        
        for ratio in risk_reward_ratios:
            profit_target = entry_price + (risk_amount * ratio)
            take_profit_levels[f'rr_{ratio}'] = profit_target
            
        return take_profit_levels
        
    def calculate_portfolio_risk(self, positions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate total portfolio risk and correlation"""
        
        if not positions:
            return {'total_risk': 0, 'diversification_ratio': 1.0}
            
        total_exposure = sum(pos['position_value'] for pos in positions)
        portfolio_risk = (total_exposure / self.account_balance) * 100
        
        # Calculate sector concentration
        sector_exposure = {}
        for pos in positions:
            sector = pos.get('sector', 'Unknown')
            sector_exposure[sector] = sector_exposure.get(sector, 0) + pos['position_value']
            
        max_sector_concentration = max(sector_exposure.values()) / self.account_balance * 100 if sector_exposure else 0
        
        # Calculate correlation risk (simplified)
        correlation_risk = self._estimate_correlation_risk(positions)
        
        # Diversification ratio
        diversification_ratio = self._calculate_diversification_ratio(positions)
        
        return {
            'total_risk': portfolio_risk,
            'max_sector_concentration': max_sector_concentration,
            'correlation_risk': correlation_risk,
            'diversification_ratio': diversification_ratio,
            'risk_status': self._assess_portfolio_risk(portfolio_risk, max_sector_concentration)
        }
        
    def calculate_kelly_criterion(self, win_rate: float, avg_win: float, avg_loss: float) -> float:
        """Calculate Kelly Criterion for optimal position sizing"""
        
        if avg_loss == 0:
            return 0
            
        win_loss_ratio = avg_win / abs(avg_loss)
        kelly_percentage = win_rate - ((1 - win_rate) / win_loss_ratio)
        
        # Apply safety factor (typically 25-50% of Kelly)
        safe_kelly = kelly_percentage * 0.25
        
        return max(0, min(safe_kelly, 0.10))  # Cap at 10%
        
    def calculate_sharpe_ratio(self, returns: List[float], periods_per_year: int = 252) -> float:
        """Calculate Sharpe ratio for strategy performance"""
        
        if not returns or len(returns) < 2:
            return 0
            
        avg_return = np.mean(returns)
        std_return = np.std(returns)
        
        if std_return == 0:
            return 0
            
        # Annualized return and volatility
        annual_return = avg_return * periods_per_year
        annual_volatility = std_return * math.sqrt(periods_per_year)
        
        # Risk-free rate (daily)
        daily_risk_free_rate = self.risk_profile.risk_free_rate / 100 / periods_per_year
        
        sharpe_ratio = (annual_return - (daily_risk_free_rate * periods_per_year)) / annual_volatility
        
        return sharpe_ratio
        
    def calculate_max_drawdown(self, equity_curve: List[float]) -> Dict[str, float]:
        """Calculate maximum drawdown and related metrics"""
        
        if not equity_curve:
            return {'max_drawdown': 0, 'max_drawdown_pct': 0}
            
        peak = equity_curve[0]
        max_drawdown = 0
        max_drawdown_pct = 0
        current_drawdown = 0
        
        drawdown_periods = 0
        max_drawdown_periods = 0
        in_drawdown = False
        
        for value in equity_curve:
            if value > peak:
                peak = value
                if in_drawdown:
                    in_drawdown = False
                    if drawdown_periods > max_drawdown_periods:
                        max_drawdown_periods = drawdown_periods
                    drawdown_periods = 0
            else:
                current_drawdown = peak - value
                current_drawdown_pct = (current_drawdown / peak) * 100
                
                if current_drawdown > max_drawdown:
                    max_drawdown = current_drawdown
                    max_drawdown_pct = current_drawdown_pct
                    
                if not in_drawdown:
                    in_drawdown = True
                    
                drawdown_periods += 1
                
        return {
            'max_drawdown': max_drawdown,
            'max_drawdown_pct': max_drawdown_pct,
            'max_drawdown_periods': max_drawdown_periods,
            'current_drawdown': current_drawdown
        }
        
    def calculate_var(self, returns: List[float], confidence_level: float = 0.95) -> float:
        """Calculate Value at Risk (VaR)"""
        
        if not returns:
            return 0
            
        sorted_returns = sorted(returns)
        index = int((1 - confidence_level) * len(sorted_returns))
        
        if index >= len(sorted_returns):
            return sorted_returns[-1]
            
        return sorted_returns[index]
        
    def calculate_expected_shortfall(self, returns: List[float], confidence_level: float = 0.95) -> float:
        """Calculate Expected Shortfall (Conditional VaR)"""
        
        var = self.calculate_var(returns, confidence_level)
        tail_returns = [r for r in returns if r <= var]
        
        if not tail_returns:
            return 0
            
        return np.mean(tail_returns)

    # --- Added static convenience methods for external modules ---
    @staticmethod
    def calculate_risk_metrics(returns_series, confidence_level: float = 0.95) -> Dict[str, float]:
        """Convenience wrapper returning common risk metrics.
        Accepts a pandas Series or list-like of returns.
        """
        try:
            import numpy as _np  # local import for safety
            returns = list(returns_series) if not hasattr(returns_series, 'dropna') else list(returns_series.dropna())
            if not returns:
                return {}
            sorted_returns = sorted(returns)
            index_95 = int((1 - confidence_level) * len(sorted_returns))
            index_99 = int((1 - 0.99) * len(sorted_returns))
            var_95 = sorted_returns[index_95] if index_95 < len(sorted_returns) else sorted_returns[-1]
            var_99 = sorted_returns[index_99] if index_99 < len(sorted_returns) else sorted_returns[-1]
            # Expected shortfall (average of tail below VaR 95)
            tail = [r for r in returns if r <= var_95]
            expected_shortfall = _np.mean(tail) if tail else 0
            return {
                'daily_var_95': abs(var_95),
                'daily_var_99': abs(var_99),
                'expected_shortfall': abs(expected_shortfall)
            }
        except Exception:
            return {}

    @staticmethod
    def calculate_portfolio_metrics(returns_list, weights) -> Dict[str, float]:
        """Simplified portfolio metrics (Sharpe, Sortino, Drawdown, Volatility)."""
        try:
            import numpy as _np
            if not returns_list:
                return {}
            # Combine weighted returns
            combined = None
            for r, w in zip(returns_list, weights):
                series = r.dropna() if hasattr(r, 'dropna') else r
                arr = _np.array(series)
                combined = arr * w if combined is None else combined + arr * w
            if combined is None or len(combined) < 2:
                return {}
            mean = _np.mean(combined)
            std = _np.std(combined)
            downside = [x for x in combined if x < 0]
            downside_std = _np.std(downside) if downside else 0
            sharpe = (mean / std) * (_np.sqrt(252)) if std else 0
            sortino = (mean / downside_std) * (_np.sqrt(252)) if downside_std else 0
            # Max drawdown
            cumulative = (1 + combined).cumprod() if hasattr((1 + combined), 'cumprod') else _np.cumprod(1 + combined)
            peak = cumulative[0]
            max_dd = 0
            for val in cumulative:
                if val > peak:
                    peak = val
                drawdown = (peak - val) / peak
                if drawdown > max_dd:
                    max_dd = drawdown
            volatility = std * _np.sqrt(252)
            return {
                'sharpe_ratio': float(sharpe),
                'sortino_ratio': float(sortino),
                'max_drawdown': float(max_dd),
                'volatility': float(volatility)
            }
        except Exception:
            return {}

    @staticmethod
    def kelly_criterion_position_size(win_rate: float, win_loss_ratio: float, loss_probability: float) -> float:
        """Simplified Kelly criterion based sizing (safety-adjusted)."""
        try:
            # Kelly = W - (1-W)/R
            k = win_rate - (1 - win_rate) / max(win_loss_ratio, 1e-9)
            k = max(0, k)
            # Safety factor (25%)
            k *= 0.25
            return round(min(k, 0.1), 4)  # cap at 10%
        except Exception:
            return 0.01
        
    def assess_trade_risk(self, symbol: str, entry_price: float, stop_loss: float,
                         take_profit: float = None, position_size: float = None) -> Dict[str, Any]:
        """Comprehensive trade risk assessment"""
        
        if position_size is None:
            pos_calc = self.calculate_position_size(entry_price, stop_loss)
            position_size = pos_calc['position_size']
            
        position_value = position_size * entry_price
        max_loss = position_size * abs(entry_price - stop_loss)
        max_loss_pct = (max_loss / self.account_balance) * 100
        
        risk_assessment = {
            'symbol': symbol,
            'entry_price': entry_price,
            'stop_loss': stop_loss,
            'take_profit': take_profit,
            'position_size': position_size,
            'position_value': position_value,
            'max_loss': max_loss,
            'max_loss_percentage': max_loss_pct,
            'position_as_pct_of_account': (position_value / self.account_balance) * 100
        }
        
        if take_profit:
            max_profit = position_size * abs(take_profit - entry_price)
            risk_reward_ratio = max_profit / max_loss if max_loss > 0 else 0
            
            risk_assessment.update({
                'max_profit': max_profit,
                'risk_reward_ratio': risk_reward_ratio,
                'profit_probability_breakeven': 1 / (1 + risk_reward_ratio) * 100
            })
            
        # Risk warnings
        warnings = []
        if max_loss_pct > self.risk_profile.max_risk_per_trade:
            warnings.append(f"Risk exceeds maximum per trade ({self.risk_profile.max_risk_per_trade}%)")
            
        if (position_value / self.account_balance) * 100 > 50:
            warnings.append("Position size exceeds 50% of account")
            
        risk_assessment['warnings'] = warnings
        risk_assessment['risk_level'] = self._assess_risk_level(max_loss_pct)
        
        return risk_assessment
        
    def generate_risk_report(self) -> Dict[str, Any]:
        """Generate comprehensive risk management report"""
        
        portfolio_risk = self.calculate_portfolio_risk(self.positions)
        
        report = {
            'account_balance': self.account_balance,
            'risk_profile': {
                'max_risk_per_trade': self.risk_profile.max_risk_per_trade,
                'max_portfolio_risk': self.risk_profile.max_portfolio_risk,
                'max_sector_exposure': self.risk_profile.max_sector_exposure
            },
            'portfolio_metrics': portfolio_risk,
            'position_count': len(self.positions),
            'available_buying_power': self._calculate_buying_power(),
            'recommendations': self._generate_recommendations(portfolio_risk)
        }
        
        return report
        
    def _get_position_recommendation(self, risk_pct: float) -> str:
        """Get position size recommendation"""
        if risk_pct <= 1:
            return "Conservative - Low risk"
        elif risk_pct <= 2:
            return "Moderate - Appropriate risk"
        elif risk_pct <= 3:
            return "Aggressive - Higher risk"
        else:
            return "Excessive - Reduce position size"
            
    def _estimate_correlation_risk(self, positions: List[Dict[str, Any]]) -> float:
        """Estimate correlation risk (simplified calculation)"""
        if len(positions) <= 1:
            return 0
            
        # Simplified: assume 30% correlation between positions in same sector
        sector_groups = {}
        for pos in positions:
            sector = pos.get('sector', 'Unknown')
            if sector not in sector_groups:
                sector_groups[sector] = []
            sector_groups[sector].append(pos['position_value'])
            
        correlation_risk = 0
        for sector, values in sector_groups.items():
            if len(values) > 1:
                sector_exposure = sum(values)
                # Higher correlation risk for concentrated sectors
                correlation_risk += (sector_exposure / self.account_balance) * 0.3
                
        return min(correlation_risk * 100, 100)  # Cap at 100%
        
    def _calculate_diversification_ratio(self, positions: List[Dict[str, Any]]) -> float:
        """Calculate portfolio diversification ratio"""
        if len(positions) <= 1:
            return 1.0
            
        # Simplified diversification calculation
        equal_weight = 1.0 / len(positions)
        actual_weights = [pos['position_value'] / sum(p['position_value'] for p in positions) 
                         for pos in positions]
        
        # Herfindahl-Hirschman Index
        hhi = sum(w**2 for w in actual_weights)
        max_diversification = 1.0 / len(positions)
        
        return max_diversification / hhi if hhi > 0 else 1.0
        
    def _assess_portfolio_risk(self, total_risk: float, sector_concentration: float) -> str:
        """Assess overall portfolio risk level"""
        if total_risk > self.risk_profile.max_portfolio_risk:
            return "HIGH - Reduce exposure"
        elif sector_concentration > self.risk_profile.max_sector_exposure:
            return "MEDIUM - Sector concentration risk"
        elif total_risk > 10:
            return "MEDIUM - Moderate exposure"
        else:
            return "LOW - Conservative exposure"
            
    def _assess_risk_level(self, risk_pct: float) -> str:
        """Assess individual trade risk level"""
        if risk_pct <= 1:
            return "LOW"
        elif risk_pct <= 2:
            return "MEDIUM"
        elif risk_pct <= 3:
            return "HIGH"
        else:
            return "EXCESSIVE"
            
    def _calculate_buying_power(self) -> float:
        """Calculate available buying power"""
        used_capital = sum(pos.get('position_value', 0) for pos in self.positions)
        return self.account_balance - used_capital
        
    def _generate_recommendations(self, portfolio_risk: Dict[str, Any]) -> List[str]:
        """Generate risk management recommendations"""
        recommendations = []
        
        if portfolio_risk['total_risk'] > self.risk_profile.max_portfolio_risk:
            recommendations.append("Reduce overall portfolio exposure")
            
        if portfolio_risk['max_sector_concentration'] > self.risk_profile.max_sector_exposure:
            recommendations.append("Diversify across more sectors")
            
        if portfolio_risk['correlation_risk'] > 15:
            recommendations.append("Reduce correlation risk between positions")
            
        if portfolio_risk['diversification_ratio'] < 0.5:
            recommendations.append("Improve portfolio diversification")
            
        if not recommendations:
            recommendations.append("Portfolio risk levels are within acceptable limits")
            
        return recommendations


class MonteCarloSimulator:
    """Monte Carlo simulation for risk analysis"""
    
    @staticmethod
    def simulate_portfolio_returns(expected_returns: List[float], volatilities: List[float],
                                  correlations: np.ndarray, num_simulations: int = 10000,
                                  time_horizon: int = 252) -> Dict[str, Any]:
        """Simulate portfolio returns using Monte Carlo"""
        
        num_assets = len(expected_returns)
        
        # Generate random returns
        simulated_returns = []
        
        for _ in range(num_simulations):
            # Generate correlated random variables
            random_vars = np.random.multivariate_normal([0] * num_assets, correlations)
            
            # Convert to returns
            daily_returns = []
            for i in range(num_assets):
                daily_return = expected_returns[i] + volatilities[i] * random_vars[i]
                daily_returns.append(daily_return)
                
            # Calculate portfolio return (equal weighted for simplicity)
            portfolio_return = np.mean(daily_returns)
            simulated_returns.append(portfolio_return)
            
        # Calculate statistics
        annual_returns = [r * time_horizon for r in simulated_returns]
        
        return {
            'mean_return': np.mean(annual_returns),
            'std_return': np.std(annual_returns),
            'var_95': np.percentile(annual_returns, 5),
            'var_99': np.percentile(annual_returns, 1),
            'max_loss': min(annual_returns),
            'max_gain': max(annual_returns),
            'probability_of_loss': len([r for r in annual_returns if r < 0]) / len(annual_returns)
        }
