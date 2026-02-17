"""
Strategy Backtesting Engine for CMC Markets-style MT4 functionality
Professional backtesting with detailed performance analytics and reporting
"""

try:
    import pandas as pd  # type: ignore
except Exception:
    pd = None  # type: ignore
try:
    import numpy as np  # type: ignore
except Exception:
    class _NPStub:
        def mean(self, arr):
            return sum(arr)/len(arr) if arr else 0
        def std(self, arr):
            m = self.mean(arr)
            import math
            return math.sqrt(sum((x-m)**2 for x in arr)/len(arr)) if arr else 0
    np = _NPStub()  # type: ignore
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
import json
import logging
from dataclasses import dataclass, asdict
import math

@dataclass
class BacktestConfig:
    """Backtesting configuration parameters"""
    initial_capital: float = 10000.0
    commission_per_trade: float = 0.001  # 0.1%
    slippage: float = 0.0005  # 0.05%
    max_positions: int = 1
    position_sizing: str = "fixed"  # "fixed", "percent", "kelly"
    position_size: float = 1000.0  # Fixed amount or percentage
    start_date: str = None
    end_date: str = None
    benchmark_symbol: str = "SPY"

@dataclass
class Trade:
    """Individual trade record"""
    entry_date: datetime
    exit_date: datetime
    symbol: str
    side: str  # "LONG" or "SHORT"
    entry_price: float
    exit_price: float
    quantity: float
    commission: float
    slippage_cost: float
    pnl: float
    pnl_percent: float
    duration_days: int
    exit_reason: str  # "SIGNAL", "STOP_LOSS", "TAKE_PROFIT", "END_OF_TEST"

@dataclass
class PerformanceMetrics:
    """Comprehensive performance metrics"""
    # Basic metrics
    total_return: float
    annual_return: float
    total_trades: int
    winning_trades: int
    losing_trades: int
    win_rate: float
    
    # Profit metrics
    total_profit: float
    total_loss: float
    net_profit: float
    profit_factor: float
    average_win: float
    average_loss: float
    largest_win: float
    largest_loss: float
    
    # Risk metrics
    max_drawdown: float
    max_drawdown_percent: float
    volatility: float
    sharpe_ratio: float
    sortino_ratio: float
    calmar_ratio: float
    var_95: float
    
    # Trading metrics
    avg_trade_duration: float
    max_consecutive_wins: int
    max_consecutive_losses: int
    expectancy: float
    
    # Benchmark comparison
    benchmark_return: float
    alpha: float
    beta: float
    information_ratio: float

class StrategyBacktester:
    """Professional strategy backtesting engine"""
    
    def __init__(self, config: BacktestConfig = None):
        self.config = config or BacktestConfig()
        self.trades: List[Trade] = []
        self.equity_curve: List[float] = []
        self.positions: Dict[str, Dict] = {}
        self.cash = self.config.initial_capital
        self.portfolio_value = self.config.initial_capital
        self.daily_returns: List[float] = []
        self.benchmark_data: pd.DataFrame = None
        
    def run_backtest(self, data, strategy_signals,
                    stop_loss_pct: float = None, take_profit_pct: float = None) -> Dict[str, Any]:
        """Run comprehensive backtest"""
        
        # Reset state
        self._reset_backtest()
        
        # Align data and signals
        aligned_data = self._align_data(data, strategy_signals)
        
        # Process each day
        for i, (date, row) in enumerate(aligned_data.iterrows()):
            self._process_day(date, row, stop_loss_pct, take_profit_pct)
            
        # Close any remaining positions
        self._close_all_positions(aligned_data.iloc[-1])
        
        # Calculate performance metrics
        metrics = self._calculate_performance_metrics(aligned_data)
        
        # Generate report
        return self._generate_backtest_report(metrics, aligned_data)
        
    def _reset_backtest(self):
        """Reset backtest state"""
        self.trades = []
        self.equity_curve = [self.config.initial_capital]
        self.positions = {}
        self.cash = self.config.initial_capital
        self.portfolio_value = self.config.initial_capital
        self.daily_returns = []
        
    def _align_data(self, data, signals):
        """Align price data with strategy signals"""
        if pd is None:
            return data  # fallback (no merge logic)
        aligned = data.join(signals, how='inner')
        
        # Filter by date range if specified
        if self.config.start_date:
            aligned = aligned[aligned.index >= self.config.start_date]
        if self.config.end_date:
            aligned = aligned[aligned.index <= self.config.end_date]
            
        return aligned
        
    def _process_day(self, date: datetime, row, 
                    stop_loss_pct: float = None, take_profit_pct: float = None):
        """Process a single trading day"""
        
        current_price = row['close']
        
        # Check existing positions for stops
        self._check_stop_conditions(date, row, stop_loss_pct, take_profit_pct)
        
        # Process new signals
        if 'signal' in row and (pd is None or not pd.isna(row['signal'])):
            signal = row['signal']
            if signal in ['BUY', 'SELL'] and len(self.positions) < self.config.max_positions:
                self._open_position(date, row, signal)
            elif signal == 'CLOSE':
                self._close_all_positions(row)
                
        # Update portfolio value
        self._update_portfolio_value(row)
        
    def _check_stop_conditions(self, date: datetime, row: pd.Series,
                              stop_loss_pct: float = None, take_profit_pct: float = None):
        """Check stop loss and take profit conditions"""
        
        current_price = row['close']
        positions_to_close = []
        
        for symbol, position in self.positions.items():
            entry_price = position['entry_price']
            side = position['side']
            
            # Check stop loss
            if stop_loss_pct:
                if side == 'LONG':
                    stop_price = entry_price * (1 - stop_loss_pct)
                    if current_price <= stop_price:
                        positions_to_close.append((symbol, 'STOP_LOSS'))
                else:  # SHORT
                    stop_price = entry_price * (1 + stop_loss_pct)
                    if current_price >= stop_price:
                        positions_to_close.append((symbol, 'STOP_LOSS'))
                        
            # Check take profit
            if take_profit_pct:
                if side == 'LONG':
                    target_price = entry_price * (1 + take_profit_pct)
                    if current_price >= target_price:
                        positions_to_close.append((symbol, 'TAKE_PROFIT'))
                else:  # SHORT
                    target_price = entry_price * (1 - take_profit_pct)
                    if current_price <= target_price:
                        positions_to_close.append((symbol, 'TAKE_PROFIT'))
                        
        # Close flagged positions
        for symbol, reason in positions_to_close:
            self._close_position(date, row, symbol, reason)
            
    def _open_position(self, date: datetime, row: pd.Series, signal: str):
        """Open a new position"""
        
        symbol = row.get('symbol', 'STOCK')
        entry_price = row['close']
        
        # Apply slippage
        if signal == 'BUY':
            entry_price *= (1 + self.config.slippage)
            side = 'LONG'
        else:  # SELL
            entry_price *= (1 - self.config.slippage)
            side = 'SHORT'
            
        # Calculate position size
        position_value = self._calculate_position_size()
        quantity = position_value / entry_price
        
        # Calculate commission
        commission = position_value * self.config.commission_per_trade
        
        # Check if enough cash
        total_cost = position_value + commission
        if total_cost > self.cash:
            return  # Not enough cash
            
        # Create position
        position = {
            'symbol': symbol,
            'side': side,
            'entry_date': date,
            'entry_price': entry_price,
            'quantity': quantity,
            'commission': commission
        }
        
        self.positions[symbol] = position
        self.cash -= total_cost
        
    def _close_position(self, date: datetime, row: pd.Series, symbol: str, reason: str):
        """Close an existing position"""
        
        if symbol not in self.positions:
            return
            
        position = self.positions[symbol]
        exit_price = row['close']
        
        # Apply slippage
        if position['side'] == 'LONG':
            exit_price *= (1 - self.config.slippage)
        else:  # SHORT
            exit_price *= (1 + self.config.slippage)
            
        # Calculate P&L
        if position['side'] == 'LONG':
            pnl = (exit_price - position['entry_price']) * position['quantity']
        else:  # SHORT
            pnl = (position['entry_price'] - exit_price) * position['quantity']
            
        # Calculate commission for exit
        exit_commission = position['quantity'] * exit_price * self.config.commission_per_trade
        total_commission = position['commission'] + exit_commission
        
        # Calculate slippage cost
        slippage_cost = position['quantity'] * position['entry_price'] * self.config.slippage * 2
        
        # Net P&L
        net_pnl = pnl - total_commission - slippage_cost
        pnl_percent = net_pnl / (position['quantity'] * position['entry_price']) * 100
        
        # Duration
        duration = (date - position['entry_date']).days
        
        # Create trade record
        trade = Trade(
            entry_date=position['entry_date'],
            exit_date=date,
            symbol=symbol,
            side=position['side'],
            entry_price=position['entry_price'],
            exit_price=exit_price,
            quantity=position['quantity'],
            commission=total_commission,
            slippage_cost=slippage_cost,
            pnl=net_pnl,
            pnl_percent=pnl_percent,
            duration_days=duration,
            exit_reason=reason
        )
        
        self.trades.append(trade)
        
        # Update cash
        proceeds = position['quantity'] * exit_price - exit_commission
        self.cash += proceeds
        
        # Remove position
        del self.positions[symbol]
        
    def _close_all_positions(self, row: pd.Series):
        """Close all open positions"""
        symbols_to_close = list(self.positions.keys())
        for symbol in symbols_to_close:
            self._close_position(row.name, row, symbol, 'SIGNAL')
            
    def _calculate_position_size(self) -> float:
        """Calculate position size based on configuration"""
        
        if self.config.position_sizing == "fixed":
            return min(self.config.position_size, self.cash)
        elif self.config.position_sizing == "percent":
            return self.portfolio_value * (self.config.position_size / 100)
        elif self.config.position_sizing == "kelly":
            # Simplified Kelly criterion implementation
            if len(self.trades) < 10:
                return self.portfolio_value * 0.02  # Conservative start
            
            winning_trades = [t for t in self.trades if t.pnl > 0]
            losing_trades = [t for t in self.trades if t.pnl < 0]
            
            if not winning_trades or not losing_trades:
                return self.portfolio_value * 0.02
                
            win_rate = len(winning_trades) / len(self.trades)
            avg_win = np.mean([t.pnl_percent for t in winning_trades]) / 100
            avg_loss = abs(np.mean([t.pnl_percent for t in losing_trades])) / 100
            
            if avg_loss == 0:
                return self.portfolio_value * 0.02
                
            kelly = win_rate - ((1 - win_rate) / (avg_win / avg_loss))
            safe_kelly = max(0.01, min(0.10, kelly * 0.25))  # Conservative Kelly
            
            return self.portfolio_value * safe_kelly
        
        return self.config.position_size
        
    def _update_portfolio_value(self, row: pd.Series):
        """Update portfolio value and equity curve"""
        
        # Calculate position values
        position_value = 0
        for position in self.positions.values():
            current_price = row['close']
            if position['side'] == 'LONG':
                value = position['quantity'] * current_price
            else:  # SHORT
                value = position['quantity'] * (2 * position['entry_price'] - current_price)
            position_value += value
            
        # Total portfolio value
        new_portfolio_value = self.cash + position_value
        
        # Calculate daily return
        if self.portfolio_value > 0:
            daily_return = (new_portfolio_value - self.portfolio_value) / self.portfolio_value
            self.daily_returns.append(daily_return)
            
        self.portfolio_value = new_portfolio_value
        self.equity_curve.append(new_portfolio_value)
        
    def _calculate_performance_metrics(self, data: pd.DataFrame) -> PerformanceMetrics:
        """Calculate comprehensive performance metrics"""
        
        if not self.trades:
            return PerformanceMetrics(
                total_return=0, annual_return=0, total_trades=0, winning_trades=0,
                losing_trades=0, win_rate=0, total_profit=0, total_loss=0,
                net_profit=0, profit_factor=0, average_win=0, average_loss=0,
                largest_win=0, largest_loss=0, max_drawdown=0, max_drawdown_percent=0,
                volatility=0, sharpe_ratio=0, sortino_ratio=0, calmar_ratio=0,
                var_95=0, avg_trade_duration=0, max_consecutive_wins=0,
                max_consecutive_losses=0, expectancy=0, benchmark_return=0,
                alpha=0, beta=0, information_ratio=0
            )
            
        # Basic trade statistics
        winning_trades = [t for t in self.trades if t.pnl > 0]
        losing_trades = [t for t in self.trades if t.pnl < 0]
        
        total_trades = len(self.trades)
        win_count = len(winning_trades)
        loss_count = len(losing_trades)
        win_rate = win_count / total_trades * 100 if total_trades > 0 else 0
        
        # Profit metrics
        total_profit = sum(t.pnl for t in winning_trades)
        total_loss = sum(t.pnl for t in losing_trades)
        net_profit = total_profit + total_loss
        profit_factor = abs(total_profit / total_loss) if total_loss != 0 else float('inf')
        
        avg_win = total_profit / win_count if win_count > 0 else 0
        avg_loss = total_loss / loss_count if loss_count > 0 else 0
        
        largest_win = max([t.pnl for t in winning_trades]) if winning_trades else 0
        largest_loss = min([t.pnl for t in losing_trades]) if losing_trades else 0
        
        # Returns
        total_return = (self.portfolio_value - self.config.initial_capital) / self.config.initial_capital
        
        # Calculate annualized return
        days = len(data)
        years = days / 252 if days > 0 else 1
        annual_return = ((1 + total_return) ** (1 / years)) - 1 if years > 0 else 0
        
        # Risk metrics
        max_dd, max_dd_pct = self._calculate_max_drawdown()
        
        # Volatility and ratios
        volatility = np.std(self.daily_returns) * np.sqrt(252) if self.daily_returns else 0
        sharpe_ratio = self._calculate_sharpe_ratio()
        sortino_ratio = self._calculate_sortino_ratio()
        calmar_ratio = annual_return / abs(max_dd_pct) if max_dd_pct != 0 else 0
        
        # VaR
        var_95 = np.percentile(self.daily_returns, 5) if self.daily_returns else 0
        
        # Trading metrics
        avg_duration = np.mean([t.duration_days for t in self.trades]) if self.trades else 0
        max_consecutive_wins, max_consecutive_losses = self._calculate_consecutive_trades()
        
        # Expectancy
        expectancy = (win_rate / 100 * avg_win) + ((100 - win_rate) / 100 * avg_loss)
        
        # Benchmark metrics (simplified)
        benchmark_return = 0.08  # Assume 8% benchmark
        alpha = annual_return - benchmark_return
        beta = 1.0  # Simplified
        information_ratio = alpha / volatility if volatility != 0 else 0
        
        return PerformanceMetrics(
            total_return=total_return * 100,
            annual_return=annual_return * 100,
            total_trades=total_trades,
            winning_trades=win_count,
            losing_trades=loss_count,
            win_rate=win_rate,
            total_profit=total_profit,
            total_loss=total_loss,
            net_profit=net_profit,
            profit_factor=profit_factor,
            average_win=avg_win,
            average_loss=avg_loss,
            largest_win=largest_win,
            largest_loss=largest_loss,
            max_drawdown=max_dd,
            max_drawdown_percent=max_dd_pct,
            volatility=volatility * 100,
            sharpe_ratio=sharpe_ratio,
            sortino_ratio=sortino_ratio,
            calmar_ratio=calmar_ratio,
            var_95=var_95 * 100,
            avg_trade_duration=avg_duration,
            max_consecutive_wins=max_consecutive_wins,
            max_consecutive_losses=max_consecutive_losses,
            expectancy=expectancy,
            benchmark_return=benchmark_return * 100,
            alpha=alpha * 100,
            beta=beta,
            information_ratio=information_ratio
        )
        
    def _calculate_max_drawdown(self) -> Tuple[float, float]:
        """Calculate maximum drawdown"""
        
        if len(self.equity_curve) < 2:
            return 0, 0
            
        peak = self.equity_curve[0]
        max_drawdown = 0
        max_drawdown_pct = 0
        
        for value in self.equity_curve:
            if value > peak:
                peak = value
            else:
                drawdown = peak - value
                drawdown_pct = (drawdown / peak) * 100
                
                if drawdown > max_drawdown:
                    max_drawdown = drawdown
                    max_drawdown_pct = drawdown_pct
                    
        return max_drawdown, max_drawdown_pct
        
    def _calculate_sharpe_ratio(self) -> float:
        """Calculate Sharpe ratio"""
        
        if not self.daily_returns:
            return 0
            
        excess_returns = [r - 0.02/252 for r in self.daily_returns]  # Assume 2% risk-free rate
        
        if len(excess_returns) == 0:
            return 0
            
        mean_excess = np.mean(excess_returns)
        std_excess = np.std(excess_returns)
        
        if std_excess == 0:
            return 0
            
        return (mean_excess / std_excess) * np.sqrt(252)
        
    def _calculate_sortino_ratio(self) -> float:
        """Calculate Sortino ratio"""
        
        if not self.daily_returns:
            return 0
            
        excess_returns = [r - 0.02/252 for r in self.daily_returns]
        negative_returns = [r for r in excess_returns if r < 0]
        
        if len(negative_returns) == 0:
            return float('inf') if np.mean(excess_returns) > 0 else 0
            
        mean_excess = np.mean(excess_returns)
        downside_std = np.std(negative_returns)
        
        if downside_std == 0:
            return 0
            
        return (mean_excess / downside_std) * np.sqrt(252)
        
    def _calculate_consecutive_trades(self) -> Tuple[int, int]:
        """Calculate maximum consecutive wins and losses"""
        
        if not self.trades:
            return 0, 0
            
        max_wins = 0
        max_losses = 0
        current_wins = 0
        current_losses = 0
        
        for trade in self.trades:
            if trade.pnl > 0:
                current_wins += 1
                current_losses = 0
                max_wins = max(max_wins, current_wins)
            else:
                current_losses += 1
                current_wins = 0
                max_losses = max(max_losses, current_losses)
                
        return max_wins, max_losses
        
    def _generate_backtest_report(self, metrics: PerformanceMetrics, data: pd.DataFrame) -> Dict[str, Any]:
        """Generate comprehensive backtest report"""
        
        return {
            'config': asdict(self.config),
            'performance_metrics': asdict(metrics),
            'trades': [asdict(trade) for trade in self.trades],
            'equity_curve': self.equity_curve,
            'daily_returns': self.daily_returns,
            'summary': {
                'start_date': data.index[0].strftime('%Y-%m-%d') if len(data) > 0 else None,
                'end_date': data.index[-1].strftime('%Y-%m-%d') if len(data) > 0 else None,
                'duration_days': len(data),
                'initial_capital': self.config.initial_capital,
                'final_value': self.portfolio_value,
                'total_return_pct': metrics.total_return,
                'annual_return_pct': metrics.annual_return,
                'max_drawdown_pct': metrics.max_drawdown_percent,
                'sharpe_ratio': metrics.sharpe_ratio,
                'win_rate': metrics.win_rate
            }
        }


def create_sample_strategy_signals(data: pd.DataFrame, strategy_type: str = "sma_crossover") -> pd.DataFrame:
    """Create sample strategy signals for testing"""
    
    signals = pd.DataFrame(index=data.index)
    
    if strategy_type == "sma_crossover":
        # Simple Moving Average Crossover
        signals['sma_fast'] = data['close'].rolling(10).mean()
        signals['sma_slow'] = data['close'].rolling(20).mean()
        
        signals['signal'] = None
        signals.loc[signals['sma_fast'] > signals['sma_slow'], 'signal'] = 'BUY'
        signals.loc[signals['sma_fast'] < signals['sma_slow'], 'signal'] = 'SELL'
        
    elif strategy_type == "rsi":
        # RSI Strategy
        delta = data['close'].diff()
        gain = delta.where(delta > 0, 0)
        loss = -delta.where(delta < 0, 0)
        avg_gain = gain.rolling(14).mean()
        avg_loss = loss.rolling(14).mean()
        
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        
        signals['rsi'] = rsi
        signals['signal'] = None
        signals.loc[rsi < 30, 'signal'] = 'BUY'
        signals.loc[rsi > 70, 'signal'] = 'SELL'
        
    return signals

# Global backtester instance alias for imports expecting strategy_backtester symbol
try:
    strategy_backtester  # type: ignore  # noqa
except NameError:
    strategy_backtester = StrategyBacktester()
