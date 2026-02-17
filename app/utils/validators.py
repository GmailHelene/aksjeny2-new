# Simple validators module
def validate_email(email):
    """Basic email validation"""
    return '@' in email and '.' in email.split('@')[1]

def validate_username(username):
    """Basic username validation"""
    return len(username) >= 3 and len(username) <= 20

def validate_password(password):
    """Basic password validation"""
    return len(password) >= 8

def validate_stock_symbol(symbol):
    """Basic stock symbol validation"""
    return symbol and len(symbol) <= 10 and symbol.replace('.', '').isalnum()

def validate_url(url):
    """Basic URL validation"""
    return url.startswith(('http://', 'https://'))
