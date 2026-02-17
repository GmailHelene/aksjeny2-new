// Service Worker for Aksjeradar PWA
const CACHE_VERSION = '2.1.0';
const CACHE_NAME = `aksjeradar-cache-v${CACHE_VERSION}`;
const STATIC_CACHE = 'aksjeradar-static-v2';
const DYNAMIC_CACHE = 'aksjeradar-dynamic-v2';

// Essential files to cache for offline functionality
const urlsToCache = [
  '/',
  '/static/css/style.css',
  '/static/js/main.js',
  '/static/js/pwa-install.js',
  '/static/js/cache-buster.js',
  '/static/images/logo-192.png',
  '/static/images/logo-512.png',
  '/static/images/logo-192-maskable.png',
  '/static/images/logo-512-maskable.png',
  '/static/manifest.json',
  '/static/offline.html',
  'https://cdn.jsdelivr.net/npm/bootstrap@5.3.0-alpha1/dist/css/bootstrap.min.css',
  'https://cdn.jsdelivr.net/npm/bootstrap-icons@1.10.0/font/bootstrap-icons.css',
  'https://cdn.jsdelivr.net/npm/bootstrap@5.3.0-alpha1/dist/js/bootstrap.bundle.min.js',
  'https://cdn.jsdelivr.net/npm/chart.js'
];

// Install event - cache resources
self.addEventListener('install', function(event) {
  console.log('Service Worker: Installing...');
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then(function(cache) {
        console.log('Service Worker: Caching app resources');
        return cache.addAll(urlsToCache);
      })
      .catch(function(err) {
        console.error('Service Worker: Cache failed', err);
      })
  );
  self.skipWaiting();
});

// Activate event - clean up old caches
self.addEventListener('activate', function(event) {
  console.log('Service Worker: Activating...');
  event.waitUntil(
    caches.keys().then(function(cacheNames) {
      return Promise.all(
        cacheNames.map(function(cacheName) {
          if (cacheName !== CACHE_NAME) {
            console.log('Service Worker: Deleting old cache:', cacheName);
            return caches.delete(cacheName);
          }
        })
      );
    })
  );
  self.clients.claim();
});

// Fetch event - serve from cache, fallback to network
self.addEventListener('fetch', function(event) {
  // Skip cross-origin requests except CDN resources
  if (!event.request.url.startsWith(self.location.origin) && 
      !event.request.url.includes('cdn.jsdelivr.net')) {
    return;
  }

  // Handle navigation requests
  if (event.request.destination === 'document') {
    event.respondWith(
      caches.match(event.request)
        .then(function(response) {
          if (response) {
            return response;
          }
          
          return fetch(event.request)
            .then(function(networkResponse) {
              if (networkResponse && networkResponse.status === 200) {
                const responseToCache = networkResponse.clone();
                caches.open(DYNAMIC_CACHE).then(function(cache) {
                  cache.put(event.request, responseToCache);
                });
              }
              return networkResponse;
            })
            .catch(function() {
              return caches.match('/static/offline.html');
            });
        })
    );
    return;
  }

  // Handle other requests
  event.respondWith(
    caches.match(event.request)
      .then(function(response) {
        // Return cached version if available
        if (response) {
          return response;
        }
        
        // Not in cache, fetch from network
        return fetch(event.request)
          .then(function(networkResponse) {
            // Check if we received a valid response
            if (!networkResponse || networkResponse.status !== 200 || networkResponse.type !== 'basic') {
              return networkResponse;
            }

            // Clone the response for caching
            const responseToCache = networkResponse.clone();

            // Add successful responses to dynamic cache for static assets
            if (event.request.url.includes('/static/') || event.request.url.includes('cdn.jsdelivr.net')) {
              caches.open(STATIC_CACHE).then(function(cache) {
                cache.put(event.request, responseToCache);
              });
            } else {
              caches.open(DYNAMIC_CACHE).then(function(cache) {
                cache.put(event.request, responseToCache);
              });
            }

            return networkResponse;
          })
          .catch(function() {
            // For images, return a placeholder or nothing
            if (event.request.destination === 'image') {
              // Return cached logo as placeholder
              return caches.match('/static/images/logo-192.png');
            }
          });
      }
    )
  );
});

// Push notification handler
self.addEventListener('push', function(event) {
  console.log('Service Worker: Push notification received');
  
  const data = event.data ? event.data.json() : {};
  const title = data.title || 'Aksjeradar';
  const options = {
    body: data.body || 'Ny oppdatering tilgjengelig',
    icon: '/static/images/logo-192.png',
    badge: '/static/images/logo-192.png',
    vibrate: [200, 100, 200],
    data: data.url || '/',
    actions: [
      {
        action: 'open',
        title: 'Åpne app'
      },
      {
        action: 'close', 
        title: 'Lukk'
      }
    ]
  };

  event.waitUntil(
    self.registration.showNotification(title, options)
  );
});

// Notification click handler
self.addEventListener('notificationclick', function(event) {
  console.log('Service Worker: Notification clicked');
  event.notification.close();

  if (event.action === 'open' || !event.action) {
    event.waitUntil(
      clients.openWindow(event.notification.data || '/')
    );
  }
});

// Message handler for communication with main app
self.addEventListener('message', function(event) {
  if (event.data === 'SKIP_WAITING') {
    self.skipWaiting();
  }
});

// Background sync for offline actions
self.addEventListener('sync', function(event) {
  if (event.tag === 'sync-portfolio') {
    event.waitUntil(syncPortfolioData());
  }
});

// Function to sync portfolio data when back online
function syncPortfolioData() {
  return self.registration.sync.getTags().then(tags => {
    if (tags.includes('sync-portfolio')) {
      return fetch('/api/portfolio/sync', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          timestamp: new Date().toISOString(),
          source: 'service_worker'
        })
      }).catch(err => {
        console.log('Portfolio sync failed:', err);
      });
    }
  });
}

// Cache management - limit dynamic cache size
function limitCacheSize(cacheName, maxItems) {
  caches.open(cacheName).then(cache => {
    cache.keys().then(keys => {
      if (keys.length > maxItems) {
        cache.delete(keys[0]).then(() => {
          limitCacheSize(cacheName, maxItems);
        });
      }
    });
  });
}

// Clean up dynamic cache periodically
setInterval(() => {
  limitCacheSize(DYNAMIC_CACHE, 50);
}, 60000); // Check every minute
