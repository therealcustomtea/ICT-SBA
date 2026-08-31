// Computes and stores CACHE for subsequent operations.
const CACHE = 'cipherboard-shell-v3';
// Computes and stores SHELL for subsequent operations.
const SHELL = ['/en/offline', '/zh-Hant/offline', '/icon.svg', '/icon-192.png', '/icon-512.png', '/icon-maskable-512.png', '/social-preview.png', '/manifest.webmanifest'];
// Calls self.addEventListener with the supplied values.
self.addEventListener('install', (event) => event.waitUntil(caches.open(CACHE).then((cache) => cache.addAll(SHELL))));
// Calls self.addEventListener with the supplied values.
self.addEventListener('message', (event) => {
  // Checks this condition before running the nested branch.
  if (event.data?.type === 'SKIP_WAITING') self.skipWaiting();
// Closes the expression, call, or declaration started above.
});
// Calls self.addEventListener with the supplied values.
self.addEventListener('activate', (event) => event.waitUntil(Promise.all([
  // Calls caches.keys with the supplied values.
  caches.keys().then((keys) => Promise.all(keys.filter((key) => key !== CACHE).map((key) => caches.delete(key)))),
  // Calls self.clients.claim with the supplied values.
  self.clients.claim(),
// Closes the expression, call, or declaration started above.
])));
// Calls self.addEventListener with the supplied values.
self.addEventListener('fetch', (event) => {
  // Checks this condition before running the nested branch.
  if (event.request.method !== 'GET') return;
  // Computes and stores url for subsequent operations.
  const url = new URL(event.request.url);
  // Checks this condition before running the nested branch.
  if (event.request.mode === 'navigate') {
    // Calls event.respondWith with the supplied values.
    event.respondWith(fetch(event.request).catch(() => {
      // Computes and stores locale for subsequent operations.
      const locale = url.pathname.startsWith('/zh-Hant') ? 'zh-Hant' : 'en';
      // Returns this result to the caller and ends the current function.
      return caches.match(`/${locale}/offline`).then((response) => response ?? Response.error());
    // Closes the expression, call, or declaration started above.
    }));
    // Returns this result to the caller and ends the current function.
    return;
  // Closes the expression, call, or declaration started above.
  }
  // Computes and stores safeStaticAsset for subsequent operations.
  const safeStaticAsset = url.origin === self.location.origin && (url.pathname.startsWith('/_next/static/') || SHELL.includes(url.pathname));
  // Checks this condition before running the nested branch.
  if (!safeStaticAsset) return;
  // Calls event.respondWith with the supplied values.
  event.respondWith(caches.match(event.request).then((cached) => cached ?? fetch(event.request).then((response) => {
    // Checks this condition before running the nested branch.
    if (response.ok) void caches.open(CACHE).then((cache) => cache.put(event.request, response.clone()));
    // Returns this result to the caller and ends the current function.
    return response;
  // Closes the expression, call, or declaration started above.
  })));
// Closes the expression, call, or declaration started above.
});
