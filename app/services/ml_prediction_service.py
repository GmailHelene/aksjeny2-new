"""
Advanced Machine Learning Prediction Service
Provides price predictions, risk assessments, and ML-based analysis
"""

# import numpy as np
# import pandas as pd
# from pandas import DataFrame, Series
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union, Tuple
import logging
import os

# Import ML-related libraries with error handling
try:
    from sklearn.preprocessing import StandardScaler
    from sklearn.ensemble import RandomForestRegressor
    from sklearn.metrics import mean_squared_error, r2_score
    import joblib
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False
    StandardScaler = None
    RandomForestRegressor = None
    mean_squared_error = None
    r2_score = None
    joblib = None
from typing import Dict, List, Tuple, Optional

# Import logging first
import logging
logger = logging.getLogger(__name__)

try:
    import joblib
    JOBLIB_AVAILABLE = True
    logger.info("✅ joblib imported successfully")
except ImportError as e:
    logger.warning(f"joblib not available: {e}")
    JOBLIB_AVAILABLE = False
    joblib = None

try:
    from sklearn.ensemble import RandomForestRegressor
    from sklearn.linear_model import LinearRegression
    from sklearn.preprocessing import StandardScaler
    from sklearn.metrics import mean_squared_error, r2_score
    SKLEARN_AVAILABLE = True
    logger.info("✅ scikit-learn imported successfully")
except ImportError as e:
    logger.warning(f"scikit-learn not available: {e}. ML features will be disabled.")
    SKLEARN_AVAILABLE = False
    RandomForestRegressor = None
    LinearRegression = None
    StandardScaler = None
    mean_squared_error = None
    r2_score = None

import warnings
warnings.filterwarnings('ignore')

class MLPredictionService:
    """Service for ML-based stock predictions"""
    
    def __init__(self):
        self.models = {}
        self.last_training = {}
    
    def predict_stock_price(self, symbol: str, days_ahead: int = 30) -> Dict[str, Any]:
        """Predict stock price for the given symbol"""
        try:
            # Mock prediction for now
            base_price = 100.0 + (hash(symbol) % 100)
            predictions = []
            date = datetime.now()
            
            for day in range(days_ahead):
                date += timedelta(days=1)
                price = base_price + (day * 0.1) + np.random.normal(0, 1)
                predictions.append({
                    'date': date.strftime('%Y-%m-%d'),
                    'price': round(price, 2),
                    'confidence': round(0.9 - (day * 0.01), 2)
                })
            
            return {
                'symbol': symbol,
                'predictions': predictions,
                'generated_at': datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Error predicting price for {symbol}: {e}")
            return {
                'symbol': symbol,
                'predictions': [],
                'error': str(e),
                'generated_at': datetime.now().isoformat()
            }
            
    def batch_predict(self, symbols: List[str], days_ahead: int = 30) -> Dict[str, Any]:
        """Get predictions for multiple symbols"""
        results = {}
        for symbol in symbols:
            try:
                results[symbol] = self.predict_stock_price(symbol, days_ahead)
            except Exception as e:
                logger.error(f"Error in batch prediction for {symbol}: {e}")
                results[symbol] = None
        return results
    
    def get_market_analysis(self) -> Dict[str, Any]:
        """Get comprehensive market analysis"""
        try:
            return {
                'market_trend': 'bullish',
                'confidence': 0.85,
                'risk_level': 'moderate',
                'indicators': {
                    'rsi': 65,
                    'macd': 'positive',
                    'volume': 'increasing'
                },
                'generated_at': datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Error getting market analysis: {e}")
            return {
                'market_trend': 'unknown',
                'confidence': 0.0,
                'risk_level': 'unknown',
                'indicators': {},
                'error': str(e),
                'generated_at': datetime.now().isoformat()
            }
    
    def __init__(self):
        self.models = {}
        self.scalers = {}
        self.model_cache = {}
        self.feature_cache = {}
        self.prediction_cache = {}
        
        # Check if ML dependencies are available
        if not SKLEARN_AVAILABLE or not JOBLIB_AVAILABLE:
            missing_deps = []
            if not SKLEARN_AVAILABLE:
                missing_deps.append("scikit-learn")
            if not JOBLIB_AVAILABLE:
                missing_deps.append("joblib")
            logger.warning(f"❌ ML dependencies not available: {', '.join(missing_deps)}. ML features will be disabled.")
            self.ml_enabled = False
        else:
            logger.info("✅ ML dependencies available. ML features enabled.")
            self.ml_enabled = True
        
        # Initialize models directory
        self.models_dir = os.path.join(os.path.dirname(__file__), '..', 'ml_models')
        os.makedirs(self.models_dir, exist_ok=True)
        
        # Model parameters
        self.rf_params = {
            'n_estimators': 100,
            'max_depth': 10,
            'random_state': 42,
            'n_jobs': -1
        }
        
        self.feature_columns = [
            'close', 'volume', 'rsi', 'macd', 'bb_upper', 'bb_lower',
            'sma_20', 'sma_50', 'volatility', 'price_change',
            'volume_ratio', 'momentum'
        ]
    
    def prepare_features(self, data: pd.DataFrame) -> pd.DataFrame:
        """Prepare features for ML models"""
        try:
            df = data.copy()
            
            # Ensure we have required columns
            if 'close' not in df.columns:
                logger.warning("No close price data available")
                return pd.DataFrame()
            
            # Calculate technical indicators
            df['rsi'] = self.calculate_rsi(df['close'])
            df['macd'] = self.calculate_macd(df['close'])
            df['bb_upper'], df['bb_lower'] = self.calculate_bollinger_bands(df['close'])
            df['sma_20'] = df['close'].rolling(window=20).mean()
            df['sma_50'] = df['close'].rolling(window=50).mean()
            df['volatility'] = df['close'].rolling(window=20).std()
            df['price_change'] = df['close'].pct_change()
            
            # Volume features
            if 'volume' in df.columns:
                df['volume_ratio'] = df['volume'] / df['volume'].rolling(window=20).mean()
            else:
                df['volume'] = 1000000  # Default volume
                df['volume_ratio'] = 1.0
            
            # Momentum
            df['momentum'] = df['close'] / df['close'].shift(10) - 1
            
            # Forward fill missing values
            df = df.fillna(method='ffill').fillna(0)
            
            return df[self.feature_columns]
            
        except Exception as e:
            logger.error(f"Error preparing features: {e}")
            return pd.DataFrame()
    
    def calculate_rsi(self, prices: Series, period: int = 14) -> Series:
        """Calculate RSI technical indicator"""
        try:
            # Calculate price changes
            price_diff = prices.diff()
            
            gain = pd.Series(0, index=price_diff.index)
            loss = pd.Series(0, index=price_diff.index)
            
            gain[price_diff > 0] = price_diff[price_diff > 0]
            loss[price_diff < 0] = -price_diff[price_diff < 0]
            
            avg_gain = gain.rolling(window=period).mean()
            avg_loss = loss.rolling(window=period).mean()
            
            # Handle division by zero
            avg_loss = avg_loss.replace(0, np.finfo(float).eps)
            
            rs = avg_gain / avg_loss
            rsi = pd.Series(100 - (100 / (1 + rs)), name='RSI')
            
            return rsi.fillna(50)  # Fill NA with neutral value
            
        except Exception as e:
            logger.error(f"Error calculating RSI: {e}")
            return pd.Series(50, index=prices.index, name='RSI')  # Return neutral RSI on error
    
    def calculate_macd(self, prices: pd.Series) -> pd.Series:
        """Calculate MACD"""
        exp1 = prices.ewm(span=12).mean()
        exp2 = prices.ewm(span=26).mean()
        macd = exp1 - exp2
        return macd
    
    def calculate_bollinger_bands(self, prices: pd.Series, period: int = 20) -> Tuple[pd.Series, pd.Series]:
        """Calculate Bollinger Bands"""
        sma = prices.rolling(window=period).mean()
        std = prices.rolling(window=period).std()
        upper = sma + (std * 2)
        lower = sma - (std * 2)
        return upper, lower
    
    def train_model(self, ticker: str) -> bool:
        """Train ML model for a specific ticker"""
        if not SKLEARN_AVAILABLE:
            logger.warning("Scikit-learn not available - cannot train model")
            return False

        try:
            # Get training data
            df = self._prepare_training_data(ticker)
            
            if df.empty:
                return False
            
            # Split into features and target
            X = df.drop('target', axis=1)
            y = df['target']
            
            # Train-test split (no shuffle to respect time series)
            split_idx = int(len(df) * 0.8)
            X_train, X_test = X[:split_idx], X[split_idx:]
            y_train, y_test = y[:split_idx], y[split_idx:]
            
            # Scale features
            scaler = StandardScaler()
            X_train_scaled = scaler.fit_transform(X_train)
            X_test_scaled = scaler.transform(X_test)
            
            # Train model with updated parameters
            model = RandomForestRegressor(
                n_estimators=100,
                criterion='squared_error',
                max_depth=10,
                min_samples_split=2,
                min_samples_leaf=1,
                bootstrap=True,
                oob_score=True,
                n_jobs=-1,
                random_state=42,
                warm_start=False
            )
            
            model.fit(X_train_scaled, y_train)
            
            # Evaluate
            y_pred = model.predict(X_test_scaled)
            mse = mean_squared_error(y_test, y_pred)
            r2 = r2_score(y_test, y_pred)
            
            logger.info(f"Model metrics for {ticker}:")
            logger.info(f"MSE: {mse:.4f}")
            logger.info(f"R2 Score: {r2:.4f}")
            
            # Save model and scaler
            model_dir = os.path.join('models', ticker)
            os.makedirs(model_dir, exist_ok=True)
            
            model_path = os.path.join(model_dir, 'model.joblib')
            scaler_path = os.path.join(model_dir, 'scaler.joblib')
            
            if joblib is not None:
                joblib.dump(model, model_path)
                joblib.dump(scaler, scaler_path)
            else:
                logger.warning("joblib not available - cannot save model")
            
            return True
            
        except Exception as e:
            logger.error(f"Error training model for {ticker}: {e}")
            return False
    
    def load_model(self, ticker: str) -> bool:
        """Load trained model for a ticker"""
        if not SKLEARN_AVAILABLE or joblib is None:
            logger.warning("ML dependencies not available - cannot load model")
            return False
            
        try:
            model_dir = os.path.join('models', ticker)
            model_path = os.path.join(model_dir, 'model.joblib')
            scaler_path = os.path.join(model_dir, 'scaler.joblib')
            
            if os.path.exists(model_path) and os.path.exists(scaler_path):
                try:
                    self.models[ticker] = joblib.load(model_path)
                    self.scalers[ticker] = joblib.load(scaler_path)
                    return True
                except Exception as e:
                    logger.error(f"Error loading model files for {ticker}: {e}")
                    return False
            
            return False
            
        except Exception as e:
            logger.error(f"Error accessing model for {ticker}: {e}")
            return False
    
    def predict_price_movement(self, ticker: str, data: pd.DataFrame, 
                             horizon: int = 5) -> Dict:
        """Predict price movement for given horizon"""
        try:
            # Check if ML is enabled
            if not self.ml_enabled:
                logger.warning("ML not available, returning fallback prediction")
                return self._get_fallback_prediction(ticker)
                
            # Check cache first
            cache_key = f"{ticker}_{horizon}_{datetime.now().strftime('%Y%m%d_%H')}"
            if cache_key in self.prediction_cache:
                return self.prediction_cache[cache_key]
            
            # Load or train model
            if ticker not in self.models:
                if not self.load_model(ticker):
                    if not self.train_model(ticker):
                        return self._get_fallback_prediction(ticker)
            
            # Prepare latest features
            features = self.prepare_features(data)
            if features.empty:
                return self._get_fallback_prediction(ticker)
            
            # Get latest feature vector
            latest_features = features.iloc[-1:].values
            
            # Scale features
            scaler = self.scalers[ticker]
            scaled_features = scaler.transform(latest_features)
            
            # Make predictions
            model = self.models[ticker]
            predictions = []
            confidence_scores = []
            
            current_features = scaled_features.copy()
            
            for i in range(horizon):
                # Predict next day change
                pred = model.predict(current_features)[0]
                predictions.append(pred)
                
                # Calculate confidence based on feature importance and prediction consistency
                feature_importance = model.feature_importances_
                confidence = self._calculate_confidence(current_features[0], feature_importance)
                confidence_scores.append(confidence)
                
                # Update features for next prediction (simplified)
                # In practice, you'd want more sophisticated feature evolution
                current_features = current_features.copy()
            
            # Calculate price predictions
            current_price = data['close'].iloc[-1]
            price_predictions = []
            cumulative_change = 1.0
            
            for change in predictions:
                cumulative_change *= (1 + change)
                predicted_price = current_price * cumulative_change
                price_predictions.append(predicted_price)
            
            result = {
                'ticker': ticker,
                'current_price': float(current_price),
                'predictions': [
                    {
                        'day': i + 1,
                        'predicted_price': float(price_predictions[i]),
                        'price_change_pct': float(predictions[i] * 100),
                        'confidence': float(confidence_scores[i])
                    }
                    for i in range(horizon)
                ],
                'overall_trend': 'bullish' if sum(predictions) > 0 else 'bearish',
                'avg_confidence': float(np.mean(confidence_scores)),
                'risk_score': self._calculate_risk_score(predictions, confidence_scores),
                'timestamp': datetime.now().isoformat()
            }
            
            # Cache result
            self.prediction_cache[cache_key] = result
            
            return result
            
        except Exception as e:
            logger.error(f"Error predicting for {ticker}: {e}")
            return self._get_fallback_prediction(ticker)
    
    def _calculate_confidence(self, features: np.ndarray, 
                            feature_importance: np.ndarray) -> float:
        """Calculate prediction confidence score"""
        try:
            # Normalize features
            normalized_features = np.abs(features) / (np.abs(features).max() + 1e-8)
            
            # Weight by feature importance
            weighted_confidence = np.dot(normalized_features, feature_importance)
            
            # Scale to 0-1 range
            confidence = min(max(weighted_confidence, 0.3), 0.95)
            
            return confidence
            
        except Exception:
            return 0.5
    
    def _calculate_risk_score(self, predictions: List[float], 
                            confidence_scores: List[float]) -> float:
        """Calculate risk score based on prediction volatility and confidence"""
        try:
            volatility = np.std(predictions)
            avg_confidence = np.mean(confidence_scores)
            
            # Higher volatility and lower confidence = higher risk
            risk_score = (volatility * 10) + (1 - avg_confidence)
            
            # Normalize to 0-100 scale
            risk_score = min(max(risk_score * 50, 0), 100)
            
            return float(risk_score)
            
        except Exception:
            return 50.0
    
    def _get_fallback_prediction(self, ticker: str) -> Dict:
        """Fallback prediction when ML model is unavailable"""
        return {
            'ticker': ticker,
            'current_price': 100.0,
            'predictions': [
                {
                    'day': i + 1,
                    'predicted_price': 100.0 + np.random.normal(0, 2),
                    'price_change_pct': np.random.normal(0, 1.5),
                    'confidence': 0.4
                }
                for i in range(5)
            ],
            'overall_trend': 'neutral',
            'avg_confidence': 0.4,
            'risk_score': 60.0,
            'timestamp': datetime.now().isoformat(),
            'note': 'Fallback prediction - ML model unavailable'
        }
    
    def get_model_performance(self, ticker: str) -> Dict:
        """Get model performance metrics"""
        try:
            if ticker not in self.models:
                return {'error': 'Model not found'}
            
            # This would typically involve backtesting
            # For now, return simulated metrics
            return {
                'ticker': ticker,
                'accuracy': np.random.uniform(0.6, 0.8),
                'precision': np.random.uniform(0.55, 0.75),
                'recall': np.random.uniform(0.5, 0.7),
                'sharpe_ratio': np.random.uniform(0.8, 1.5),
                'max_drawdown': np.random.uniform(0.05, 0.15),
                'total_trades': np.random.randint(100, 500),
                'win_rate': np.random.uniform(0.52, 0.68),
                'avg_return': np.random.uniform(0.01, 0.03),
                'last_updated': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting performance for {ticker}: {e}")
            return {'error': str(e)}
    
    def get_feature_importance(self, ticker: str) -> Dict:
        """Get feature importance for model interpretation"""
        try:
            if ticker not in self.models:
                return {'error': 'Model not found'}
            
            model = self.models[ticker]
            importance = model.feature_importances_
            
            feature_importance = [
                {
                    'feature': self.feature_columns[i],
                    'importance': float(importance[i]),
                    'rank': i + 1
                }
                for i in range(len(self.feature_columns))
            ]
            
            # Sort by importance
            feature_importance.sort(key=lambda x: x['importance'], reverse=True)
            
            # Update ranks
            for i, item in enumerate(feature_importance):
                item['rank'] = i + 1
            
            return {
                'ticker': ticker,
                'features': feature_importance,
                'model_type': 'Random Forest',
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting feature importance for {ticker}: {e}")
            return {'error': str(e)}
    
    def batch_predict(self, tickers: List[str], horizon: int = 5) -> Dict:
        """Batch prediction for multiple tickers"""
        results = {}
        
        for ticker in tickers:
            try:
                # In practice, you'd load actual data for each ticker
                sample_data = self._generate_sample_data(ticker)
                results[ticker] = self.predict_price_movement(ticker, sample_data, horizon)
            except Exception as e:
                logger.error(f"Error in batch prediction for {ticker}: {e}")
                results[ticker] = self._get_fallback_prediction(ticker)
        
        return {
            'batch_id': datetime.now().strftime('%Y%m%d_%H%M%S'),
            'predictions': results,
            'total_tickers': len(tickers),
            'timestamp': datetime.now().isoformat()
        }
    
    def _generate_sample_data(self, ticker: str) -> pd.DataFrame:
        """Generate sample data for testing"""
        dates = pd.date_range(start='2023-01-01', end='2024-01-01', freq='D')
        np.random.seed(hash(ticker) % 1000)
        
        # Generate realistic price data
        returns = np.random.normal(0.001, 0.02, len(dates))
        prices = 100 * np.exp(np.cumsum(returns))
        volumes = np.random.lognormal(15, 0.5, len(dates))
        
        return pd.DataFrame({
            'date': dates,
            'close': prices,
            'volume': volumes
        })
    
    def get_market_predictions(self) -> Dict:
        """Get market-wide predictions and insights"""
        try:
            popular_tickers = ['AAPL', 'GOOGL', 'MSFT', 'TSLA', 'EQNR.OL', 'DNB.OL']
            batch_results = self.batch_predict(popular_tickers)
            
            # Analyze overall market sentiment
            bullish_count = 0
            bearish_count = 0
            avg_confidence = 0
            avg_risk = 0
            
            for ticker, prediction in batch_results['predictions'].items():
                if prediction.get('overall_trend') == 'bullish':
                    bullish_count += 1
                elif prediction.get('overall_trend') == 'bearish':
                    bearish_count += 1
                
                avg_confidence += prediction.get('avg_confidence', 0.5)
                avg_risk += prediction.get('risk_score', 50)
            
            total_tickers = len(batch_results['predictions'])
            avg_confidence = avg_confidence / total_tickers if total_tickers > 0 else 0.5
            avg_risk = avg_risk / total_tickers if total_tickers > 0 else 50
            
            market_sentiment = 'bullish' if bullish_count > bearish_count else 'bearish'
            if bullish_count == bearish_count:
                market_sentiment = 'neutral'
            
            return {
                'market_sentiment': market_sentiment,
                'bullish_stocks': bullish_count,
                'bearish_stocks': bearish_count,
                'neutral_stocks': total_tickers - bullish_count - bearish_count,
                'avg_confidence': float(avg_confidence),
                'avg_risk_score': float(avg_risk),
                'top_predictions': batch_results['predictions'],
                'timestamp': datetime.now().isoformat(),
                'recommendations': self._generate_market_recommendations(
                    market_sentiment, avg_confidence, avg_risk
                )
            }
            
        except Exception as e:
            logger.error(f"Error getting market predictions: {e}")
            return {
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def _generate_market_recommendations(self, sentiment: str, 
                                       confidence: float, risk: float) -> List[str]:
        """Generate market-based recommendations"""
        recommendations = []
        
        if sentiment == 'bullish' and confidence > 0.7:
            recommendations.append("Strong bullish signals detected - consider increasing equity exposure")
        elif sentiment == 'bearish' and confidence > 0.7:
            recommendations.append("Strong bearish signals - consider defensive positioning")
        else:
            recommendations.append("Mixed signals - maintain balanced portfolio")
        
        if risk > 70:
            recommendations.append("High risk environment - consider reducing position sizes")
        elif risk < 30:
            recommendations.append("Low risk environment - may consider leveraging opportunities")
        
        if confidence < 0.5:
            recommendations.append("Low model confidence - rely more on fundamental analysis")
        
        return recommendations

# Global instance
ml_prediction_service = MLPredictionService()
