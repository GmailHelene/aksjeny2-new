Quarantined demo/mock-only files moved from templates or services.

- app/templates/stocks/data_service.py: Not imported by Python runtime; contained synthetic/demo fallback logic. Moved for clarity and to prevent accidental use.

If needed for reference, inspect this directory, but do not reintroduce into runtime paths.
