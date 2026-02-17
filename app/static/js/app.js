/**
 * Main application JavaScript
 * Handles global functionality and initialization
 */

// Global app configuration
window.app = {
    version: '1.0.0',
    debug: false,
    initialized: false
};

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    console.log('🚀 Aksjeradar app initializing...');
    
    try {
        // Initialize global error handling
        initErrorHandling();
        
        // Initialize CSRF token handling
        initCSRFHandling();
        
        // Initialize loading states
        initLoadingStates();
        
        // Initialize tooltips if Bootstrap is available
        if (typeof bootstrap !== 'undefined') {
            initTooltips();
        }
        
        // Mark as initialized
        window.app.initialized = true;
        console.log('✅ Aksjeradar app initialized successfully');
        
    } catch (error) {
        console.error('❌ App initialization failed:', error);
    }
});

/**
 * Initialize global error handling
 */
function initErrorHandling() {
    window.addEventListener('error', function(event) {
        console.error('Global error:', event.error);
        showToast('En feil oppstod. Prøv å laste siden på nytt.', 'error');
    });
    
    window.addEventListener('unhandledrejection', function(event) {
        console.error('Unhandled promise rejection:', event.reason);
        showToast('En feil oppstod ved lasting av data.', 'error');
    });
}

/**
 * Initialize CSRF token handling
 */
function initCSRFHandling() {
    // Make CSRF token globally available
    const csrfToken = document.querySelector('meta[name="csrf-token"]')?.getAttribute('content');
    if (csrfToken) {
        window.csrfToken = csrfToken;
    }
}

/**
 * Initialize loading states
 */
function initLoadingStates() {
    // Hide any loading spinners that might be stuck
    setTimeout(function() {
        const loadingElements = document.querySelectorAll('.loading, .spinner-border');
        loadingElements.forEach(el => {
            if (el.style.display !== 'none') {
                el.style.display = 'none';
            }
        });
    }, 100);
}

/**
 * Initialize Bootstrap tooltips
 */
function initTooltips() {
    try {
        const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
        tooltipTriggerList.map(function(tooltipTriggerEl) {
            return new bootstrap.Tooltip(tooltipTriggerEl);
        });
    } catch (error) {
        console.warn('Could not initialize tooltips:', error);
    }
}

/**
 * Global toast notification function
 * @param {string} message - Message to display
 * @param {string} type - Type: success, error, warning, info
 */
function showToast(message, type = 'info') {
    // Create toast element if it doesn't exist
    let toastContainer = document.querySelector('.toast-container');
    if (!toastContainer) {
        toastContainer = document.createElement('div');
        toastContainer.className = 'toast-container position-fixed top-0 end-0 p-3';
        toastContainer.style.zIndex = '9999';
        document.body.appendChild(toastContainer);
    }
    
    // Create toast
    const toastId = 'toast-' + Date.now();
    const iconMap = {
        success: 'bi-check-circle-fill text-success',
        error: 'bi-exclamation-triangle-fill text-danger',
        warning: 'bi-exclamation-triangle-fill text-warning',
        info: 'bi-info-circle-fill text-primary'
    };
    
    const toastHtml = `
        <div id="${toastId}" class="toast" role="alert" aria-live="assertive" aria-atomic="true">
            <div class="toast-header">
                <i class="bi ${iconMap[type] || iconMap.info} me-2"></i>
                <strong class="me-auto">Aksjeradar</strong>
                <button type="button" class="btn-close" data-bs-dismiss="toast" aria-label="Lukk"></button>
            </div>
            <div class="toast-body">
                ${message}
            </div>
        </div>
    `;
    
    toastContainer.insertAdjacentHTML('beforeend', toastHtml);
    
    // Show toast
    const toastElement = document.getElementById(toastId);
    if (typeof bootstrap !== 'undefined') {
        const toast = new bootstrap.Toast(toastElement, {
            delay: type === 'error' ? 5000 : 3000
        });
        toast.show();
        
        // Clean up after toast is hidden
        toastElement.addEventListener('hidden.bs.toast', function() {
            toastElement.remove();
        });
    } else {
        // Fallback for when Bootstrap is not available
        toastElement.style.display = 'block';
        setTimeout(() => {
            toastElement.remove();
        }, type === 'error' ? 5000 : 3000);
    }
}

/**
 * Utility function to get CSRF token
 */
function getCSRFToken() {
    return window.csrfToken || document.querySelector('meta[name="csrf-token"]')?.getAttribute('content') || '';
}

/**
 * Utility function for safe fetch requests with CSRF
 */
async function safeFetch(url, options = {}) {
    const defaultOptions = {
        headers: {
            'Content-Type': 'application/json',
            'X-Requested-With': 'XMLHttpRequest',
            'X-CSRFToken': getCSRFToken()
        }
    };
    
    const finalOptions = {
        ...defaultOptions,
        ...options,
        headers: {
            ...defaultOptions.headers,
            ...(options.headers || {})
        }
    };
    
    try {
        const response = await fetch(url, finalOptions);
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        return response;
    } catch (error) {
        console.error('Fetch error:', error);
        throw error;
    }
}

// Export globally for compatibility
window.showToast = showToast;
window.getCSRFToken = getCSRFToken;
window.safeFetch = safeFetch;

console.log('📦 App.js loaded successfully');
