"""
Advanced notification service for real-time alerts and user notifications
"""
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from flask import current_app
from flask_login import current_user
from ..extensions import db
from ..models.user import User
from ..models.notifications import Notification
from ..services.cache_service import get_cache_service
import json

logger = logging.getLogger(__name__)

class NotificationService:
    """Service for managing user notifications and alerts"""
    
    def __init__(self):
        self.notification_types = {
            'PRICE_ALERT': 'Prisvarsel',
            'EARNINGS_ALERT': 'Resultatvarsel', 
            'INSIDER_TRADING': 'Innsidehandel',
            'ANALYST_UPGRADE': 'Analytiker-oppgradering',
            'ANALYST_DOWNGRADE': 'Analytiker-nedgradering',
            'VOLUME_SPIKE': 'Volumøkning',
            'DIVIDEND_ANNOUNCEMENT': 'Utbyttekunngjøring',
            'MARKET_NEWS': 'Markedsnyheter',
            'SYSTEM_UPDATE': 'Systemoppdatering',
            'SUBSCRIPTION_REMINDER': 'Abonnementspåminnelse',
            'TRIAL_EXPIRY': 'Prøveperiode utløper',
            'DAILY_SUMMARY': 'Daglig sammendrag'
        }
    
    def create_notification(self, 
                          user_id: int,
                          notification_type: str,
                          title: str,
                          message: str,
                          ticker: Optional[str] = None,
                          priority: str = 'medium',
                          action_url: Optional[str] = None,
                          metadata: Optional[Dict] = None) -> Optional[Notification]:
        """Create a new notification for a user"""
        try:
            # Translate notification types to Norwegian
            type_translations = {
                'PRICE_ALERT': 'Prisvarsel',
                'INSIDER_TRADING': 'Innsidehandel',
                'EARNINGS_ALERT': 'Resultatvarsel',
                'ANALYST_UPGRADE': 'Analytikeroppgradering',
                'ANALYST_DOWNGRADE': 'Analytikernedgradering',
                'VOLUME_SPIKE': 'Volumøkning',
                'DIVIDEND_ANNOUNCEMENT': 'Utbyttekunngjøring',
                'MARKET_NEWS': 'Markedsnyheter',
                'SYSTEM_UPDATE': 'Systemoppdatering',
                'SUBSCRIPTION_REMINDER': 'Abonnementspåminnelse',
                'TRIAL_EXPIRY': 'Prøveperiode utløper',
                'DAILY_SUMMARY': 'Daglig oppsummering'
            }
            
            # Create notification with Norwegian title if not provided
            norwegian_title = type_translations.get(notification_type, title)
            
            notification = Notification(
                user_id=user_id,
                type=notification_type,
                title=norwegian_title if not title else title,
                message=message,
                ticker=ticker,
                priority=priority,
                action_url=action_url,
                metadata=json.dumps(metadata) if metadata else None,
                created_at=datetime.utcnow()
            )
            
            db.session.add(notification)
            db.session.commit()
            
            logger.info(f"Created notification for user {user_id}: {title}")
            
            # Clear cache for user notifications
            cache_service = get_cache_service()
            cache_service.delete(f'user_notifications_{user_id}')
            cache_service.delete(f'user_unread_count_{user_id}')
            
            return notification
            
        except Exception as e:
            logger.error(f"Feil ved opprettelse av varsel: {e}")
            db.session.rollback()
            return None
    
    def get_user_notifications(self, 
                             user_id: int,
                             limit: int = 20,
                             unread_only: bool = False) -> List[Notification]:
        """Get notifications for a user"""
        try:
            # Try cache first
            cache_key = f"user_notifications_{user_id}_{limit}_{unread_only}"
            cache_service = get_cache_service()
            cached_notifications = cache_service.get(cache_key)
            
            if cached_notifications:
                return cached_notifications
            
            query = Notification.query.filter_by(user_id=user_id)
            
            if unread_only:
                query = query.filter_by(read=False)
            
            notifications = query.order_by(Notification.created_at.desc()).limit(limit).all()
            
            # Cache for 5 minutes
            cache_service.set(cache_key, notifications, ttl=300)
            
            return notifications
            
        except Exception as e:
            logger.error(f"Error getting user notifications: {e}")
            return []
    
    def mark_as_read(self, notification_id: int, user_id: int) -> bool:
        """Mark a notification as read"""
        try:
            notification = Notification.query.filter_by(
                id=notification_id, 
                user_id=user_id
            ).first()
            
            if notification:
                notification.read = True
                notification.read_at = datetime.utcnow()
                db.session.commit()
                
                # Invalidate cache
                self._invalidate_user_cache(user_id)
                
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error marking notification as read: {e}")
            db.session.rollback()
            return False
    
    def mark_all_as_read(self, user_id: int) -> bool:
        """Mark all notifications as read for a user"""
        try:
            notifications = Notification.query.filter_by(
                user_id=user_id, 
                read=False
            ).all()
            
            for notification in notifications:
                notification.read = True
                notification.read_at = datetime.utcnow()
            
            db.session.commit()
            
            count = Notification.query.filter_by(
                user_id=user_id, 
                read=False
            ).count()
            
            # Cache for 2 minutes
            cache_service = get_cache_service()
            cache_service.set(cache_key, count, ttl=120)
            
            return count
            
        except Exception as e:
            logger.error(f"Error getting unread count: {e}")
            return 0
    
    def delete_notification(self, notification_id: int, user_id: int) -> bool:
        """Delete a notification"""
        try:
            notification = Notification.query.filter_by(
                id=notification_id, 
                user_id=user_id
            ).first()
            
            if notification:
                db.session.delete(notification)
                db.session.commit()
                
                # Invalidate cache
                self._invalidate_user_cache(user_id)
                
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error deleting notification: {e}")
            db.session.rollback()
            return False
    
    def create_price_alert(self, 
                          user_id: int,
                          ticker: str,
                          target_price: float,
                          condition: str,  # 'above' or 'below'
                          current_price: float) -> Optional[Notification]:
        """Create a price alert notification"""
        condition_text = "over" if condition == "above" else "under"
        
        title = f"Prisvarsel: {ticker}"
        message = f"{ticker} er nå {condition_text} din målpris på {target_price:.2f}. Nåværende pris: {current_price:.2f}"
        
        return self.create_notification(
            user_id=user_id,
            notification_type='PRICE_ALERT',
            title=title,
            message=message,
            ticker=ticker,
            priority='high',
            action_url=f"/stocks/details/{ticker}",
            metadata={
                'target_price': target_price,
                'current_price': current_price,
                'condition': condition
            }
        )
    
    def create_insider_trading_alert(self, 
                                   user_id: int,
                                   ticker: str,
                                   insider_name: str,
                                   transaction_type: str,
                                   shares: int,
                                   price: float) -> Optional[Notification]:
        """Create an insider trading alert"""
        action_text = "kjøpt" if transaction_type.lower() == "buy" else "solgt"
        
        title = f"Innsidehandel: {ticker}"
        message = f"{insider_name} har {action_text} {shares:,} aksjer i {ticker} til {price:.2f} per aksje"
        
        return self.create_notification(
            user_id=user_id,
            notification_type='INSIDER_TRADING',
            title=title,
            message=message,
            ticker=ticker,
            priority='medium',
            action_url=f"/market-intel/insider-trading?ticker={ticker}",
            metadata={
                'insider_name': insider_name,
                'transaction_type': transaction_type,
                'shares': shares,
                'price': price
            }
        )
    
    def create_earnings_alert(self, 
                            user_id: int,
                            ticker: str,
                            earnings_date: datetime,
                            eps_estimate: float) -> Optional[Notification]:
        """Create an earnings alert"""
        title = f"Resultatvarsel: {ticker}"
        message = f"{ticker} publiserer kvartalsresultater {earnings_date.strftime('%d.%m.%Y')}. EPS-estimat: {eps_estimate:.2f}"
        
        return self.create_notification(
            user_id=user_id,
            notification_type='EARNINGS_ALERT',
            title=title,
            message=message,
            ticker=ticker,
            priority='medium',
            action_url=f"/stocks/details/{ticker}",
            metadata={
                'earnings_date': earnings_date.isoformat(),
                'eps_estimate': eps_estimate
            }
        )
    
    def create_analyst_rating_alert(self, 
                                  user_id: int,
                                  ticker: str,
                                  analyst_firm: str,
                                  old_rating: str,
                                  new_rating: str,
                                  target_price: float) -> Optional[Notification]:
        pass  # Implement the function logic here

    def create_trial_expiry_alert(self, user_id: int) -> Optional[Notification]:
        pass  # Implement the function logic here

    def create_subscription_reminder(self, user_id: int, days_until_expiry: int) -> Optional[Notification]:
        pass  # Implement the function logic here

    def create_system_update_alert(self, title: str, message: str) -> List[Notification]:
        try:
            # Implement the alert creation logic here
            pass
        except Exception as e:
            logger.error(f"Error creating system update alert: {e}")
            return []

    def _cache_user_notifications(self, user_id: int):
        """Cache user notifications for quick access"""
        try:
            # Implement caching logic here
            pass
        except Exception as e:
            logger.error(f"Error caching user notifications: {e}")

    def _invalidate_user_cache(self, user_id: int):
        """Invalidate all cached data for a user"""
        try:
            cache.invalidate_pattern(f"unread_count_{user_id}")
        except Exception as e:
            logger.error(f"Error invalidating user cache: {e}")

    def cleanup_old_notifications(self, days_old: int = 30) -> int:
        """Clean up old notifications"""
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days_old)
            
            # Delete old read notifications
            count = Notification.query.filter(
                Notification.created_at < cutoff_date,
                Notification.read == True
            ).delete()
            
            db.session.commit()
            logger.info(f"Cleaned up {count} old notifications")
            return count
        except Exception as e:
            logger.error(f"Error cleaning up old notifications: {e}")
            db.session.rollback()
            return 0

    def get_notification_summary(self, user_id: int) -> Dict[str, Any]:
        """Get notification summary for a user"""
        try:
            notifications = self.get_user_notifications(user_id, limit=100)
            # Count by type
            type_counts = {}
            for notification in notifications:
                type_counts[notification.type] = type_counts.get(notification.type, 0) + 1
            # Count by priority
            priority_counts = {'high': 0, 'medium': 0, 'low': 0}
            for notification in notifications:
                priority_counts[notification.priority] += 1
            # Recent activity (last 7 days)
            recent_cutoff = datetime.utcnow() - timedelta(days=7)
            recent_notifications = [n for n in notifications if n.created_at >= recent_cutoff]
            return {
                'total_notifications': len(notifications),
                'unread_count': self.get_unread_count(user_id),
                'type_breakdown': type_counts,
                'priority_breakdown': priority_counts,
                'recent_activity': len(recent_notifications),
                'most_recent': notifications[0] if notifications else None
            }
        except Exception as e:
            logger.error(f"Error getting notification summary: {e}")
            return {
                'total_notifications': 0,
                'unread_count': 0,
                'type_breakdown': {},
                'priority_breakdown': {'high': 0, 'medium': 0, 'low': 0},
                'recent_activity': 0,
                'most_recent': None
            }

# Global instance
notification_service = NotificationService()
