import pytest
from app import create_app, db
from app.models.user import User
from app.models.price_alert import PriceAlert, EmailQueue
from app.services.price_monitor_service import price_monitor
from datetime import datetime


@pytest.fixture
def app_instance():
    app = create_app('testing')
    with app.app_context():
        db.create_all()
        user = User(email='qh@example.com', username='qhuser', password='pass')
        db.session.add(user)
        db.session.commit()
    yield app


@pytest.fixture
def client(app_instance):
    return app_instance.test_client()


def login(client):
    return client.post('/login', data={'email': 'qh@example.com', 'password': 'pass'}, follow_redirects=True)


def test_email_suppressed_in_quiet_hours(monkeypatch, app_instance, client):
    login(client)
    with app_instance.app_context():
        user = User.query.filter_by(email='qh@example.com').first()
        # Create an alert that would be "triggered"
        alert = PriceAlert(user_id=user.id, symbol='TEST', target_price=100, alert_type='above', current_price=120)
        alert.is_active = False
        alert.is_triggered = True
        alert.triggered_at = datetime.utcnow()
        db.session.add(alert)
        db.session.commit()

        # Ensure unified prefs exist and set quiet hours to include now
        from app.services.notification_preferences_service import get_prefs
        prefs = get_prefs(user.id)
        prefs.email_enabled = True
        prefs.email_price_alerts = True
        prefs.quiet_hours_start = '00:00'
        prefs.quiet_hours_end = '23:59'
        db.session.commit()

        sent_payloads = []
        def fake_send_email(to_email, subject, template, context):
            sent_payloads.append((to_email, subject))
        # Monkeypatch EmailService
        monkeypatch.setattr('app.services.email_service.EmailService.send_email', fake_send_email)

        # Run notification sending for that alert
        price_monitor._send_alert_notifications([alert])

        # Expect no emails sent due to quiet hours
        assert sent_payloads == []


def test_email_sent_outside_quiet_hours(monkeypatch, app_instance, client):
    login(client)
    with app_instance.app_context():
        user = User.query.filter_by(email='qh@example.com').first()
        # Create a new alert
        alert = PriceAlert(user_id=user.id, symbol='TEST2', target_price=50, alert_type='below', current_price=40)
        alert.is_active = False
        alert.is_triggered = True
        alert.triggered_at = datetime.utcnow()
        db.session.add(alert)
        db.session.commit()

        from app.services.notification_preferences_service import get_prefs
        prefs = get_prefs(user.id)
        prefs.email_enabled = True
        prefs.email_price_alerts = True
        prefs.quiet_hours_start = '23:00'
        prefs.quiet_hours_end = '23:00'  # same start=end disables quiet hours
        db.session.commit()

        sent_payloads = []
        def fake_send_email(to_email, subject, template, context):
            sent_payloads.append((to_email, subject))
        monkeypatch.setattr('app.services.email_service.EmailService.send_email', fake_send_email)

        price_monitor._send_alert_notifications([alert])
        assert len(sent_payloads) == 1
