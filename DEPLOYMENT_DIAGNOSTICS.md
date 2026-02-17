# Deployment Diagnostics & Verification

## Purpose
Ensure production environment loads all optional blueprints (e.g. `sentiment_tracker`) without triggering template `BuildError` and reduce log noise for clearer real-data authenticity signals.

## Navigation Safety Guards
Navigation templates now guard optional endpoints:
- `base.html`
- `base_clean.html`
- `base_clean_version.html`

They check `current_app.view_functions` before rendering the Sentiment Tracker link:
```
{% if 'sentiment_tracker.sentiment_tracker_page' in current_app.view_functions %}
  <li>...</li>
{% endif %}
```
If the blueprint isn't registered, link is hidden (no 500 error).

## Route Diagnostics Endpoint
A new endpoint lists all registered routes:
```
GET /api/routes
```
Response shape:
```
{
  "success": true,
  "route_count": 312,
  "has_sentiment_tracker": true,
  "routes": [
    {"endpoint": "sentiment_tracker.sentiment_tracker_page", "rule": "/sentiment/", "methods": ["GET"]},
    ...
  ]
}
```
Use this right after deploy to confirm presence:
```
curl -s https://yourdomain/api/routes | jq '.has_sentiment_tracker'
```

## Log Noise Reduction
Duplicate high-volume warnings are suppressed:
- All-real-data-failed per symbol (EKTE-only) now logs once per symbol (category: `all_real_data_failed`).
Implementation: `app/services/warning_tracker.py` with `should_log()` gate.

Deterministic yfinance no-data situations raise `NonRetryableError`, stopping futile retries and immediately attempting fallback.

## How To Verify After Deploy
1. Health check:
   - `curl -s https://yourdomain/api/health` => status healthy
2. Routes check:
   - `curl -s https://yourdomain/api/routes | jq '.has_sentiment_tracker'` should be true (unless intentionally disabled)
3. No BuildError:
   - Load homepage, ensure navigation renders (Sentiment Tracker link appears if blueprint loaded)
4. Tail logs:
   - Confirm no repeating lines of `ALL REAL DATA SOURCES FAILED for <same symbol>` more than once.
   - Confirm yfinance deterministic failures show `⛔ yfinance history non-retryable` rather than multiple exponential retry warnings.
5. Premium access verification scripts (local):
   - Run: `python3 verify_premium_access.py` (ensures auth & gating intact)

## Troubleshooting
| Symptom | Action |
|---------|--------|
| Sentiment link missing | Check `/api/routes` for endpoint; if absent, ensure `app/routes/sentiment_tracker.py` exists and no import errors in logs. |
| Still seeing duplicate failing warnings | Ensure deploy included `warning_tracker.py` and updated `data_service.py`. Restart application. |
| Excessive yfinance retries | Confirm updated `enhanced_yfinance_service.py` deployed (contains `NonRetryableError`). |

## Safe Rollback
Changes are additive and defensive. To rollback a single part:
- Remove block in templates (not recommended) or keep—guards are harmless.
- Revert `warning_tracker` import section in `data_service.py` if necessary (will reintroduce more noise only).

## Next Improvement Ideas
- Add rate limiting metrics to `/api/health` (cache hit %, circuit breaker status per symbol group)
- Optional auth on `/api/routes` behind admin if exposure concerns arise
- Aggregate suppressed counts in periodic summary log.

---
Last updated: (auto-generated)