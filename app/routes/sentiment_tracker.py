from flask import Blueprint, redirect, url_for
from flask_login import login_required

sentiment_tracker = Blueprint('sentiment_tracker', __name__)


@sentiment_tracker.route('/')
@login_required
def sentiment_tracker_page():
    """Redirect /sentiment/ to the real sentiment view under /analysis.

    The standalone placeholder previously shown here has been retired per
    EKTE_ONLY policy ("ekte data eller ingenting"). The canonical sentiment
    page is `analysis.sentiment`, which uses Finnhub when configured and
    shows an honest empty state when not.
    """
    return redirect(url_for('analysis.sentiment'), code=302)
