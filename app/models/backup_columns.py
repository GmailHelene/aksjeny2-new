"""
Backup solution - graceful database column handling
This adds fallback properties to User model for missing columns
"""

from ..models.user import User
from datetime import datetime

# Add graceful property handling for missing columns
def add_missing_column_properties():
    """Add properties to handle missing database columns gracefully"""
    
    # Backup getter for reports_used_this_month
    def get_reports_used_this_month(self):
        try:
            return getattr(self, '_reports_used_this_month', 0)
        except:
            return 0
    
    def set_reports_used_this_month(self, value):
        try:
            self._reports_used_this_month = value
        except:
            pass
    
    # Backup getter for last_reset_date
    def get_last_reset_date(self):
        try:
            return getattr(self, '_last_reset_date', datetime.utcnow())
        except:
            return datetime.utcnow()
    
    def set_last_reset_date(self, value):
        try:
            self._last_reset_date = value
        except:
            pass
    
    # Backup getter for is_admin
    def get_is_admin(self):
        try:
            return getattr(self, '_is_admin', False)
        except:
            # Check if user is in exempt list
            from ..utils.access_control import EXEMPT_EMAILS
            return self.email in EXEMPT_EMAILS if hasattr(self, 'email') else False
    
    def set_is_admin(self, value):
        try:
            self._is_admin = value
        except:
            pass
    
    # Only add properties if they don't exist (missing columns)
    if not hasattr(User, 'reports_used_this_month'):
        User.reports_used_this_month = property(get_reports_used_this_month, set_reports_used_this_month)
    
    if not hasattr(User, 'last_reset_date'):
        User.last_reset_date = property(get_last_reset_date, set_last_reset_date)
    
    if not hasattr(User, 'is_admin'):
        User.is_admin = property(get_is_admin, set_is_admin)

# Auto-apply when module is imported
try:
    add_missing_column_properties()
except:
    pass  # Fail silently
