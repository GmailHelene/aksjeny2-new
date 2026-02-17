"""
Custom Jinja2 filters for the application
"""
from typing import Union


def norwegian_number(value: Union[int, float], decimals: int = 2, currency: str = None) -> str:
    """
    Format number according to Norwegian conventions.
    
    Args:
        value: The number to format
        decimals: Number of decimal places
        currency: Currency symbol to prepend (kr, $, €, etc.)
    
    Returns:
        Formatted string with Norwegian number formatting
    """
    if value is None:
        return '-'
    
    try:
        # Handle negative numbers
        negative = value < 0
        value = abs(value)
        
        # Format the number
        if decimals > 0:
            formatted = f"{value:,.{decimals}f}"
        else:
            formatted = f"{value:,.0f}"
        
        # Replace separators for Norwegian format
        # First replace commas with a placeholder
        formatted = formatted.replace(',', '§')
        # Replace decimal point with comma
        formatted = formatted.replace('.', ',')
        # Replace placeholder with space
        formatted = formatted.replace('§', ' ')
        
        # Add negative sign if needed
        if negative:
            formatted = f"-{formatted}"
        
        # Add currency if provided
        if currency:
            if currency == 'kr':
                formatted = f"kr {formatted}"
            elif currency in ['$', '€', '£']:
                formatted = f"{currency} {formatted}"
            else:
                formatted = f"{formatted} {currency}"
        
        return formatted
        
    except (ValueError, TypeError):
        return '-'


def percentage(value: Union[int, float], decimals: int = 2, show_plus: bool = True) -> str:
    """
    Format percentage with Norwegian conventions.
    
    Args:
        value: The percentage value
        decimals: Number of decimal places
        show_plus: Whether to show + for positive values
    
    Returns:
        Formatted percentage string
    """
    if value is None:
        return '-'
    
    try:
        formatted = norwegian_number(value, decimals)
        
        if show_plus and value > 0:
            formatted = f"+{formatted}"
        
        return f"{formatted}%"
        
    except (ValueError, TypeError):
        return '-'


def large_number(value: Union[int, float]) -> str:
    """
    Format large numbers with abbreviations (K, M, B).
    
    Args:
        value: The number to format
    
    Returns:
        Formatted string with abbreviation
    """
    if value is None:
        return '-'
    
    try:
        value = float(value)
        
        if value >= 1_000_000_000:
            return norwegian_number(value / 1_000_000_000, 2) + ' mrd'
        elif value >= 1_000_000:
            return norwegian_number(value / 1_000_000, 2) + ' mill'
        elif value >= 1_000:
            return norwegian_number(value / 1_000, 1) + ' k'
        else:
            return norwegian_number(value, 0)
            
    except (ValueError, TypeError):
        return '-'


def register_filters(app):
    """Register custom filters with the Flask app."""
    app.jinja_env.filters['norwegian_number'] = norwegian_number
    app.jinja_env.filters['percentage'] = percentage
    app.jinja_env.filters['large_number'] = large_number
    
    # Shorthand aliases
    app.jinja_env.filters['nn'] = norwegian_number
    app.jinja_env.filters['pct'] = percentage
    app.jinja_env.filters['ln'] = large_number
