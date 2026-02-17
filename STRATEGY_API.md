# Strategy Builder API

## Endpoints

### List / Create Strategies
GET /analysis/api/strategies
POST /analysis/api/strategies
Payload (POST):
{
  "name": "Momentum 1",
  "buy": {"indicator":"rsi","condition":"below","value":30},
  "sell": {"indicator":"rsi","condition":"above","value":70},
  "risk": {"stop_loss":5,"take_profit":10}
}
Response success: {"success":true,"id":123,"name":"Momentum 1"}

### Get / Update / Delete Single
GET /analysis/api/strategies/<id>
PATCH /analysis/api/strategies/<id>
DELETE /analysis/api/strategies/<id>
PATCH payload keys: name, buy, sell, risk (objects)
Response: {"success":true,"strategy": { ...full strategy... }}

### Backtest
POST /analysis/api/strategies/<id>/backtest
Payload: {"symbol":"DNB.OL","period":"6M"}
Stub Response: {"success":true,"backtest": {"symbol":"DNB.OL","period":"6M","metrics": {"return_pct":12.3,"volatility":4.1,"sharpe":1.2,"trades":14,"win_rate_pct":57.1,"max_drawdown_pct":-6.4}}}

### Version History
GET /analysis/api/strategies/<id>/versions
Response: {"success":true,"versions":[{"id":11,"strategy_id":4,"version":3,"name":"Momentum 1","buy":{},"sell":{},"risk":{},"created_at":"2025-09-14T11:22:00.123Z"}, ...]}

### Rollback
POST /analysis/api/strategies/<id>/rollback/<version_id>
Effect: Clones the selected version content into the live strategy, then creates a new snapshot with version = last+1. Does not mutate historical rows.
Response: {"success":true,"strategy": { ...updated... }, "new_version": 7}

## Versioning Rules
- Version 1 created automatically on initial create
- Each PATCH that changes at least one field commits and appends new version (incremental)
- Rollback always appends a new version reflecting the rolled state
- History capped to 200 latest in fetch endpoint (UI consumes)

### Additional Guarantees
- Versions are immutable; no in-place edits or deletions.
- Monotonic integer sequence per strategy (no gaps except theoretical skipped numbers if a transaction fails before commit; system currently commits sequentially so gaps should not occur).
- A SHA-256 checksum of the canonical payload (name + buy + sell + risk sorted JSON) is stored per snapshot.
- Duplicate snapshots (identical checksum to latest) are skipped to reduce noise (updates with no effective change return message `Ingen endringer`).
- Rollback avoids creating a duplicate if the target state already matches current checksum.

### Checksum Field
- Field name: `checksum` (exposed optionally in versions list when `?include_checksum=1`).
- Use case: quickly detect identical historical states; diff short-circuit; ETag generation.
- Duplicate snapshots (same checksum as latest) are skipped.

### Versions Pagination
- Endpoint now supports query params: `page` (default 1), `per_page` (default 50, max 200).
- Response fields: `page`, `per_page`, `total` plus `versions` array.
- Backwards compatible: legacy clients (no params) still see at most 200 latest versions.

### Diff Endpoint
GET /analysis/api/strategies/<id>/diff/<v1>/<v2>
Response:
{
  "success": true,
  "identical": false,
  "checksum_equal": false,
  "left_version": 3,
  "right_version": 7,
  "diff": {
    "fields_changed": ["name","buy","risk"],
    "details": {
      "name": {"left":"Old","right":"New"},
      "buy_rules": {"left":{...}, "right":{...}}
    }
  }
}
- If checksums match, returns `identical: true` and empty diff without computing field comparisons.

### ETag Support
- GET single strategy now returns `ETag: W/"<checksum>"` using latest version checksum.
- If client sends matching `If-None-Match`, server returns `304 Not Modified` with same ETag and empty body.
- Use to reduce payload transfer for frequent polling.

### Rate Limiting
- Applied lightweight in-memory per-user window counters (subject to future Redis upgrade):
- Create (POST /strategies): 30 per 60s
- Update/Delete (PUT/PATCH/DELETE /strategies/<id>): 60 total mutating ops per 60s
- Backtest (POST /strategies/<id>/backtest): 25 per 300s
- Rollback (POST /rollback/<version_id>): 20 per 300s
- Exceeded => HTTP 429 with body {"success":false,"error":"Rate limit"}

### Optional Checksum Exposure
- Add `?include_checksum=1` to versions endpoint to include each snapshot checksum (for client caching / diff pre-check).
- Omit the param to preserve lean payload.

### API Versioning Alias
- All endpoints have `/analysis/api/v1/...` aliases in addition to existing `/analysis/api/...` paths.
- Future breaking changes will introduce `/v2` while keeping `/v1` stable.

## UI Behavior
- After save: Automatic backtest triggered with default {symbol:'DNB.OL',period:'6M'}
- Version panel fetches on entering edit mode (click pencil).
- "Load version" fills form (not persisted until user presses Save).
- "Rollback" calls backend and refreshes list.

## Error Handling Patterns
- Consistent JSON: {success:false,error:"..."}
- 404 for missing strategy / version
- 500 for commit or snapshot failures

## Future Enhancements (Recommended)
- Diff endpoint to compare two versions
- Tagging / labeling versions (e.g., "baseline", "experiment")
- Batch backtest across symbols
- Export/import strategies (JSON)
- Surface checksum & optional hash-based diff summary
- ETag / conditional GET for strategy detail & versions
- Pagination for very long histories (once >200 snapshots common)

## Example Strategy Object (Full)
{
  "id": 42,
  "name": "Momentum 1",
  "buy": {"indicator":"rsi","condition":"below","value":30},
  "sell": {"indicator":"rsi","condition":"above","value":70},
  "risk": {"stop_loss":5,"take_profit":10},
  "created_at": "2025-09-14T11:10:33.912Z",
  "updated_at": "2025-09-14T11:21:10.441Z"
}

