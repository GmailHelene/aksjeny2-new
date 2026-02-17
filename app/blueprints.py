def register_blueprints(app):
    """Register all blueprints"""
    from .routes.main import main
    from .routes.auth import auth
    from .routes.stocks import stocks 
    from .routes.portfolio import portfolio
    from .routes.watchlist import watchlist
    from .routes.api import api
    from .routes.analysis import analysis
    from .routes.news import news

    # Register blueprints
    app.register_blueprint(main)
    app.register_blueprint(auth)
    app.register_blueprint(stocks, url_prefix='/stocks')
    app.register_blueprint(portfolio)
    app.register_blueprint(watchlist)  # Added watchlist blueprint
    app.register_blueprint(api)
    app.register_blueprint(analysis)
    app.register_blueprint(news)
