class DataSource:
    """Central string constants for data_source field in API responses.

    Using constants prevents typos and eases future refactors / analytics.
    Keep values stable; only append new ones.
    """
    DB = "DB"
    CACHE = "CACHE"
    FALLBACK_SYNTHETIC = "FALLBACK_SYNTHETIC"
    EXTERNAL_API = "EXTERNAL_API"
    DB_ERROR_FALLBACK = "DB_ERROR_FALLBACK"
    COMPUTED = "COMPUTED"
    UNKNOWN = "UNKNOWN"

    @classmethod
    def all(cls):
        return {v for k, v in cls.__dict__.items() if k.isupper()}
