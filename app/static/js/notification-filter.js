/**
 * Notification Manager - Controls and filters unwanted toast notifications
 */

class NotificationManager {
    constructor() {
        this.disabledNotificationTypes = new Set([
            'realtime_connect',
            'realtime_disconnect', 
            'portfolio_sync',
            'data_refresh',
            'auto_save'
        ]);
        
        this.pageBlacklist = new Set([
            '/stocks/details/',
            '/subscription'
        ]);
        
        this.initializeFilters();
    }

    initializeFilters() {
        // Override bootstrap Toast constructor to filter unwanted notifications
        if (typeof bootstrap !== 'undefined' && bootstrap.Toast) {
            const originalToast = bootstrap.Toast;
            
            bootstrap.Toast = function(element, options) {
                // Check if this notification should be blocked
                if (window.notificationManager && 
                    window.notificationManager.shouldBlockNotification(element)) {
                    console.log('NotificationManager: Blocked unwanted notification');
                    return {
                        show: () => {},
                        hide: () => {},
                        dispose: () => {}
                    };
                }
                
                return new originalToast(element, options);
            };
            
            // Copy static properties
            Object.setPrototypeOf(bootstrap.Toast, originalToast);
            Object.defineProperty(bootstrap.Toast, 'VERSION', { value: originalToast.VERSION });
            Object.defineProperty(bootstrap.Toast, 'Default', { value: originalToast.Default });
        }

        // Override common notification functions
        this.overrideCommonNotificationMethods();
    }

    shouldBlockNotification(element) {
        // Check current page
        const currentPath = window.location.pathname;
        for (const blacklistedPath of this.pageBlacklist) {
            if (currentPath.includes(blacklistedPath)) {
                return true;
            }
        }

        // Check notification content
        if (element && element.innerHTML) {
            const content = element.innerHTML.toLowerCase();
            
            // Block notifications with certain keywords
            const blockedKeywords = [
                'document.body.appendchild',
                'const toast = new bootstrap.toast',
                'notification.addeventlistener',
                'auto-save',
                'connection status',
                'data refreshed'
            ];
            
            for (const keyword of blockedKeywords) {
                if (content.includes(keyword)) {
                    return true;
                }
            }
        }

        return false;
    }

    overrideCommonNotificationMethods() {
        // Override showToast function if it exists globally
        if (typeof window.showToast === 'function') {
            const originalShowToast = window.showToast;
            window.showToast = (message, type, options) => {
                if (this.shouldBlockToastMessage(message, type)) {
                    console.log('NotificationManager: Blocked toast message:', message);
                    return;
                }
                return originalShowToast(message, type, options);
            };
        }

        // Override showNotification function if it exists globally
        if (typeof window.showNotification === 'function') {
            const originalShowNotification = window.showNotification;
            window.showNotification = (message, type, options) => {
                if (this.shouldBlockToastMessage(message, type)) {
                    console.log('NotificationManager: Blocked notification:', message);
                    return;
                }
                return originalShowNotification(message, type, options);
            };
        }
    }

    shouldBlockToastMessage(message, type) {
        if (!message) return false;
        
        const currentPath = window.location.pathname;
        
        // Block all notifications on subscription page
        if (currentPath.includes('/subscription')) {
            return true;
        }
        
        // Block notifications on stock details pages
        if (currentPath.includes('/stocks/details/')) {
            return true;
        }
        
        // Block specific message types
        const blockedMessages = [
            'connection established',
            'data updated',
            'auto-saved',
            'refreshing data',
            'portfolio synced'
        ];
        
        const messageText = message.toString().toLowerCase();
        return blockedMessages.some(blocked => messageText.includes(blocked));
    }

    // Allow certain notifications to still show
    allowNotification(message, type = 'info', options = {}) {
        // This bypasses the filtering for important notifications
        const element = document.createElement('div');
        element.className = 'toast align-items-center text-white bg-primary border-0';
        element.setAttribute('role', 'alert');
        element.style.cssText = 'position: fixed; top: 20px; right: 20px; z-index: 9999;';
        
        element.innerHTML = `
            <div class="d-flex">
                <div class="toast-body">
                    <i class="bi bi-info-circle me-2"></i>${message}
                </div>
                <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
            </div>
        `;

        document.body.appendChild(element);
        
        // Use the original Bootstrap Toast constructor directly
        const toast = new (Object.getPrototypeOf(bootstrap.Toast).constructor)(element, {
            delay: options.delay || 3000
        });
        
        toast.show();

        element.addEventListener('hidden.bs.toast', () => {
            element.remove();
        });
    }

    // Clean up any existing unwanted toasts
    removeExistingToasts() {
        const toasts = document.querySelectorAll('.toast');
        toasts.forEach(toast => {
            if (this.shouldBlockNotification(toast)) {
                toast.remove();
            }
        });
    }
}

// Initialize notification manager when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.notificationManager = new NotificationManager();
    
    // Clean up any existing toasts after a short delay
    setTimeout(() => {
        window.notificationManager.removeExistingToasts();
    }, 1000);
    
    console.log('NotificationManager: Initialized and filtering unwanted notifications');
});

// Export for use in other scripts
if (typeof module !== 'undefined' && module.exports) {
    module.exports = NotificationManager;
}
