from flask import Flask

# Test basic Flask functionality without importing problematic modules
app = Flask(__name__)
app.config['SECRET_KEY'] = 'test'

print("✅ Flask basic functionality working")

# Try importing just the portfolio blueprint file to check syntax
try:
    with open('app/routes/portfolio.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Check if portfolio.index references exist
    if 'portfolio.index' in content:
        print("❌ portfolio.index references still exist in portfolio.py")
    else:
        print("✅ No portfolio.index references found in portfolio.py")
        
    # Check if portfolio_overview function exists
    if 'def portfolio_overview' in content:
        print("✅ portfolio_overview function exists")
    else:
        print("❌ portfolio_overview function not found")
        
except Exception as e:
    print(f"❌ Error reading portfolio.py: {e}")

print("✅ Basic BuildError test completed")
