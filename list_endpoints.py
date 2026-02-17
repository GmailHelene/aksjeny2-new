from app import create_app
app = create_app()
with app.app_context():
    print('--- Endpoints ---')
    for rule in sorted(app.url_map.iter_rules(), key=lambda r: r.endpoint):
        if rule.endpoint.startswith('analysis'):
            print(rule.endpoint, '->', rule)
