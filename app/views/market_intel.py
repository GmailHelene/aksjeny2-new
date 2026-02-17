"""Legacy market_intel view-based route definitions.

This file previously registered a direct app.route('/market-intel/sector-analysis')
inside an init helper. The active/maintained implementation now lives in
`app/routes/market_intel.py` under the `market_intel` blueprint.

Having both active caused route duplication / unpredictable handler selection
in production (Flask will keep the last registered). That manifested as the
"Beklager, en feil oppsto" page despite a healthy blueprint route with richer
fallback data.

We disable the legacy registration below while keeping a minimal stub for
historic reference. If re‑enabled intentionally, rename the function to avoid
shadowing and ensure only ONE sector-analysis endpoint is registered.
"""

# NOTE: Intentionally NOT importing render_template or utilities here to avoid
# accidental side effects / partial imports during app startup.

def init_market_intel_routes(app):  # pragma: no cover - legacy stub
    app.logger.info("init_market_intel_routes called - legacy sector-analysis route is disabled (using blueprint version)")
    # Intentionally do nothing.
