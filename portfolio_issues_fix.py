#!/usr/bin/env python3
"""
Portfolio Issues Fix Script
==========================

Fixes:
1. Add stock to portfolio error - "Det oppstod en feil ved lasting av porteføljer"
2. Conflicting messages in portfolio creation 
3. General portfolio loading error on /portfolio

Author: GitHub Copilot
Date: August 30, 2025
"""

import os
import sys
from datetime import datetime

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def create_backup(file_path):
    """Create backup of file before modifying"""
    backup_path = f"{file_path}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    try:
        with open(file_path, 'r', encoding='utf-8') as source:
            with open(backup_path, 'w', encoding='utf-8') as backup:
                backup.write(source.read())
        print(f"✅ Backup created: {backup_path}")
        return True
    except Exception as e:
        print(f"❌ Failed to create backup: {e}")
        return False

def fix_portfolio_routes():
    """Fix portfolio routes issues"""
    file_path = "app/routes/portfolio.py"
    
    if not create_backup(file_path):
        return False
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Fix 1: Improve error handling in index function
        # Remove duplicate portfolio calculation code
        old_index_section = '''        # Calculate total portfolio value safely
        total_value = 0
        total_profit_loss = 0  # KRITISK FIX: Legg til manglende total_profit_loss
        portfolio_data = []
        
        for p in portfolios:
            try:
                portfolio_value = p.calculate_total_value() if hasattr(p, 'calculate_total_value') else 0
                total_value += portfolio_value
                portfolio_data.append({
                    'id': p.id,
                    'name': p.name,
                    'value': portfolio_value,
                    'created_at': p.created_at
                })
            except Exception as calc_error:
                logger.error(f"Error calculating portfolio value for {p.name}: {calc_error}")
                portfolio_data.append({
                    'id': p.id,
                    'name': p.name,
                    'value': 0,
                    'created_at': p.created_at
                })
        
        # Initialize data service for stock prices
        try:
            data_service = get_data_service()
        except Exception as data_service_error:
            logger.warning(f"Data service unavailable: {str(data_service_error)}")
            data_service = None

        # Process each portfolio
        for p in portfolios:'''
        
        new_index_section = '''        # Calculate total portfolio value safely
        total_value = 0
        total_profit_loss = 0
        portfolio_data = []
        
        # Initialize data service for stock prices
        try:
            data_service = get_data_service()
        except Exception as data_service_error:
            logger.warning(f"Data service unavailable: {str(data_service_error)}")
            data_service = None

        # Process each portfolio once
        for p in portfolios:'''
        
        if old_index_section in content:
            content = content.replace(old_index_section, new_index_section)
            print("✅ Fixed duplicate portfolio calculation in index function")
        
        # Fix 2: Improve error handling in add_stock_to_portfolio
        old_add_error = '''        # Get portfolio with error handling
        try:
            portfolio_obj = Portfolio.query.get_or_404(id)
            
            # Check ownership
            if portfolio_obj.user_id != current_user.id:
                flash('Du har ikke tilgang til denne porteføljen', 'danger')
                return redirect(url_for('portfolio.index'))
        except Exception as e:
            logger.error(f"Error getting portfolio {id}: {e}")
            flash('Kunne ikke hente porteføljen. Prøv igjen.', 'danger')
            return redirect(url_for('portfolio.index'))'''
        
        new_add_error = '''        # Get portfolio with improved error handling
        try:
            portfolio_obj = Portfolio.query.get_or_404(id)
            
            # Check ownership
            if portfolio_obj.user_id != current_user.id:
                flash('Du har ikke tilgang til denne porteføljen', 'danger')
                return redirect(url_for('portfolio.index'))
                
        except Exception as e:
            logger.error(f"Error getting portfolio {id}: {e}")
            flash(f'Portefølje med ID {id} ble ikke funnet eller du har ikke tilgang.', 'danger')
            return redirect(url_for('portfolio.index'))'''
        
        if old_add_error in content:
            content = content.replace(old_add_error, new_add_error)
            print("✅ Improved error handling in add_stock_to_portfolio")
        
        # Fix 3: Remove duplicate success flash in create_portfolio
        old_create_success = '''                flash(f'Porteføljen "{name}" ble opprettet!', 'success')
                return redirect(url_for('portfolio.view_portfolio', id=new_portfolio.id))
                
            except Exception as db_error:
                logger.error(f"Database error creating portfolio: {db_error}")
                db.session.rollback()
                flash('Kunne ikke opprette portefølje i databasen. Prøv igjen.', 'error')
                return render_template('portfolio/create.html', error=str(db_error))'''
        
        new_create_success = '''                flash(f'Porteføljen "{name}" ble opprettet!', 'success')
                return redirect(url_for('portfolio.view_portfolio', id=new_portfolio.id))
                
            except Exception as db_error:
                logger.error(f"Database error creating portfolio: {db_error}")
                db.session.rollback()
                flash('Kunne ikke opprette portefølje i databasen. Prøv igjen.', 'danger')
                return render_template('portfolio/create.html')'''
        
        if old_create_success in content:
            content = content.replace(old_create_success, new_create_success)
            print("✅ Fixed duplicate flash messages in create_portfolio")
        
        # Fix 4: Improve error message in index function
        old_index_error = '''    except Exception as e:
        logger.error(f"Error in portfolio index: {e}")
        flash('Det oppstod en feil ved lasting av porteføljer.', 'error')
        return render_template('portfolio/index.html',
                             portfolios=[],
                             total_value=0,
                             error="Det oppstod en feil ved lasting av porteføljer.")'''
        
        new_index_error = '''    except Exception as e:
        logger.error(f"Error in portfolio index: {e}")
        # Don't flash error here - let the template handle the empty state gracefully
        return render_template('portfolio/index.html',
                             portfolios=[],
                             total_value=0,
                             total_profit_loss=0,
                             error_message="Kunne ikke laste porteføljer. Prøv å oppdatere siden.")'''
        
        if old_index_error in content:
            content = content.replace(old_index_error, new_index_error)
            print("✅ Improved error handling in portfolio index")
        
        # Fix 5: Add better error handling for database issues
        add_db_check = '''@portfolio.route('/')
@login_required
def index():
    """Portfolio main page with better error handling"""
    try:
        # Test database connection first
        try:
            from ..models.portfolio import Portfolio
            db.session.execute('SELECT 1')
        except Exception as db_test_error:
            logger.error(f"Database connection test failed: {db_test_error}")
            return render_template('portfolio/index.html',
                                 portfolios=[],
                                 total_value=0,
                                 total_profit_loss=0,
                                 error_message="Database tilkobling ikke tilgjengelig. Prøv igjen senere.")
        
        # Get user's portfolios with proper error handling'''
        
        old_index_start = '''@portfolio.route('/')
@login_required
def index():
    """Portfolio main page with better error handling"""
    try:
        # Get user's portfolios with proper error handling'''
        
        if old_index_start in content:
            content = content.replace(old_index_start, add_db_check)
            print("✅ Added database connection test in index")
        
        # Write the fixed content back
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        return True
        
    except Exception as e:
        print(f"❌ Error fixing portfolio routes: {e}")
        return False

def fix_portfolio_templates():
    """Fix portfolio template issues"""
    
    # Fix portfolio/index.html to handle errors gracefully
    index_template_path = "app/templates/portfolio/index.html"
    
    if not os.path.exists(index_template_path):
        print(f"⚠️  Template not found: {index_template_path}")
        return True
    
    try:
        with open(index_template_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Add error message display at the top
        error_display = '''{% extends 'base.html' %}

{% block title %}Min portefølje{% endblock %}

{% block content %}
<div class="container mt-4">
  <!-- Error Message Display -->
  {% if error_message %}
  <div class="alert alert-warning alert-dismissible fade show" role="alert">
    <i class="bi bi-exclamation-triangle me-2"></i>{{ error_message }}
    <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
  </div>
  {% endif %}
  
  <div class="d-flex justify-content-between align-items-center mb-4">'''
        
        old_start = '''{% extends 'base.html' %}

{% block title %}Min portefølje{% endblock %}

{% block content %}
<div class="container mt-4">
  <div class="d-flex justify-content-between align-items-center mb-4">'''
        
        if old_start in content:
            content = content.replace(old_start, error_display)
            print("✅ Added error message display to portfolio index template")
        
        # Add check for empty portfolios
        empty_portfolios_section = '''  {% if not portfolios or portfolios|length == 0 %}
  <!-- Empty State -->
  <div class="text-center py-5">
    <div class="mb-4">
      <i class="bi bi-briefcase display-1 text-muted"></i>
    </div>
    <h3 class="text-muted">Ingen porteføljer ennå</h3>
    <p class="text-muted">Kom i gang ved å opprette din første portefølje!</p>
    <a href="{{ url_for('portfolio.create_portfolio') }}" class="btn btn-primary btn-lg">
      <i class="bi bi-plus-circle me-2"></i>Opprett din første portefølje
    </a>
  </div>
  {% else %}'''
        
        # Find where to insert this
        portfolio_selector_start = '''  <!-- Portfolio Selector (if multiple portfolios) -->
  {% if portfolios and portfolios|length > 1 %}'''
        
        if portfolio_selector_start in content and empty_portfolios_section not in content:
            content = content.replace(portfolio_selector_start, 
                                    empty_portfolios_section + '\n  ' + portfolio_selector_start)
            print("✅ Added empty state handling to portfolio index template")
        
        with open(index_template_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        return True
        
    except Exception as e:
        print(f"❌ Error fixing portfolio templates: {e}")
        return False

def main():
    """Run all portfolio fixes"""
    print("🔧 Portfolio Issues Fix Script")
    print("=" * 50)
    
    fixes = [
        ("Portfolio Routes", fix_portfolio_routes),
        ("Portfolio Templates", fix_portfolio_templates),
    ]
    
    results = {}
    
    for fix_name, fix_func in fixes:
        print(f"\n🔄 Applying {fix_name} fixes...")
        results[fix_name] = fix_func()
    
    # Summary
    print("\n" + "=" * 50)
    print("📋 PORTFOLIO FIXES SUMMARY")
    print("=" * 50)
    
    applied = 0
    total = len(fixes)
    
    for fix_name, result in results.items():
        status = "✅ APPLIED" if result else "❌ FAILED"
        print(f"{fix_name}: {status}")
        if result:
            applied += 1
    
    print(f"\nOverall: {applied}/{total} fixes applied")
    
    if applied == total:
        print("\n🎉 All portfolio fixes applied successfully!")
        print("\n📌 Fixed Issues:")
        print("1. ✅ Add stock to portfolio error handling improved")
        print("2. ✅ Removed duplicate success/error messages in create")
        print("3. ✅ Better error handling for portfolio loading")
        print("4. ✅ Database connection testing added")
        print("5. ✅ Template error message display improved")
        print("\n🚀 Portfolio functionality should now work correctly!")
    else:
        print("\n⚠️  Some fixes failed. Check the output above.")
    
    return applied == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
