"""Utility helpers for stock/crypto symbol normalization and validation."""
from __future__ import annotations
import re
from typing import Optional, Tuple

# Allowed pattern: alphanumeric plus dot and dash separators (common for exchanges e.g. EQNR.OL, BRK.B, RDS-A)
_ALLOWED_RE = re.compile(r'^[A-Z0-9][A-Z0-9\.\-/]{0,19}$')  # max length 20, allow / for currency

COMMON_DEFAULT = 'EQNR.OL'

def sanitize_symbol(raw: Optional[str], default: str = COMMON_DEFAULT) -> Tuple[str, bool]:
    """Return a cleaned, uppercased trading symbol and validity flag.

    Rules:
      * Strip whitespace
      * Uppercase
      * Replace commas/underscores with dashes (legacy inputs)
      * Validate length (<=15) & allowed chars (A-Z0-9 . -)
      * If invalid or empty => return default with False validity

    Returns (symbol, is_valid_original)
    """
    if not raw:
        return default, False
    sym = raw.strip().upper().replace(',', '-').replace('_', '-')
    # Collapse consecutive separators (dot, dash, slash)
    sym = re.sub(r'[\.\-/]{2,}', '-', sym)
    if not _ALLOWED_RE.match(sym):
        return default, False
    return sym, True

__all__ = ["sanitize_symbol", "COMMON_DEFAULT"]
