import re
from typing import Tuple, Dict, Any

NAME_REGEX = re.compile(r'^[A-Za-z0-9 æøåÆØÅ_\-]{2,120}$')

class StrategyValidationError(Exception):
    def __init__(self, message: str, status: int = 400):
        super().__init__(message)
        self.status = status


def validate_strategy_payload(data: Dict[str, Any], existing_names_lower=None, current_id=None) -> Tuple[str, Dict[str, Any], Dict[str, Any], Dict[str, Any]]:
    """Validate incoming strategy create/update payload.

    existing_names_lower: optional iterable of lowercase names for duplicate detection (create path)
    current_id: id of current strategy (update path) to exclude from duplicate check
    Returns normalized (name, buy, sell, risk)
    Raises StrategyValidationError on failure
    """
    raw_name = data.get('name')
    name = (raw_name or '').strip() if raw_name is not None else None

    if name is not None:  # only validate name if provided (update may omit)
        if not name:
            raise StrategyValidationError('Navn kan ikke være tomt', 400)
        if len(name) < 2:
            raise StrategyValidationError('Navn for kort', 400)
        if len(name) > 120:
            raise StrategyValidationError('Navn kan ikke overstige 120 tegn', 422)
        if not NAME_REGEX.match(name):
            raise StrategyValidationError('Navn inneholder ugyldige tegn', 400)
        if existing_names_lower is not None and name.lower() in existing_names_lower:
            raise StrategyValidationError('Strateginavn finnes allerede', 409)

    def ensure_obj(field: str):
        val = data.get(field)
        if val is None:
            return None
        if not isinstance(val, dict):
            raise StrategyValidationError(f'{field} må være et objekt', 400)
        return val

    buy = ensure_obj('buy')
    sell = ensure_obj('sell')
    risk = ensure_obj('risk')

    return name, buy, sell, risk
