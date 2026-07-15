const CACHE = 'cipherboard-shell-v3';
const SHELL = ['/en/offline', '/zh-Hant/offline', '/icon.svg', '/icon-192.png', '/icon-512.png', '/icon-maskable-512.png', '/social-preview.png', '/manifest.webmanifest'];
self.addEventListener('install', (event) => event.waitUntil(caches.open(CACHE).then((cache) => cache.addAll(SHELL))));
self.addEventListener('message', (event) => {
  if (event.data?.type === 'SKIP_WAITING') self.skipWaiting();
});
self.addEventListener('activate', (event) => event.waitUntil(Promise.all([
  caches.keys().then((keys) => Promise.all(keys.filter((key) => key !== CACHE).map((key) => caches.delete(key)))),
  self.clients.claim(),
])));
self.addEventListener('fetch', (event) => {
  if (event.request.method !== 'GET') return;
  const url = new URL(event.request.url);
  if (event.request.mode === 'navigate') {
    event.respondWith(fetch(event.request).catch(() => {
      const locale = url.pathname.startsWith('/zh-Hant') ? 'zh-Hant' : 'en';
      return caches.match(`/${locale}/offline`).then((response) => response ?? Response.error());
    }));
    return;
  }
  const safeStaticAsset = url.origin === self.location.origin && (url.pathname.startsWith('/_next/static/') || SHELL.includes(url.pathname));
  if (!safeStaticAsset) return;
  event.respondWith(caches.match(event.request).then((cached) => cached ?? fetch(event.request).then((response) => {
    if (response.ok) void caches.open(CACHE).then((cache) => cache.put(event.request, response.clone()));
    return response;
  })));
});
