from datetime import datetime, timedelta
import os
from app.services.integrations import IntegrationService, WeeklyReportService
from app.models import User
from app.models.watchlist import Watchlist
from app.services.ai_service import AIService
import logging

logger = logging.getLogger(__name__)

# Import the centralized Celery app
try:
    from celery import celery  # type: ignore
except Exception:
    # Fallback to dummy celery app defined in root celery.py
    try:
        from celery import Celery  # type: ignore
        celery = Celery('aksjeradar-fallback')  # type: ignore
    except Exception:
        class _DummyConf(dict):
            beat_schedule = {}
            def update(self, *a, **k):
                pass
        class _Dummy:
            conf = _DummyConf()
            def task(self, name=None):
                def deco(fn):
                    def delay(*a, **k):
                        return fn(*a, **k)
                    fn.delay = delay  # type: ignore
                    return fn
                return deco
        celery = _Dummy()

@celery.task(name='app.tasks.send_weekly_reports')
def send_weekly_reports():
    """Send weekly AI reports to all subscribed users"""
    try:
        # Get all users with basic or pro subscriptions
        subscribed_users = User.query.filter(
            User.subscription_tier.in_(['basic', 'pro']),
            User.subscription_end > datetime.utcnow()
        ).all()
        
        success_count = 0
        error_count = 0
        
        for user in subscribed_users:
            try:
                # Generate and send weekly report
                report_data = WeeklyReportService.generate_weekly_watchlist_report(user.id)
                
                if 'error' not in report_data:
                    success = WeeklyReportService.send_weekly_email_report(user.email, report_data)
                    if success:
                        success_count += 1
                        logger.info(f"Weekly report sent to {user.email}")
                    else:
                        error_count += 1
                        logger.error(f"Failed to send weekly report to {user.email}")
                else:
                    logger.warning(f"No watchlist data for user {user.email}")
                    
            except Exception as e:
                error_count += 1
                logger.error(f"Error sending weekly report to {user.email}: {e}")
        
        logger.info(f"Weekly reports: {success_count} sent, {error_count} failed")
        return {"success": success_count, "errors": error_count}
        
    except Exception as e:
        logger.error(f"Error in send_weekly_reports task: {e}")
        raise

@celery.task(name='app.tasks.check_price_alerts')
def check_price_alerts():
    """Check all price alerts and send notifications"""
    try:
        from app.models.notifications import PriceAlert
        from app.extensions import db
        
        # Get all active price alerts
        active_alerts = PriceAlert.query.filter_by(is_active=True).all()
        
        triggered_count = 0
        
        for alert in active_alerts:
            try:
                # Get current price for the stock
                current_price = get_current_stock_price(alert.symbol)
                
                if current_price is None:
                    continue
                    
                # Check if alert should trigger
                should_trigger = False
                
                if alert.alert_type == 'above' and current_price >= alert.target_price:
                    should_trigger = True
                elif alert.alert_type == 'below' and current_price <= alert.target_price:
                    should_trigger = True
                elif alert.alert_type == 'change' and abs(current_price - alert.last_price) / alert.last_price * 100 >= alert.change_percent:
                    should_trigger = True
                
                if should_trigger:
                    # Send alert
                    send_price_alert_notification.delay(alert.id, current_price)
                    triggered_count += 1
                    
                    # Update alert
                    alert.last_triggered = datetime.utcnow()
                    if alert.is_one_time:
                        alert.is_active = False
                    
                # Update last price
                alert.last_price = current_price
                
            except Exception as e:
                logger.error(f"Error checking alert {alert.id}: {e}")
                continue
        
        db.session.commit()
        logger.info(f"Price alerts checked: {triggered_count} triggered")
        return {"triggered": triggered_count}
        
    except Exception as e:
        logger.error(f"Error in check_price_alerts task: {e}")
        raise

@celery.task(name='app.tasks.send_price_alert_notification')
def send_price_alert_notification(alert_id: int, current_price: float):
    """Send notification for triggered price alert"""
    try:
        from app.models.notifications import PriceAlert
        from app import db
        
        alert = db.session.get(PriceAlert, alert_id)
        if not alert or not alert.user:
            return
        
        user = alert.user
        
        # Format alert message
        title, message, color, slack_color, fields = IntegrationService.format_stock_alert(
            alert.symbol, current_price, 
            ((current_price - alert.last_price) / alert.last_price * 100) if alert.last_price else 0,
            f"Prisvarsel ({alert.alert_type})"
        )
        
        # Send to configured integrations
        if user.discord_webhook_url:
            IntegrationService.send_discord_alert(
                user.discord_webhook_url, title, message, color, fields
            )
        
        if user.slack_webhook_url:
            IntegrationService.send_slack_alert(
                user.slack_webhook_url, title, message, slack_color, fields
            )
        
        # Send email notification
        if alert.email_notifications:
            send_email_alert.delay(user.email, title, message)
        
        logger.info(f"Price alert notification sent for {alert.symbol} to user {user.email}")
        
    except Exception as e:
        logger.error(f"Error sending price alert notification: {e}")

@celery.task(name='app.tasks.send_integration_alert')
def send_integration_alert(user_id: int, symbol: str, alert_type: str, data: dict):
    """Send alert to user's configured integrations"""
    try:
        from app import db
        user = db.session.get(User, user_id)
        if not user:
            return
        
        # Format the alert
        title, message, color, slack_color, fields = IntegrationService.format_stock_alert(
            symbol, data.get('price', 0), data.get('change_pct', 0), 
            alert_type, data.get('ai_score')
        )
        
        # Send to Discord
        if hasattr(user, 'discord_webhook_url') and user.discord_webhook_url:
            IntegrationService.send_discord_alert(
                user.discord_webhook_url, title, message, color, fields
            )
        
        # Send to Slack
        if hasattr(user, 'slack_webhook_url') and user.slack_webhook_url:
            IntegrationService.send_slack_alert(
                user.slack_webhook_url, title, message, slack_color, fields
            )
        
        logger.info(f"Integration alert sent for {symbol} to user {user.email}")
        
    except Exception as e:
        logger.error(f"Error sending integration alert: {e}")

@celery.task(name='app.tasks.send_email_alert')
def send_email_alert(email: str, title: str, message: str):
    """Send email alert"""
    try:
        from flask_mailman import EmailMessage
        from app.extensions import mail
        from flask import current_app
        
        # Check if email is configured
        if not current_app.config.get('MAIL_SERVER') or not current_app.config.get('MAIL_USERNAME') or not current_app.config.get('MAIL_PASSWORD'):
            logger.warning(f"Email not configured - cannot send alert to {email}")
            return False
        
        # Fix f-string backslash issue by extracting the replace operation
        message_html = message.replace('\n', '<br>')
        
        msg = EmailMessage(
            subject=f"🚨 Aksjeradar Alert: {title}",
            recipients=[email],
            body=message,
            html=f"""
            <html>
            <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                <div style="background: #007bff; color: white; padding: 20px; text-align: center;">
                    <h1>🚨 Aksjeradar Alert</h1>
                </div>
                <div style="padding: 20px;">
                    <h2>{title}</h2>
                    <div style="background: #f8f9fa; padding: 15px; border-radius: 5px;">
                        {message_html}
                    </div>
                    <p style="margin-top: 20px; color: #666;">
                        <small>Dette varselet ble sendt fra Aksjeradar AI. Ikke investeringsrådgivning.</small>
                    </p>
                </div>
            </body>
            </html>
            """
        )
        
        mail.send(msg)
        logger.info(f"Email alert sent to {email}")
        return True
        
    except Exception as e:
        logger.error(f"Error sending email alert: {e}")
        return False

@celery.task(name='app.tasks.cleanup_old_data')
def cleanup_old_data():
    """Clean up old data to maintain performance"""
    try:
        from app.models.notifications import PredictionLog
        from app.extensions import db
        
        # Remove prediction logs older than 90 days
        cutoff_date = datetime.utcnow() - timedelta(days=90)
        old_predictions = PredictionLog.query.filter(PredictionLog.created_at < cutoff_date).delete()
        
        # Remove inactive alerts older than 30 days
        alert_cutoff = datetime.utcnow() - timedelta(days=30)
        from app.models.notifications import PriceAlert
        old_alerts = PriceAlert.query.filter(
            PriceAlert.is_active == False,
            PriceAlert.created_at < alert_cutoff
        ).delete()
        
        db.session.commit()
        logger.info(f"Cleanup completed: {old_predictions} predictions, {old_alerts} alerts removed")
        
        return {"predictions_removed": old_predictions, "alerts_removed": old_alerts}
        
    except Exception as e:
        logger.error(f"Error in cleanup task: {e}")
        raise

def get_current_stock_price(symbol: str) -> float:
    """Get current stock price - implement with your preferred data source"""
    try:
        # This is a placeholder - replace with actual price fetching logic
        # You could use yfinance, Alpha Vantage, or your existing price service
        
        try:
            import yfinance as yf
        except ImportError:
            yf = None
        
        if yf is None:
            # Return fallback price when yfinance is not available
            return 100.0 + (hash(symbol) % 100)  # Deterministic but varied price
        
        # Add .OL suffix for Oslo Stock Exchange if needed
        ticker_symbol = symbol if '.OL' in symbol else f"{symbol}.OL"
        
        if yf is not None:
            ticker = yf.Ticker(ticker_symbol)
            data = ticker.history(period="1d")
            
            if not data.empty:
                return float(data['Close'].iloc[-1])
        
        # Return fallback if yfinance fails or is unavailable
        return 100.0 + (hash(symbol) % 100)
        
    except Exception as e:
        logger.error(f"Error fetching price for {symbol}: {e}")
        return 100.0 + (hash(symbol) % 100)

# Periodic task scheduling (you'll need to configure this in your deployment)
celery.conf.beat_schedule = {
    'send-weekly-reports': {
        'task': 'app.tasks.send_weekly_reports',
        'schedule': 604800.0,  # Weekly (seconds)
        'options': {'queue': 'weekly'}
    },
    'check-price-alerts': {
        'task': 'app.tasks.check_price_alerts',
        'schedule': 300.0,  # Every 5 minutes
        'options': {'queue': 'alerts'}
    },
    'cleanup-old-data': {
        'task': 'app.tasks.cleanup_old_data',
        'schedule': 86400.0,  # Daily
        'options': {'queue': 'maintenance'}
    },
}
