/**
 * Loading State Utilities
 */

class LoadingUtils {
    constructor() {
        this.activeLoaders = new Set();
    }

    /**
     * Show loading state for an element
     * @param {string|HTMLElement} element - Element or selector
     * @param {string} type - Type of loading state (skeleton, spinner, overlay)
     * @returns {void}
     */
    showLoading(element, type = 'skeleton') {
        const el = typeof element === 'string' ? document.querySelector(element) : element;
        if (!el) return;

        // Store original content
        el.setAttribute('data-original-content', el.innerHTML);
        this.activeLoaders.add(el);

        switch (type) {
            case 'skeleton':
                this.showSkeleton(el);
                break;
            case 'spinner':
                this.showSpinner(el);
                break;
            case 'overlay':
                this.showOverlay(el);
                break;
            default:
                this.showSkeleton(el);
        }
    }

    /**
     * Hide loading state and restore content
     * @param {string|HTMLElement} element - Element or selector
     * @returns {void}
     */
    hideLoading(element) {
        const el = typeof element === 'string' ? document.querySelector(element) : element;
        if (!el || !this.activeLoaders.has(el)) return;

        const originalContent = el.getAttribute('data-original-content');
        if (originalContent) {
            el.innerHTML = originalContent;
            el.removeAttribute('data-original-content');
        }

        this.activeLoaders.delete(el);
        el.classList.add('fade-in');
    }

    /**
     * Show skeleton loading state
     * @param {HTMLElement} element - Target element
     * @returns {void}
     */
    showSkeleton(element) {
        const isDark = element.closest('.bg-dark') !== null;
        const skeletonClass = isDark ? 'skeleton-dark' : 'skeleton';

        // Create skeleton based on element type
        if (element.tagName === 'TABLE' || element.classList.contains('table')) {
            element.innerHTML = this.createTableSkeleton(5, skeletonClass);
        } else if (element.classList.contains('card')) {
            element.innerHTML = this.createCardSkeleton(skeletonClass);
        } else {
            element.innerHTML = this.createTextSkeleton(3, skeletonClass);
        }
    }

    /**
     * Show spinner loading state
     * @param {HTMLElement} element - Target element
     * @returns {void}
     */
    showSpinner(element) {
        const isDark = element.closest('.bg-dark') !== null;
        const spinnerClass = isDark ? 'loading-spinner white' : 'loading-spinner';
        
        element.innerHTML = `
            <div class="text-center p-4">
                <div class="${spinnerClass}"></div>
                <p class="loading-text mt-2">Laster...</p>
            </div>
        `;
    }

    /**
     * Show overlay loading state
     * @param {HTMLElement} element - Target element
     * @returns {void}
     */
    showOverlay(element) {
        // Make element relative if not already
        if (getComputedStyle(element).position === 'static') {
            element.style.position = 'relative';
        }

        const isDark = element.closest('.bg-dark') !== null;
        const overlayClass = isDark ? 'loading-overlay dark' : 'loading-overlay';
        const spinnerClass = isDark ? 'loading-spinner white' : 'loading-spinner';

        const overlay = document.createElement('div');
        overlay.className = overlayClass;
        overlay.innerHTML = `
            <div class="loading-content">
                <div class="${spinnerClass}"></div>
                <p class="loading-text">Laster data...</p>
            </div>
        `;

        element.appendChild(overlay);
    }

    /**
     * Create table skeleton
     * @param {number} rows - Number of rows
     * @param {string} skeletonClass - Skeleton class name
     * @returns {string} HTML string
     */
    createTableSkeleton(rows, skeletonClass) {
        let html = '<div class="skeleton-table">';
        for (let i = 0; i < rows; i++) {
            html += `
                <div class="skeleton-table-row">
                    <div class="${skeletonClass} skeleton-table-cell"></div>
                    <div class="${skeletonClass} skeleton-table-cell"></div>
                    <div class="${skeletonClass} skeleton-table-cell"></div>
                    <div class="${skeletonClass} skeleton-table-cell"></div>
                </div>
            `;
        }
        html += '</div>';
        return html;
    }

    /**
     * Create card skeleton
     * @param {string} skeletonClass - Skeleton class name
     * @returns {string} HTML string
     */
    createCardSkeleton(skeletonClass) {
        return `
            <div class="p-3">
                <div class="${skeletonClass} skeleton-title"></div>
                <div class="${skeletonClass} skeleton-text"></div>
                <div class="${skeletonClass} skeleton-text w-75"></div>
                <div class="${skeletonClass} skeleton-text w-50"></div>
                <div class="${skeletonClass} skeleton-button mt-3"></div>
            </div>
        `;
    }

    /**
     * Create text skeleton
     * @param {number} lines - Number of lines
     * @param {string} skeletonClass - Skeleton class name
     * @returns {string} HTML string
     */
    createTextSkeleton(lines, skeletonClass) {
        let html = '<div class="p-2">';
        for (let i = 0; i < lines; i++) {
            const width = i === lines - 1 ? 'w-50' : '';
            html += `<div class="${skeletonClass} skeleton-text ${width}"></div>`;
        }
        html += '</div>';
        return html;
    }

    /**
     * Show error state
     * @param {string|HTMLElement} element - Element or selector
     * @param {string} message - Error message
     * @param {boolean} showRetry - Show retry button
     * @param {Function} retryCallback - Retry callback function
     * @returns {void}
     */
    showError(element, message = 'En feil oppstod', showRetry = true, retryCallback = null) {
        const el = typeof element === 'string' ? document.querySelector(element) : element;
        if (!el) return;

        let retryButton = '';
        if (showRetry && retryCallback) {
            retryButton = '<button class="btn btn-primary retry-button">Prøv igjen</button>';
        }

        el.innerHTML = `
            <div class="error-state">
                <i class="bi bi-exclamation-triangle"></i>
                <h4>Oops!</h4>
                <p>${message}</p>
                ${retryButton}
            </div>
        `;

        if (showRetry && retryCallback) {
            el.querySelector('.retry-button').addEventListener('click', retryCallback);
        }
    }

    /**
     * Show empty state
     * @param {string|HTMLElement} element - Element or selector
     * @param {string} message - Empty state message
     * @param {string} icon - Bootstrap icon class
     * @param {string} actionText - Action button text
     * @param {Function} actionCallback - Action callback function
     * @returns {void}
     */
    showEmpty(element, message = 'Ingen data tilgjengelig', icon = 'bi-inbox', actionText = null, actionCallback = null) {
        const el = typeof element === 'string' ? document.querySelector(element) : element;
        if (!el) return;

        let actionButton = '';
        if (actionText && actionCallback) {
            actionButton = `<button class="btn btn-primary action-button">${actionText}</button>`;
        }

        el.innerHTML = `
            <div class="empty-state">
                <i class="bi ${icon}"></i>
                <h4>Ingen resultater</h4>
                <p>${message}</p>
                ${actionButton}
            </div>
        `;

        if (actionText && actionCallback) {
            el.querySelector('.action-button').addEventListener('click', actionCallback);
        }
    }

    /**
     * Load data with loading state
     * @param {string|HTMLElement} element - Element or selector
     * @param {Function} loadFunction - Function that loads data
     * @param {string} loadingType - Type of loading state
     * @returns {Promise} Promise that resolves when loading is complete
     */
    async loadWithState(element, loadFunction, loadingType = 'skeleton') {
        const el = typeof element === 'string' ? document.querySelector(element) : element;
        if (!el) return;

        try {
            this.showLoading(el, loadingType);
            const result = await loadFunction();
            this.hideLoading(el);
            return result;
        } catch (error) {
            this.showError(el, 'Kunne ikke laste data. Vennligst prøv igjen.', true, () => {
                this.loadWithState(element, loadFunction, loadingType);
            });
            throw error;
        }
    }
}

// Create global instance
window.loadingUtils = new LoadingUtils();

// Export for use in other scripts
if (typeof module !== 'undefined' && module.exports) {
    module.exports = LoadingUtils;
}
