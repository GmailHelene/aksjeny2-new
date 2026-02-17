"""Centralized service for PriceAlert CRUD to reduce duplication across blueprints."""
from __future__ import annotations
from typing import List, Optional, Dict, Any
import logging

from flask import current_app
from flask_login import current_user  # optional, not strictly required

try:
    from ..models.price_alert import PriceAlert
    from ..extensions import db
except Exception:  # pragma: no cover
    PriceAlert = None  # type: ignore
    db = None  # type: ignore

logger = logging.getLogger(__name__)

# Deprecation notice: This legacy AlertService is superseded by price_monitor_service + EmailQueue.
# It is retained only for backward compatibility and should not be started automatically.
if not globals().get('_ALERT_SERVICE_DEPRECATED_LOGGED'):
    logger.warning("DEPRECATED: app.services.alert_service.AlertService is legacy and should not be used for monitoring. Use price_monitor_service instead.")
    globals()['_ALERT_SERVICE_DEPRECATED_LOGGED'] = True


def list_user_alerts(user_id: int) -> List[Dict[str, Any]]:
    """Return all alerts for a user ordered active first, newest first."""
    if not PriceAlert:
        return []
    try:
        alerts = PriceAlert.query.filter_by(user_id=user_id).order_by(
            PriceAlert.is_active.desc(),
            PriceAlert.created_at.desc()
        ).all()
        return [a.to_dict() for a in alerts]
    except Exception as e:  # pragma: no cover
        logger.error(f"list_user_alerts error: {e}")
        return []


def create_alert(user_id: int, symbol: str, alert_type: str, target_price: float,
                 email_enabled: bool = True, browser_enabled: bool = False,
                 notes: Optional[str] = None) -> Dict[str, Any]:
    """Create a new PriceAlert and return dict form. Raises on validation errors."""
    if not PriceAlert or not db:  # pragma: no cover
        raise RuntimeError("PriceAlert model or db not available")
    symbol_up = symbol.strip().upper()
    if not symbol_up:
        raise ValueError("Symbol is required")
    if alert_type not in ("above", "below"):
        raise ValueError("alert_type must be 'above' or 'below'")
    if target_price <= 0:
        raise ValueError("target_price must be positive")
    alert = PriceAlert(
        user_id=user_id,
        ticker=symbol_up,
        symbol=symbol_up,
        target_price=float(target_price),
        alert_type=alert_type,
        is_active=True,
        email_enabled=email_enabled,
        browser_enabled=browser_enabled,
        notes=notes
    )
    db.session.add(alert)
    db.session.commit()
    # Register with monitor if available
    try:  # pragma: no cover
        from ..services.price_monitor_service import price_monitor
        price_monitor.add_alert(alert.to_dict())
    except Exception as mon_err:
        logger.warning(f"Alert monitor registration failed: {mon_err}")
    return alert.to_dict()


def delete_alert(user_id: int, alert_id: int) -> bool:
    """Delete alert if owned by user. Returns True if deleted."""
    if not PriceAlert or not db:
        return False
    try:
        alert = PriceAlert.query.filter_by(id=alert_id, user_id=user_id).first()
        if not alert:
            return False
        db.session.delete(alert)
        db.session.commit()
        return True
    except Exception as e:  # pragma: no cover
        logger.error(f"delete_alert error: {e}")
        try:
            db.session.rollback()
        except Exception:
            pass
        return False
"""
Alert service for monitoring stocks and triggering notifications
"""
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from ..services.data_service import DataService
from ..services.notification_service import notification_service
from ..services.external_apis import ExternalAPIService
from ..models.user import User
from ..models.watchlist import WatchlistItem
from ..extensions import db
import threading
import time

logger = logging.getLogger(__name__)

class AlertService:
    """Service for monitoring stocks and creating alerts"""
    
    def __init__(self):
        self.running = False
        self.thread = None
        self.check_interval = 300  # 5 minutes
        self.external_api = ExternalAPIService()
        
    def start_monitoring(self):
        """Start background monitoring thread"""
        logger.warning("DEPRECATED: start_monitoring called on legacy AlertService - no action taken")
        return
    
    def stop_monitoring(self):
        """Stop background monitoring"""
        self.running = False
        if self.thread:
            self.thread.join()
        logger.info("Alert monitoring stopped")
    
    def _monitoring_loop(self):
        """Main monitoring loop"""
        while self.running:
            try:
                self._check_all_alerts()
                time.sleep(self.check_interval)
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                time.sleep(30)  # Wait 30 seconds on error
    
    def _check_all_alerts(self):
        """Check all types of alerts"""
        try:
            # Check watchlist price alerts
            self._check_watchlist_alerts()
            
            # Check insider trading alerts
            self._check_insider_trading_alerts()
            
            # Check earnings alerts
            self._check_earnings_alerts()
            
            # Check analyst rating changes
            self._check_analyst_rating_alerts()
            
            # Check volume spikes
            self._check_volume_spike_alerts()
            
            logger.info("Completed alert check cycle")
            
        except Exception as e:
            logger.error(f"Error checking alerts: {e}")
    
    def _check_watchlist_alerts(self):
        """Check for price alerts on watchlist items"""
        try:
            # Get all watchlist items with price alerts
            watchlist_items = WatchlistItem.query.filter(
                WatchlistItem.price_alert_enabled == True
            ).all()
            
            for item in watchlist_items:
                if not item.price_alert_target:
                    continue
                
                # Get current price
                stock_info = DataService.get_stock_info(item.ticker)
                if not stock_info:
                    continue
                
                current_price = stock_info.get('regularMarketPrice', 0)
                target_price = item.price_alert_target
                condition = item.price_alert_condition  # 'above' or 'below'
                
                # Check if alert condition is met
                alert_triggered = False
                if condition == 'above' and current_price >= target_price:
                    alert_triggered = True
                elif condition == 'below' and current_price <= target_price:
                    alert_triggered = True
                
                if alert_triggered:
                    # Create notification
                    notification_service.create_price_alert(
                        user_id=item.user_id,
                        ticker=item.ticker,
                        target_price=target_price,
                        condition=condition,
                        current_price=current_price
                    )
                    
                    # Disable the alert to prevent spam
                    item.price_alert_enabled = False
                    db.session.commit()
                    
                    logger.info(f"Price alert triggered for {item.ticker}: {current_price} {condition} {target_price}")
                    
        except Exception as e:
            logger.error(f"Error checking watchlist alerts: {e}")
    
    def _check_insider_trading_alerts(self):
        """Check for new insider trading activity"""
        try:
            # Get popular Norwegian stocks
            popular_tickers = ['EQNR.OL', 'DNB.OL', 'TEL.OL', 'YAR.OL', 'NHY.OL', 'MOWI.OL']
            
            for ticker in popular_tickers:
                try:
                    # Get insider trading data
                    insider_data = self.external_api.get_insider_trading(ticker)
                    if not insider_data:
                        continue
                    
                    # Check for recent insider trades (last 2 days)
                    recent_cutoff = datetime.now() - timedelta(days=2)
                    
                    for trade in insider_data[:3]:  # Check latest 3 trades
                        trade_date = datetime.strptime(trade['transaction_date'], '%Y-%m-%d')
                        
                        if trade_date >= recent_cutoff:
                            # Check if we've already alerted about this trade
                            if not self._has_alerted_for_trade(ticker, trade):
                                # Find users who have this stock in their watchlist
                                users_to_alert = self._get_users_watching_ticker(ticker)
                                
                                for user_id in users_to_alert:
                                    notification_service.create_insider_trading_alert(
                                        user_id=user_id,
                                        ticker=ticker,
                                        insider_name=trade['reporting_name'],
                                        transaction_type=trade['transaction_type'],
                                        shares=trade['securities_transacted'],
                                        price=trade['price']
                                    )
                                
                                # Mark as alerted
                                self._mark_trade_as_alerted(ticker, trade)
                                
                    time.sleep(2)  # Rate limiting
                    
                except Exception as e:
                    logger.error(f"Error checking insider trading for {ticker}: {e}")
                    continue
                    
        except Exception as e:
            logger.error(f"Error checking insider trading alerts: {e}")
    
    def _check_earnings_alerts(self):
        """Check for upcoming earnings announcements"""
        try:
            # Get earnings calendar
            earnings_calendar = self.external_api.get_earnings_calendar()
            if not earnings_calendar:
                return
            
            # Check for earnings in next 3 days
            alert_cutoff = datetime.now() + timedelta(days=3)
            
            for earnings in earnings_calendar:
                earnings_date = datetime.strptime(earnings['date'], '%Y-%m-%d')
                
                if earnings_date <= alert_cutoff:
                    ticker = earnings['symbol']
                    
                    # Check if we've already alerted about this earnings
                    if not self._has_alerted_for_earnings(ticker, earnings_date):
                        # Find users who have this stock in their watchlist
                        users_to_alert = self._get_users_watching_ticker(ticker)
                        
                        for user_id in users_to_alert:
                            notification_service.create_earnings_alert(
                                user_id=user_id,
                                ticker=ticker,
                                earnings_date=earnings_date,
                                eps_estimate=earnings['eps_estimated']
                            )
                        
                        # Mark as alerted
                        self._mark_earnings_as_alerted(ticker, earnings_date)
                        
        except Exception as e:
            logger.error(f"Error checking earnings alerts: {e}")
    
    def _check_analyst_rating_alerts(self):
        """Check for analyst rating changes"""
        try:
            # Get popular stocks
            popular_tickers = ['EQNR.OL', 'DNB.OL', 'AAPL', 'MSFT', 'GOOGL']
            
            for ticker in popular_tickers:
                try:
                    # Get analyst recommendations
                    recommendations = self.external_api.get_analyst_recommendations(ticker)
                    if not recommendations:
                        continue
                    
                    # Check for recent rating changes (last 1 day)
                    recent_cutoff = datetime.now() - timedelta(days=1)
                    
                    for rec in recommendations[:2]:  # Check latest 2 recommendations
                        rec_date = datetime.strptime(rec['date'], '%Y-%m-%d')
                        
                        if rec_date >= recent_cutoff:
                            # Check if we've already alerted about this rating
                            if not self._has_alerted_for_rating(ticker, rec):
                                # Find users who have this stock in their watchlist
                                users_to_alert = self._get_users_watching_ticker(ticker)
                                
                                # Simulate old rating for demo
                                old_rating = 'HOLD'
                                new_rating = rec['recommendation']
                                
                                for user_id in users_to_alert:
                                    notification_service.create_analyst_rating_alert(
                                        user_id=user_id,
                                        ticker=ticker,
                                        analyst_firm=rec['analyst_company'],
                                        old_rating=old_rating,
                                        new_rating=new_rating,
                                        target_price=rec['target_price']
                                    )
                                
                                # Mark as alerted
                                self._mark_rating_as_alerted(ticker, rec)
                                
                    time.sleep(2)  # Rate limiting
                    
                except Exception as e:
                    logger.error(f"Error checking analyst ratings for {ticker}: {e}")
                    continue
                    
        except Exception as e:
            logger.error(f"Error checking analyst rating alerts: {e}")
    
    def _check_volume_spike_alerts(self):
        """Check for unusual volume spikes"""
        try:
            # Get market data for popular stocks
            oslo_stocks = DataService.get_oslo_bors_overview()
            
            for ticker, stock_data in oslo_stocks.items():
                current_volume = stock_data.get('volume', 0)
                
                # Simple volume spike detection (more than 2x normal volume)
                # In a real system, you'd calculate average volume over time
                estimated_normal_volume = current_volume * 0.4  # Rough estimate
                
                if current_volume > estimated_normal_volume * 2:
                    # Find users who have this stock in their watchlist
                    users_to_alert = self._get_users_watching_ticker(ticker)
                    
                    for user_id in users_to_alert:
                        notification_service.create_notification(
                            user_id=user_id,
                            notification_type='VOLUME_SPIKE',
                            title=f'Volumøkning: {ticker}',
                            message=f'{ticker} viser uvanlig høyt handelsvolum: {current_volume:,} aksjer',
                            ticker=ticker,
                            priority='medium',
                            action_url=f'/stocks/details/{ticker}',
                            metadata={
                                'current_volume': current_volume,
                                'normal_volume': estimated_normal_volume
                            }
                        )
                    
                    logger.info(f"Volume spike alert for {ticker}: {current_volume:,} volume")
                    
        except Exception as e:
            logger.error(f"Error checking volume spike alerts: {e}")
    
    def _get_users_watching_ticker(self, ticker: str) -> List[int]:
        """Get list of user IDs who have this ticker in their watchlist"""
        try:
            watchlist_items = WatchlistItem.query.filter_by(ticker=ticker).all()
            return [item.user_id for item in watchlist_items]
        except Exception as e:
            logger.error(f"Error getting users watching {ticker}: {e}")
            return []
    
    def _has_alerted_for_trade(self, ticker: str, trade: Dict) -> bool:
        """Check if we've already alerted for this insider trade"""
        # In a real system, you'd store this in a database
        # For now, we'll use a simple time-based check
        return False
    
    def _mark_trade_as_alerted(self, ticker: str, trade: Dict):
        """Mark insider trade as alerted"""
        # In a real system, you'd store this in a database
        pass
    
    def _has_alerted_for_earnings(self, ticker: str, earnings_date: datetime) -> bool:
        """Check if we've already alerted for this earnings announcement"""
        # In a real system, you'd store this in a database
        return False
    
    def _mark_earnings_as_alerted(self, ticker: str, earnings_date: datetime):
        """Mark earnings announcement as alerted"""
        # In a real system, you'd store this in a database
        pass
    
    def _has_alerted_for_rating(self, ticker: str, rating: Dict) -> bool:
        """Check if we've already alerted for this analyst rating"""
        # In a real system, you'd store this in a database
        return False
    
    def _mark_rating_as_alerted(self, ticker: str, rating: Dict):
        """Mark analyst rating as alerted"""
        # In a real system, you'd store this in a database
        pass
    
    def create_manual_alert(self, 
                          user_id: int,
                          ticker: str,
                          alert_type: str,
                          condition: str,
                          target_value: float) -> bool:
        """Create a manual alert for a user"""
        try:
            # This would typically be stored in a database
            # For now, we'll just create an immediate notification
            if alert_type == 'price':
                notification_service.create_notification(
                    user_id=user_id,
                    notification_type='PRICE_ALERT',
                    title=f'Prisvarsel opprettet: {ticker}',
                    message=f'Du vil få varsel når {ticker} {condition} {target_value:.2f}',
                    ticker=ticker,
                    priority='medium',
                    action_url=f'/stocks/details/{ticker}',
                    metadata={
                        'alert_type': alert_type,
                        'condition': condition,
                        'target_value': target_value
                    }
                )
            
            return True
            
        except Exception as e:
            logger.error(f"Error creating manual alert: {e}")
            return False
    
    def get_alert_statistics(self) -> Dict[str, Any]:
        """Get statistics about alert system"""
        try:
            # In a real system, you'd get these from the database
            return {
                'total_alerts_created': 0,
                'active_price_alerts': 0,
                'users_with_alerts': 0,
                'most_watched_ticker': 'EQNR.OL',
                'alert_types': {
                    'price_alerts': 0,
                    'insider_trading': 0,
                    'earnings': 0,
                    'analyst_ratings': 0,
                    'volume_spikes': 0
                }
            }
        except Exception as e:
            logger.error(f"Error getting alert statistics: {e}")
            return {}

# Global instance (kept for import compatibility, does not auto-start)
alert_service = AlertService()
