"""
Usage tracking service for monitoring user activity and enforcing tier limits
"""
from flask import session, request
from flask_login import current_user
from datetime import datetime, date, timedelta
from ..extensions import db
from ..models.user import User
import hashlib

class UsageTracker:
    """Track user usage for different features and enforce tier limits"""
    
    @staticmethod
    def track_analysis_request(ticker=None):
        """Track when a user requests an analysis - simplified without limits"""
        # Just track for analytics purposes, no restrictions
        pass
    
    @staticmethod
    def get_daily_analysis_usage():
        """Get current daily analysis usage count - always return 0 (no limits)"""
        return 0
    
    @staticmethod
    def can_make_analysis_request():
        """Check if user can make another analysis request"""
        # For demo access only - always allow with mock data
        # For paid users - always allow with real data
        # No daily limits - only subscription based access
        return True, -1, 0
    
    @staticmethod
    def track_watchlist_addition(ticker):
        """Track when a user adds a stock to watchlist"""
        if current_user.is_authenticated:
            # For authenticated users, actual watchlist count is used
            return True
        
        # For anonymous users, track in session
        usage_key = UsageTracker._get_usage_key('watchlist_items')
        current_items = session.get(usage_key, [])
        
        if ticker not in current_items:
            current_items.append(ticker)
            session[usage_key] = current_items
            session.permanent = True
        
        return len(current_items)
    
    @staticmethod
    def get_watchlist_usage():
        """Get current watchlist usage"""
        if current_user.is_authenticated:
            # Count actual watchlist items for authenticated users
            try:
                from ..models.watchlist import Watchlist
                return Watchlist.query.filter_by(user_id=current_user.id).count()
            except:
                return 0
        
        # For anonymous users, count session items
        usage_key = UsageTracker._get_usage_key('watchlist_items')
        current_items = session.get(usage_key, [])
        return len(current_items)
    
    @staticmethod
    def can_add_to_watchlist():
        """Check if user can add more items to watchlist"""
        from ..routes.pricing import get_tier_limits
        
        limits = get_tier_limits()
        watchlist_limit = limits.get('watchlist_size', 5)
        
        # Unlimited for paid users
        if watchlist_limit == -1:
            return True, -1, -1
        
        current_usage = UsageTracker.get_watchlist_usage()
        remaining = max(0, watchlist_limit - current_usage)
        
        return current_usage < watchlist_limit, watchlist_limit, remaining
    
    @staticmethod
    def can_access_advanced_features():
        """Check if user can access advanced features"""
        from ..routes.pricing import get_tier_limits
        
        limits = get_tier_limits()
        return limits.get('advanced_features', False)
    
    @staticmethod
    def track_ai_report_usage():
        """Track AI consultant report usage for the month"""
        if not current_user.is_authenticated:
            return False
        
        # Initialize if not exists
        if not hasattr(current_user, 'reports_used_this_month'):
            current_user.reports_used_this_month = 0
        
        current_user.reports_used_this_month += 1
        
        try:
            db.session.commit()
            return True
        except:
            db.session.rollback()
            return False
    
    @staticmethod
    def get_remaining_ai_reports():
        """Get remaining AI reports for current month"""
        from ..routes.pricing import get_tier_limits
        
        if not current_user.is_authenticated:
            return 0
        
        limits = get_tier_limits()
        monthly_limit = limits.get('consultant_reports', 0)
        
        if monthly_limit <= 0:
            return 0
        
        used_this_month = getattr(current_user, 'reports_used_this_month', 0)
        return max(0, monthly_limit - used_this_month)
    
    @staticmethod
    def _get_usage_key(feature):
        """Get unique usage key for feature tracking"""
        if current_user.is_authenticated:
            return f"usage_{feature}_{current_user.id}"
        else:
            # For anonymous users, use device fingerprint
            fingerprint_data = f"{request.remote_addr}:{request.headers.get('User-Agent', '')}"
            device_hash = hashlib.md5(fingerprint_data.encode()).hexdigest()[:8]
            return f"usage_{feature}_{device_hash}"
    
    @staticmethod
    def get_usage_summary():
        """Get a summary of current usage for templates"""
        can_analyze, daily_limit, remaining_analyses = UsageTracker.can_make_analysis_request()
        can_watchlist, watchlist_limit, remaining_watchlist = UsageTracker.can_add_to_watchlist()
        
        return {
            'daily_analyses': {
                'used': UsageTracker.get_daily_analysis_usage(),
                'limit': daily_limit,
                'remaining': remaining_analyses,
                'can_use': can_analyze
            },
            'watchlist': {
                'used': UsageTracker.get_watchlist_usage(),
                'limit': watchlist_limit,
                'remaining': remaining_watchlist,
                'can_use': can_watchlist
            },
            'advanced_features': UsageTracker.can_access_advanced_features(),
            'ai_reports_remaining': UsageTracker.get_remaining_ai_reports() if current_user.is_authenticated else 0
        }

# Create global instance
usage_tracker = UsageTracker()
