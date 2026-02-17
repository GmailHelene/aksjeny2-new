/**
 * Advanced Loading Manager for Premium UX
 */
class LoadingManager {
    constructor() {
        this.activeLoaders = new Set();
        this.loadingStates = new Map();
        this.skeletonTemplates = new Map();
        this.init();
    }

    init() {
        this.createLoadingOverlay();
        this.initSkeletonTemplates();
        this.bindEvents();
    }

    createLoadingOverlay() {
        if (document.getElementById('global-loading-overlay')) return;
        
        const overlay = document.createElement('div');
        overlay.id = 'global-loading-overlay';
        overlay.className = 'loading-overlay';
        overlay.style.display = 'none';
        overlay.innerHTML = `
            <div class="loading-content">
                <div class="loading-spinner"></div>
                <div class="loading-text mt-3">Laster...</div>
            </div>
        `;
        document.body.appendChild(overlay);
    }

    initSkeletonTemplates() {
        this.skeletonTemplates.set('stock-card', `
            <div class="stock-skeleton">
                <div class="skeleton skeleton-avatar"></div>
                <div class="skeleton-content">
                    <div class="skeleton skeleton-text large"></div>
                    <div class="skeleton skeleton-text small" style="width: 60%;"></div>
                </div>
                <div class="skeleton skeleton-price"></div>
            </div>
        `);

        this.skeletonTemplates.set('news-item', `
            <div class="skeleton-card">
                <div class="skeleton skeleton-text large"></div>
                <div class="skeleton skeleton-text" style="width: 80%;"></div>
                <div class="skeleton skeleton-text" style="width: 60%;"></div>
                <div class="skeleton skeleton-text small" style="width: 30%;"></div>
            </div>
        `);

        this.skeletonTemplates.set('chart', `
            <div class="skeleton-card">
                <div class="skeleton skeleton-text large" style="width: 200px; margin-bottom: 20px;"></div>
                <div class="skeleton" style="height: 300px; border-radius: 8px;"></div>
            </div>
        `);

        this.skeletonTemplates.set('table-row', `
            <tr class="skeleton-row">
                <td><div class="skeleton skeleton-text"></div></td>
                <td><div class="skeleton skeleton-text"></div></td>
                <td><div class="skeleton skeleton-text"></div></td>
                <td><div class="skeleton skeleton-text"></div></td>
            </tr>
        `);
    }

    bindEvents() {
        // Show loading on page navigation
        window.addEventListener('beforeunload', () => {
            this.showGlobalLoading('Navigerer...');
        });

        // Hide loading when page is ready
        document.addEventListener('DOMContentLoaded', () => {
            this.hideGlobalLoading();
        });
    }

    showGlobalLoading(text = 'Laster...') {
        const overlay = document.getElementById('global-loading-overlay');
        const textElement = overlay.querySelector('.loading-text');
        if (textElement) textElement.textContent = text;
        overlay.style.display = 'flex';
    }

    hideGlobalLoading() {
        const overlay = document.getElementById('global-loading-overlay');
        overlay.style.display = 'none';
    }

    showSkeleton(containerId, type, count = 3) {
        const container = document.getElementById(containerId);
        if (!container) return;

        const template = this.skeletonTemplates.get(type);
        if (!template) return;

        container.innerHTML = Array(count).fill(template).join('');
        this.loadingStates.set(containerId, true);
    }

    hideSkeleton(containerId) {
        this.loadingStates.set(containerId, false);
    }

    showLoadingButton(buttonElement, text = 'Laster...') {
        if (!buttonElement) return;

        buttonElement.originalText = buttonElement.innerHTML;
        buttonElement.disabled = true;
        buttonElement.innerHTML = `
            <span class="spinner-border spinner-border-sm me-2" role="status"></span>
            ${text}
        `;
    }

    hideLoadingButton(buttonElement) {
        if (!buttonElement || !buttonElement.originalText) return;

        buttonElement.disabled = false;
        buttonElement.innerHTML = buttonElement.originalText;
    }

    showProgressBar(containerId, progress = 0) {
        const container = document.getElementById(containerId);
        if (!container) return;

        container.innerHTML = `
            <div class="progress" style="height: 4px;">
                <div class="progress-bar bg-primary" role="progressbar" 
                     style="width: ${progress}%" aria-valuenow="${progress}" 
                     aria-valuemin="0" aria-valuemax="100"></div>
            </div>
        `;
    }

    updateProgressBar(containerId, progress) {
        const container = document.getElementById(containerId);
        const progressBar = container?.querySelector('.progress-bar');
        if (progressBar) {
            progressBar.style.width = `${progress}%`;
            progressBar.setAttribute('aria-valuenow', progress);
        }
    }

    // Enhanced fetch with loading states
    async enhancedFetch(url, options = {}, loadingConfig = {}) {
        const {
            showGlobal = false,
            showButton = null,
            showSkeleton = null,
            loadingText = 'Laster...'
        } = loadingConfig;

        try {
            // Show loading states
            if (showGlobal) this.showGlobalLoading(loadingText);
            if (showButton) this.showLoadingButton(showButton, loadingText);
            if (showSkeleton) this.showSkeleton(showSkeleton.container, showSkeleton.type, showSkeleton.count);

            const response = await fetch(url, options);
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data = await response.json();
            return data;

        } catch (error) {
            console.error('Fetch error:', error);
            throw error;
        } finally {
            // Hide loading states
            if (showGlobal) this.hideGlobalLoading();
            if (showButton) this.hideLoadingButton(showButton);
            if (showSkeleton) this.hideSkeleton(showSkeleton.container);
        }
    }

    // Smooth content replacement
    async replaceContent(containerId, newContent, animationDuration = 300) {
        const container = document.getElementById(containerId);
        if (!container) return;

        // Fade out
        container.style.transition = `opacity ${animationDuration}ms ease`;
        container.style.opacity = '0';

        await new Promise(resolve => setTimeout(resolve, animationDuration));

        // Replace content
        container.innerHTML = newContent;

        // Fade in
        container.style.opacity = '1';
    }

    // Create loading toast
    showLoadingToast(message, duration = 3000) {
        const toast = document.createElement('div');
        toast.className = 'toast align-items-center text-white bg-primary border-0 position-fixed';
        toast.style.cssText = 'top: 20px; right: 20px; z-index: 9999;';
        toast.innerHTML = `
            <div class="d-flex">
                <div class="toast-body">
                    <span class="spinner-border spinner-border-sm me-2" role="status"></span>
                    ${message}
                </div>
                <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
            </div>
        `;

        document.body.appendChild(toast);
        const bsToast = new bootstrap.Toast(toast, { delay: duration });
        bsToast.show();

        toast.addEventListener('hidden.bs.toast', () => {
            toast.remove();
        });

        return bsToast;
    }
}

// Initialize global loading manager
const loadingManager = new LoadingManager();

// Export for use in other modules
window.loadingManager = loadingManager;
