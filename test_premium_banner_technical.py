from app import create_app, db
from app.models.user import User
from flask import url_for


def ensure_premium_user():
    with db.session.begin():
        user = User.query.filter_by(email='premium@example.com').first()
        if not user:
            user = User(username='premiumuser', email='premium@example.com', has_subscription=True, subscription_type='monthly')
            user.set_password('Secret123!')
            db.session.add(user)
        else:
            user.has_subscription = True
            user.subscription_type = 'monthly'
    return user


def test_banner_hidden_on_technical():
    app = create_app()
    app.config['TESTING'] = True
    with app.app_context():
        ensure_premium_user()
        db.session.commit()
    with app.test_client() as client:
        # login
        client.post('/auth/login', data={'email':'premium@example.com','password':'Secret123!'}, follow_redirects=True)
        resp = client.get('/analysis/technical?symbol=TSLA', follow_redirects=True)
        text = resp.get_data(as_text=True)
        banner_present = 'Begrenset modus:' in text
        print('Premium banner present on /analysis/technical with premium user:', banner_present)
        # minimal assertion style
        if banner_present:
            print('ERROR: Banner should be hidden for premium user.')
        else:
            print('OK: Banner hidden for premium user.')

if __name__ == '__main__':
    test_banner_hidden_on_technical()
