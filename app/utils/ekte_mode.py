from flask import current_app

def is_ekte_only() -> bool:
    try:
        cfg = current_app.config
        return bool(cfg.get('EKTE_ONLY', True))
    except Exception:
        # If current_app isn't available, default to EKTE-only for safety
        return True
