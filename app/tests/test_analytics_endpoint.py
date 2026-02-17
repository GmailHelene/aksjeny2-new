import unittest
from app import create_app

class AnalyticsEndpointTest(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.client = self.app.test_client()

    def test_dashboard_keys(self):
        resp = self.client.get('/analytics/api/dashboard/EURUSD')
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(resp.is_json)
        data = resp.get_json()
        # Assert core keys
        for key in [
            'market_data', 'risk_metrics', 'technical_analysis',
            'pattern_recognition', 'performance_metrics', 'alerts',
            'symbol', 'timeframe', 'timestamp'
        ]:
            self.assertIn(key, data)

if __name__ == '__main__':
    unittest.main()
