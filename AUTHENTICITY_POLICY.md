# Data Authenticity & Simulation Policy

## Objective
Ensure users always see real data when available. When real data is unavailable, fallback simulated values are displayed **without fabrication** and clearly labeled as `Simulert`. Demo-only placeholder values (legacy 'AI generated' numbers) have been removed for authenticated premium contexts.

## Labeling Rules
| Context | Label | Behavior |
|---------|-------|----------|
| Real market / recommendation data | `Ekte` badge | Full real values shown |
| Simulated fallback (structural) | `Simulert` badge | Only structural placeholders / neutral None values; no invented metrics |
| Demo mode example content | `Demo` badge | May show illustrative values; clearly separated |

## Affected Pages
- Market Overview (`/analysis/market_overview`) – mixed real + simulated rows, each simulated row labeled.
- Recommendations Overview (`/analysis/recommendations`) – real aggregated movers & breadth, no fabricated targets.
- Recommendation Detail (`/analysis/recommendations/<ticker>`) – real metrics if present; otherwise neutral placeholders with `Simulert` badge.
- TradingView / Technical Analysis – always real embed; fallback iframe only if symbol mapping fails.

## Implementation Highlights
- Central DataService returns either real data payloads or enhanced fallback dictionaries flagged for simulation.
- Templates use conditional guards: numeric formatting only applied when value is not None.
- Badges added via Jinja conditionals: `real_data`, `simulated`, `demo_mode` flags.
- No randomization for premium user fallbacks; deterministic structural placeholders only.

## Strategy Builder Integrity (Related)
While not data authenticity per se, strategy versioning uses checksum-based snapshots ensuring no duplicate versions on unchanged updates, reinforcing trust and transparency in user configuration history.

## Tests Covering Policy
| Test File | Purpose |
|-----------|---------|
| `test_market_overview_simulated.py` | Ensures simulated entries labeled and present |
| `test_recommendations_overview_real.py` | Confirms real overview renders without demo artifacts |
| `test_recommendation_detail.py` | Validates demo badge, simulated fallback path, and no fabricated metrics |
| `test_strategy_*` suite | Indirect integrity via reliable snapshotting (trustworthy history) |

## Future Enhancements
- Add explicit badge legend component reused across pages.
- Centralize authenticity flags in a helper to reduce repetition.
- Extend logging to track frequency of simulated fallbacks for monitoring data source reliability.

## Monitoring
Add lightweight counter metrics (future) for occurrences of simulated render events to identify data source degradation patterns.

---
Generated: automated policy documentation ensuring platform-wide consistency.
