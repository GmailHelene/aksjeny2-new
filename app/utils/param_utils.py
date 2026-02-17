"""Utility helpers for normalizing and sanitizing incoming query/form parameters.

Central place to coerce javascript 'undefined', 'null', empty strings and excessive
whitespace into safe Python None values. Avoids scattered ad-hoc checks across routes.
"""
from typing import Optional, Dict, Any

UNDEFINED_STRINGS = {"undefined", "null", "none", ""}

def normalize_symbol(raw: Optional[str]) -> Optional[str]:
    if raw is None:
        return None
    cleaned = raw.strip().upper()
    if cleaned.lower() in UNDEFINED_STRINGS:
        return None
    # Basic guard: excessively long symbols rejected
    if len(cleaned) > 15:
        return None
    return cleaned

def sanitize_params(params: Dict[str, Any], keys: Optional[list] = None) -> Dict[str, Any]:
    """Return copy with normalized values.

    keys: subset of keys to normalize; if None normalize all string values.
    """
    result = {}
    target_keys = keys or list(params.keys())
    for k, v in params.items():
        if k not in target_keys:
            result[k] = v
            continue
        if isinstance(v, str):
            low = v.strip().lower()
            result[k] = None if low in UNDEFINED_STRINGS else v.strip()
        else:
            result[k] = v
    return result

__all__ = ["normalize_symbol", "sanitize_params"]
