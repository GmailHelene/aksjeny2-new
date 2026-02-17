import pytest
from app import create_app
from app.extensions import db

@pytest.fixture(scope="session")
def app_instance():
    app = create_app()
    app.config.update(TESTING=True, SQLALCHEMY_DATABASE_URI="sqlite:///:memory:")
    with app.app_context():
        try:
            db.create_all()
        except Exception:
            pass
        yield app

@pytest.fixture
def client(app_instance):
    return app_instance.test_client()

def test_live(client):
    r = client.get('/health/live')
    assert r.status_code == 200
    assert r.is_json
    assert r.json.get('alive') is True or r.json.get('status') == 'ok'


def test_ready(client):
    r = client.get('/health/ready')
    assert r.status_code == 200
    assert r.is_json
    assert r.json.get('status') in ['ready', 'degraded']


def test_monitoring_single_price_monitor_thread(client):
    # Monitoring endpoint should exist
    r = client.get('/health/monitoring')
    assert r.status_code == 200
    assert r.is_json
    data = r.json
    # Ensure price alert table presence field exists
    assert 'database' in data
    # Validate price monitor service structure
    services = data.get('services') or {}
    pm = services.get('price_monitor') or {}
    assert 'started_flag' in pm or 'error' in pm
    if 'started_flag' in pm:
        assert 'thread_alive' in pm
        # New counters & uptime fields
        assert 'uptime_seconds' in pm
        if pm['uptime_seconds'] is not None:
            assert pm['uptime_seconds'] >= 0
        # Counters may all be zero in test mode but must exist
        assert 'alerts_checked_total' in pm
        assert 'alerts_triggered_total' in pm
        assert 'symbols_checked_total' in pm
        assert 'start_count' in pm
    # Thread count keys added
    assert 'price_monitor_threads_count' in data
    # In TESTING mode, monitor may be skipped; allow 0 or 1 but never >1
    assert data['price_monitor_threads_count'] <= 1, f"Too many PriceMonitor threads: {data['price_monitor_threads']}"


def test_email_queue_processor_status(client):
    r = client.get('/health/monitoring')
    assert r.status_code == 200
    assert r.is_json
    data = r.json
    # Expect email queue processor info nested under services
    services = data.get('services') or {}
    eq = services.get('email_queue_processor') or {}
    # Keys as implemented: running_flag, thread_alive (not configured_active)
    assert 'running_flag' in eq
    assert 'thread_alive' in eq
    assert isinstance(eq.get('running_flag'), bool)
    assert isinstance(eq.get('thread_alive'), bool)
    # New counters & uptime fields
    assert 'uptime_seconds' in eq
    if eq['uptime_seconds'] is not None:
        assert eq['uptime_seconds'] >= 0
    assert 'emails_processed_total' in eq
    assert 'emails_error_total' in eq
    # Service runtime section present
    sr = data.get('service_runtime') or {}
    assert isinstance(sr, dict)
