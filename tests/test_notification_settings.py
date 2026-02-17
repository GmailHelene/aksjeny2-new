import json

from app.models.user import User
from app import db


def test_update_notification_settings(auth_client):
    client, user = auth_client

    def refresh_user():
        db.session.expire_all()
        return User.query.get(user.id)

    # Ensure initial attribute present
    initial = refresh_user()
    assert hasattr(initial, 'email_notifications_enabled')

    # Toggle OFF
    resp = client.post('/update-notification-settings', data=json.dumps({
        'setting': 'emailNotifications',
        'enabled': False
    }), content_type='application/json')
    assert resp.status_code == 200
    data = resp.get_json()
    assert data['success'] is True
    after_off = refresh_user()
    # Debug raw DB value
    raw_val = db.session.execute(db.text('SELECT email_notifications_enabled FROM users WHERE id = :id'), {'id': user.id}).fetchone()[0]
    print('Raw DB value after OFF:', raw_val, 'ORM attr:', after_off.email_notifications_enabled)
    assert raw_val in (0, False, None)  # Accept 0/False/None for off
    assert after_off.email_notifications_enabled is False

    # Toggle ON
    resp2 = client.post('/update-notification-settings', data=json.dumps({
        'setting': 'emailNotifications',
        'enabled': True
    }), content_type='application/json')
    assert resp2.status_code == 200
    data2 = resp2.get_json()
    assert data2['success'] is True
    after_on = refresh_user()
    assert after_on.email_notifications_enabled is True

    # Basic sanity: profile page loads
    profile = client.get('/profile')
    assert profile.status_code == 200
    assert b'id="emailNotifications"' in profile.data
