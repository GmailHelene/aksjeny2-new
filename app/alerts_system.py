"""
Real-time Alerts System for CMC Markets-style MT4 functionality
Professional alert system with email, SMS, and push notifications
"""

import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable
from enum import Enum
import json
import logging
import threading
import time
from dataclasses import dataclass, asdict

# Deprecation: This module (alerts_system) is legacy and replaced by price_monitor_service + EmailQueue.
import logging as _legacy_logging
if not globals().get('_ALERTS_SYSTEM_DEPRECATED_LOGGED'):
    _legacy_logging.warning("DEPRECATED: app.alerts_system is legacy; new price alert functionality uses price_monitor_service.")
    globals()['_ALERTS_SYSTEM_DEPRECATED_LOGGED'] = True

class AlertType(Enum):
    PRICE = "PRICE_ALERT"
    INDICATOR = "INDICATOR_ALERT"
    PATTERN = "PATTERN_ALERT"
    NEWS = "NEWS_ALERT"
    VOLUME = "VOLUME_ALERT"
    VOLATILITY = "VOLATILITY_ALERT"

class AlertCondition(Enum):
    GREATER_THAN = "GREATER_THAN"
    LESS_THAN = "LESS_THAN"
    EQUALS = "EQUALS"
    CROSSES_ABOVE = "CROSSES_ABOVE"
    CROSSES_BELOW = "CROSSES_BELOW"
    BETWEEN = "BETWEEN"
    OUTSIDE = "OUTSIDE"

class AlertStatus(Enum):
    ACTIVE = "ACTIVE"
    TRIGGERED = "TRIGGERED"
    EXPIRED = "EXPIRED"
    DISABLED = "DISABLED"

class NotificationChannel(Enum):
    EMAIL = "EMAIL"
    SMS = "SMS"
    PUSH = "PUSH"
    WEBHOOK = "WEBHOOK"

@dataclass
class Alert:
    """Professional trading alert"""
    id: str
    user_id: str
    symbol: str
    alert_type: AlertType
    condition: AlertCondition
    value: float
    secondary_value: Optional[float] = None  # For BETWEEN/OUTSIDE conditions
    indicator_name: Optional[str] = None
    indicator_params: Optional[Dict] = None
    expiry_date: Optional[datetime] = None
    notification_channels: List[NotificationChannel] = None
    message: Optional[str] = None
    created_at: datetime = None
    status: AlertStatus = AlertStatus.ACTIVE
    last_checked: Optional[datetime] = None
    triggered_at: Optional[datetime] = None
    trigger_count: int = 0
    max_triggers: int = 1
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.notification_channels is None:
            self.notification_channels = [NotificationChannel.EMAIL]

    # Compatibility property for legacy code expecting alert_id
    @property
    def alert_id(self):
        return self.id

@dataclass
class NotificationSettings:
    """User notification preferences"""
    email: Optional[str] = None
    phone: Optional[str] = None
    push_token: Optional[str] = None
    webhook_url: Optional[str] = None
    email_enabled: bool = True
    sms_enabled: bool = False
    push_enabled: bool = True
    quiet_hours_start: Optional[str] = None  # "22:00"
    quiet_hours_end: Optional[str] = None    # "07:00"
    timezone: str = "UTC"

class AlertManager:
    """Professional alert management system"""
    
    def __init__(self):
        self.alerts: Dict[str, Alert] = {}
        self.user_settings: Dict[str, NotificationSettings] = {}
        self.notification_handlers: Dict[NotificationChannel, Callable] = {}
        self.market_data: Dict[str, Dict] = {}
        self.running = False
        self.check_interval = 1  # seconds
        self._setup_notification_handlers()
        
    def _setup_notification_handlers(self):
        """Setup notification handlers"""
        self.notification_handlers[NotificationChannel.EMAIL] = self._send_email
        self.notification_handlers[NotificationChannel.SMS] = self._send_sms
        self.notification_handlers[NotificationChannel.PUSH] = self._send_push
        self.notification_handlers[NotificationChannel.WEBHOOK] = self._send_webhook

    # --- Added compatibility helper methods expected by professional_analytics ---
    def get_active_alerts(self):
        return [a for a in self.alerts.values() if a.status == AlertStatus.ACTIVE]

    def get_recent_alerts(self, limit: int = 10):
        # Return last N alerts by created_at
        return sorted(self.alerts.values(), key=lambda a: a.created_at)[-limit:]
        
    def add_alert(self, alert: Alert) -> bool:
        """Add a new alert"""
        try:
            self.alerts[alert.id] = alert
            logging.info(f"Alert added: {alert.id} for {alert.symbol}")
            return True
        except Exception as e:
            logging.error(f"Error adding alert: {e}")
            return False
            
    def remove_alert(self, alert_id: str, user_id: str) -> bool:
        """Remove an alert"""
        if alert_id in self.alerts and self.alerts[alert_id].user_id == user_id:
            del self.alerts[alert_id]
            logging.info(f"Alert removed: {alert_id}")
            return True
        return False
        
    def get_user_alerts(self, user_id: str) -> List[Alert]:
        """Get all alerts for a user"""
        return [alert for alert in self.alerts.values() if alert.user_id == user_id]
        
    def update_user_settings(self, user_id: str, settings: NotificationSettings):
        """Update user notification settings"""
        self.user_settings[user_id] = settings
        
    def update_market_data(self, symbol: str, data: Dict[str, Any]):
        """Update market data for alert checking"""
        self.market_data[symbol] = {
            **data,
            'timestamp': datetime.now()
        }
        
        # Check alerts for this symbol
        self._check_symbol_alerts(symbol)
        
    def start_monitoring(self):
        """Start the alert monitoring system"""
        logging.warning("DEPRECATED: AlertManager.start_monitoring called - legacy system disabled. No loop started.")
        return
        
    def stop_monitoring(self):
        """Stop the alert monitoring system"""
        self.running = False
        logging.info("Alert monitoring stopped")
        
    def _monitoring_loop(self):
        """Main monitoring loop"""
        while self.running:
            try:
                self._check_all_alerts()
                self._cleanup_expired_alerts()
                time.sleep(self.check_interval)
            except Exception as e:
                logging.error(f"Error in monitoring loop: {e}")
                time.sleep(5)  # Wait before retrying
                
    def _check_all_alerts(self):
        """Check all active alerts"""
        for alert in self.alerts.values():
            if alert.status == AlertStatus.ACTIVE:
                self._check_alert(alert)
                
    def _check_symbol_alerts(self, symbol: str):
        """Check alerts for a specific symbol"""
        for alert in self.alerts.values():
            if alert.symbol == symbol and alert.status == AlertStatus.ACTIVE:
                self._check_alert(alert)
                
    def _check_alert(self, alert: Alert):
        """Check if an alert should be triggered"""
        try:
            alert.last_checked = datetime.now()
            
            # Check if alert has expired
            if alert.expiry_date and datetime.now() > alert.expiry_date:
                alert.status = AlertStatus.EXPIRED
                return
                
            # Get market data
            if alert.symbol not in self.market_data:
                return
                
            market_data = self.market_data[alert.symbol]
            
            # Check alert condition
            should_trigger = self._evaluate_alert_condition(alert, market_data)
            
            if should_trigger:
                self._trigger_alert(alert, market_data)
                
        except Exception as e:
            logging.error(f"Error checking alert {alert.id}: {e}")
            
    def _evaluate_alert_condition(self, alert: Alert, market_data: Dict) -> bool:
        """Evaluate if alert condition is met"""
        
        if alert.alert_type == AlertType.PRICE_ALERT:
            current_price = market_data.get('price', market_data.get('close', 0))
            return self._check_condition(alert.condition, current_price, alert.value, alert.secondary_value)
            
        elif alert.alert_type == AlertType.INDICATOR_ALERT:
            # Calculate indicator value
            indicator_value = self._calculate_indicator(alert, market_data)
            if indicator_value is not None:
                return self._check_condition(alert.condition, indicator_value, alert.value, alert.secondary_value)
                
        elif alert.alert_type == AlertType.VOLUME_ALERT:
            current_volume = market_data.get('volume', 0)
            avg_volume = market_data.get('avg_volume', current_volume)
            volume_ratio = current_volume / avg_volume if avg_volume > 0 else 0
            return self._check_condition(alert.condition, volume_ratio, alert.value, alert.secondary_value)
            
        elif alert.alert_type == AlertType.VOLATILITY_ALERT:
            volatility = market_data.get('volatility', 0)
            return self._check_condition(alert.condition, volatility, alert.value, alert.secondary_value)
            
        return False
        
    def _check_condition(self, condition: AlertCondition, current_value: float, 
                        target_value: float, secondary_value: Optional[float] = None) -> bool:
        """Check if condition is met"""
        
        if condition == AlertCondition.GREATER_THAN:
            return current_value > target_value
        elif condition == AlertCondition.LESS_THAN:
            return current_value < target_value
        elif condition == AlertCondition.EQUALS:
            tolerance = target_value * 0.001  # 0.1% tolerance
            return abs(current_value - target_value) <= tolerance
        elif condition == AlertCondition.BETWEEN:
            if secondary_value is not None:
                return min(target_value, secondary_value) <= current_value <= max(target_value, secondary_value)
        elif condition == AlertCondition.OUTSIDE:
            if secondary_value is not None:
                return current_value < min(target_value, secondary_value) or current_value > max(target_value, secondary_value)
        # CROSSES_ABOVE and CROSSES_BELOW would need historical data
        
        return False
        
    def _calculate_indicator(self, alert: Alert, market_data: Dict) -> Optional[float]:
        """Calculate indicator value for alert"""
        
        # This would integrate with the TechnicalIndicators class
        # For now, return a placeholder
        indicator_name = alert.indicator_name
        
        if indicator_name == "RSI":
            return market_data.get('rsi', None)
        elif indicator_name == "MACD":
            return market_data.get('macd', None)
        elif indicator_name == "SMA":
            period = alert.indicator_params.get('period', 20) if alert.indicator_params else 20
            return market_data.get(f'sma_{period}', None)
        elif indicator_name == "EMA":
            period = alert.indicator_params.get('period', 20) if alert.indicator_params else 20
            return market_data.get(f'ema_{period}', None)
            
        return None
        
    def _trigger_alert(self, alert: Alert, market_data: Dict):
        """Trigger an alert and send notifications"""
        
        # Check if we've reached max triggers
        if alert.trigger_count >= alert.max_triggers:
            alert.status = AlertStatus.TRIGGERED
            return
            
        alert.trigger_count += 1
        alert.triggered_at = datetime.now()
        
        # Check quiet hours
        user_settings = self.user_settings.get(alert.user_id)
        if user_settings and self._is_quiet_hours(user_settings):
            logging.info(f"Alert {alert.id} triggered during quiet hours - notification delayed")
            return
            
        # Send notifications
        self._send_notifications(alert, market_data)
        
        # Mark as triggered if max triggers reached
        if alert.trigger_count >= alert.max_triggers:
            alert.status = AlertStatus.TRIGGERED
            
        logging.info(f"Alert triggered: {alert.id} for {alert.symbol}")
        
    def _send_notifications(self, alert: Alert, market_data: Dict):
        """Send notifications through all configured channels"""
        
        user_settings = self.user_settings.get(alert.user_id)
        if not user_settings:
            return
            
        # Prepare message
        message = self._format_alert_message(alert, market_data)
        
        # Send through each channel
        for channel in alert.notification_channels:
            try:
                if channel in self.notification_handlers:
                    self.notification_handlers[channel](alert, user_settings, message)
            except Exception as e:
                logging.error(f"Error sending notification via {channel}: {e}")
                
    def _format_alert_message(self, alert: Alert, market_data: Dict) -> str:
        """Format alert message"""
        
        if alert.message:
            return alert.message
            
        current_price = market_data.get('price', market_data.get('close', 0))
        
        message = f"🚨 ALERT: {alert.symbol}\n"
        message += f"Type: {alert.alert_type.value}\n"
        message += f"Current Price: ${current_price:.2f}\n"
        message += f"Condition: {alert.condition.value} {alert.value}\n"
        message += f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        
        return message
        
    def _send_email(self, alert: Alert, user_settings: NotificationSettings, message: str):
        """Send email notification"""
        
        if not user_settings.email_enabled or not user_settings.email:
            return
            
        try:
            # Email configuration (would be in environment variables)
            smtp_server = "smtp.gmail.com"
            smtp_port = 587
            sender_email = "alerts@aksjeradar.no"
            sender_password = "app_password"  # App password
            
            # Create message
            msg = MIMEMultipart()
            msg['From'] = sender_email
            msg['To'] = user_settings.email
            msg['Subject'] = f"Trading Alert: {alert.symbol}"
            
            msg.attach(MIMEText(message, 'plain'))
            
            # Send email
            context = ssl.create_default_context()
            with smtplib.SMTP(smtp_server, smtp_port) as server:
                server.starttls(context=context)
                server.login(sender_email, sender_password)
                server.send_message(msg)
                
            logging.info(f"Email sent for alert {alert.id}")
            
        except Exception as e:
            logging.error(f"Failed to send email for alert {alert.id}: {e}")
            
    def _send_sms(self, alert: Alert, user_settings: NotificationSettings, message: str):
        """Send SMS notification"""
        
        if not user_settings.sms_enabled or not user_settings.phone:
            return
            
        # SMS implementation would use a service like Twilio
        logging.info(f"SMS notification for alert {alert.id} (implementation needed)")
        
    def _send_push(self, alert: Alert, user_settings: NotificationSettings, message: str):
        """Send push notification"""
        
        if not user_settings.push_enabled or not user_settings.push_token:
            return
            
        # Push notification implementation would use Firebase or similar
        logging.info(f"Push notification for alert {alert.id} (implementation needed)")
        
    def _send_webhook(self, alert: Alert, user_settings: NotificationSettings, message: str):
        """Send webhook notification"""
        
        if not user_settings.webhook_url:
            return
            
        try:
            import requests
            
            payload = {
                'alert_id': alert.id,
                'symbol': alert.symbol,
                'alert_type': alert.alert_type.value,
                'condition': alert.condition.value,
                'value': alert.value,
                'message': message,
                'timestamp': datetime.now().isoformat()
            }
            
            response = requests.post(user_settings.webhook_url, json=payload, timeout=10)
            response.raise_for_status()
            
            logging.info(f"Webhook sent for alert {alert.id}")
            
        except Exception as e:
            logging.error(f"Failed to send webhook for alert {alert.id}: {e}")
            
    def _is_quiet_hours(self, user_settings: NotificationSettings) -> bool:
        """Check if current time is within quiet hours"""
        
        if not user_settings.quiet_hours_start or not user_settings.quiet_hours_end:
            return False
            
        try:
            now = datetime.now().time()
            start_time = datetime.strptime(user_settings.quiet_hours_start, "%H:%M").time()
            end_time = datetime.strptime(user_settings.quiet_hours_end, "%H:%M").time()
            
            if start_time <= end_time:
                return start_time <= now <= end_time
            else:  # Crosses midnight
                return now >= start_time or now <= end_time
                
        except Exception as e:
            logging.error(f"Error checking quiet hours: {e}")
            return False
            
    def _cleanup_expired_alerts(self):
        """Remove expired and old triggered alerts"""
        
        expired_alerts = []
        cutoff_date = datetime.now() - timedelta(days=30)  # Keep for 30 days
        
        for alert_id, alert in self.alerts.items():
            # Mark expired alerts
            if alert.expiry_date and datetime.now() > alert.expiry_date:
                alert.status = AlertStatus.EXPIRED
                
            # Remove old triggered/expired alerts
            if (alert.status in [AlertStatus.TRIGGERED, AlertStatus.EXPIRED] and
                alert.triggered_at and alert.triggered_at < cutoff_date):
                expired_alerts.append(alert_id)
                
        # Remove expired alerts
        for alert_id in expired_alerts:
            del self.alerts[alert_id]
            
        if expired_alerts:
            logging.info(f"Cleaned up {len(expired_alerts)} old alerts")
            
    def get_alert_statistics(self, user_id: str) -> Dict[str, Any]:
        """Get alert statistics for a user"""
        
        user_alerts = self.get_user_alerts(user_id)
        
        stats = {
            'total_alerts': len(user_alerts),
            'active_alerts': len([a for a in user_alerts if a.status == AlertStatus.ACTIVE]),
            'triggered_alerts': len([a for a in user_alerts if a.status == AlertStatus.TRIGGERED]),
            'expired_alerts': len([a for a in user_alerts if a.status == AlertStatus.EXPIRED]),
            'alert_types': {},
            'symbols': {}
        }
        
        # Count by type and symbol
        for alert in user_alerts:
            alert_type = alert.alert_type.value
            stats['alert_types'][alert_type] = stats['alert_types'].get(alert_type, 0) + 1
            stats['symbols'][alert.symbol] = stats['symbols'].get(alert.symbol, 0) + 1
            
        return stats


# Global alert manager instance (kept for compatibility; no auto-start)
alert_manager = AlertManager()


def create_price_alert(user_id: str, symbol: str, condition: str, price: float,
                      channels: List[str] = None, expiry_hours: int = None) -> Alert:
    """Helper function to create a price alert"""
    
    alert_id = f"price_{user_id}_{symbol}_{int(datetime.now().timestamp())}"
    
    # Convert string condition to enum
    condition_map = {
        'above': AlertCondition.GREATER_THAN,
        'below': AlertCondition.LESS_THAN,
        'equals': AlertCondition.EQUALS
    }
    
    # Convert string channels to enums
    channel_map = {
        'email': NotificationChannel.EMAIL,
        'sms': NotificationChannel.SMS,
        'push': NotificationChannel.PUSH
    }
    
    notification_channels = []
    if channels:
        notification_channels = [channel_map.get(c, NotificationChannel.EMAIL) for c in channels]
    else:
        notification_channels = [NotificationChannel.EMAIL]
        
    expiry_date = None
    if expiry_hours:
        expiry_date = datetime.now() + timedelta(hours=expiry_hours)
        
    alert = Alert(
        id=alert_id,
        user_id=user_id,
        symbol=symbol,
        alert_type=AlertType.PRICE_ALERT,
        condition=condition_map.get(condition, AlertCondition.GREATER_THAN),
        value=price,
        notification_channels=notification_channels,
        expiry_date=expiry_date
    )
    
    return alert


def create_indicator_alert(user_id: str, symbol: str, indicator: str, condition: str,
                          value: float, indicator_params: Dict = None,
                          channels: List[str] = None) -> Alert:
    """Helper function to create an indicator alert"""
    
    alert_id = f"indicator_{user_id}_{symbol}_{indicator}_{int(datetime.now().timestamp())}"
    
    condition_map = {
        'above': AlertCondition.GREATER_THAN,
        'below': AlertCondition.LESS_THAN,
        'equals': AlertCondition.EQUALS
    }
    
    channel_map = {
        'email': NotificationChannel.EMAIL,
        'sms': NotificationChannel.SMS,
        'push': NotificationChannel.PUSH
    }
    
    notification_channels = []
    if channels:
        notification_channels = [channel_map.get(c, NotificationChannel.EMAIL) for c in channels]
    else:
        notification_channels = [NotificationChannel.EMAIL]
        
    alert = Alert(
        id=alert_id,
        user_id=user_id,
        symbol=symbol,
        alert_type=AlertType.INDICATOR_ALERT,
        condition=condition_map.get(condition, AlertCondition.GREATER_THAN),
        value=value,
        indicator_name=indicator.upper(),
        indicator_params=indicator_params or {},
        notification_channels=notification_channels
    )
    
    return alert
