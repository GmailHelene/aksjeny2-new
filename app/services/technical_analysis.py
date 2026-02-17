"""
Enhanced Technical Analysis Module for Aksjeradar
This module provides real technical indicator calculations instead of synthetic demo data.
"""

# import pandas as pd
# import numpy as np
from typing import Dict, Optional, Any

def calculate_rsi(prices: pd.Series, period: int = 14) -> float:
    """
    Calculate Relative Strength Index (RSI)
    
    Args:
        prices: Series of price data
        period: RSI period (default 14)
    
    Returns:
        Latest RSI value
    """
    try:
        if len(prices) < period + 1:
            return 50.0  # Neutral RSI if insufficient data
            
        delta = prices.diff()
        gain = delta.where(delta > 0, 0)
        loss = -delta.where(delta < 0, 0)
        
        avg_gain = gain.rolling(window=period).mean()
        avg_loss = loss.rolling(window=period).mean()
        
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        
        return float(rsi.iloc[-1]) if not pd.isna(rsi.iloc[-1]) else 50.0
    except Exception as e:
        print(f"Error calculating RSI: {e}")
        return 50.0

def calculate_macd(prices: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9) -> Dict[str, float]:
    """
    Calculate MACD (Moving Average Convergence Divergence)
    
    Args:
        prices: Series of price data
        fast: Fast EMA period (default 12)
        slow: Slow EMA period (default 26)
        signal: Signal line EMA period (default 9)
    
    Returns:
        Dictionary with macd, signal, and histogram values
    """
    try:
        if len(prices) < slow + signal:
            return {'macd': 0.0, 'signal': 0.0, 'histogram': 0.0}
            
        ema_fast = prices.ewm(span=fast).mean()
        ema_slow = prices.ewm(span=slow).mean()
        
        macd_line = ema_fast - ema_slow
        signal_line = macd_line.ewm(span=signal).mean()
        histogram = macd_line - signal_line
        
        return {
            'macd': float(macd_line.iloc[-1]) if not pd.isna(macd_line.iloc[-1]) else 0.0,
            'signal': float(signal_line.iloc[-1]) if not pd.isna(signal_line.iloc[-1]) else 0.0,
            'histogram': float(histogram.iloc[-1]) if not pd.isna(histogram.iloc[-1]) else 0.0
        }
    except Exception as e:
        print(f"Error calculating MACD: {e}")
        return {'macd': 0.0, 'signal': 0.0, 'histogram': 0.0}

def calculate_bollinger_bands(prices: pd.Series, period: int = 20, std_dev: int = 2) -> Dict[str, float]:
    """
    Calculate Bollinger Bands
    
    Args:
        prices: Series of price data
        period: Moving average period (default 20)
        std_dev: Standard deviation multiplier (default 2)
    
    Returns:
        Dictionary with upper, middle, and lower band values
    """
    try:
        if len(prices) < period:
            current_price = float(prices.iloc[-1]) if len(prices) > 0 else 100.0
            return {
                'upper': current_price * 1.02,
                'middle': current_price,
                'lower': current_price * 0.98
            }
            
        sma = prices.rolling(window=period).mean()
        std = prices.rolling(window=period).std()
        
        upper_band = sma + (std * std_dev)
        lower_band = sma - (std * std_dev)
        
        return {
            'upper': float(upper_band.iloc[-1]) if not pd.isna(upper_band.iloc[-1]) else float(prices.iloc[-1]) * 1.02,
            'middle': float(sma.iloc[-1]) if not pd.isna(sma.iloc[-1]) else float(prices.iloc[-1]),
            'lower': float(lower_band.iloc[-1]) if not pd.isna(lower_band.iloc[-1]) else float(prices.iloc[-1]) * 0.98
        }
    except Exception as e:
        print(f"Error calculating Bollinger Bands: {e}")
        current_price = float(prices.iloc[-1]) if len(prices) > 0 else 100.0
        return {
            'upper': current_price * 1.02,
            'middle': current_price,
            'lower': current_price * 0.98
        }

def calculate_moving_averages(prices: pd.Series) -> Dict[str, float]:
    """
    Calculate various moving averages
    
    Args:
        prices: Series of price data
    
    Returns:
        Dictionary with SMA and EMA values
    """
    try:
        current_price = float(prices.iloc[-1]) if len(prices) > 0 else 100.0
        
        result = {}
        
        # Simple Moving Averages
        for period in [20, 50, 200]:
            if len(prices) >= period:
                sma = prices.rolling(window=period).mean().iloc[-1]
                result[f'sma_{period}'] = float(sma) if not pd.isna(sma) else current_price
            else:
                result[f'sma_{period}'] = current_price
                
        # Exponential Moving Averages
        for period in [12, 26]:
            if len(prices) >= period:
                ema = prices.ewm(span=period).mean().iloc[-1]
                result[f'ema_{period}'] = float(ema) if not pd.isna(ema) else current_price
            else:
                result[f'ema_{period}'] = current_price
                
        return result
    except Exception as e:
        print(f"Error calculating moving averages: {e}")
        current_price = float(prices.iloc[-1]) if len(prices) > 0 else 100.0
        return {
            'sma_20': current_price,
            'sma_50': current_price,
            'sma_200': current_price,
            'ema_12': current_price,
            'ema_26': current_price
        }

def calculate_stochastic(high: pd.Series, low: pd.Series, close: pd.Series, 
                        k_period: int = 14, d_period: int = 3) -> Dict[str, float]:
    """
    Calculate Stochastic Oscillator
    
    Args:
        high: Series of high prices
        low: Series of low prices
        close: Series of close prices
        k_period: %K period (default 14)
        d_period: %D period (default 3)
    
    Returns:
        Dictionary with %K and %D values
    """
    try:
        if len(close) < k_period:
            return {'k': 50.0, 'd': 50.0}
            
        lowest_low = low.rolling(window=k_period).min()
        highest_high = high.rolling(window=k_period).max()
        
        k_percent = 100 * ((close - lowest_low) / (highest_high - lowest_low))
        d_percent = k_percent.rolling(window=d_period).mean()
        
        return {
            'k': float(k_percent.iloc[-1]) if not pd.isna(k_percent.iloc[-1]) else 50.0,
            'd': float(d_percent.iloc[-1]) if not pd.isna(d_percent.iloc[-1]) else 50.0
        }
    except Exception as e:
        print(f"Error calculating Stochastic: {e}")
        return {'k': 50.0, 'd': 50.0}

def generate_technical_signal(rsi: float, macd: Dict[str, float], price: float, 
                             sma_20: float, sma_50: float) -> Dict[str, Any]:
    """
    Generate trading signal based on technical indicators
    
    Args:
        rsi: RSI value
        macd: MACD dictionary
        price: Current price
        sma_20: 20-period SMA
        sma_50: 50-period SMA
    
    Returns:
        Dictionary with signal and reasoning
    """
    try:
        signals = []
        
        # RSI signals
        if rsi < 30:
            signals.append(('BUY', 'RSI oversold'))
        elif rsi > 70:
            signals.append(('SELL', 'RSI overbought'))
            
        # MACD signals
        if macd['macd'] > macd['signal'] and macd['histogram'] > 0:
            signals.append(('BUY', 'MACD bullish'))
        elif macd['macd'] < macd['signal'] and macd['histogram'] < 0:
            signals.append(('SELL', 'MACD bearish'))
            
        # Moving average signals
        if price > sma_20 > sma_50:
            signals.append(('BUY', 'Price above moving averages'))
        elif price < sma_20 < sma_50:
            signals.append(('SELL', 'Price below moving averages'))
            
        # Determine overall signal
        buy_signals = len([s for s in signals if s[0] == 'BUY'])
        sell_signals = len([s for s in signals if s[0] == 'SELL'])
        
        if buy_signals > sell_signals:
            signal = 'BUY'
            strength = 'Strong' if buy_signals >= 2 else 'Weak'
        elif sell_signals > buy_signals:
            signal = 'SELL'
            strength = 'Strong' if sell_signals >= 2 else 'Weak'
        else:
            signal = 'HOLD'
            strength = 'Medium'
            
        reasons = [s[1] for s in signals]
        
        return {
            'signal': signal,
            'strength': strength,
            'reasons': reasons,
            'confidence': min(90, max(50, (max(buy_signals, sell_signals) * 20) + 50))
        }
    except Exception as e:
        print(f"Error generating technical signal: {e}")
        return {
            'signal': 'HOLD',
            'strength': 'Medium',
            'reasons': ['Unable to calculate signals'],
            'confidence': 50
        }

def calculate_comprehensive_technical_data(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Calculate comprehensive technical analysis data from OHLCV dataframe
    
    Args:
        df: DataFrame with Open, High, Low, Close, Volume columns
    
    Returns:
        Dictionary with all technical indicators
    """
    try:
        print(f"[TECHNICAL_CALC] Input DataFrame shape: {df.shape if df is not None else 'None'}")
        if df is not None:
            print(f"[TECHNICAL_CALC] DataFrame columns: {df.columns.tolist()}")
            print(f"[TECHNICAL_CALC] DataFrame head:\n{df.head()}")
            
        if df is None or df.empty:
            print("[TECHNICAL_CALC] No data provided, returning neutral values")
            # Return neutral values if no data
            return {
                'rsi': 50.0,
                'macd': 0.0,
                'macd_signal': 0.0,
                'macd_histogram': 0.0,
                'bollinger_upper': 100.0,
                'bollinger_middle': 100.0,
                'bollinger_lower': 100.0,
                'sma_20': 100.0,
                'sma_50': 100.0,
                'sma_200': 100.0,
                'ema_12': 100.0,
                'ema_26': 100.0,
                'stochastic_k': 50.0,
                'stochastic_d': 50.0,
                'signal': 'HOLD',
                'signal_strength': 'Medium',
                'signal_reason': 'Insufficient data'
            }
            
        # Ensure we have the required columns
        required_cols = ['Close']
        if not all(col in df.columns for col in required_cols):
            print(f"[TECHNICAL_CALC] Missing required columns. Available: {df.columns.tolist()}")
            # Use the first numeric column as Close if Close is not available
            numeric_cols = df.select_dtypes(include=[np.number]).columns
            if len(numeric_cols) > 0:
                close_col = numeric_cols[0]
                print(f"[TECHNICAL_CALC] Using column '{close_col}' as Close")
                df = df.rename(columns={close_col: 'Close'})
            else:
                raise ValueError("No numeric columns found")
                
        close_prices = df['Close'].dropna()
        print(f"[TECHNICAL_CALC] Close prices length: {len(close_prices)}")
        
        if len(close_prices) == 0:
            raise ValueError("No valid close prices")
            
        # Use Close for High/Low if not available
        high_prices = df.get('High', close_prices)
        low_prices = df.get('Low', close_prices)
        
        # Calculate indicators
        print("[TECHNICAL_CALC] Calculating RSI...")
        rsi = calculate_rsi(close_prices)
        print(f"[TECHNICAL_CALC] RSI calculated: {rsi}")
        
        print("[TECHNICAL_CALC] Calculating MACD...")
        macd_data = calculate_macd(close_prices)
        print(f"[TECHNICAL_CALC] MACD calculated: {macd_data}")
        
        print("[TECHNICAL_CALC] Calculating Bollinger Bands...")
        bollinger = calculate_bollinger_bands(close_prices)
        print(f"[TECHNICAL_CALC] Bollinger calculated: {bollinger}")
        
        print("[TECHNICAL_CALC] Calculating Moving Averages...")
        moving_averages = calculate_moving_averages(close_prices)
        print(f"[TECHNICAL_CALC] Moving averages calculated: {moving_averages}")
        
        print("[TECHNICAL_CALC] Calculating Stochastic...")
        stochastic = calculate_stochastic(high_prices, low_prices, close_prices)
        print(f"[TECHNICAL_CALC] Stochastic calculated: {stochastic}")
        
        # Generate trading signal
        signal_data = generate_technical_signal(
            rsi=rsi,
            macd=macd_data,
            price=float(close_prices.iloc[-1]),
            sma_20=moving_averages.get('sma_20', float(close_prices.iloc[-1])),
            sma_50=moving_averages.get('sma_50', float(close_prices.iloc[-1]))
        )
        
        # Combine all data
        result = {
            'rsi': rsi,
            'macd': macd_data['macd'],
            'macd_signal': macd_data['signal'],
            'macd_histogram': macd_data['histogram'],
            'bollinger_upper': bollinger['upper'],
            'bollinger_middle': bollinger['middle'],
            'bollinger_lower': bollinger['lower'],
            'stochastic_k': stochastic['k'],
            'stochastic_d': stochastic['d'],
            'signal': signal_data['signal'],
            'signal_strength': signal_data['strength'],
            'signal_reason': ' | '.join(signal_data['reasons']) if signal_data['reasons'] else 'No clear signals'
        }
        
        # Add moving averages
        result.update(moving_averages)
        
        return result
        
    except Exception as e:
        print(f"Error calculating comprehensive technical data: {e}")
        # Return safe fallback values
        return {
            'rsi': 50.0,
            'macd': 0.0,
            'macd_signal': 0.0,
            'macd_histogram': 0.0,
            'bollinger_upper': 100.0,
            'bollinger_middle': 100.0,
            'bollinger_lower': 100.0,
            'sma_20': 100.0,
            'sma_50': 100.0,
            'sma_200': 100.0,
            'ema_12': 100.0,
            'ema_26': 100.0,
            'stochastic_k': 50.0,
            'stochastic_d': 50.0,
            'signal': 'HOLD',
            'signal_strength': 'Medium',
            'signal_reason': 'Calculation error - using defaults'
        }
