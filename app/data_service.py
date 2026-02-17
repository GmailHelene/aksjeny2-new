# import numpy as np
import random
from datetime import datetime, timedelta
try:
    import yfinance as yf
except ImportError:
    yf = None
import requests
from bs4 import BeautifulSoup
import time
import logging
import warnings
from contextlib import redirect_stdout, redirect_stderr
from io import StringIO

# Import rate limiter
try:
    from .rate_limiter import rate_limiter
    from .simple_cache import simple_cache
except ImportError:
    # Fallback if rate limiter is not available
    class DummyRateLimiter:
        def wait_if_needed(self, api_name='default'):
            time.sleep(0.5)  # Simple fallback delay
    class DummyCache:
        def get(self, key, cache_type='default'):
            return None
        def set(self, key, value, cache_type='default'):
            pass
    rate_limiter = DummyRateLimiter()
    simple_cache = DummyCache()
import sys
from contextlib import redirect_stderr, redirect_stdout
from io import StringIO

# Suppress yfinance warnings and errors
warnings.filterwarnings('ignore')
logging.getLogger('yfinance').setLevel(logging.CRITICAL)

# Import cache service
try:
    from .cache_service import get_cache_service
except ImportError:
    get_cache_service = None

# Define some constants for demo data
OSLO_BORS_TICKERS = [
    "EQNR.OL", "DNB.OL", "TEL.OL", "YAR.OL", "NHY.OL", "AKSO.OL", 
    "MOWI.OL", "ORK.OL", "SALM.OL", "AKERBP.OL", "SUBC.OL", "KAHOT.OL",
    "BAKKA.OL", "SCATC.OL", "MPCC.OL", "GOGL.OL", "FRONTLINE.OL", "FLEX.OL",
    "AKER.OL", "SUBSEA7.OL", "OKEA.OL", "VARENERGI.OL", "BORR.OL", "ARCHER.OL",
    "NEL.OL", "REC.OL", "SCANA.OL", "THIN.OL", "OTELLO.OL", "AEGA.OL", "BEWI.OL", "BONHR.OL"