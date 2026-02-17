"""Utility script to report active monitoring services status.

Usage:
  python monitor_status.py

Outputs:
  - Whether price_monitor_service thread appears running
  - Whether email_queue_processor thread appears running
  - DB path and presence of key tables
  - Count of pending email_queue items (if table exists)
"""
import os
import threading
import logging
from datetime import datetime

from app import create_app, db
from sqlalchemy import inspect, text

# Import services lazily to avoid side-effects
try:
    from app.services.price_monitor_service import price_monitor
except Exception:
    price_monitor = None  # type: ignore

try:
    from app.services.email_queue_processor import email_queue_processor
except Exception:
    email_queue_processor = None  # type: ignore

logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(levelname)s %(message)s')
logger = logging.getLogger("monitor_status")

def thread_alive(thread_obj):
    if not thread_obj:
        return False
    return thread_obj.is_alive()

def summarize_threads():
    details = {}
    try:
        for th in threading.enumerate():
            details[th.name] = {
                'daemon': th.daemon,
                'ident': th.ident
            }
    except Exception:
        pass
    return details

def main():
    app = create_app()
    with app.app_context():
        logger.info("=== Monitoring Status Report ===")
        db_uri = app.config.get('SQLALCHEMY_DATABASE_URI')
        logger.info(f"DB URI: {db_uri}")
        db_path = db.engine.url.database if db.engine.url else 'unknown'
        if db_path and os.path.exists(db_path):
            logger.info(f"SQLite file exists: {db_path} ({os.path.getsize(db_path)} bytes)")
        else:
            logger.warning(f"SQLite file missing: {db_path}")
        insp = inspect(db.engine)
        tables = sorted(insp.get_table_names())
        logger.info(f"Tables ({len(tables)}): {tables}")
        has_price_alerts = 'price_alerts' in tables
        has_email_queue = 'email_queue' in tables
        logger.info(f"price_alerts table present: {has_price_alerts}")
        logger.info(f"email_queue table present: {has_email_queue}")

        # Thread / service status
        if price_monitor:
            pm_running = getattr(price_monitor, '_monitoring_started', False)
            pm_thread = getattr(price_monitor, '_thread', None)
            logger.info(f"price_monitor_service started_flag={pm_running} thread_alive={thread_alive(pm_thread)}")
        else:
            logger.warning("price_monitor_service import failed / not available")
        if email_queue_processor:
            eq_running = getattr(email_queue_processor, 'running', False)
            eq_thread = getattr(email_queue_processor, 'thread', None)
            logger.info(f"email_queue_processor running_flag={eq_running} thread_alive={thread_alive(eq_thread)}")
        else:
            logger.warning("email_queue_processor import failed / not available")

        # Pending email queue items
        if has_email_queue:
            try:
                pending = db.session.execute(text("SELECT COUNT(*) FROM email_queue WHERE status='pending'"))
                count = pending.scalar() or 0
                logger.info(f"Pending email_queue items: {count}")
            except Exception as e:
                logger.warning(f"Could not count email_queue items: {e}")

        # Enumerate current threads
        threads = summarize_threads()
        logger.info(f"Active threads: {len(threads)}")
        for name, meta in threads.items():
            logger.info(f"Thread: {name} ident={meta['ident']} daemon={meta['daemon']}")

        logger.info("=== End Monitoring Status Report ===")

if __name__ == '__main__':
    main()
