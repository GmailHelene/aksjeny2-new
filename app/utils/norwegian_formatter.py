"""
Norwegian number and date formatting utilities
"""
from datetime import datetime
from typing import Union, Optional

class NorwegianFormatter:
    """Utility class for Norwegian formatting"""
    
    @staticmethod
    def format_number(value: Union[int, float], decimals: int = 2) -> str:
        """Format number with Norwegian conventions (space as thousand separator, comma as decimal)"""
        if value is None:
            return "—"
        
        try:
            if decimals == 0:
                formatted = f"{int(value):,}".replace(',', ' ')
            else:
                formatted = f"{value:,.{decimals}f}".replace(',', ' ').replace('.', ',')
            return formatted
        except (ValueError, TypeError):
            return "—"
    
    @staticmethod
    def format_currency(value: Union[int, float], currency: str = "NOK", decimals: int = 2) -> str:
        """Format currency with Norwegian conventions"""
        formatted_number = NorwegianFormatter.format_number(value, decimals)
        
        if currency.upper() in ['USD', '$']:
            return f"$ {formatted_number}"
        elif currency.upper() in ['EUR', '€']:
            return f"€ {formatted_number}"
        else:
            return f"{formatted_number} {currency.upper()}"
    
    @staticmethod
    def format_percentage(value: Union[int, float], decimals: int = 2) -> str:
        """Format percentage with Norwegian conventions"""
        if value is None:
            return "—"
        
        try:
            formatted = f"{value:.{decimals}f}".replace('.', ',')
            return f"{formatted} %"
        except (ValueError, TypeError):
            return "—"
    
    @staticmethod
    def format_date(date: datetime, format: str = "short") -> str:
        """Format date in Norwegian style"""
        if not date:
            return "—"
        
        if format == "short":
            return date.strftime("%d.%m.%Y")
        elif format == "long":
            months = {
                1: "januar", 2: "februar", 3: "mars", 4: "april",
                5: "mai", 6: "juni", 7: "juli", 8: "august",
                9: "september", 10: "oktober", 11: "november", 12: "desember"
            }
            return f"{date.day}. {months[date.month]} {date.year}"
        elif format == "time":
            return date.strftime("%d.%m.%Y %H:%M")
        else:
            return date.strftime("%d.%m.%Y")
    
    @staticmethod
    def format_large_number(value: Union[int, float]) -> str:
        """Format large numbers with abbreviations (K, M, B)"""
        if value is None:
            return "—"
        
        try:
            abs_value = abs(value)
            if abs_value >= 1_000_000_000:
                return f"{value / 1_000_000_000:.1f}B".replace('.', ',')
            elif abs_value >= 1_000_000:
                return f"{value / 1_000_000:.1f}M".replace('.', ',')
            elif abs_value >= 1_000:
                return f"{value / 1_000:.1f}K".replace('.', ',')
            else:
                return NorwegianFormatter.format_number(value, 0)
        except (ValueError, TypeError):
            return "—"

# Register as Jinja2 filters
def register_norwegian_filters(app):
    """Register Norwegian formatting filters for Jinja2"""
    app.jinja_env.filters['no_number'] = NorwegianFormatter.format_number
    app.jinja_env.filters['no_currency'] = NorwegianFormatter.format_currency
    app.jinja_env.filters['no_percentage'] = NorwegianFormatter.format_percentage
    app.jinja_env.filters['no_date'] = NorwegianFormatter.format_date
    app.jinja_env.filters['no_large'] = NorwegianFormatter.format_large_number
