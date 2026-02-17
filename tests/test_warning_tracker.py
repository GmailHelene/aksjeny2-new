import logging
from app.services.warning_tracker import should_log, reset_category, stats

def test_should_log_once():
    reset_category('all_real_data_failed')
    assert should_log('all_real_data_failed', 'AAPL') is True
    # Second time suppressed
    assert should_log('all_real_data_failed', 'AAPL') is False
    # Different symbol logs
    assert should_log('all_real_data_failed', 'MSFT') is True
    s = stats()
    assert s.get('all_real_data_failed') == 2  # AAPL + MSFT recorded
