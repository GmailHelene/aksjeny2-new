
// Enhanced Analyst Coverage Filter System
document.addEventListener('DOMContentLoaded', function() {
    console.log('🎯 Analyst Coverage Filter System initializing...');
    
    // Find all filter elements
    const filterButtons = document.querySelectorAll('[data-filter]');
    const tableRows = document.querySelectorAll('#analyst-table tbody tr');
    const analysisCards = document.querySelectorAll('.analyst-card');
    
    console.log(`Found ${filterButtons.length} filter buttons`);
    console.log(`Found ${tableRows.length} table rows`);
    console.log(`Found ${analysisCards.length} analysis cards`);
    
    if (filterButtons.length === 0) {
        console.warn('⚠️  No filter buttons found!');
        return;
    }
    
    // Enhanced filter functionality
    filterButtons.forEach((button, index) => {
        console.log(`🔧 Setting up filter button ${index}: ${button.textContent}`);
        
        button.addEventListener('click', function(e) {
            e.preventDefault();
            console.log(`🎯 Filter clicked: ${this.getAttribute('data-filter')}`);
            
            // Visual feedback
            this.style.transform = 'scale(0.95)';
            setTimeout(() => {
                this.style.transform = 'scale(1)';
            }, 100);
            
            // Update button states with animation
            filterButtons.forEach(btn => {
                btn.classList.remove('active', 'btn-light');
                btn.classList.add('btn-outline-light');
                btn.style.transition = 'all 0.3s ease';
            });
            
            this.classList.remove('btn-outline-light');
            this.classList.add('active', 'btn-light');
            
            const filter = this.getAttribute('data-filter');
            let visibleCount = 0;
            
            // Enhanced filtering logic
            tableRows.forEach(row => {
                const ratingCell = row.querySelector('td:nth-child(4)'); // Rating column
                const ratingBadge = row.querySelector('.badge') || ratingCell;
                
                if (!ratingBadge) {
                    console.warn('No rating badge found in row');
                    return;
                }
                
                const rating = ratingBadge.textContent.toLowerCase().trim();
                let shouldShow = false;
                
                switch(filter) {
                    case 'all':
                        shouldShow = true;
                        break;
                    case 'buy':
                        shouldShow = rating.includes('kjøp') || 
                                   rating.includes('buy') || 
                                   rating.includes('strong buy') ||
                                   rating.includes('outperform');
                        break;
                    case 'hold':
                        shouldShow = rating.includes('hold') || 
                                   rating.includes('neutral') ||
                                   rating.includes('market perform');
                        break;
                    case 'sell':
                        shouldShow = rating.includes('selg') || 
                                   rating.includes('sell') ||
                                   rating.includes('underperform');
                        break;
                }
                
                // Smooth show/hide animation
                if (shouldShow) {
                    row.style.display = '';
                    row.style.opacity = '0';
                    row.style.transition = 'opacity 0.3s ease-in-out';
                    setTimeout(() => {
                        row.style.opacity = '1';
                    }, 50);
                    visibleCount++;
                } else {
                    row.style.transition = 'opacity 0.3s ease-in-out';
                    row.style.opacity = '0';
                    setTimeout(() => {
                        row.style.display = 'none';
                    }, 300);
                }
            });
            
            // Show feedback message
            console.log(`📊 Filter "${filter}" applied: ${visibleCount} rows visible`);
            
            // Add temporary feedback notification
            const notification = document.createElement('div');
            notification.className = 'alert alert-info alert-dismissible fade show position-fixed';
            notification.style.cssText = 'top: 20px; right: 20px; z-index: 9999; min-width: 300px;';
            notification.innerHTML = `
                <i class="bi bi-funnel"></i> Filter applied: <strong>${filter.toUpperCase()}</strong>
                <br>Showing ${visibleCount} analyst recommendations
                <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
            `;
            
            document.body.appendChild(notification);
            
            // Auto-remove notification after 3 seconds
            setTimeout(() => {
                if (notification.parentNode) {
                    notification.remove();
                }
            }, 3000);
        });
        
        // Add hover effects
        button.addEventListener('mouseenter', function() {
            if (!this.classList.contains('active')) {
                this.style.transform = 'translateY(-2px)';
                this.style.boxShadow = '0 4px 8px rgba(0,0,0,0.2)';
            }
        });
        
        button.addEventListener('mouseleave', function() {
            if (!this.classList.contains('active')) {
                this.style.transform = 'translateY(0)';
                this.style.boxShadow = 'none';
            }
        });
    });
    
    // Initialize with "all" filter active
    const allButton = document.querySelector('[data-filter="all"]');
    if (allButton && !allButton.classList.contains('active')) {
        allButton.click();
    }
    
    console.log('✅ Analyst Coverage Filter System ready');
});
