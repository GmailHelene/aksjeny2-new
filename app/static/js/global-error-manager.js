/**
 * Global Error Handler and Loading Manager for Aksjeradar
 * Handles API errors, loading states, and provides comprehensive user feedback
 */

class GlobalErrorManager {
    constructor() {
        this.initializeGlobalErrorHandling();
        this.initializeLoadingStates();
        this.initializeNetworkMonitoring();
    }

    initializeGlobalErrorHandling() {
        // Enhanced fetch wrapper with retry logic
        const originalFetch = window.fetch;
        window.fetch = async (...args) => {
            const maxRetries = 3;
            let attempt = 0;
            
            while (attempt < maxRetries) {
                try {
                    const response = await originalFetch(...args);
                    
                    // Handle specific error status codes
                    if (!response.ok) {
                        await this.handleResponseError(response);
                    }
                    
                    return response;
                } catch (error) {
                    attempt++;
                    if (attempt >= maxRetries) {
                        this.handleNetworkError(error);
                        throw error;
                    }
                    // Wait before retry with exponential backoff
                    await this.delay(Math.pow(2, attempt) * 1000);
                }
            }
        };

        // Handle JavaScript errors
        window.addEventListener('error', (event) => {
            this.logError('JavaScript Error', {
                message: event.error?.message || event.message,
                filename: event.filename,
                lineno: event.lineno,
                colno: event.colno,
                stack: event.error?.stack
            });
        });

        // Handle promise rejections
        window.addEventListener('unhandledrejection', (event) => {
            this.logError('Promise Rejection', {
                reason: event.reason,
                promise: event.promise
            });
        });
    }

    async handleResponseError(response) {
        const errorHandlers = {
            401: () => this.handleAuthError(),
            403: () => this.handleForbiddenError(), 
            429: () => this.handleRateLimitError(),
            500: () => this.handleServerError(),
            502: () => this.handleBadGatewayError(),
            503: () => this.handleServiceUnavailableError()
        };

        const handler = errorHandlers[response.status];
        if (handler) {
            handler();
        } else if (response.status >= 400) {
            this.handleGenericError(response.status, response.statusText);
        }
    }

    initializeLoadingStates() {
        // Global loading indicator
        this.createGlobalLoadingIndicator();

        // Form loading states
        document.addEventListener('submit', (e) => {
            const form = e.target;
            if (form.tagName === 'FORM') {
                this.showFormLoading(form);
            }
        });

        // Button loading states
        document.addEventListener('click', (e) => {
            const button = e.target.closest('[data-loading-text]');
            if (button && button.type === 'submit') {
                this.showButtonLoading(button);
            }
        });
    }

    initializeNetworkMonitoring() {
        // Monitor online/offline status
        window.addEventListener('online', () => {
            this.showNetworkStatus('Internettforbindelse gjenopprettet', 'success');
            this.hideOfflineIndicator();
        });

        window.addEventListener('offline', () => {
            this.showNetworkStatus('Ingen internettforbindelse', 'warning');
            this.showOfflineIndicator();
        });

        // Check connection status on load
        if (!navigator.onLine) {
            this.showOfflineIndicator();
        }
    }

    handleAuthError() {
        this.showPersistentToast(
            'Din sesjon er utløpt. Du blir omdirigert til innloggingssiden...',
            'warning',
            { persistent: true }
        );
        
        setTimeout(() => {
            window.location.href = '/login?next=' + encodeURIComponent(window.location.pathname);
        }, 3000);
    }

    handleForbiddenError() {
        this.showToast(
            'Du har ikke tilgang til denne funksjonen. Vurder å oppgradere abonnementet ditt.',
            'warning',
            { duration: 8000 }
        );
    }

    handleRateLimitError() {
        this.showToast(
            'For mange forespørsler. Vennligst vent litt før du prøver igjen.',
            'warning',
            { duration: 10000 }
        );
    }

    handleServerError() {
        this.showToast(
            'Det oppstod en serverfeil. Vi jobber med å løse problemet.',
            'error',
            { duration: 8000, allowRetry: true }
        );
    }

    handleBadGatewayError() {
        this.showToast(
            'Serveren er midlertidig utilgjengelig. Prøv igjen om litt.',
            'error',
            { duration: 10000, allowRetry: true }
        );
    }

    handleServiceUnavailableError() {
        this.showToast(
            'Tjenesten er midlertidig utilgjengelig. Vi utfører vedlikehold.',
            'warning',
            { duration: 15000 }
        );
    }

    handleGenericError(status, statusText) {
        this.showToast(
            `Det oppstod en feil (${status}). Prøv igjen senere.`,
            'error',
            { duration: 6000 }
        );
    }

    handleNetworkError(error) {
        if (!navigator.onLine) {
            this.showToast(
                'Ingen internettforbindelse. Sjekk tilkoblingen din.',
                'error',
                { persistent: true }
            );
        } else {
            this.showToast(
                'Nettverksfeil. Kontroller tilkoblingen din og prøv igjen.',
                'error',
                { duration: 8000, allowRetry: true }
            );
        }
    }

    createGlobalLoadingIndicator() {
        const indicator = document.createElement('div');
        indicator.id = 'global-loading-indicator';
        indicator.className = 'position-fixed top-0 start-0 w-100 h-100 d-none';
        indicator.style.cssText = `
            background: rgba(0, 0, 0, 0.5);
            z-index: 9998;
            backdrop-filter: blur(2px);
        `;
        
        indicator.innerHTML = `
            <div class="d-flex align-items-center justify-content-center h-100">
                <div class="bg-white rounded p-4 shadow-lg text-center">
                    <div class="spinner-border text-primary mb-3" role="status">
                        <span class="visually-hidden">Laster...</span>
                    </div>
                    <div class="loading-text">Laster...</div>
                </div>
            </div>
        `;
        
        document.body.appendChild(indicator);
    }

    showGlobalLoading(text = 'Laster...') {
        const indicator = document.getElementById('global-loading-indicator');
        if (indicator) {
            const textElement = indicator.querySelector('.loading-text');
            if (textElement) textElement.textContent = text;
            indicator.classList.remove('d-none');
        }
    }

    hideGlobalLoading() {
        const indicator = document.getElementById('global-loading-indicator');
        if (indicator) {
            indicator.classList.add('d-none');
        }
    }

    showFormLoading(form) {
        const submitButton = form.querySelector('[type="submit"]');
        if (submitButton) {
            this.showButtonLoading(submitButton);
        }
        
        // Disable all form inputs
        const inputs = form.querySelectorAll('input, select, textarea, button');
        inputs.forEach(input => {
            if (input !== submitButton) {
                input.disabled = true;
                input.dataset.wasDisabled = input.disabled;
            }
        });
    }

    showButtonLoading(button) {
        if (button.dataset.loading === 'true') return; // Already loading
        
        button.dataset.loading = 'true';
        button.dataset.originalText = button.innerHTML;
        button.disabled = true;
        
        const loadingText = button.dataset.loadingText || 'Behandler...';
        button.innerHTML = `
            <span class="spinner-border spinner-border-sm me-2" role="status"></span>
            ${loadingText}
        `;
    }

    restoreButton(button) {
        if (button.dataset.loading !== 'true') return;
        
        button.dataset.loading = 'false';
        button.disabled = false;
        button.innerHTML = button.dataset.originalText || button.textContent;
        delete button.dataset.originalText;
    }

    showOfflineIndicator() {
        let indicator = document.getElementById('offline-indicator');
        if (!indicator) {
            indicator = document.createElement('div');
            indicator.id = 'offline-indicator';
            indicator.className = 'position-fixed top-0 start-0 end-0 bg-warning text-dark text-center py-2 z-3';
            indicator.innerHTML = `
                <i class="bi bi-wifi-off me-2"></i>
                Du er offline. Noen funksjoner kan være begrenset.
            `;
            document.body.appendChild(indicator);
        }
    }

    hideOfflineIndicator() {
        const indicator = document.getElementById('offline-indicator');
        if (indicator) {
            indicator.remove();
        }
    }

    showNetworkStatus(message, type) {
        this.showToast(message, type, { duration: 3000 });
    }

    showToast(message, type = 'info', options = {}) {
        const {
            duration = 5000,
            persistent = false,
            allowRetry = false
        } = options;

        // Create toast container if it doesn't exist
        let container = document.getElementById('toast-container');
        if (!container) {
            container = document.createElement('div');
            container.id = 'toast-container';
            container.className = 'toast-container position-fixed top-0 end-0 p-3';
            container.style.zIndex = '9999';
            document.body.appendChild(container);
        }

        const toastId = 'toast-' + Date.now();
        const toast = document.createElement('div');
        toast.className = `toast align-items-center text-white bg-${this.getBootstrapColorClass(type)} border-0`;
        toast.id = toastId;
        toast.setAttribute('role', 'alert');
        
        let retryButton = '';
        if (allowRetry) {
            retryButton = `
                <button type="button" class="btn btn-sm btn-outline-light me-2" onclick="window.location.reload()">
                    <i class="bi bi-arrow-clockwise"></i> Prøv igjen
                </button>
            `;
        }
        
        toast.innerHTML = `
            <div class="d-flex">
                <div class="toast-body">
                    <i class="bi bi-${this.getBootstrapIcon(type)} me-2"></i>
                    ${message}
                </div>
                <div class="d-flex align-items-center">
                    ${retryButton}
                    ${!persistent ? '<button type="button" class="btn-close btn-close-white me-2" data-bs-dismiss="toast"></button>' : ''}
                </div>
            </div>
        `;

        container.appendChild(toast);
        
        // Initialize Bootstrap toast
        if (typeof bootstrap !== 'undefined') {
            const bsToast = new bootstrap.Toast(toast, { 
                delay: persistent ? 0 : duration,
                autohide: !persistent
            });
            bsToast.show();
            
            // Remove from DOM after hiding
            if (!persistent) {
                toast.addEventListener('hidden.bs.toast', () => {
                    if (container.contains(toast)) {
                        container.removeChild(toast);
                    }
                });
            }
        }
    }

    showPersistentToast(message, type, options = {}) {
        this.showToast(message, type, { ...options, persistent: true });
    }

    getBootstrapColorClass(type) {
        const colorMap = {
            'error': 'danger',
            'success': 'success',
            'warning': 'warning',
            'info': 'primary'
        };
        return colorMap[type] || 'primary';
    }

    getBootstrapIcon(type) {
        const iconMap = {
            'error': 'exclamation-triangle',
            'success': 'check-circle',
            'warning': 'exclamation-triangle',
            'info': 'info-circle'
        };
        return iconMap[type] || 'info-circle';
    }

    logError(type, details) {
        // Send error to server for logging (if endpoint exists)
        fetch('/api/log-error', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': document.querySelector('meta[name="csrf-token"]')?.getAttribute('content') || ''
            },
            body: JSON.stringify({
                type,
                details,
                url: window.location.href,
                userAgent: navigator.userAgent,
                timestamp: new Date().toISOString(),
                user_id: document.body.dataset.userId || null
            })
        }).catch(() => {
            // Silently fail if logging endpoint doesn't exist
            console.warn('Error logging endpoint not available');
        });
    }

    delay(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }
}

// Initialize error manager
document.addEventListener('DOMContentLoaded', () => {
    window.globalErrorManager = new GlobalErrorManager();
});

// Export for use in other scripts
if (typeof module !== 'undefined' && module.exports) {
    module.exports = GlobalErrorManager;
}
