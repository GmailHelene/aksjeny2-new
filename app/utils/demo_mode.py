"""Centralized demo mode logic.

Only the /demo route should render the full demo experience. Other routes
may show a lightweight upgrade/login notice but must not embed full demo.html.
"""
from flask_login import current_user

DEMO_ELIGIBLE_SUBSCRIPTIONS = {None, 'free', 'basic', 'trial'}

def in_demo_mode():
    """Return True if current request should be treated as demo mode.

    Rules:
    - Unauthenticated users => demo context allowed
    - Authenticated users with premium/active subscriptions => False
    - Authenticated users with free/basic/trial => demo context (upgrade prompts) but NOT full demo.html outside /demo
    """
    try:
        if not current_user.is_authenticated:
            return True
        sub = getattr(current_user, 'subscription_type', None)
        if sub is None:
            return True
        return sub.lower() in DEMO_ELIGIBLE_SUBSCRIPTIONS
    except Exception:
        return True

def should_render_full_demo(path: str) -> bool:
    """Return True only for the dedicated /demo route."""
    return path.rstrip('/') == '/demo'
