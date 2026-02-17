"""Utility for aggregating/suppressing duplicate warning messages.

Tracks symbols (or arbitrary keys) for which a particular warning pattern has
already been emitted during the current process lifetime. Prevents log spam
from repeating the same high-volume fallback warnings (e.g. ALL REAL DATA SOURCES FAILED).
"""
from __future__ import annotations
from threading import RLock

_emitted = {}
_lock = RLock()

def should_log(category: str, key: str) -> bool:
    """Return True if this (category, key) pair has not been logged before.

    Args:
        category: Logical group of warnings (e.g. 'all_real_data_failed').
        key: Specific identifier (e.g. symbol).
    """
    with _lock:
        bucket = _emitted.setdefault(category, set())
        if key in bucket:
            return False
        bucket.add(key)
        return True

def reset_category(category: str):
    with _lock:
        _emitted.pop(category, None)

def stats():
    with _lock:
        return {k: len(v) for k, v in _emitted.items()}
