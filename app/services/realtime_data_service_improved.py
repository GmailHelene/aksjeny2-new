"""
Real-time data service for live stock prices and market data with WebSocket streaming
Enhanced version with robust error handling, fallbacks, and rate limiting
"""
import asyncio
import aiohttp
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Set, Tuple
try:
    import yfinance as yf
except ImportError:
    yf = None
from flask import current_app
import threading
import time
from app.extensions import db
from dataclasses import dataclass, asdict
# import numpy as np
from collections import defaultdict, deque
import queue
import random
import os
import traceback

# Import rate limiter
try:
    from app.utils.rate_limiter import rate_limiter
except ImportError:
    # Fallback if rate limiter is not available
    class DummyRateLimiter:
        def wait_if_needed(self, api_name='default'):
            time.sleep(2.0)  # Simple fallback delay
    rate_limiter = DummyRateLimiter()

# Set up logging
logger = logging.getLogger(__name__)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler = logging.StreamHandler()
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(logging.INFO)

# Configure yfinance if available
if yf is not None:
    yf.set_tz_session_explicitly = True
