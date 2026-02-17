import threading
import time
import logging
from typing import Optional
from flask import current_app
from ..extensions import db
from ..models.price_alert import EmailQueue, PriceAlert
from ..models.user import User
from .email_service import EmailService

logger = logging.getLogger(__name__)

class EmailQueueProcessor:
    def __init__(self, app=None, interval_seconds: int = 300):
        self.app = app
        self.interval = interval_seconds
        self.thread: Optional[threading.Thread] = None
        self.active = False  # internal flag
        # Metrics counters
        self.emails_processed_total = 0
        self.emails_error_total = 0

    def start(self, app=None):
        if app:
            self.app = app
        if self.active:
            logger.warning("EmailQueueProcessor already running")
            return
        if not self.app:
            logger.error("EmailQueueProcessor has no app context")
            return
        self.active = True
        self._start_time = time.time()
        try:
            from ..models import ServiceRuntime
            ServiceRuntime.record_start('email_queue_processor')
        except Exception as _sr_err:
            logger.debug(f"ServiceRuntime record_start failed (email_queue_processor): {_sr_err}")
        self.thread = threading.Thread(target=self._loop, daemon=True)
        self.thread.start()
        logger.info("📬 EmailQueueProcessor started")

    def stop(self):
        self.active = False
        if self.thread:
            self.thread.join(timeout=5)
        logger.info("📬 EmailQueueProcessor stopped")

    # Compatibility property expected by monitoring endpoint
    @property
    def running(self):
        return self.active

    def _loop(self):
        while self.active:
            try:
                with self.app.app_context():
                    self._process_pending()
            except Exception as e:
                logger.error(f"EmailQueueProcessor loop error: {e}")
            time.sleep(self.interval)

    def _process_pending(self, batch_size: int = 25):
        pending = EmailQueue.query.filter_by(status='pending').order_by(EmailQueue.created_at.asc()).limit(batch_size).all()
        if not pending:
            return
        logger.info(f"EmailQueueProcessor processing {len(pending)} queued items")
        for item in pending:
            try:
                payload = item.payload or {}
                if payload.get('type') == 'price_alert':
                    # Already sent immediately by monitor; mark processed
                    item.status = 'processed'
                    item.processed_at = db.func.now()
                    self.emails_processed_total += 1
                else:
                    # Future types: attempt send
                    user = User.query.get(item.user_id)
                    if not user or not user.email:
                        item.status = 'error'
                        item.error = 'User/email missing'
                        self.emails_error_total += 1
                    else:
                        if EmailService:
                            EmailService.send_email(
                                to_email=user.email,
                                subject=payload.get('subject', 'Notification'),
                                template=payload.get('template', 'generic_notification.html'),
                                context=payload.get('context', {})
                            )
                            item.status = 'processed'
                            item.processed_at = db.func.now()
                            self.emails_processed_total += 1
                        else:
                            item.status = 'error'
                            item.error = 'EmailService unavailable'
                            self.emails_error_total += 1
            except Exception as e:
                item.status = 'error'
                item.error = str(e)
                logger.error(f"Failed processing queue item {item.id}: {e}")
                self.emails_error_total += 1
        try:
            db.session.commit()
        except Exception as commit_err:
            logger.error(f"Failed committing queue updates: {commit_err}")
            db.session.rollback()

email_queue_processor = EmailQueueProcessor()
