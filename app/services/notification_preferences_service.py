from ..extensions import db
from ..models.user_notification_preferences import UserNotificationPreferences
from ..models.user import User

def get_prefs(user_id: int) -> UserNotificationPreferences:
    return UserNotificationPreferences.get_or_create_for_user(user_id)

def to_dict(prefs: UserNotificationPreferences):
    return {
        'email': {
            'enabled': prefs.email_enabled,
            'price_alerts': prefs.email_price_alerts,
            'news_alerts': prefs.email_news_alerts,
            'portfolio_updates': prefs.email_portfolio_updates,
            'watchlist_alerts': prefs.email_watchlist_alerts,
            'weekly_reports': prefs.email_weekly_reports,
        },
        'push': {
            'enabled': prefs.push_enabled,
            'price_alerts': prefs.push_price_alerts,
            'news_alerts': prefs.push_news_alerts,
            'portfolio_updates': prefs.push_portfolio_updates,
            'watchlist_alerts': prefs.push_watchlist_alerts,
            'weekly_reports': prefs.push_weekly_reports,
        },
        'inapp': {
            'price_alerts': prefs.inapp_price_alerts,
            'news_alerts': prefs.inapp_news_alerts,
            'portfolio_updates': prefs.inapp_portfolio_updates,
            'watchlist_alerts': prefs.inapp_watchlist_alerts,
            'weekly_reports': prefs.inapp_weekly_reports,
        },
        'quiet_hours': {
            'start': prefs.quiet_hours_start,
            'end': prefs.quiet_hours_end,
            'timezone': prefs.timezone,
        }
    }

def update_prefs(user_id: int, data: dict) -> UserNotificationPreferences:
    prefs = get_prefs(user_id)
    mapping = {
        # email
        'email.enabled': 'email_enabled',
        'email.price_alerts': 'email_price_alerts',
        'email.news_alerts': 'email_news_alerts',
        'email.portfolio_updates': 'email_portfolio_updates',
        'email.watchlist_alerts': 'email_watchlist_alerts',
        'email.weekly_reports': 'email_weekly_reports',
        # push
        'push.enabled': 'push_enabled',
        'push.price_alerts': 'push_price_alerts',
        'push.news_alerts': 'push_news_alerts',
        'push.portfolio_updates': 'push_portfolio_updates',
        'push.watchlist_alerts': 'push_watchlist_alerts',
        'push.weekly_reports': 'push_weekly_reports',
        # inapp
        'inapp.price_alerts': 'inapp_price_alerts',
        'inapp.news_alerts': 'inapp_news_alerts',
        'inapp.portfolio_updates': 'inapp_portfolio_updates',
        'inapp.watchlist_alerts': 'inapp_watchlist_alerts',
        'inapp.weekly_reports': 'inapp_weekly_reports',
        # quiet hours
        'quiet_hours.start': 'quiet_hours_start',
        'quiet_hours.end': 'quiet_hours_end',
        'quiet_hours.timezone': 'timezone',
    }

    def norm_bool(val):
        if isinstance(val, bool):
            return val
        if isinstance(val, str):
            return val.lower() in ('1','true','yes','on')
        return bool(val)

    # Flatten nested dict keys like email: {enabled: ...}
    def walk(prefix, obj, collector):
        if isinstance(obj, dict):
            for k,v in obj.items():
                walk(f"{prefix}.{k}" if prefix else k, v, collector)
        else:
            collector[prefix] = obj

    flat = {}
    walk('', data, flat)

    changed = False
    for in_key, value in flat.items():
        if in_key in mapping:
            attr = mapping[in_key]
            current = getattr(prefs, attr)
            if attr.startswith(('quiet_hours_', 'timezone')):
                if current != value:
                    setattr(prefs, attr, value)
                    changed = True
            else:
                bval = norm_bool(value)
                if current != bval:
                    setattr(prefs, attr, bval)
                    changed = True
    if changed:
        db.session.commit()
    return prefs

def migrate_user_legacy_preferences(user):
    """Map existing scattered fields on User / JSON into unified preferences (idempotent)."""
    prefs = get_prefs(user.id)
    # Only set values if prefs are freshly created (heuristic: created_at == updated_at and default booleans untouched)
    # We just selectively override based on user legacy fields.
    override_map = {
        'email_enabled': getattr(user, 'email_notifications', True),
        'email_price_alerts': getattr(user, 'price_alerts', True),
        'push_price_alerts': False,  # Legacy had no explicit push toggle
        'inapp_price_alerts': True,
    }
    changed = False
    for attr, val in override_map.items():
        if getattr(prefs, attr) != val:
            setattr(prefs, attr, bool(val))
            changed = True
    if changed:
        db.session.commit()
    return prefs

__all__ = [
    'get_prefs', 'to_dict', 'update_prefs', 'migrate_user_legacy_preferences'
]