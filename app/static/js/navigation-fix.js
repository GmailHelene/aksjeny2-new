/**
 * Simplified Navigation Handler to Fix Back Button Hanging Issue
 * This replaces the complex navigation logic with a simpler, more reliable approach
 */

(function() {
    'use strict';
    
    // Simple navigation state
    let isPageLoading = false;
    let loadTimeout = null;
    
    // Initialize when DOM is ready
    document.addEventListener('DOMContentLoaded', function() {
        initializeSimpleNavigation();
    });
    
    function initializeSimpleNavigation() {
        console.log('Simple navigation handler initialized');
        
        // Handle back/forward navigation
        window.addEventListener('popstate', function(event) {
            console.log('Browser navigation detected');
            handleBrowserNavigation(event);
        });
        
        // Handle page show (including back from cache)
        window.addEventListener('pageshow', function(event) {
            console.log('Page show event, persisted:', event.persisted);
            if (event.persisted) {
                // Page loaded from browser cache (bfcache)
                handlePageFromCache();
            }
            clearLoadingStates();
        });
        
        // Handle page before unload
        window.addEventListener('beforeunload', function(event) {
            console.log('Page unloading');
            clearAllResources();
        });
        
        // Handle visibility change
        document.addEventListener('visibilitychange', function() {
            if (document.visibilityState === 'visible') {
                console.log('Page became visible');
                clearLoadingStates();
            }
        });
        
        // Set initial state
        if (history.state === null) {
            history.replaceState({
                timestamp: Date.now(),
                page: window.location.pathname
            }, '', window.location.href);
        }
    }
    
    function handleBrowserNavigation(event) {
        // Clear any loading states that might be stuck
        clearLoadingStates();
        
        // Clear resources from previous page
        clearPageResources();
        
        // If page is not responding, force reload
        if (isPageLoading) {
            console.warn('Page seems stuck, forcing reload');
            setTimeout(() => {
                if (isPageLoading) {
                    window.location.reload();
                }
            }, 2000);
        }
    }
    
    function handlePageFromCache() {
        // Page loaded from browser cache
        clearLoadingStates();
        clearPageResources();
        
        // Check if page content is stale
        const state = history.state || {};
        if (state.timestamp && (Date.now() - state.timestamp) > 300000) { // 5 minutes
            console.log('Page is stale, refreshing');
            window.location.reload();
            return;
        }
        
        // Re-initialize components that might need refreshing
        initializePageComponents();
    }
    
    function clearLoadingStates() {
        isPageLoading = false;
        
        if (loadTimeout) {
            clearTimeout(loadTimeout);
            loadTimeout = null;
        }
        
        // Remove any stuck loading overlays
        const overlays = document.querySelectorAll('.loading-overlay, [id*="loading"], [class*="loading"]');
        overlays.forEach(overlay => {
            if (overlay.style.display !== 'none') {
                overlay.style.display = 'none';
            }
        });
        
        // Re-enable disabled buttons
        const disabledButtons = document.querySelectorAll('button[disabled], a[disabled]');
        disabledButtons.forEach(button => {
            if (!button.hasAttribute('data-permanent-disabled')) {
                button.disabled = false;
                button.style.opacity = '';
                button.style.pointerEvents = '';
            }
        });
        
        // Clear loading spinners
        const spinners = document.querySelectorAll('.spinner-border');
        spinners.forEach(spinner => {
            if (!spinner.hasAttribute('data-permanent-spinner')) {
                const parent = spinner.closest('.btn, .card-body, .loading-container');
                if (parent && parent.hasAttribute('data-original-content')) {
                    parent.innerHTML = parent.getAttribute('data-original-content');
                    parent.removeAttribute('data-original-content');
                }
            }
        });
    }
    
    function clearPageResources() {
        // Clear intervals
        if (window.chartUpdateInterval) {
            clearInterval(window.chartUpdateInterval);
            window.chartUpdateInterval = null;
        }
        
        if (window.dataRefreshInterval) {
            clearInterval(window.dataRefreshInterval);
            window.dataRefreshInterval = null;
        }
        
        // Abort fetch requests
        if (window.currentAbortController) {
            window.currentAbortController.abort();
            window.currentAbortController = null;
        }
        
        // Destroy charts
        if (window.stockChart && typeof window.stockChart.destroy === 'function') {
            try {
                window.stockChart.destroy();
                window.stockChart = null;
            } catch (e) {
                console.warn('Error destroying chart:', e);
            }
        }
        
        console.log('Page resources cleared');
    }
    
    function clearAllResources() {
        clearLoadingStates();
        clearPageResources();
        
        // Remove event listeners that might interfere
        const events = ['scroll', 'resize', 'mousemove', 'touchmove'];
        events.forEach(eventType => {
            const elements = document.querySelectorAll(`[data-${eventType}-listener]`);
            elements.forEach(element => {
                element.removeEventListener(eventType, element[`_${eventType}Handler`]);
            });
        });
    }
    
    function initializePageComponents() {
        // Only initialize essential components
        setTimeout(() => {
            // Re-initialize tooltips if needed
            if (typeof bootstrap !== 'undefined' && bootstrap.Tooltip) {
                const tooltipTriggerList = document.querySelectorAll('[data-bs-toggle="tooltip"]:not([data-tooltip-initialized])');
                tooltipTriggerList.forEach(tooltipTriggerEl => {
                    new bootstrap.Tooltip(tooltipTriggerEl);
                    tooltipTriggerEl.setAttribute('data-tooltip-initialized', 'true');
                });
            }
            
            // Re-initialize dropdowns if needed
            if (typeof bootstrap !== 'undefined' && bootstrap.Dropdown) {
                const dropdownTriggerList = document.querySelectorAll('[data-bs-toggle="dropdown"]:not([data-dropdown-initialized])');
                dropdownTriggerList.forEach(dropdownTriggerEl => {
                    new bootstrap.Dropdown(dropdownTriggerEl);
                    dropdownTriggerEl.setAttribute('data-dropdown-initialized', 'true');
                });
            }
            
            console.log('Page components re-initialized');
        }, 100);
    }
    
    // Enhanced link handling to prevent rapid clicks
    document.addEventListener('click', function(event) {
        const link = event.target.closest('a[href]');
        if (link && !link.target && !link.href.includes('#') && !link.href.includes('javascript:')) {
            // Prevent multiple rapid clicks
            if (link.hasAttribute('data-clicked')) {
                event.preventDefault();
                return;
            }
            
            link.setAttribute('data-clicked', 'true');
            setTimeout(() => {
                link.removeAttribute('data-clicked');
            }, 1000);
            
            // Add visual feedback
            link.style.opacity = '0.7';
            setTimeout(() => {
                link.style.opacity = '';
            }, 500);
        }
    });
    
    // Handle page load timeout
    window.addEventListener('load', function() {
        clearLoadingStates();
        console.log('Page fully loaded');
    });
    
    // Fallback: Force clear loading states after timeout
    setTimeout(() => {
        clearLoadingStates();
    }, 5000);
    
})();
