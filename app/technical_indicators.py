"""
Advanced Technical Indicators Suite for CMC Markets-style MT4 functionality
Professional technical analysis tools and indicators
"""

try:
    import pandas as pd  # type: ignore
except Exception:
    pd = None  # type: ignore
try:
    import numpy as np  # type: ignore
except Exception:
    class _NPStub:
        def array(self, x): return x
        def arange(self, *a, **k): return list(range(a[0], a[1]+1)) if len(a)>1 else []
        def abs(self, x): return abs(x)
        def mean(self, x): return sum(x)/len(x) if x else 0
    np = _NPStub()  # type: ignore
from typing import Dict, List, Tuple, Optional, Any
import math
from scipy import stats

class TechnicalIndicators:
    """Comprehensive technical indicators library"""
    
    @staticmethod
    def sma(prices, period: int):
        """Simple Moving Average"""
        if pd is None:
            return prices  # minimal fallback
        return prices.rolling(window=period).mean()
    
    @staticmethod
    def ema(prices, period: int):
        """Exponential Moving Average"""
        if pd is None:
            return prices
        return prices.ewm(span=period).mean()
    
    @staticmethod
    def wma(prices: pd.Series, period: int) -> pd.Series:
        """Weighted Moving Average"""
        weights = np.arange(1, period + 1)
        return prices.rolling(window=period).apply(
            lambda x: np.dot(x, weights) / weights.sum(), raw=True
        )
    
    @staticmethod
    def rsi(prices: pd.Series, period: int = 14) -> pd.Series:
        """Relative Strength Index"""
        delta = prices.diff()
        gain = delta.where(delta > 0, 0)
        loss = -delta.where(delta < 0, 0)
        
        avg_gain = gain.rolling(window=period).mean()
        avg_loss = loss.rolling(window=period).mean()
        
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        
        return rsi
    
    @staticmethod
    def macd(prices: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9) -> Dict[str, pd.Series]:
        """MACD (Moving Average Convergence Divergence)"""
        ema_fast = TechnicalIndicators.ema(prices, fast)
        ema_slow = TechnicalIndicators.ema(prices, slow)
        
        macd_line = ema_fast - ema_slow
        signal_line = TechnicalIndicators.ema(macd_line, signal)
        histogram = macd_line - signal_line
        
        return {
            'macd': macd_line,
            'signal': signal_line,
            'histogram': histogram
        }
    
    @staticmethod
    def bollinger_bands(prices: pd.Series, period: int = 20, std_dev: float = 2) -> Dict[str, pd.Series]:
        """Bollinger Bands"""
        sma = TechnicalIndicators.sma(prices, period)
        std = prices.rolling(window=period).std()
        
        upper_band = sma + (std * std_dev)
        lower_band = sma - (std * std_dev)
        
        return {
            'upper': upper_band,
            'middle': sma,
            'lower': lower_band,
            'bandwidth': (upper_band - lower_band) / sma * 100,
            'percent_b': (prices - lower_band) / (upper_band - lower_band)
        }
    
    @staticmethod
    def stochastic(high: pd.Series, low: pd.Series, close: pd.Series, 
                   k_period: int = 14, d_period: int = 3) -> Dict[str, pd.Series]:
        """Stochastic Oscillator"""
        lowest_low = low.rolling(window=k_period).min()
        highest_high = high.rolling(window=k_period).max()
        
        k_percent = 100 * (close - lowest_low) / (highest_high - lowest_low)
        d_percent = k_percent.rolling(window=d_period).mean()
        
        return {
            'k': k_percent,
            'd': d_percent
        }
    
    @staticmethod
    def atr(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> pd.Series:
        """Average True Range"""
        high_low = high - low
        high_close_prev = np.abs(high - close.shift())
        low_close_prev = np.abs(low - close.shift())
        
        true_range = pd.concat([high_low, high_close_prev, low_close_prev], axis=1).max(axis=1)
        
        return true_range.rolling(window=period).mean()
    
    @staticmethod
    def adx(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> Dict[str, pd.Series]:
        """Average Directional Index"""
        
        # Calculate True Range
        tr = TechnicalIndicators.atr(high, low, close, 1)
        
        # Calculate Directional Movement
        plus_dm = high.diff()
        minus_dm = -low.diff()
        
        plus_dm[plus_dm < 0] = 0
        minus_dm[minus_dm < 0] = 0
        
        # Smooth the values
        atr_smooth = tr.ewm(span=period).mean()
        plus_di_smooth = plus_dm.ewm(span=period).mean()
        minus_di_smooth = minus_dm.ewm(span=period).mean()
        
        # Calculate DI values
        plus_di = 100 * plus_di_smooth / atr_smooth
        minus_di = 100 * minus_di_smooth / atr_smooth
        
        # Calculate ADX
        dx = 100 * np.abs(plus_di - minus_di) / (plus_di + minus_di)
        adx = dx.ewm(span=period).mean()
        
        return {
            'adx': adx,
            'plus_di': plus_di,
            'minus_di': minus_di
        }
    
    @staticmethod
    def williams_r(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> pd.Series:
        """Williams %R"""
        highest_high = high.rolling(window=period).max()
        lowest_low = low.rolling(window=period).min()
        
        wr = -100 * (highest_high - close) / (highest_high - lowest_low)
        
        return wr
    
    @staticmethod
    def cci(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 20) -> pd.Series:
        """Commodity Channel Index"""
        typical_price = (high + low + close) / 3
        sma_tp = typical_price.rolling(window=period).mean()
        mad = typical_price.rolling(window=period).apply(
            lambda x: np.mean(np.abs(x - x.mean())), raw=True
        )
        
        cci = (typical_price - sma_tp) / (0.015 * mad)
        
        return cci
    
    @staticmethod
    def momentum(prices: pd.Series, period: int = 10) -> pd.Series:
        """Price Momentum"""
        return prices - prices.shift(period)
    
    @staticmethod
    def roc(prices: pd.Series, period: int = 10) -> pd.Series:
        """Rate of Change"""
        return ((prices - prices.shift(period)) / prices.shift(period)) * 100
    
    @staticmethod
    def obv(close: pd.Series, volume: pd.Series) -> pd.Series:
        """On-Balance Volume"""
        obv = pd.Series(index=close.index, dtype=float)
        obv.iloc[0] = volume.iloc[0]
        
        for i in range(1, len(close)):
            if close.iloc[i] > close.iloc[i-1]:
                obv.iloc[i] = obv.iloc[i-1] + volume.iloc[i]
            elif close.iloc[i] < close.iloc[i-1]:
                obv.iloc[i] = obv.iloc[i-1] - volume.iloc[i]
            else:
                obv.iloc[i] = obv.iloc[i-1]
                
        return obv
    
    @staticmethod
    def vwap(high: pd.Series, low: pd.Series, close: pd.Series, volume: pd.Series) -> pd.Series:
        """Volume Weighted Average Price"""
        typical_price = (high + low + close) / 3
        return (typical_price * volume).cumsum() / volume.cumsum()
    
    @staticmethod
    def fibonacci_retracement(high_price: float, low_price: float) -> Dict[str, float]:
        """Fibonacci Retracement Levels"""
        diff = high_price - low_price
        
        return {
            '0.0': high_price,
            '23.6': high_price - 0.236 * diff,
            '38.2': high_price - 0.382 * diff,
            '50.0': high_price - 0.500 * diff,
            '61.8': high_price - 0.618 * diff,
            '78.6': high_price - 0.786 * diff,
            '100.0': low_price
        }
    
    @staticmethod
    def pivot_points(high: float, low: float, close: float) -> Dict[str, float]:
        """Traditional Pivot Points"""
        pivot = (high + low + close) / 3
        
        return {
            'pivot': pivot,
            'r1': 2 * pivot - low,
            'r2': pivot + (high - low),
            'r3': high + 2 * (pivot - low),
            's1': 2 * pivot - high,
            's2': pivot - (high - low),
            's3': low - 2 * (high - pivot)
        }
    
    @staticmethod
    def ichimoku(high: pd.Series, low: pd.Series, close: pd.Series) -> Dict[str, pd.Series]:
        """Ichimoku Cloud"""
        
        # Tenkan-sen (Conversion Line): (9-period high + 9-period low)/2
        tenkan_sen = (high.rolling(window=9).max() + low.rolling(window=9).min()) / 2
        
        # Kijun-sen (Base Line): (26-period high + 26-period low)/2
        kijun_sen = (high.rolling(window=26).max() + low.rolling(window=26).min()) / 2
        
        # Senkou Span A (Leading Span A): (Tenkan-sen + Kijun-sen)/2, projected 26 periods ahead
        senkou_span_a = ((tenkan_sen + kijun_sen) / 2).shift(26)
        
        # Senkou Span B (Leading Span B): (52-period high + 52-period low)/2, projected 26 periods ahead
        senkou_span_b = ((high.rolling(window=52).max() + low.rolling(window=52).min()) / 2).shift(26)
        
        # Chikou Span (Lagging Span): Close projected 26 periods back
        chikou_span = close.shift(-26)
        
        return {
            'tenkan_sen': tenkan_sen,
            'kijun_sen': kijun_sen,
            'senkou_span_a': senkou_span_a,
            'senkou_span_b': senkou_span_b,
            'chikou_span': chikou_span
        }


class PatternRecognition:
    """Advanced pattern recognition for technical analysis"""
    
    @staticmethod
    def detect_candlestick_patterns(open_prices: pd.Series, high: pd.Series, 
                                   low: pd.Series, close: pd.Series) -> Dict[str, pd.Series]:
        """Detect common candlestick patterns"""
        
        patterns = {}
        
        # Doji
        body_size = np.abs(close - open_prices)
        total_range = high - low
        doji_threshold = 0.1
        patterns['doji'] = (body_size / total_range) < doji_threshold
        
        # Hammer
        lower_shadow = np.minimum(open_prices, close) - low
        upper_shadow = high - np.maximum(open_prices, close)
        patterns['hammer'] = (lower_shadow > 2 * body_size) & (upper_shadow < body_size)
        
        # Shooting Star
        patterns['shooting_star'] = (upper_shadow > 2 * body_size) & (lower_shadow < body_size)
        
        # Engulfing Patterns
        prev_body = np.abs(close.shift(1) - open_prices.shift(1))
        bullish_engulfing = (close > open_prices) & (close.shift(1) < open_prices.shift(1)) & \
                           (close > open_prices.shift(1)) & (open_prices < close.shift(1))
        patterns['bullish_engulfing'] = bullish_engulfing
        
        bearish_engulfing = (close < open_prices) & (close.shift(1) > open_prices.shift(1)) & \
                           (close < open_prices.shift(1)) & (open_prices > close.shift(1))
        patterns['bearish_engulfing'] = bearish_engulfing
        
        return patterns
    
    @staticmethod
    def detect_chart_patterns(high: pd.Series, low: pd.Series, close: pd.Series, 
                             window: int = 20) -> Dict[str, List[Dict]]:
        """Detect chart patterns like triangles, head and shoulders, etc."""
        
        patterns = {
            'triangles': [],
            'head_and_shoulders': [],
            'double_tops': [],
            'double_bottoms': []
        }
        
        # Find local peaks and troughs
        peaks = PatternRecognition._find_peaks(high, window)
        troughs = PatternRecognition._find_troughs(low, window)
        
        # Detect triangles
        triangles = PatternRecognition._detect_triangles(peaks, troughs, close)
        patterns['triangles'].extend(triangles)
        
        # Detect head and shoulders
        hns_patterns = PatternRecognition._detect_head_and_shoulders(peaks, troughs)
        patterns['head_and_shoulders'].extend(hns_patterns)
        
        # Detect double tops/bottoms
        double_tops = PatternRecognition._detect_double_tops(peaks)
        double_bottoms = PatternRecognition._detect_double_bottoms(troughs)
        patterns['double_tops'].extend(double_tops)
        patterns['double_bottoms'].extend(double_bottoms)
        
        return patterns
    
    @staticmethod
    def _find_peaks(prices: pd.Series, window: int) -> List[Tuple[int, float]]:
        """Find local peaks in price series"""
        peaks = []
        
        for i in range(window, len(prices) - window):
            if prices.iloc[i] == prices.iloc[i-window:i+window+1].max():
                peaks.append((i, prices.iloc[i]))
                
        return peaks
    
    @staticmethod
    def _find_troughs(prices: pd.Series, window: int) -> List[Tuple[int, float]]:
        """Find local troughs in price series"""
        troughs = []
        
        for i in range(window, len(prices) - window):
            if prices.iloc[i] == prices.iloc[i-window:i+window+1].min():
                troughs.append((i, prices.iloc[i]))
                
        return troughs
    
    @staticmethod
    def _detect_triangles(peaks: List[Tuple], troughs: List[Tuple], close: pd.Series) -> List[Dict]:
        """Detect triangle patterns"""
        triangles = []
        
        if len(peaks) >= 2 and len(troughs) >= 2:
            # Sort by index
            peaks.sort(key=lambda x: x[0])
            troughs.sort(key=lambda x: x[0])
            
            # Get last two peaks and troughs
            last_peaks = peaks[-2:]
            last_troughs = troughs[-2:]
            
            # Check for ascending triangle (horizontal resistance, rising support)
            if (abs(last_peaks[0][1] - last_peaks[1][1]) < 0.02 * last_peaks[0][1] and
                last_troughs[1][1] > last_troughs[0][1]):
                triangles.append({
                    'type': 'ascending',
                    'resistance': last_peaks[0][1],
                    'support_slope': 'rising',
                    'breakout_target': last_peaks[0][1] * 1.05
                })
            
            # Check for descending triangle (horizontal support, falling resistance)
            elif (abs(last_troughs[0][1] - last_troughs[1][1]) < 0.02 * last_troughs[0][1] and
                  last_peaks[1][1] < last_peaks[0][1]):
                triangles.append({
                    'type': 'descending',
                    'support': last_troughs[0][1],
                    'resistance_slope': 'falling',
                    'breakout_target': last_troughs[0][1] * 0.95
                })
        
        return triangles
    
    @staticmethod
    def _detect_head_and_shoulders(peaks: List[Tuple], troughs: List[Tuple]) -> List[Dict]:
        """Detect head and shoulders patterns"""
        patterns = []
        
        if len(peaks) >= 3 and len(troughs) >= 2:
            # Sort by index
            peaks.sort(key=lambda x: x[0])
            
            # Check last three peaks for head and shoulders
            left_shoulder = peaks[-3]
            head = peaks[-2]
            right_shoulder = peaks[-1]
            
            # Head should be higher than shoulders
            if (head[1] > left_shoulder[1] and head[1] > right_shoulder[1] and
                abs(left_shoulder[1] - right_shoulder[1]) < 0.05 * head[1]):
                
                patterns.append({
                    'type': 'head_and_shoulders',
                    'left_shoulder': left_shoulder,
                    'head': head,
                    'right_shoulder': right_shoulder,
                    'neckline': min(left_shoulder[1], right_shoulder[1]),
                    'target': min(left_shoulder[1], right_shoulder[1]) - (head[1] - min(left_shoulder[1], right_shoulder[1]))
                })
        
        return patterns
    
    @staticmethod
    def _detect_double_tops(peaks: List[Tuple]) -> List[Dict]:
        """Detect double top patterns"""
        patterns = []
        
        if len(peaks) >= 2:
            peaks.sort(key=lambda x: x[0])
            last_two_peaks = peaks[-2:]
            
            # Check if peaks are approximately equal
            if abs(last_two_peaks[0][1] - last_two_peaks[1][1]) < 0.03 * last_two_peaks[0][1]:
                patterns.append({
                    'type': 'double_top',
                    'first_peak': last_two_peaks[0],
                    'second_peak': last_two_peaks[1],
                    'resistance': max(last_two_peaks[0][1], last_two_peaks[1][1])
                })
        
        return patterns
    
    @staticmethod
    def _detect_double_bottoms(troughs: List[Tuple]) -> List[Dict]:
        """Detect double bottom patterns"""
        patterns = []
        
        if len(troughs) >= 2:
            troughs.sort(key=lambda x: x[0])
            last_two_troughs = troughs[-2:]
            
            # Check if troughs are approximately equal
            if abs(last_two_troughs[0][1] - last_two_troughs[1][1]) < 0.03 * last_two_troughs[0][1]:
                patterns.append({
                    'type': 'double_bottom',
                    'first_trough': last_two_troughs[0],
                    'second_trough': last_two_troughs[1],
                    'support': min(last_two_troughs[0][1], last_two_troughs[1][1])
                })
        
        return patterns


class TradingSignals:
    """Generate trading signals based on technical indicators"""
    
    @staticmethod
    def generate_ma_crossover_signals(prices: pd.Series, fast_period: int = 10, 
                                     slow_period: int = 20) -> pd.Series:
        """Generate signals based on moving average crossover"""
        fast_ma = TechnicalIndicators.sma(prices, fast_period)
        slow_ma = TechnicalIndicators.sma(prices, slow_period)
        
        signals = pd.Series(index=prices.index, dtype=object)
        signals[(fast_ma > slow_ma) & (fast_ma.shift(1) <= slow_ma.shift(1))] = 'BUY'
        signals[(fast_ma < slow_ma) & (fast_ma.shift(1) >= slow_ma.shift(1))] = 'SELL'
        
        return signals
    

# Facade / compatibility layer expected by other modules
class _TechnicalIndicatorsFacade:
    """Lightweight facade providing calculate_all_indicators() interface
    referenced by professional_analytics and other modules. Uses the
    TechnicalIndicators static methods when pandas is available and
    returns simplified placeholder values otherwise. The structure of
    the returned dict matches existing downstream expectations: each
    key maps either to a dict-like series (original design) or to a
    scalar fallback value.
    """
    def calculate_all_indicators(self, data):
        try:
            if pd is None:
                # Fallback simplified metrics using last close values from list data
                if isinstance(data, list) and data:
                    last = data[-1]
                    price = last.get('close', 0)
                else:
                    price = 0
                return {
                    'sma_20': { 'fallback': price },
                    'sma_50': { 'fallback': price },
                    'ema_12': { 'fallback': price },
                    'ema_26': { 'fallback': price },
                    'rsi': { 'fallback': 50 },
                    'macd': { 'fallback': 0 },
                    'macd_signal': { 'fallback': 0 },
                    'stochastic_k': { 'fallback': 50 },
                    'stochastic_d': { 'fallback': 50 },
                    'bollinger_upper': { 'fallback': price * 1.02 if price else 0 },
                    'bollinger_lower': { 'fallback': price * 0.98 if price else 0 },
                    'atr': { 'fallback': 0 }
                }
            # pandas path
            close = data['close']
            high = data['high']
            low = data['low']
            volume = data['volume'] if 'volume' in data else None

            indicators = {}
            # Moving averages
            indicators['sma_20'] = TechnicalIndicators.sma(close, 20)
            indicators['sma_50'] = TechnicalIndicators.sma(close, 50)
            indicators['ema_12'] = TechnicalIndicators.ema(close, 12)
            indicators['ema_26'] = TechnicalIndicators.ema(close, 26)

            # RSI
            indicators['rsi'] = TechnicalIndicators.rsi(close)

            # MACD
            macd_data = TechnicalIndicators.macd(close)
            indicators['macd'] = macd_data['macd']
            indicators['macd_signal'] = macd_data['signal']

            # Stochastic
            stoch = TechnicalIndicators.stochastic(high, low, close)
            indicators['stochastic_k'] = stoch['k']
            indicators['stochastic_d'] = stoch['d']

            # Bollinger Bands
            bb = TechnicalIndicators.bollinger_bands(close)
            indicators['bollinger_upper'] = bb['upper']
            indicators['bollinger_lower'] = bb['lower']

            # ATR
            indicators['atr'] = TechnicalIndicators.atr(high, low, close)

            # CCI
            indicators['cci'] = TechnicalIndicators.cci(high, low, close)

            # Momentum
            indicators['momentum'] = TechnicalIndicators.momentum(close)

            # ROC
            indicators['roc'] = TechnicalIndicators.roc(close)

            # OBV
            if volume is not None:
                indicators['obv'] = TechnicalIndicators.obv(close, volume)

            # VWAP
            if volume is not None:
                indicators['vwap'] = TechnicalIndicators.vwap(high, low, close, volume)

            # ADX
            indicators['adx'] = TechnicalIndicators.adx(high, low, close)

            # Williams %R
            indicators['williams_r'] = TechnicalIndicators.williams_r(high, low, close)

            return indicators
        except Exception:
            return {}


class _PatternRecognitionAdapter:
    """Adapter exposing detect_patterns(data) used elsewhere."""
    def detect_patterns(self, data):
        try:
            if pd is None:
                return {'patterns': []}
            # Use simple wrapper around existing PatternRecognition for now
            # Expect data has columns open/high/low/close
            pr = PatternRecognition()
            patterns = pr.detect_candlestick_patterns(
                data['open'], data['high'], data['low'], data['close']
            )
            return patterns
        except Exception:
            return {'patterns': []}


class _TradingSignalsAdapter:
    def generate_signals(self, data, indicators):  # compatibility
        try:
            if pd is None:
                return {'primary_signal': 'HOLD', 'confidence': 'Low'}
            prices = data['close']
            # Simple rule: compare ema_12 and ema_26
            ema12 = indicators.get('ema_12')
            ema26 = indicators.get('ema_26')
            signal = 'HOLD'
            if hasattr(ema12, 'iloc') and hasattr(ema26, 'iloc'):
                if ema12.iloc[-1] > ema26.iloc[-1]:
                    signal = 'BUY'
                elif ema12.iloc[-1] < ema26.iloc[-1]:
                    signal = 'SELL'
            return {'primary_signal': signal}
        except Exception:
            return {'primary_signal': 'HOLD'}


# Exported module-level instances expected by import sites
technical_indicators = _TechnicalIndicatorsFacade()
PatternRecognition = _PatternRecognitionAdapter
TradingSignals = _TradingSignalsAdapter

