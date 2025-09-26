// serviceworker.js (Updated Code)

const CACHE_NAME = 'aquaalert-v2'; // Increment the version to trigger an update
const urlsToCache = [
    '/',
    '/static/css/style.css',
    '/static/js/worker_app.js',
];

// Install event: cache the application shell
self.addEventListener('install', event => {
    event.waitUntil(
        caches.open(CACHE_NAME)
            .then(cache => {
                console.log('Opened cache');
                return cache.addAll(urlsToCache);
            })
    );
});

// Activate event: remove old caches
self.addEventListener('activate', event => {
    event.waitUntil(
        caches.keys().then(cacheNames => {
            return Promise.all(
                cacheNames.map(cache => {
                    if (cache !== CACHE_NAME) {
                        console.log('Service Worker: clearing old cache');
                        return caches.delete(cache);
                    }
                })
            );
        })
    );
});

// Fetch event: Apply a "Network falling back to cache" strategy for pages
self.addEventListener('fetch', event => {
    // For HTML pages, always try the network first.
    if (event.request.mode === 'navigate') {
        event.respondWith(
            fetch(event.request).catch(() => {
                // If the network fails, serve the root page from cache.
                return caches.match('/');
            })
        );
        return;
    }

    // For other requests (CSS, JS, etc.), use the cache-first strategy.
    event.respondWith(
        caches.match(event.request)
            .then(response => {
                return response || fetch(event.request);
            })
    );
});