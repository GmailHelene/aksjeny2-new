from flask import Blueprint, render_template, current_app
from flask_login import login_required, current_user

sentiment_tracker = Blueprint('sentiment_tracker', __name__)

@sentiment_tracker.route('/')
@login_required
def sentiment_tracker_page():
    """Minimal sentiment tracker placeholder page.

    Added to resolve BuildError caused by template references to
    url_for('sentiment_tracker.sentiment_tracker_page'). Replace with
    real implementation later (market sentiment, social sentiment, etc.).
    """
    try:
        # Placeholder context; expand with real data later
        context = {
            'title': 'Sentiment Tracker',
            'description': 'Denne siden viser markeds- og sosialt sentiment (kommer snart).',
            'user': current_user if current_user.is_authenticated else None
        }
        return render_template('sentiment_tracker/index.html', **context)
    except Exception as e:
        current_app.logger.error(f"Error rendering sentiment tracker page: {e}")
        return render_template('sentiment_tracker/index.html', title='Sentiment Tracker', error=True)
