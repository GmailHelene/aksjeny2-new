# Squash Migration Plan

## Objective
Provide a clean baseline migration that represents the current production schema to eliminate multi-root history and idempotent guards. Future fresh environments should apply a single baseline migration, then only new linear revisions.

## Current Issues
- Historical multiple roots: `769884445837` (initial) and `46b5a3c74c95` (user_stats) originally both had `down_revision = None`.
- Idempotent guards added to avoid failures (duplicate table / column) now mask underlying divergence.
- Column/table existence checks make schema drift harder to detect (silent skips).

## Recommended Strategy
1. Freeze schema from a live DB (introspect via SQLAlchemy inspector or `pg_dump --schema-only` / `sqlite .schema` depending on backend).
2. Generate a new migration `0001_baseline.py` containing full schema creation (omit dynamic / runtime ephemeral tables if any).
3. Mark all existing historical migrations as deprecated (leave in repo for reference temporarily but remove from alembic version chain for new deployments).
4. For existing production database, STAMP the DB at the new baseline revision (no DDL executed):
   ```bash
   flask db stamp 0001_baseline
   ```
5. Remove idempotent guards in new forward migrations (guards only for truly optional experimental tables).
6. Enforce linear chain going forward.

## Detailed Steps
| Step | Action | Rationale |
|------|--------|-----------|
| 1 | Create branch `migration-squash` | Isolate changes |
| 2 | Inventory tables | Ensure no orphan / legacy tables included |
| 3 | Autogenerate draft | `flask db revision --autogenerate -m "baseline squash"` |
| 4 | Manually review | Remove unwanted / ephemeral tables |
| 5 | Rename revision file to `0001_baseline.py` | Clear starting point |
| 6 | Update Alembic script to prune old versions when creating *fresh* env | Avoid dual heads |
| 7 | Add doc warning that legacy revisions are deprecated | Clarity |
| 8 | Stamp existing prod DB | Avoid DDL duplication |
| 9 | Delete (or archive) old versions in a `legacy_migrations/` folder | History preserved |
| 10 | CI check to assert single head (`alembic heads` returns one) | Prevent regression |

## Table Inventory (from monitor_status.py output)
```
achievements, ai_models, alembic_version, alert_notification_settings, audit_logs, device_trial_tracker, email_queue, favorites, forum_categories, forum_post_likes, forum_posts, forum_topic_views, forum_topics, login_attempts, notification_settings, notifications, portfolio_audit_log, portfolio_stocks, portfolios, prediction_logs, price_alerts, referral_discounts, referrals, stock_tips, strategies, strategy_versions, transactions, trial_sessions, user_achievements, user_activities, user_sessions, user_stats, users, watchlist_alerts, watchlist_items, watchlist_stocks, watchlists
```

## Exclusion Candidates
- `alembic_version` (managed by Alembic).
- Any temporary / cache tables (none listed presently).

## Optional Enhancements
- Add script `scripts/dump_schema.py` to output deterministic DDL snapshot for diffing in CI.
- Add pre-commit hook to reject multiple heads.

## Rollback Strategy
If baseline causes issues:
1. Revert branch.
2. Restore previous migrations folder.
3. Re-run `flask db upgrade` (guards still prevent breakage).

## Acceptance Criteria
- Single Alembic head after squash.
- Fresh clone: `flask db upgrade` results in full schema with no extra migrations needed.
- Production DB stamped without running DDL.

## Next Actions (Not Yet Executed)
- Implement branch & baseline generation.
- Provide baseline revision template.

---
*This document is a plan only—no squash executed yet.*
