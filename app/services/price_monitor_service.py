"""
Price Monitor Service for tracking stock prices and triggering alerts
"""
import logging
import asyncio
from typing import List, Dict, Optional
from datetime import datetime, timedelta
from ..models.price_alert import PriceAlert, AlertNotificationSettings, EmailQueue
from ..models.user import User
from ..services.data_service import DataService
from ..services.email_service import EmailService
from ..extensions import db
import threading
import time
from flask import current_app
import os
import uuid
from sqlalchemy import inspect as _inspect
from datetime import time as _time

logger = logging.getLogger(__name__)

class PriceMonitorService:
    """Service for monitoring stock prices and managing alerts"""
    
    def __init__(self, app=None):
        self.monitoring_active = False
        self.monitor_thread = None
        self.check_interval = 300  # 5 minutes between checks
        self.last_check = None
        self.app = app
        self.instance_id = uuid.uuid4().hex[:8]
        self._start_count = 0
        # Metrics counters
        self.alerts_checked_total = 0
        self.alerts_triggered_total = 0
        self.symbols_checked_total = 0
        
    def start_monitoring(self, app=None):
        """Start the price monitoring service"""
        if app:
            self.app = app
            
        if self.monitoring_active:
            logger.warning(f"Price monitoring already active (instance={self.instance_id})")
            return
        
        if not self.app:
            logger.error("No Flask app provided to price monitor")
            return
        
        self._start_count += 1
        self._start_time = time.time()
        self.monitoring_active = True
        try:
            from ..models import ServiceRuntime
            ServiceRuntime.record_start('price_monitor')
        except Exception as _sr_err:
            logger.debug(f"ServiceRuntime record_start failed (price_monitor): {_sr_err}")
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True, name=f"PriceMonitor-{self.instance_id}")
        self.monitor_thread.start()
        # compatibility attributes for external status checks
        setattr(self, '_monitoring_started', True)
        setattr(self, '_thread', self.monitor_thread)
        try:
            engine = db.get_engine() if hasattr(db, 'get_engine') else db.engine
            db_path = str(getattr(engine.url, 'database', 'unknown'))
            tables = []
            try:
                insp = _inspect(engine)
                tables = sorted(insp.get_table_names())
            except Exception as insp_err:
                tables = [f"<inspect error: {insp_err}>"]
            logger.info(
                f"🚀 Price monitoring service started instance={self.instance_id} start_count={self._start_count} "
                f"thread_ident={self.monitor_thread.ident} db_path={db_path} tables={tables}"
            )
        except Exception as meta_err:
            logger.warning(f"Could not log engine metadata on start: {meta_err}")
    
    def stop_monitoring(self):
        """Stop the price monitoring service"""
        self.monitoring_active = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)
        setattr(self, '_monitoring_started', False)
        logger.info("🛑 Price monitoring service stopped")
    
    def _monitor_loop(self):
        """Main monitoring loop that runs in background thread"""
        logger.info(f"PriceMonitorService loop start instance={self.instance_id} thread_ident={threading.get_ident()}")
        while self.monitoring_active:
            try:
                if self.app:
                    with self.app.app_context():
                        self._check_all_alerts()
                        self.last_check = datetime.utcnow()
                else:
                    logger.error("No app context available for price monitoring")
                time.sleep(self.check_interval)
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                time.sleep(60)  # Wait 1 minute before retrying on error
    
    def _check_all_alerts(self):
        """Check all active price alerts - assumes app context is already set"""
        try:
            # Ensure we're in app context 
            if not self.app:
                logger.error("No Flask app available for database operations")
                return
            # Verify table exists before querying to avoid OperationalError spam during startup/migrations
            try:
                insp = _inspect(db.engine)
                if not insp.has_table('price_alerts'):
                    logger.debug(f"instance={self.instance_id} skip cycle: price_alerts table missing")
                    return
            except Exception as insp_err:
                logger.warning(f"instance={self.instance_id} inspect error: {insp_err}")
                return
                
            # Get all active alerts within app context
            active_alerts = PriceAlert.query.filter_by(is_active=True).all()
            
            if not active_alerts:
                logger.debug("No active alerts to check")
                return
            # Increment counters for raw alerts and grouped symbols
            self.alerts_checked_total += len(active_alerts)
            
            # Group alerts by symbol to minimize API calls
            alerts_by_symbol = {}
            for alert in active_alerts:
                symbol = alert.symbol.upper()
                if symbol not in alerts_by_symbol:
                    alerts_by_symbol[symbol] = []
                alerts_by_symbol[symbol].append(alert)
            self.symbols_checked_total += len(alerts_by_symbol)
            
            logger.info(f"📊 instance={self.instance_id} Checking {len(active_alerts)} alerts for {len(alerts_by_symbol)} symbols")
            
            # Check each symbol
            for symbol, alerts in alerts_by_symbol.items():
                try:
                    current_price = self._get_current_price(symbol)
                    if current_price:
                        self._check_alerts_for_symbol(symbol, current_price, alerts)
                    else:
                        logger.warning(f"Could not get price for {symbol}")
                except Exception as e:
                    logger.error(f"Error checking alerts for {symbol}: {e}")
            
            # Commit all changes
            db.session.commit()
            
        except Exception as e:
            logger.error(f"Error in _check_all_alerts: {e}")
            try:
                db.session.rollback()
            except Exception as rollback_error:
                logger.error(f"Error during rollback: {rollback_error}")
    
    def _get_current_price(self, symbol: str) -> Optional[float]:
        """Get current price for a symbol"""
        try:
            if DataService:
                # Try to get live quote
                quote_data = DataService.get_live_quote(symbol)
                if quote_data and 'price' in quote_data:
                    return float(quote_data['price'])
                
                # Fallback to stock info
                stock_info = DataService.get_stock_info(symbol)
                if stock_info and 'currentPrice' in stock_info:
                    return float(stock_info['currentPrice'])
                elif stock_info and 'regularMarketPrice' in stock_info:
                    return float(stock_info['regularMarketPrice'])
            
            logger.warning(f"No price data available for {symbol}")
            return None
            
        except Exception as e:
            logger.error(f"Error getting price for {symbol}: {e}")
            return None
    
    def _check_alerts_for_symbol(self, symbol: str, current_price: float, alerts: List[PriceAlert]):
        """Check all alerts for a specific symbol"""
        triggered_alerts = []
        
        for alert in alerts:
            try:
                if alert.check_and_trigger(current_price):
                    triggered_alerts.append(alert)
                    logger.info(f"🚨 Alert triggered: {alert.symbol} reached {current_price} (target: {alert.target_price})")
            except Exception as e:
                logger.error(f"Error checking alert {alert.id}: {e}")
        
        # Send notifications for triggered alerts
        if triggered_alerts:
            # Increment triggered counter
            self.alerts_triggered_total += len(triggered_alerts)
            self._send_alert_notifications(triggered_alerts)
    
    def _send_alert_notifications(self, alerts: List[PriceAlert]):
        """Send email notifications for triggered alerts"""
        # Group alerts by user to send fewer emails
        alerts_by_user = {}
        for alert in alerts:
            user_id = alert.user_id
            if user_id not in alerts_by_user:
                alerts_by_user[user_id] = []
            alerts_by_user[user_id].append(alert)
        
        for user_id, user_alerts in alerts_by_user.items():
            try:
                user = User.query.get(user_id)
                if user and user.email:
                    # Prefer unified preferences; fallback to legacy settings
                    language = getattr(user, 'preferred_language', 'no') or 'no'
                    should_email = True
                    prefs = None
                    try:
                        from ..services.notification_preferences_service import get_prefs
                        prefs = get_prefs(user_id)
                        should_email = bool(getattr(prefs, 'email_enabled', True) and getattr(prefs, 'email_price_alerts', True))
                        # Respect quiet hours if configured
                        try:
                            if self._is_quiet_hours(prefs):
                                should_email = False
                                logger.info(f"Quiet hours active for user {user_id}; suppressing immediate email send")
                        except Exception as _qh_err:
                            logger.debug(f"Quiet hours check failed for user {user_id}: {_qh_err}")
                    except Exception as _pref_err:
                        logger.debug(f"Unified prefs unavailable, falling back (user={user_id}): {_pref_err}")
                        try:
                            settings = AlertNotificationSettings.get_or_create_for_user(user_id)
                            should_email = bool(getattr(settings, 'email_enabled', True) and getattr(settings, 'email_instant', True))
                            language = getattr(settings, 'language', language)
                        except Exception:
                            should_email = True
                    if should_email:
                        # Build payload for queue
                        alert_payload = [
                            {
                                'symbol': a.symbol,
                                'current_price': a.current_price,
                                'target_price': a.target_price,
                                'alert_type': a.alert_type,
                                'triggered_at': a.triggered_at.isoformat() if a.triggered_at else None
                            } for a in user_alerts
                        ]
                        EmailQueue.enqueue(user_id, {
                            'type': 'price_alert',
                            'alerts': alert_payload,
                            'language': language,
                            'email': user.email
                        })
                        self._send_email_notification(user, user_alerts, language)
            except Exception as e:
                logger.error(f"Error sending notification to user {user_id}: {e}")

    def _is_quiet_hours(self, prefs) -> bool:
        """Return True if current local time for prefs.timezone is within quiet hours.

        Quiet hours are defined by start/end in HH:MM (24h). If start < end, it's a same-day window.
        If start > end, it crosses midnight (e.g., 22:00-08:00).
        If parsing fails, assume not quiet to avoid suppressing important alerts.
        """
        try:
            start_str = getattr(prefs, 'quiet_hours_start', '22:00') or '22:00'
            end_str = getattr(prefs, 'quiet_hours_end', '08:00') or '08:00'
            tz_name = getattr(prefs, 'timezone', 'Europe/Oslo') or 'Europe/Oslo'
            # Lazy import pytz to avoid startup cost
            try:
                import pytz  # type: ignore
                tz = pytz.timezone(tz_name)
                now_local = datetime.now(tz)
            except Exception:
                # Fallback: naive local time without tz conversion
                now_local = datetime.now()
            def _parse_hhmm(s: str) -> _time:
                hh, mm = s.split(':')
                return _time(hour=int(hh), minute=int(mm))
            start_t = _parse_hhmm(start_str)
            end_t = _parse_hhmm(end_str)
            now_t = now_local.time()
            if start_t == end_t:
                return False
            if start_t < end_t:
                return start_t <= now_t < end_t
            else:
                return now_t >= start_t or now_t < end_t
        except Exception as e:
            logger.debug(f"Quiet hours evaluation error: {e}")
            return False
    
    def _send_email_notification(self, user: User, alerts: List[PriceAlert], language: str = 'no'):
        """Send email notification to user"""
        try:
            if len(alerts) == 1:
                alert = alerts[0]
                subject = f"Prisvarsel utløst: {alert.symbol}"
                if language == 'en':
                    subject = f"Price Alert Triggered: {alert.symbol}"
            else:
                subject = f"{len(alerts)} prisvarsler utløst"
                if language == 'en':
                    subject = f"{len(alerts)} Price Alerts Triggered"
            
            # Prepare email content
            alert_details = []
            for alert in alerts:
                details = {
                    'symbol': alert.symbol,
                    'company_name': alert.company_name or alert.symbol,
                    'current_price': alert.current_price,
                    'target_price': alert.target_price,
                    'alert_type': alert.alert_type,
                    'triggered_at': alert.triggered_at
                }
                alert_details.append(details)
            
            # Send email using EmailService
            if EmailService:
                template = 'price_alert_triggered.html'
                EmailService.send_email(
                    to_email=user.email,
                    subject=subject,
                    template=template,
                    context={
                        'user': user,
                        'alerts': alert_details,
                        'language': language,
                        'alert_count': len(alerts)
                    }
                )
                
                # Mark emails as sent
                for alert in alerts:
                    alert.email_sent = True
                
                logger.info(f"📧 Sent alert notification to {user.email} for {len(alerts)} alerts")
            else:
                logger.error("EmailService not available")
                
        except Exception as e:
            logger.error(f"Error sending email to {user.email}: {e}")
    
    def create_alert(self, user_id: int, symbol: str, target_price: float, 
                    alert_type: str, company_name: str = None, notes: str = None) -> PriceAlert:
        """Create a new price alert"""
        try:
            # Check if user has subscription for alerts
            user = User.query.get(user_id)
            if not user:
                raise ValueError("User not found")
            
            if not user.has_subscription:
                # Check if user has reached free alert limit
                active_alerts_count = PriceAlert.query.filter_by(
                    user_id=user_id, 
                    is_active=True
                ).count()
                
                if active_alerts_count >= 3:  # Free users get 3 alerts max
                    raise ValueError("Du har nådd grensen for gratis prisvarsler. Oppgrader til Pro for ubegrenset tilgang.")
            
            # Validate input
            if alert_type not in ['above', 'below']:
                raise ValueError("Alert type must be 'above' or 'below'")
            
            if target_price <= 0:
                raise ValueError("Target price must be positive")
            
            symbol = symbol.upper().strip()
            if not symbol:
                raise ValueError("Symbol cannot be empty")
            
            # Get current price for validation
            current_price = self._get_current_price(symbol)
            
            # Create the alert
            alert = PriceAlert(
                user_id=user_id,
                ticker=symbol,  # Set ticker to same value as symbol
                symbol=symbol,
                target_price=target_price,
                alert_type=alert_type,
                current_price=current_price,
                company_name=company_name,
                notes=notes
            )
            
            db.session.add(alert)
            db.session.commit()
            
            logger.info(f"✅ Created price alert: {symbol} {alert_type} {target_price} for user {user_id}")
            return alert
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error creating alert: {e}")
            raise
    
    def delete_alert(self, alert_id: int, user_id: int) -> bool:
        """Delete a price alert"""
        try:
            alert = PriceAlert.query.filter_by(id=alert_id, user_id=user_id).first()
            if not alert:
                return False
            
            db.session.delete(alert)
            db.session.commit()
            
            logger.info(f"🗑️ Deleted price alert {alert_id} for user {user_id}")
            return True
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error deleting alert {alert_id}: {e}")
            return False
    
    def get_user_alerts(self, user_id: int) -> List[Dict]:
        """Get all alerts for a user"""
        try:
            alerts = PriceAlert.query.filter_by(user_id=user_id).order_by(
                PriceAlert.is_active.desc(),
                PriceAlert.created_at.desc()
            ).all()
            
            return [alert.to_dict() for alert in alerts]
            
        except Exception as e:
            logger.error(f"Error getting alerts for user {user_id}: {e}")
            return []
    
    def update_alert_settings(self, user_id: int, settings_data: Dict) -> bool:
        """Update user's alert notification settings"""
        try:
            settings = AlertNotificationSettings.get_or_create_for_user(user_id)
            
            if 'email_enabled' in settings_data:
                settings.email_enabled = bool(settings_data['email_enabled'])
            if 'email_instant' in settings_data:
                settings.email_instant = bool(settings_data['email_instant'])
            if 'email_daily_summary' in settings_data:
                settings.email_daily_summary = bool(settings_data['email_daily_summary'])
            if 'language' in settings_data:
                settings.language = settings_data['language']
            
            settings.updated_at = datetime.utcnow()
            db.session.commit()
            
            logger.info(f"📝 Updated alert settings for user {user_id}")
            return True
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error updating alert settings for user {user_id}: {e}")
            return False
    
    def get_service_status(self) -> Dict:
        """Get monitoring service status"""
        return {
            'monitoring_active': self.monitoring_active,
            'last_check': self.last_check.isoformat() if self.last_check else None,
            'check_interval_minutes': self.check_interval // 60,
            'total_active_alerts': PriceAlert.query.filter_by(is_active=True).count(),
            'alerts_checked_total': self.alerts_checked_total,
            'alerts_triggered_total': self.alerts_triggered_total,
            'symbols_checked_total': self.symbols_checked_total,
            'start_count': self._start_count
        }


# Global instance (no side-effect start). Add compatibility attrs for health checks
price_monitor = PriceMonitorService()
price_monitor._monitoring_started = False  # compatibility flag
price_monitor._thread = None
