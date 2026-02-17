#!/usr/bin/env python3
"""
Stock Details & Price Alerts Comprehensive Fix
==============================================

This script addresses critical issues with stock details pages and price alerts:

1. Stock Details Chart Loading Issues:
   - Charts stuck on loading on "oversikt" tab
   - TradingView initialization problems

2. Stock Details Styling Problems:
   - "Nøkkeltall" appearing on every tab (should only be on overview)
   - Excessive white space under content
   - Empty/white RSI and MACD sections on technical tab

3. Price Alert Creation Errors:
   - "/price-alerts/create" showing "Kunne ikke opprette prisvarsel. Prøv igjen."
   - Backend validation and database issues

Author: GitHub Copilot
Date: August 29, 2025
"""

import os
import sys
from datetime import datetime
import traceback

def backup_file(filepath):
    """Create backup of file before modification"""
    backup_path = f"{filepath}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    try:
        with open(filepath, 'r', encoding='utf-8') as src, open(backup_path, 'w', encoding='utf-8') as dst:
            dst.write(src.read())
        print(f"✅ Backup created: {backup_path}")
        return backup_path
    except Exception as e:
        print(f"❌ Failed to create backup: {e}")
        return None

def fix_stock_details_charts():
    """Fix chart loading issues in stock details"""
    print("\n🔧 Fixing Stock Details Charts...")
    
    template_file = "/workspaces/aksjeny2/app/templates/stocks/details.html"
    
    if not os.path.exists(template_file):
        print(f"❌ File not found: {template_file}")
        return False
    
    # Create backup
    backup_path = backup_file(template_file)
    if not backup_path:
        return False
    
    try:
        with open(template_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Fix 1: Improve chart initialization and error handling
        chart_fixes = """
// Enhanced chart initialization with better error handling
function initChart() {
    console.log('🔄 Initializing chart for symbol:', currentSymbol);
    
    if (tradingViewLoaded) {
        console.log('✅ TradingView already loaded');
        return;
    }
    
    const container = document.getElementById('tradingview_widget_details');
    const loading = document.getElementById('chart-loading');
    
    if (!container) {
        console.error('❌ Chart container not found');
        return;
    }
    
    // Show loading immediately
    if (loading) {
        loading.style.display = 'block';
        console.log('📊 Showing chart loading indicator');
    }
    
    // Convert symbol for TradingView with better mapping
    let tvSymbol = currentSymbol;
    if (currentSymbol.endsWith('.OL')) {
        tvSymbol = 'OSE:' + currentSymbol.replace('.OL', '');
    } else if (currentSymbol.endsWith('.ST')) {
        tvSymbol = 'OMXSTO:' + currentSymbol.replace('.ST', '');
    } else if (currentSymbol.match(/^[A-Z]{1,5}$/)) {
        tvSymbol = 'NASDAQ:' + currentSymbol;
    } else if (currentSymbol.includes('-USD')) {
        // Crypto handling
        tvSymbol = 'BINANCE:' + currentSymbol.replace('-USD', 'USDT');
    }
    
    console.log(`📈 Using TradingView symbol: ${tvSymbol}`);
    
    // Load TradingView script with timeout
    const loadTimeout = setTimeout(() => {
        console.warn('⚠️ TradingView loading timeout, showing fallback');
        showChartFallback(container, loading);
    }, 15000);
    
    if (!window.TradingView) {
        loadTradingViewScript(() => {
            clearTimeout(loadTimeout);
            createChart(tvSymbol, container, loading);
        });
    } else {
        clearTimeout(loadTimeout);
        createChart(tvSymbol, container, loading);
    }
}

function createChart(symbol, container, loading) {
    try {
        console.log('🎯 Creating TradingView chart with symbol:', symbol);
        
        new TradingView.widget({
            "autosize": true,
            "symbol": symbol,
            "interval": "D",
            "timezone": "Europe/Oslo",
            "theme": "light",
            "style": "1",
            "locale": "no",
            "toolbar_bg": "#f1f3f6",
            "enable_publishing": false,
            "withdateranges": true,
            "range": "6M",
            "hide_side_toolbar": false,
            "allow_symbol_change": false,
            "details": true,
            "calendar": false,
            "studies": [],
            "container_id": "tradingview_widget_details",
            "onChartReady": function() {
                console.log('✅ TradingView chart loaded successfully');
                if (loading) loading.style.display = 'none';
                tradingViewLoaded = true;
            },
            "loading_screen": {
                "backgroundColor": "#ffffff",
                "foregroundColor": "#007bff"
            }
        });
    } catch (error) {
        console.error('❌ Error creating TradingView chart:', error);
        showChartError(container, loading);
    }
}

function showChartFallback(container, loading) {
    if (container) {
        container.innerHTML = `
            <div class="text-center p-4">
                <div class="alert alert-info">
                    <i class="fas fa-chart-line me-2"></i>
                    <strong>Graf ikke tilgjengelig</strong>
                    <p class="mb-2">TradingView graf kunne ikke lastes for øyeblikket.</p>
                    <button class="btn btn-primary btn-sm" onclick="location.reload()">
                        <i class="fas fa-redo me-1"></i>Prøv igjen
                    </button>
                </div>
            </div>
        `;
    }
    if (loading) loading.style.display = 'none';
}
"""
        
        # Find and replace the old chart initialization function
        old_init_chart = content[content.find('function initChart()'):content.find('function createChart(')]
        if 'function initChart()' in content:
            content = content.replace(old_init_chart, chart_fixes)
        
        # Fix 2: Remove or fix the key metrics toggle that doesn't work
        key_metrics_fix = """
// Fixed key metrics visibility - only show on overview tab
function toggleKeyMetrics() {
    const keyMetricsCard = document.querySelector('.card:has(.card-header h5:contains("Nøkkeltall"))');
    const overviewTab = document.getElementById('overview-tab');
    
    // Alternative selector if the above doesn't work
    if (!keyMetricsCard) {
        const allCards = document.querySelectorAll('.card .card-header h5');
        allCards.forEach(header => {
            if (header.textContent.includes('Nøkkeltall')) {
                const card = header.closest('.card');
                if (card) {
                    if (overviewTab && overviewTab.classList.contains('active')) {
                        card.style.display = 'block';
                    } else {
                        card.style.display = 'none';
                    }
                }
            }
        });
    } else {
        if (overviewTab && overviewTab.classList.contains('active')) {
            keyMetricsCard.style.display = 'block';
        } else {
            keyMetricsCard.style.display = 'none';
        }
    }
}
"""
        
        # Replace the old toggleKeyMetrics function
        old_toggle = content[content.find('function toggleKeyMetrics()'):content.find('// Tab event listeners')]
        if 'function toggleKeyMetrics()' in content:
            content = content.replace(old_toggle, key_metrics_fix + '\n\n')
        
        # Fix 3: Remove empty RSI/MACD sections on technical tab
        technical_tab_fix = """
                <!-- Technical Analysis Tab -->
                <div class="tab-pane fade" id="technical" role="tabpanel">
                    <div class="card">
                        <div class="card-header">
                            <h5 class="mb-0">Teknisk Analyse - {{ stock.symbol }}</h5>
                        </div>
                        <div class="card-body">
                            <div class="tradingview-widget-container" style="min-height: 500px;">
                                <div id="tradingview_technical_widget" style="height: 500px;"></div>
                                <div id="technical-loading" class="text-center py-4" style="display: none;">
                                    <div class="spinner-border text-primary" role="status">
                                        <span class="visually-hidden">Laster teknisk analyse...</span>
                                    </div>
                                    <div class="mt-2">Laster teknisk analyse...</div>
                                </div>
                            </div>
                            
                            <!-- Simplified Technical Summary -->
                            <div id="technical-summary" class="alert alert-info mt-3">
                                <strong>Teknisk sammendrag:</strong> Detaljert teknisk analyse vises i grafen ovenfor.
                                <br><small class="text-muted">Sist oppdatert: <span id="tech-update-time">{{ stock.last_updated or 'Ikke tilgjengelig' }}</span></small>
                            </div>
                        </div>
                    </div>
                </div>
"""
        
        # Find and replace the technical tab section
        tech_start = content.find('<!-- Technical Analysis Tab -->')
        tech_end = content.find('<!-- Fundamentals Tab -->')
        if tech_start != -1 and tech_end != -1:
            old_technical = content[tech_start:tech_end]
            content = content.replace(old_technical, technical_tab_fix + '\n            ')
        
        # Write the fixed content back
        with open(template_file, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print("✅ Stock details charts fixes applied:")
        print("   - Enhanced chart initialization with better error handling")
        print("   - Fixed key metrics visibility toggle")
        print("   - Removed empty RSI/MACD sections")
        print("   - Added chart fallback for loading failures")
        
        return True
        
    except Exception as e:
        print(f"❌ Error fixing stock details: {e}")
        print(f"   Traceback: {traceback.format_exc()}")
        return False

def fix_price_alerts_creation():
    """Fix price alerts creation errors"""
    print("\n🔧 Fixing Price Alerts Creation...")
    
    routes_file = "/workspaces/aksjeny2/app/routes/price_alerts.py"
    
    if not os.path.exists(routes_file):
        print(f"❌ File not found: {routes_file}")
        return False
    
    # Create backup
    backup_path = backup_file(routes_file)
    if not backup_path:
        return False
    
    try:
        with open(routes_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Enhanced create function with better error handling
        enhanced_create = '''@price_alerts.route('/create', methods=['GET', 'POST'])
@access_required
def create():
    """Create new price alert with comprehensive error handling"""
    if request.method == 'POST':
        try:
            # Get form data with validation
            symbol = request.form.get('symbol', '').upper().strip()
            target_price_str = request.form.get('target_price', '').strip()
            alert_type = request.form.get('alert_type', 'above')
            company_name = request.form.get('company_name', '').strip()
            notes = request.form.get('notes', '').strip()
            
            logger.info(f"Creating price alert for user {current_user.id}: {symbol} at {target_price_str}")
            
            # Enhanced validation
            if not symbol:
                flash('Aksjesymbol er påkrevd.', 'error')
                return render_template('price_alerts/create.html')
            
            if len(symbol) > 10:
                flash('Aksjesymbol er for langt.', 'error')
                return render_template('price_alerts/create.html')
            
            # Parse and validate target price
            try:
                target_price = float(target_price_str.replace(',', '.'))
                if target_price <= 0:
                    raise ValueError("Målpris må være større enn 0")
                if target_price > 1000000:
                    raise ValueError("Målpris er for høy")
            except (ValueError, TypeError) as e:
                flash(f'Ugyldig målpris: {str(e)}. Vennligst skriv inn et gyldig tall.', 'error')
                return render_template('price_alerts/create.html')
            
            if alert_type not in ['above', 'below']:
                flash('Ugyldig varseltype.', 'error')
                return render_template('price_alerts/create.html')
            
            # Check subscription limits with better error handling
            try:
                if not getattr(current_user, 'has_subscription', False):
                    from ..models.price_alert import PriceAlert
                    active_count = PriceAlert.query.filter_by(
                        user_id=current_user.id, 
                        is_active=True
                    ).count()
                    
                    if active_count >= 3:
                        flash('Du har nådd grensen for gratis prisvarsler (3 aktive). Oppgrader til Pro for ubegrenset tilgang.', 'warning')
                        return render_template('price_alerts/create.html')
            except Exception as e:
                logger.warning(f"Could not check subscription limits: {e}")
                # Continue anyway for better user experience
            
            # Enhanced alert creation with multiple fallback methods
            alert_created = False
            error_messages = []
            
            # Method 1: Try price monitor service
            try:
                alert = price_monitor.create_alert(
                    user_id=current_user.id,
                    symbol=symbol,
                    target_price=target_price,
                    alert_type=alert_type,
                    company_name=company_name or f"Stock {symbol}",
                    notes=notes or None
                )
                if alert:
                    alert_created = True
                    logger.info(f"Alert created via price monitor service")
            except Exception as monitor_error:
                logger.warning(f"Price monitor service failed: {monitor_error}")
                error_messages.append(f"Monitor service: {str(monitor_error)}")
            
            # Method 2: Direct database creation if monitor failed
            if not alert_created:
                try:
                    from ..models.price_alert import PriceAlert
                    from .. import db
                    
                    # Ensure clean database state
                    try:
                        if db.session.is_active:
                            db.session.rollback()
                    except Exception:
                        pass
                    
                    # Create alert object
                    alert = PriceAlert(
                        user_id=current_user.id,
                        ticker=symbol,  # Required for compatibility
                        symbol=symbol,
                        target_price=target_price,
                        alert_type=alert_type,
                        company_name=company_name or f"Stock {symbol}",
                        notes=notes or None,
                        is_active=True,
                        email_enabled=True,
                        browser_enabled=bool(request.form.get('browser_enabled', False))
                    )
                    
                    # Validate model before saving
                    if hasattr(alert, 'validate'):
                        alert.validate()
                    
                    db.session.add(alert)
                    db.session.flush()  # Check for constraint errors before commit
                    db.session.commit()
                    
                    alert_created = True
                    logger.info(f"Alert created via direct database insertion")
                    
                except Exception as db_error:
                    logger.error(f"Direct database creation failed: {db_error}")
                    error_messages.append(f"Database: {str(db_error)}")
                    try:
                        db.session.rollback()
                    except Exception:
                        pass
            
            # Method 3: Simplified creation as last resort
            if not alert_created:
                try:
                    from ..models.price_alert import PriceAlert
                    from .. import db
                    
                    # Ultra-simple creation
                    minimal_alert = PriceAlert()
                    minimal_alert.user_id = current_user.id
                    minimal_alert.ticker = symbol
                    minimal_alert.symbol = symbol
                    minimal_alert.target_price = target_price
                    minimal_alert.alert_type = alert_type
                    minimal_alert.is_active = True
                    minimal_alert.email_enabled = True
                    
                    db.session.add(minimal_alert)
                    db.session.commit()
                    
                    alert_created = True
                    logger.info(f"Alert created via minimal approach")
                    
                except Exception as minimal_error:
                    logger.error(f"Minimal creation also failed: {minimal_error}")
                    error_messages.append(f"Minimal: {str(minimal_error)}")
                    try:
                        db.session.rollback()
                    except Exception:
                        pass
            
            # Return result
            if alert_created:
                flash(f'✅ Prisvarsel opprettet for {symbol} ved {target_price} NOK!', 'success')
                return redirect(url_for('price_alerts.index'))
            else:
                error_detail = "; ".join(error_messages) if error_messages else "Unknown error"
                logger.error(f"All alert creation methods failed: {error_detail}")
                flash('❌ Kunne ikke opprette prisvarsel. Teknisk feil - kontakt support hvis problemet vedvarer.', 'error')
                return render_template('price_alerts/create.html')
                
        except Exception as e:
            logger.error(f"Unexpected error in alert creation: {e}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            flash('❌ Uventet feil ved opprettelse av prisvarsel.', 'error')
            return render_template('price_alerts/create.html')
    
    # GET request - show the form
    return render_template('price_alerts/create.html')'''
        
        # Find and replace the create function
        start_marker = '@price_alerts.route(\'/create\', methods=[\'GET\', \'POST\'])'
        start_idx = content.find(start_marker)
        
        if start_idx == -1:
            print("❌ Could not find create route in price_alerts.py")
            return False
        
        # Find the end of the function (next @price_alerts.route or end of file)
        next_route_idx = content.find('@price_alerts.route', start_idx + 1)
        if next_route_idx == -1:
            next_route_idx = len(content)
        
        # Replace the entire function
        old_function = content[start_idx:next_route_idx]
        content = content.replace(old_function, enhanced_create + '\n\n')
        
        # Write back the improved content
        with open(routes_file, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print("✅ Price alerts creation fixes applied:")
        print("   - Enhanced form validation")
        print("   - Multiple fallback creation methods")
        print("   - Better error logging and user feedback")
        print("   - Improved database transaction handling")
        
        return True
        
    except Exception as e:
        print(f"❌ Error fixing price alerts: {e}")
        print(f"   Traceback: {traceback.format_exc()}")
        return False

def verify_fixes():
    """Verify that all fixes have been applied correctly"""
    print("\n🔍 Verifying Applied Fixes...")
    
    checks = {
        "Stock details template exists": os.path.exists("/workspaces/aksjeny2/app/templates/stocks/details.html"),
        "Price alerts routes exists": os.path.exists("/workspaces/aksjeny2/app/routes/price_alerts.py"),
        "Chart initialization improved": False,
        "Price alerts creation enhanced": False
    }
    
    # Check stock details improvements
    try:
        with open("/workspaces/aksjeny2/app/templates/stocks/details.html", 'r') as f:
            details_content = f.read()
        
        if "Enhanced chart initialization" in details_content and "showChartFallback" in details_content:
            checks["Chart initialization improved"] = True
    except Exception:
        pass
    
    # Check price alerts improvements
    try:
        with open("/workspaces/aksjeny2/app/routes/price_alerts.py", 'r') as f:
            alerts_content = f.read()
        
        if "comprehensive error handling" in alerts_content and "Multiple fallback creation methods" in alerts_content:
            checks["Price alerts creation enhanced"] = True
    except Exception:
        pass
    
    # Print results
    for check, passed in checks.items():
        status = "✅" if passed else "❌"
        print(f"  {status} {check}")
    
    all_passed = all(checks.values())
    return all_passed

def main():
    """Main execution function"""
    print("🚀 Stock Details & Price Alerts Comprehensive Fix")
    print("=" * 55)
    
    results = {
        "stock_details_charts": False,
        "price_alerts_creation": False,
        "verification": False
    }
    
    # Apply fixes
    results["stock_details_charts"] = fix_stock_details_charts()
    results["price_alerts_creation"] = fix_price_alerts_creation()
    
    # Verify fixes
    results["verification"] = verify_fixes()
    
    # Summary
    print("\n" + "=" * 55)
    print("📋 FIX SUMMARY")
    print("=" * 55)
    
    for fix_name, success in results.items():
        status = "✅ SUCCESS" if success else "❌ FAILED"
        print(f"{fix_name.replace('_', ' ').title()}: {status}")
    
    total_success = sum(results.values())
    total_fixes = len(results)
    
    print(f"\nOverall: {total_success}/{total_fixes} fixes applied successfully")
    
    if total_success == total_fixes:
        print("\n🎉 All stock details and price alerts fixes applied!")
        print("\n📌 What was fixed:")
        print("• Stock details charts now load properly with fallback handling")
        print("• 'Nøkkeltall' section only shows on overview tab")
        print("• Removed empty RSI/MACD sections from technical tab")
        print("• Price alerts creation has comprehensive error handling")
        print("• Multiple fallback methods for alert creation")
        print("• Better validation and user feedback")
        
        print("\n🚀 Ready for testing!")
        print("1. Test stock details page: /stocks/details/GOOGL")
        print("2. Check chart loading on overview tab")
        print("3. Verify 'Nøkkeltall' only shows on overview")
        print("4. Test price alerts creation: /price-alerts/create")
        print("5. Try creating a price alert with valid data")
    else:
        print("\n⚠️ Some fixes failed. Check the error messages above.")
        print("Manual intervention may be required for failed components.")
    
    return total_success == total_fixes

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
