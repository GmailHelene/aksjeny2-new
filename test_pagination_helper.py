import pytest
from app import create_app, db
from flask import Blueprint
from app.utils.api_response import ok


bp = Blueprint('pagination_test', __name__)

@bp.route('/_test/paginated')
def paginated():
    items = [{'id': i} for i in range(5)]
    return ok({'items': items, 'data_points': len(items)}, page=2, pages=5, total=25)


@pytest.fixture
def app_instance():
    app = create_app('testing')
    with app.app_context():
        db.create_all()
    app.register_blueprint(bp)
    return app


@pytest.fixture
def client(app_instance):
    return app_instance.test_client()


def test_pagination_metadata(client):
    r = client.get('/_test/paginated')
    assert r.status_code == 200
    data = r.get_json()
    assert data['page'] == 2
    assert data['pages'] == 5
    assert data['total'] == 25
    assert data['data_points'] == 5
    assert data['success'] is True