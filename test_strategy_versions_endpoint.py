from app import create_app
from app.extensions import db
from app.models.strategy import Strategy

app = create_app()

with app.app_context():
    client = app.test_client()
    strat = Strategy.query.first()
    if not strat:
        print('No strategies found to test')
    else:
        url = f"/analysis/api/strategies/{strat.id}/versions"
        resp = client.get(url)
        print('URL:', url)
        print('Status:', resp.status_code)
        print('JSON:', resp.get_json())
