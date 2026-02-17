import json
from app.utils import api_response


def extract(resp_tuple):
    resp, status = resp_tuple
    # Flask test responses would differ; here we call jsonify which creates a Response
    # But in isolation (without app context) this may fail; tests assume app context provided externally.
    return json.loads(resp.get_data(as_text=True)), status


def test_ok_with_list_counts(monkeypatch, app):  # assuming pytest fixture 'app' provides context
    with app.app_context():
        data_list = [1, 2, 3]
        body, status = extract(api_response.ok({'data': data_list}))
        assert status == 200
        assert body['success'] is True
        assert body['data_points'] == 3
        assert body['data'] == data_list


def test_ok_with_extra_metadata(app):
    with app.app_context():
        body, status = extract(api_response.ok({'items': ['a']}, extra={'foo': 'bar', 'cache_hit': 'should_not_override'}))
        assert status == 200
        assert body['foo'] == 'bar'
        # Ensure existing cache_hit default bool not overridden by extra string
        assert isinstance(body['cache_hit'], bool)
        assert body['data_points'] == 1


def test_fail_with_data_and_auto_count(app):
    with app.app_context():
        body, status = extract(api_response.fail('ERROR_CODE', data={'results': [10, 20]}))
        assert status == 200
        assert body['success'] is False
        assert body['error'] == 'ERROR_CODE'
        assert body['data_points'] == 2
        assert body['results'] == [10, 20]


def test_single_key_payload_list(app):
    with app.app_context():
        body, status = extract(api_response.ok({'records': []}))
        assert status == 200
        assert body['data_points'] == 0


def test_no_list_no_data_points(app):
    with app.app_context():
        body, status = extract(api_response.ok({'value': 42}))
        assert 'data_points' not in body
