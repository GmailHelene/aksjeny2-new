from datetime import datetime
from ..extensions import db

class PortfolioAuditLog(db.Model):
    __tablename__ = 'portfolio_audit_log'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, index=True, nullable=False)
    portfolio_id = db.Column(db.Integer, index=True, nullable=True)
    stock_id = db.Column(db.Integer, index=True, nullable=True)
    ticker = db.Column(db.String(20), index=True)
    action = db.Column(db.String(32), nullable=False)  # add_stock, edit_stock, delete_stock, delete_portfolio
    before_state = db.Column(db.JSON)
    after_state = db.Column(db.JSON)
    ip_address = db.Column(db.String(64))
    user_agent = db.Column(db.String(256))
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)

    def __repr__(self):  # pragma: no cover
        return f"<PortfolioAuditLog action={self.action} ticker={self.ticker} id={self.id}>"
