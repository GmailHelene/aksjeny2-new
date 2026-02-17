from datetime import datetime
from ..extensions import db

class Portfolio(db.Model):
    __tablename__ = 'portfolios'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), nullable=False)
    description = db.Column(db.String(256))
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    stocks = db.relationship('PortfolioStock', backref='portfolio', lazy='dynamic', cascade='all, delete-orphan')
    # NOTE: user relationship is defined in User model to avoid conflicts
    is_watchlist = db.Column(db.Boolean, default=False)
    
    def __init__(self, name=None, description=None, user_id=None, **kwargs):
        super().__init__(**kwargs)
        if name is not None:
            self.name = name
        if description is not None:
            self.description = description
        if user_id is not None:
            self.user_id = user_id
    
    def calculate_total_value(self):
        total = 0.0
        for stock in self.stocks:
            # Lazy import to avoid circular dependencies
            from ..services.data_service import DataService
            stock_info = DataService.get_stock_info(stock.ticker)
            if stock_info and 'regularMarketPrice' in stock_info:
                total += stock_info['regularMarketPrice'] * stock.shares
        return total
    
    def get_stock_allocation(self):
        total_value = self.calculate_total_value()
        allocation = []
        for stock in self.stocks:
            # Lazy import to avoid circular dependencies
            from ..services.data_service import DataService
            stock_info = DataService.get_stock_info(stock.ticker)
            if stock_info and 'regularMarketPrice' in stock_info:
                value = stock_info['regularMarketPrice'] * stock.shares
                percentage = (value / total_value * 100) if total_value > 0 else 0
                allocation.append({
                    'ticker': stock.ticker,
                    'shares': stock.shares,
                    'value': value,
                    'percentage': percentage
                })
        return allocation
    
    @property
    def total_return(self):
        """Calculate total return (gain/loss) for the portfolio in currency"""
        try:
            current_value = self.calculate_total_value()
            invested_value = sum(stock.purchase_price * stock.shares for stock in self.stocks if stock.purchase_price)
            if invested_value > 0:
                return current_value - invested_value
            return 0.0
        except Exception:
            return 0.0
    
    @property
    def return_percentage(self):
        """Calculate total return percentage for the portfolio"""
        try:
            current_value = self.calculate_total_value()
            invested_value = sum(stock.purchase_price * stock.shares for stock in self.stocks if stock.purchase_price)
            if invested_value > 0:
                return ((current_value - invested_value) / invested_value) * 100
            return 0.0
        except Exception:
            return 0.0
    
    @property
    def currency(self):
        """Default currency for the portfolio"""
        # You can make this configurable per portfolio later
        return 'NOK'
    
    @property
    def holdings(self):
        """Get list of holdings for compatibility with templates"""
        return list(self.stocks)

class PortfolioStock(db.Model):
    __tablename__ = 'portfolio_stocks'
    __table_args__ = (
        db.Index('ix_portfolio_stocks_portfolio_deleted', 'portfolio_id', 'deleted_at'),
    )
    
    id = db.Column(db.Integer, primary_key=True)
    portfolio_id = db.Column(db.Integer, db.ForeignKey('portfolios.id'))
    ticker = db.Column(db.String(20))
    shares = db.Column(db.Float, default=0)
    purchase_price = db.Column(db.Float)
    purchase_date = db.Column(db.DateTime, default=datetime.utcnow)
    notes = db.Column(db.String(256))
    deleted_at = db.Column(db.DateTime, nullable=True, index=True)
    
    # Relationship - using backref for consistency  
    # NOTE: portfolio relationship is defined in Portfolio model via backref
    
    def calculate_return(self):
        # Lazy import to avoid circular dependencies
        from ..services.data_service import DataService
        stock_info = DataService.get_stock_info(self.ticker)
        if stock_info and 'regularMarketPrice' in stock_info:
            current_price = stock_info['regularMarketPrice']
            return (current_price - self.purchase_price) / self.purchase_price * 100
        return 0

class Transaction(db.Model):
    """Model for portfolio transactions"""
    __tablename__ = 'transactions'
    
    id = db.Column(db.Integer, primary_key=True)
    portfolio_id = db.Column(db.Integer, db.ForeignKey('portfolios.id'), nullable=False)
    ticker = db.Column(db.String(20), nullable=False)
    transaction_type = db.Column(db.String(10), nullable=False)  # 'buy' or 'sell'
    shares = db.Column(db.Float, nullable=False)
    price = db.Column(db.Float, nullable=False)
    transaction_date = db.Column(db.DateTime, default=datetime.utcnow)
    notes = db.Column(db.Text)
    
    # Relationships
    portfolio = db.relationship('Portfolio', backref='transactions')
    
    def __repr__(self):
        return f'<Transaction {self.transaction_type} {self.shares} {self.ticker}>'
    
    @property
    def total_value(self):
        """Calculate total value of transaction"""
        return self.shares * self.price