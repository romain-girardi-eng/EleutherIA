// Service Worker - Self-unregistering cleanup worker
// Removes all caches and unregisters itself so requests go directly to the network.
// SSE streaming (GraphRAG) cannot be cached safely — removing SW entirely.

self.addEventListener('install', (event) => {
  self.skipWaiting();
});

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((cacheNames) =>
      Promise.all(cacheNames.map((name) => caches.delete(name)))
    ).then(() => {
      console.log('[SW] All caches cleared, unregistering service worker');
      return self.registration.unregister();
    })
  );
});
