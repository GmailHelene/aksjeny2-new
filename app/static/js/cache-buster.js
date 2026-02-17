// Aksjeradar Cache Busting Utilities

class CacheBuster {
    constructor() {
        this.version = this.getCacheVersion();
    }

    getCacheVersion() {
        const meta = document.querySelector('meta[name="cache-bust"]');
        return meta ? meta.getAttribute('content') : Date.now();
    }

    // Force refresh all cached resources
    refreshStaticAssets() {
        const links = document.querySelectorAll('link[rel="stylesheet"]');
        links.forEach(link => {
            const href = link.getAttribute('href');
            if (href && !href.includes('v=')) {
                link.setAttribute('href', `${href}?v=${this.version}`);
            }
        });

        const scripts = document.querySelectorAll('script[src]');
        scripts.forEach(script => {
            if (!script.src.includes('bootstrap') && !script.src.includes('cdn')) {
                const src = script.getAttribute('src');
                if (src && !src.includes('v=')) {
                    script.setAttribute('src', `${src}?v=${this.version}`);
                }
            }
        });
    }

    // API call to trigger server-side cache bust
    async triggerServerCacheBust() {
        try {
            const response = await fetch('/api/cache/bust', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                }
            });
            const result = await response.json();
            
            if (result.success) {
                console.log('✅ Server cache busted:', result.timestamp);
                return result.timestamp;
            } else {
                console.error('❌ Cache bust failed:', result.error);
                return null;
            }
        } catch (error) {
            console.error('❌ Cache bust error:', error);
            return null;
        }
    }

    // Force reload page with cache bust
    hardRefresh() {
        const url = new URL(window.location);
        url.searchParams.set('v', this.version);
        url.searchParams.set('cache_bust', Date.now());
        window.location.href = url.toString();
    }

    // Clear browser storage
    clearBrowserCache() {
        // Clear localStorage
        if (typeof Storage !== "undefined") {
            localStorage.clear();
            sessionStorage.clear();
        }

        // Clear service worker cache if available
        if ('serviceWorker' in navigator && 'caches' in window) {
            caches.keys().then(cacheNames => {
                return Promise.all(
                    cacheNames.map(cacheName => caches.delete(cacheName))
                );
            });
        }
    }

    // Complete cache refresh
    async fullCacheRefresh() {
        console.log('🚀 Starting full cache refresh...');
        
        // 1. Clear browser cache
        this.clearBrowserCache();
        
        // 2. Trigger server cache bust
        const newVersion = await this.triggerServerCacheBust();
        
        // 3. Refresh static assets
        this.refreshStaticAssets();
        
        // 4. Hard refresh page
        setTimeout(() => {
            this.hardRefresh();
        }, 1000);
        
        return newVersion;
    }
}

// Global cache buster instance
window.cacheBuster = new CacheBuster();

// Keyboard shortcut for cache refresh (Ctrl+Shift+R alternative)
document.addEventListener('keydown', function(e) {
    if (e.ctrlKey && e.shiftKey && e.key === 'F5') {
        e.preventDefault();
        window.cacheBuster.fullCacheRefresh();
    }
});

// Expose cache busting functions globally
window.refreshCache = () => window.cacheBuster.fullCacheRefresh();
window.hardRefresh = () => window.cacheBuster.hardRefresh();
