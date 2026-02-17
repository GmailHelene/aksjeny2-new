import os
import requests

def detect_base_url(preferred_ports=None):
    """Detect a reachable base URL for the dev / test server.
    preferred_ports: optional iterable override for port order.
    Returns base URL string (e.g., http://localhost:5000).
    """
    if preferred_ports is None:
        preferred_ports = []
        if os.getenv('PORT'):
            preferred_ports.append(os.getenv('PORT'))
        preferred_ports.extend(['5002', '5000'])

    seen = set()
    port_candidates = [p for p in preferred_ports if not (p in seen or seen.add(p))]
    for port in port_candidates:
        base = f"http://localhost:{port}"
        # Try /health
        try:
            r = requests.get(base + '/health', timeout=1)
            if r.status_code in (200, 404):
                return base
        except Exception:
            pass
        # Try /auth/login
        try:
            r = requests.get(base + '/auth/login', timeout=1)
            if r.status_code in (200, 302, 401):
                return base
        except Exception:
            pass
    return 'http://localhost:5002'
