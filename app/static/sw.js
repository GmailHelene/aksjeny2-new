/**
 * Service Worker for Aksjeradar PWA
 * Provides basic caching and offline functionality
 */

const CACHE_NAME = 'aksjeradar-v1.0.0';
const STATIC_CACHE_URLS = [
    '/',
    '/static/css/style.css',
    '/static/css/mobile-optimized.css',
    '/static/css/loading-states.css',
    '/static/js/app.js',
    '/static/js/i18n.js',
    '/static/manifest.json',
    '/static/favicon.ico'
];

// Install event - cache static resources
self.addEventListener('install', event => {
    event.waitUntil(
        caches.open(CACHE_NAME)
            .then(cache => {
                console.log('Caching static resources');
                return cache.addAll(STATIC_CACHE_URLS);
            })
            .then(() => {
                console.log('Service Worker installed successfully');
                self.skipWaiting();
            })
            .catch(err => {
                console.error('Failed to cache static resources:', err);
            })
    );
});

// Activate event - clean up old caches
self.addEventListener('activate', event => {
    event.waitUntil(
        caches.keys()
            .then(cacheNames => {
                return Promise.all(
                    cacheNames
                        .filter(cacheName => cacheName !== CACHE_NAME)
                        .map(cacheName => {
                            console.log('Deleting old cache:', cacheName);
                            return caches.delete(cacheName);
                        })
                );
            })
            .then(() => {
                console.log('Service Worker activated');
                return self.clients.claim();
            })
    );
});

// Fetch event - serve from cache when possible
self.addEventListener('fetch', event => {
    // Only handle GET requests
    if (event.request.method !== 'GET') {
        return;
    }

    // Skip non-HTTP requests
    if (!event.request.url.startsWith('http')) {
        return;
    }

    event.respondWith(
        caches.match(event.request)
            .then(response => {
                // Return cached version if available
                if (response) {
                    return response;
                }

                // Fetch from network
                return fetch(event.request)
                    .then(response => {
                        // Don't cache non-successful responses
                        if (!response || response.status !== 200 || response.type !== 'basic') {
                            return response;
                        }

                        // Clone the response
                        const responseToCache = response.clone();

                        // Cache dynamic content selectively
                        if (shouldCache(event.request.url)) {
                            caches.open(CACHE_NAME)
                                .then(cache => {
                                    cache.put(event.request, responseToCache);
                                });
                        }

                        return response;
                    })
                    .catch(() => {
                        // Offline fallback
                        if (event.request.destination === 'document') {
                            return caches.match('/');
                        }
                        
                        // Return a basic offline response for other requests
                        return new Response('Offline', {
                            status: 503,
                            statusText: 'Service Unavailable'
                        });
                    });
            })
    );
});

/**
 * Determine if a URL should be cached
 */
function shouldCache(url) {
    // Cache API responses for short periods
    if (url.includes('/api/')) {
        return false; // Don't cache API responses for now
    }
    
    // Cache static assets
    if (url.includes('/static/')) {
        return true;
    }
    
    // Cache main pages
    if (url.endsWith('/') || url.includes('/stocks/') || url.includes('/analysis/')) {
        return true;
    }
    
    return false;
}

// Background sync for offline actions (if supported)
if ('sync' in self.registration) {
    self.addEventListener('sync', event => {
        console.log('Background sync triggered:', event.tag);
        
        if (event.tag === 'stock-data-sync') {
            event.waitUntil(syncStockData());
        }
    });
}

async function syncStockData() {
    try {
        // Implement background sync logic for stock data
        console.log('Syncing stock data in background');
        
        // This would typically sync any offline actions or fetch latest data
        const response = await fetch('/api/sync-data', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        });
        
        if (response.ok) {
            console.log('Stock data synced successfully');
        }
    } catch (error) {
        console.error('Failed to sync stock data:', error);
    }
}

// Push notification handling
self.addEventListener('push', event => {
    if (!event.data) {
        return;
    }

    const data = event.data.json();
    const options = {
        body: data.body || 'Ny oppdatering tilgjengelig',
        icon: '/static/favicon.ico',
        badge: '/static/favicon.ico',
        data: data.url || '/',
        actions: [
            {
                action: 'view',
                title: 'Se nå'
            },
            {
                action: 'dismiss',
                title: 'Lukk'
            }
        ]
    };

    event.waitUntil(
        self.registration.showNotification(data.title || 'Aksjeradar', options)
    );
});

// Notification click handling
self.addEventListener('notificationclick', event => {
    event.notification.close();

    if (event.action === 'view') {
        event.waitUntil(
            clients.openWindow(event.notification.data || '/')
        );
    }
});

console.log('Service Worker loaded successfully');
