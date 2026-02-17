from app import create_app
from app.extensions import db
from app.models.user import User

app = create_app()

with app.app_context():
    client = app.test_client()
    user = User.query.first()
    if not user:
        print('No user found')
    else:
        with client.session_transaction() as sess:
            sess['_user_id'] = str(user.id)
            sess['_fresh'] = True
        payload = {
            'name': 'Generated Strategy X',
            'buy': {'ma_cross': '10>50'},
            'sell': {'ma_cross': '10<50'},
            'risk': {'stop_loss': 0.05}
        }
        r = client.post('/analysis/api/strategies', json=payload, headers={'Accept':'application/json'})
        print('Create status:', r.status_code, r.get_json())
        if r.status_code == 200 and r.get_json().get('success'):
            sid = r.get_json()['id']
            v = client.get(f'/analysis/api/strategies/{sid}/versions')
            print('Versions fetch:', v.status_code, v.get_json())
