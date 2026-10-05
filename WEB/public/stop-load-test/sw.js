const resourcePath = new URL('./slow.svg', self.registration.scope).pathname;

self.addEventListener('install', event => event.waitUntil(self.skipWaiting()));
self.addEventListener('activate', event => event.waitUntil(self.clients.claim()));

self.addEventListener('fetch', event => {
  const url = new URL(event.request.url);
  if (url.origin !== self.location.origin || url.pathname !== resourcePath || event.request.method !== 'GET') return;
  const requestedDelay = Number(url.searchParams.get('delay') ?? 30000);
  const delayMs = Number.isInteger(requestedDelay) && requestedDelay >= 1000 && requestedDelay <= 120000
    ? requestedDelay : 30000;
  const runId = url.searchParams.get('run');
  if (!runId) return;
  async function notify(type) {
    const client = await self.clients.get(event.clientId);
    client?.postMessage({ fixture: 'stop-load-test', runId, type });
  }
  event.respondWith((async () => {
    await notify('worker_request_started');
    await new Promise((resolve, reject) => {
      if (event.request.signal.aborted) {
        reject(new DOMException('Request aborted', 'AbortError'));
        return;
      }
      const timer = setTimeout(resolve, delayMs);
      event.request.signal.addEventListener('abort', () => {
        clearTimeout(timer);
        reject(new DOMException('Request aborted', 'AbortError'));
      }, { once: true });
    });
    const response = await fetch(event.request, { cache: 'no-store' });
    if (!response.ok) throw new Error(`slow.svg returned ${response.status}`);
    const headers = new Headers(response.headers);
    headers.set('Cache-Control', 'no-store');
    headers.set('X-Stop-Load-Test-Delay', String(delayMs));
    await notify('worker_response_released');
    return new Response(response.body, { status: response.status, headers });
  })());
});
