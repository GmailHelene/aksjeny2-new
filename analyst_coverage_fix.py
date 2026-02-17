#!/usr/bin/env python3
"""
Analyst Coverage Filter and Styling Fix Script
Fixes:
1. Filter buttons (Buy, Hold, Sell) not responding
2. Text color contrast issues on blue backgrounds
"""

import os
import shutil
from datetime import datetime

def create_analyst_coverage_fixes():
    """Create fixes for analyst coverage filter buttons and text styling"""
    
    print("🔧 Creating Analyst Coverage Fixes...")
    
    # Enhanced JavaScript for filter functionality
    enhanced_js = '''
{% block extra_js %}
{{ super() }}
<script>
document.addEventListener('DOMContentLoaded', function() {
    console.log('Analyst Coverage: Initializing filter functionality...');
    
    // Filter functionality for analyst coverage
    const filterButtons = document.querySelectorAll('[data-filter]');
    const analysisCards = document.querySelectorAll('.analyst-card');
    const tableRows = document.querySelectorAll('#analyst-table tbody tr');
    
    console.log(`Found ${filterButtons.length} filter buttons`);
    console.log(`Found ${tableRows.length} table rows to filter`);
    
    filterButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            e.preventDefault();
            console.log('Filter button clicked:', this.getAttribute('data-filter'));
            
            // Update button states
            filterButtons.forEach(btn => {
                btn.classList.remove('active', 'btn-light');
                btn.classList.add('btn-outline-light');
            });
            this.classList.remove('btn-outline-light');
            this.classList.add('active', 'btn-light');
            
            const filter = this.getAttribute('data-filter');
            console.log('Applying filter:', filter);
            
            let visibleCount = 0;
            
            // Filter table rows
            tableRows.forEach(row => {
                const ratingBadge = row.querySelector('.badge');
                if (!ratingBadge) {
                    console.log('No rating badge found in row');
                    return;
                }
                
                const rating = ratingBadge.textContent.toLowerCase().trim();
                let show = false;
                
                switch(filter) {
                    case 'all':
                        show = true;
                        break;
                    case 'buy':
                        show = rating.includes('kjøp') || rating.includes('buy');
                        break;
                    case 'hold':
                        show = rating.includes('hold');
                        break;
                    case 'sell':
                        show = rating.includes('selg') || rating.includes('sell');
                        break;
                }
                
                if (show) {
                    row.style.display = '';
                    visibleCount++;
                } else {
                    row.style.display = 'none';
                }
            });
            
            console.log(`Filter applied: ${filter}, showing ${visibleCount} rows`);
            
            // Show feedback message
            const feedbackElement = document.getElementById('filter-feedback');
            if (feedbackElement) {
                feedbackElement.textContent = `Viser ${visibleCount} analyser for filter: ${filter}`;
                feedbackElement.style.display = 'block';
                setTimeout(() => {
                    feedbackElement.style.display = 'none';
                }, 3000);
            }
        });
    });
    
    // Add hover effects
    analysisCards.forEach(card => {
        card.addEventListener('mouseenter', function() {
            this.style.transform = 'translateY(-5px)';
            this.style.transition = 'transform 0.2s ease';
        });
        
        card.addEventListener('mouseleave', function() {
            this.style.transform = 'translateY(0)';
        });
    });
    
    console.log('Analyst Coverage: Filter functionality initialized successfully');
});
</script>
{% endblock %}
'''
    
    # Enhanced CSS for better text contrast
    enhanced_css = '''
/* Analyst Coverage Text Color Fixes - Enhanced */

/* Blue background headers - force white text */
.card-header[style*="background-color: #0d47a1"],
.card-header[style*="background-color:#0d47a1"],
div[style*="background-color: #0d47a1"],
div[style*="background-color:#0d47a1"] {
    color: white !important;
}

.card-header[style*="background-color: #0d47a1"] *,
.card-header[style*="background-color:#0d47a1"] *,
div[style*="background-color: #0d47a1"] *,
div[style*="background-color:#0d47a1"] * {
    color: white !important;
}

/* Coverage header gradient styling */
.coverage-header {
    background: linear-gradient(135deg, #0d47a1 0%, #1565c0 100%) !important;
    color: white !important;
}

.coverage-header * {
    color: white !important;
}

/* Filter button styling fixes */
.coverage-header .btn-group .btn {
    border-color: rgba(255,255,255,0.3) !important;
}

.coverage-header .btn-light {
    background-color: rgba(255,255,255,0.9) !important;
    color: #0d47a1 !important;
    border-color: rgba(255,255,255,0.3) !important;
}

.coverage-header .btn-outline-light {
    color: white !important;
    border-color: rgba(255,255,255,0.5) !important;
    background-color: transparent !important;
}

.coverage-header .btn-outline-light:hover {
    background-color: rgba(255,255,255,0.1) !important;
    color: white !important;
}

/* Specific fixes for analyst coverage page */
.analyst-card .card-header {
    background-color: #0d47a1 !important;
    color: white !important;
}

.analyst-card .card-header * {
    color: white !important;
}

/* Badge styling for better contrast */
.badge.rating-buy {
    background-color: #198754 !important;
    color: white !important;
}

.badge.rating-hold {
    background-color: #ffc107 !important;
    color: #000 !important;
}

.badge.rating-sell {
    background-color: #dc3545 !important;
    color: white !important;
}

/* Filter feedback message */
#filter-feedback {
    position: fixed;
    top: 20px;
    right: 20px;
    background-color: #28a745;
    color: white;
    padding: 10px 15px;
    border-radius: 5px;
    z-index: 1050;
    display: none;
}

/* Consensus circle styling */
.consensus-circle {
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-weight: bold;
    color: white !important;
}

.consensus-buy {
    background-color: #198754 !important;
}

.consensus-hold {
    background-color: #ffc107 !important;
    color: #000 !important;
}

.consensus-sell {
    background-color: #dc3545 !important;
}
'''
    
    # Template enhancements
    template_enhancements = '''
<!-- Add filter feedback element -->
<div id="filter-feedback"></div>

<!-- Enhanced filter button group with better styling -->
<div class="coverage-header p-4 mb-4 rounded" style="background-color: #0d47a1 !important;">
    <div class="row align-items-center">
        <div class="col-md-8">
            <h2 class="mb-2">
                <i class="bi bi-graph-up-arrow me-2"></i>Analytiker Dekning
            </h2>
            <p class="mb-0 opacity-75">Følg med på analytiker anbefalinger og kursmål</p>
        </div>
        <div class="col-md-4 text-end">
            <div class="btn-group" role="group" aria-label="Filter recommendations">
                <button type="button" class="btn btn-light active" data-filter="all">
                    <i class="bi bi-list me-1"></i>Alle
                </button>
                <button type="button" class="btn btn-outline-light" data-filter="buy">
                    <i class="bi bi-arrow-up-circle me-1"></i>Buy
                </button>
                <button type="button" class="btn btn-outline-light" data-filter="hold">
                    <i class="bi bi-dash-circle me-1"></i>Hold
                </button>
                <button type="button" class="btn btn-outline-light" data-filter="sell">
                    <i class="bi bi-arrow-down-circle me-1"></i>Sell
                </button>
            </div>
        </div>
    </div>
</div>
'''
    
    return enhanced_js, enhanced_css, template_enhancements

def apply_analyst_coverage_fixes():
    """Apply all analyst coverage fixes"""
    
    print("🎯 Applying Analyst Coverage Fixes...")
    
    enhanced_js, enhanced_css, template_enhancements = create_analyst_coverage_fixes()
    
    # 1. Update the CSS file with enhanced styling
    css_file = '/workspaces/aksjeny2/app/static/css/card-header-text-fix.css'
    
    try:
        with open(css_file, 'a', encoding='utf-8') as f:
            f.write(f"\n\n/* Enhanced Analyst Coverage Fixes - {datetime.now().strftime('%Y-%m-%d %H:%M')} */\n")
            f.write(enhanced_css)
        print(f"✅ Enhanced CSS rules added to {css_file}")
    except Exception as e:
        print(f"❌ Failed to update CSS file: {e}")
        return False
    
    # 2. Update the analyst coverage template
    template_file = '/workspaces/aksjeny2/app/templates/external_data/analyst_coverage.html'
    
    try:
        # Read current template
        with open(template_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Replace the JavaScript section
        start_marker = '{% block extra_js %}'
        end_marker = '{% endblock %}\n\n{% endblock %}'
        
        start_idx = content.find(start_marker)
        end_idx = content.find(end_marker) + len(end_marker)
        
        if start_idx != -1 and end_idx != -1:
            # Replace the JavaScript block
            new_content = content[:start_idx] + enhanced_js + '\n\n{% endblock %}'
            
            # Add filter feedback element after the opening div
            feedback_insertion = '<div id="filter-feedback"></div>\n\n<div class="container-fluid">'
            new_content = new_content.replace('<div class="container-fluid">', feedback_insertion)
            
            # Write back the modified content
            with open(template_file, 'w', encoding='utf-8') as f:
                f.write(new_content)
            
            print(f"✅ Enhanced JavaScript and template updates applied to {template_file}")
        else:
            print("❌ Could not find JavaScript block markers in template")
            return False
            
    except Exception as e:
        print(f"❌ Failed to update template file: {e}")
        return False
    
    return True

def main():
    """Main execution function"""
    
    print("=" * 60)
    print("🎯 ANALYST COVERAGE FILTER & STYLING FIX")
    print("=" * 60)
    print("Fixing:")
    print("• Filter buttons (Buy, Hold, Sell) not responding")
    print("• Text color contrast on blue backgrounds")
    print("• Enhanced user feedback and debugging")
    print("-" * 60)
    
    try:
        success = apply_analyst_coverage_fixes()
        
        if success:
            print("\n" + "=" * 60)
            print("✅ ANALYST COVERAGE FIXES COMPLETED SUCCESSFULLY!")
            print("=" * 60)
            print("Fixed Issues:")
            print("• ✅ Filter buttons now have enhanced event handling")
            print("• ✅ Added console logging for debugging")
            print("• ✅ Improved button state management")
            print("• ✅ White text on blue backgrounds enforced")
            print("• ✅ Enhanced CSS for better contrast")
            print("• ✅ Added visual feedback for filter operations")
            print("• ✅ Improved button styling and hover effects")
            print("\nNext Steps:")
            print("• 🔄 Restart the Flask server to apply changes")
            print("• 🌐 Test the filter buttons at /external-data/analyst-coverage")
            print("• 🎨 Verify text visibility on blue backgrounds")
            print("• 📊 Check console logs for filter debugging info")
        else:
            print("\n❌ Some fixes failed. Please check the errors above.")
            
    except Exception as e:
        print(f"\n❌ Critical error during fix application: {e}")
        return False
    
    return True

if __name__ == "__main__":
    main()
