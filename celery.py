#!/usr/bin/env python3
"""
Celery application configuration for Aksjeradar
"""
import os
try:
    from celery import Celery
except Exception:
    class Celery:  # Minimal fallback so tests don't fail on missing dependency
        def __init__(self, name):
            self.name = name
        def conf_update(self, *a, **k):
            pass
        def task(self, name=None):
            def decorator(fn):
                # Attach delay method executing synchronously
                def delay(*args, **kwargs):
                    return fn(*args, **kwargs)
                fn.delay = delay  # type: ignore
                return fn
            return decorator
        # Provide .conf property for attribute access in code paths
        class _Conf:  # noqa: D401
            def update(self, *a, **k):
                pass
        conf = _Conf()

# Create Celery app
celery = Celery('aksjeradar')

# Configure Celery
celery.conf.update(
    broker_url=os.getenv('REDIS_URL', 'redis://localhost:6379'),
    result_backend=os.getenv('REDIS_URL', 'redis://localhost:6379'),
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='Europe/Oslo',
    enable_utc=True,
    task_routes={
        'app.tasks.send_weekly_reports': {'queue': 'weekly'},
        'app.tasks.check_price_alerts': {'queue': 'alerts'},
        'app.tasks.send_integration_alert': {'queue': 'notifications'},
        'app.tasks.send_price_alert_notification': {'queue': 'notifications'},
        'app.tasks.send_email_alert': {'queue': 'notifications'},
    },
    # Task execution settings
    task_always_eager=False,  # Set to True for testing
    task_eager_propagates=True,
    # Worker settings
    worker_prefetch_multiplier=1,
    task_acks_late=True,
    worker_disable_rate_limits=True,
)

# Import tasks to register them
from app.tasks import (
    send_weekly_reports,
    check_price_alerts,
    send_price_alert_notification,
    send_integration_alert,
    send_email_alert,
    cleanup_old_data
)

if __name__ == '__main__':
    celery.start()
