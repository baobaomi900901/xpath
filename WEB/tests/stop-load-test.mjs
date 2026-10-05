import assert from 'node:assert/strict';
import { createServer } from 'node:http';
import { readFile } from 'node:fs/promises';
import { dirname, extname, resolve, sep } from 'node:path';
import { fileURLToPath } from 'node:url';
import { createRequire } from 'node:module';

const require = createRequire(import.meta.url);
const { chromium } = require(process.env.STOP_LOAD_PLAYWRIGHT_MODULE || 'playwright');
const publicRoot = resolve(dirname(fileURLToPath(import.meta.url)), process.argv.includes('--built') ? '../dist' : '../public');
const types = { '.html': 'text/html', '.js': 'text/javascript', '.css': 'text/css', '.svg': 'image/svg+xml' };
const server = createServer(async (request, response) => {
  const url = new URL(request.url, 'http://localhost');
  const path = resolve(publicRoot, '.' + decodeURIComponent(url.pathname.replace(/^\/xpath/, '')));
  if (!url.pathname.startsWith('/xpath/') || !path.startsWith(publicRoot + sep)) {
    response.writeHead(404).end();
    return;
  }
  try {
    const body = await readFile(path);
    response.writeHead(200, { 'Content-Type': types[extname(path)] || 'text/plain', 'Cache-Control': 'no-store' });
    response.end(body);
  } catch {
    response.writeHead(404).end();
  }
});
await new Promise(resolve => server.listen(0, '127.0.0.1', resolve));
const base = `http://127.0.0.1:${server.address().port}/xpath/stop-load-test/`;
let browser;
const output = [];
try {
  assert.equal((await fetch(base + 'index.html')).status, 200, '测试入口必须存在');
  browser = await chromium.launch({ channel: 'chrome', headless: true });
  const context = await browser.newContext();
  const page = await context.newPage();
  const response = await page.goto(base + 'index.html');
  assert.equal(response.status(), 200, '测试入口必须存在');
  await page.locator('#setup-state[data-state="ready"]').waitFor();
  assert.equal(await page.locator('#start-test').isEnabled(), true);
  output.push({ case: 'worker_ready', result: 'PASS' });

  const session = await context.newCDPSession(page);
  await session.send('Network.enable');
  const requests = new Map();
  const failures = [];
  session.on('Network.requestWillBeSent', event => requests.set(event.requestId, event.request.url));
  session.on('Network.loadingFailed', event => failures.push({ ...event, url: requests.get(event.requestId) }));
  assert.equal(await page.locator('#delay-seconds').inputValue(), '30');
  await Promise.all([
    page.waitForURL(url => url.pathname.endsWith('/loading.html'), { waitUntil: 'domcontentloaded' }),
    page.locator('#start-test').click(),
  ]);
  assert.equal(new URL(page.url()).searchParams.get('delay'), '30000');
  assert(new URL(page.url()).searchParams.get('run'), '每次开始测试须生成 run 标识');
  await page.waitForFunction(() => window.stopLoadTest.getState().heartbeat >= 2);
  const before = await page.evaluate(() => window.stopLoadTest.getState());
  assert.equal(before.controlled, true);
  assert.equal(before.delayMs, 30000);
  assert.equal(before.resourceStatus, 'pending');
  assert.equal(before.readyState, 'interactive');
  assert.equal(before.loadEvents, 0);
  await page.waitForFunction(previous => window.stopLoadTest.getState().heartbeat > previous, before.heartbeat);
  output.push({ case: 'pending_resource_and_live_js', result: 'PASS', before });

  await session.send('Page.stopLoading');
  await page.waitForFunction(() => document.readyState === 'complete');
  const after = await page.evaluate(() => window.stopLoadTest.getState());
  assert.equal(after.resourceLoaded, false);
  assert.equal(after.readyState, 'complete');
  assert(after.elapsedMs < 10000, '停止发生在默认 30 秒响应前');
  assert(failures.some(event => event.url?.includes('slow.svg') && event.canceled && event.errorText === 'net::ERR_ABORTED'),
    '必须独立观察到慢资源请求被取消');
  output.push({ case: 'stop_loading_cancels_request', result: 'PASS', after,
    failures: failures.filter(event => event.url?.includes('slow.svg')) });

  await page.goto(base + 'loading.html?delay=1200&run=natural-case', { waitUntil: 'load' });
  const natural = await page.evaluate(() => window.stopLoadTest.getState());
  assert.equal(natural.resourceLoaded, true);
  assert.equal(natural.resourceStatus, 'loaded');
  assert.equal(natural.loadEvents, 1);
  assert(natural.elapsedMs >= 1100);
  output.push({ case: 'without_stop_resource_completes', result: 'PASS', natural });

  const sibling = await context.newPage();
  await sibling.goto(new URL('../delayed-element.html', base).href);
  assert.equal(await sibling.evaluate(() => navigator.serviceWorker.controller), null);
  await sibling.close();
  output.push({ case: 'scope_isolation', result: 'PASS' });

  await page.goto(base + 'index.html');
  await page.locator('#setup-state[data-state="ready"]').waitFor();
  await page.locator('#cleanup-worker').click();
  await page.locator('#setup-state[data-state="removed"]').waitFor();
  const scopes = await page.evaluate(async () => (await navigator.serviceWorker.getRegistrations()).map(item => item.scope));
  assert(!scopes.includes(base));
  output.push({ case: 'unregister_own_worker', result: 'PASS' });
  console.log(JSON.stringify({ result: 'PASS', checks: output }, null, 2));
} finally {
  await browser?.close();
  server.closeAllConnections();
  await new Promise(resolve => server.close(resolve));
}
