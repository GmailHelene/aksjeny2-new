import pytest
from verify_helpers import detect_base_url
from types import SimpleNamespace
import requests as real_requests

class DummyResp:
    def __init__(self, status_code):
        self.status_code = status_code



@pytest.mark.parametrize(
    "port_status_map,expected_base",
    [
        ( {"5002": None, "5000": 200}, "http://localhost:5000" ),
        ( {"5002": 404, "5000": 200}, "http://localhost:5002" ),
        ( {"5002": None, "5000": None}, "http://localhost:5002" ),  # falls back to historical default
    ]
)
def test_detect_base_url(monkeypatch, port_status_map, expected_base, tmp_path):
    class FakeRequests:
        def get(self, url, timeout=1):
            port = url.split(':')[2].split('/')[0]
            status = port_status_map.get(port)
            if status is None:
                raise ConnectionError("Refused")
            return DummyResp(status)

    monkeypatch.setattr('verify_helpers.requests', FakeRequests())
    detected = detect_base_url(['5002','5000'])
    assert detected == expected_base
