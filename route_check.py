from app import app

with app.app_context():
    for rule in sorted(app.url_map.iter_rules(), key=lambda r: r.rule):
        if rule.endpoint.startswith('portfolio.'):
            print(f"{rule.rule:40} -> {rule.endpoint}")
