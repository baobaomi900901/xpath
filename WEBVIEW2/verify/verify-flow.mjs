import assert from 'node:assert/strict';
import { spawn, execFileSync } from 'node:child_process';
import { existsSync, mkdirSync, mkdtempSync, writeFileSync } from 'node:fs';
import { createServer } from 'node:net';
import { join } from 'node:path';
import { fileURLToPath } from 'node:url';

const executable = fileURLToPath(new URL('../build/Release/webview2-shooting-range.exe', import.meta.url));
assert.ok(existsSync(executable), `Executable missing: ${executable}`);
assert.equal(process.platform, 'win32', 'Run this verification on Windows');
const nativeScript = fileURLToPath(new URL('./native-controls.ps1', import.meta.url));
const artifacts = fileURLToPath(new URL('./artifacts/', import.meta.url));
mkdirSync(artifacts, { recursive: true });
const profile = mkdtempSync(join(artifacts, 'profile-'));
const server = createServer();
await new Promise(resolve => server.listen(0, '127.0.0.1', resolve));
const port = server.address().port;
await new Promise(resolve => server.close(resolve));
const app = spawn(executable, [], {
  env: {
    ...process.env,
    WEBVIEW2_ADDITIONAL_BROWSER_ARGUMENTS: `--remote-debugging-port=${port} --remote-debugging-address=127.0.0.1`,
    WEBVIEW2_USER_DATA_FOLDER: profile,
  },
  stdio: 'ignore',
});
let cdp;
let childError;
app.on('error', error => { childError = error; });
const delay = ms => new Promise(resolve => setTimeout(resolve, ms));
async function until(label, predicate, timeout = 45000) {
  const end = Date.now() + timeout;
  let lastError;
  while (Date.now() < end) {
    if (childError) throw childError;
    if (app.exitCode !== null) throw new Error(`Application exited: ${app.exitCode}`);
    try { const value = await predicate(); if (value) return value; }
    catch (error) { lastError = error; }
    await delay(200);
  }
  throw new Error(`Timed out: ${label}${lastError ? ` (${lastError.message})` : ''}`);
}
function native(action = 'Inspect', index = 0) {
  const output = execFileSync('powershell.exe', [
    '-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', nativeScript,
    '-ProcessId', String(app.pid), '-Action', action, '-Index', String(index),
  ], { encoding: 'utf8', timeout: 15000, windowsHide: true });
  return action === 'Close' ? null : JSON.parse(output.trim());
}
class Cdp {
  next = 0;
  pending = new Map();
  constructor(socket) {
    this.socket = socket;
    socket.addEventListener('message', event => {
      const message = JSON.parse(event.data);
      const request = this.pending.get(message.id);
      if (!request) return;
      clearTimeout(request.timer);
      this.pending.delete(message.id);
      if (message.error) request.reject(new Error(message.error.message));
      else request.resolve(message.result);
    });
    socket.addEventListener('close', () => {
      for (const request of this.pending.values()) {
        clearTimeout(request.timer);
        request.reject(new Error('CDP connection closed'));
      }
      this.pending.clear();
    });
  }
  static async connect(url) {
    const socket = new WebSocket(url);
    await new Promise((resolve, reject) => {
      socket.addEventListener('open', resolve, { once: true });
      socket.addEventListener('error', reject, { once: true });
    });
    return new Cdp(socket);
  }
  call(method, params = {}) {
    const id = ++this.next;
    return new Promise((resolve, reject) => {
      const timer = setTimeout(() => {
        this.pending.delete(id);
        reject(new Error(`CDP timeout: ${method}`));
      }, 15000);
      this.pending.set(id, { resolve, reject, timer });
      this.socket.send(JSON.stringify({ id, method, params }));
    });
  }
  async evaluate(expression) {
    const result = await this.call('Runtime.evaluate', { expression, returnByValue: true, awaitPromise: true });
    if (result.exceptionDetails) throw new Error(JSON.stringify(result.exceptionDetails));
    return result.result.value;
  }
}
const urls = [
  'https://baobaomi900901.github.io/xpath/#/keys-click-test',
  'https://baobaomi900901.github.io/xpath/#/form-controls',
  'https://baobaomi900901.github.io/xpath/#/iframe-shadow-form',
];
const results = [];
function pass(name) { results.push(name); console.log(`PASS ${name}`); }
async function waitPage(index, selector) {
  await until(urls[index], () => cdp.evaluate(
    `location.href === ${JSON.stringify(urls[index])} && !!document.querySelector(${JSON.stringify(selector)})`,
  ));
  const state = native();
  assert.equal(state.selected, index);
  assert.equal(state.address, urls[index]);
  assert.equal(state.refreshEnabled, true);
  assert.ok(!state.status.includes('失败'), state.status);
}
async function typeInto(expression, text) {
  assert.ok(await cdp.evaluate(`(() => { const e = ${expression}; if (!e) return false; e.scrollIntoView({block:'center'}); e.focus(); return true; })()`));
  await cdp.call('Input.insertText', { text });
  assert.equal(await cdp.evaluate(`(${expression}).value`), text);
}
try {
  const target = await until('WebView2 CDP target', async () => {
    const response = await fetch(`http://127.0.0.1:${port}/json/list`, { signal: AbortSignal.timeout(2000) });
    const targets = await response.json();
    return targets.find(item => item.type === 'page' && item.webSocketDebuggerUrl);
  });
  cdp = await Cdp.connect(target.webSocketDebuggerUrl);
  await cdp.call('Page.enable');
  await waitPage(0, 'button');
  assert.deepEqual(native().items, ['点击测试', '表单测试', 'iframe表单']);
  pass('default page and three native menu items');

  const button = await cdp.evaluate(`(() => {
    const e = document.querySelector('#btn-click-target');
    if (!e) return null; e.scrollIntoView({block:'center'});
    const r = e.getBoundingClientRect(); return {x:r.x+r.width/2, y:r.y+r.height/2};
  })()`);
  assert.ok(button, 'Click test button exists');
  await cdp.call('Input.dispatchMouseEvent', { type: 'mousePressed', ...button, button: 'left', clickCount: 1 });
  await cdp.call('Input.dispatchMouseEvent', { type: 'mouseReleased', ...button, button: 'left', clickCount: 1 });
  await until('trusted click recorded', () => cdp.evaluate(`document.body.innerText.includes('真实鼠标') && document.querySelectorAll('tbody tr').length > 0`));
  pass('click interaction recorded in real WebView2');

  native('KeyNext');
  await waitPage(1, 'input:not([disabled]):not([readonly]):not([type="checkbox"]):not([type="radio"])');
  await typeInto(`document.querySelector('input:not([disabled]):not([readonly]):not([type="checkbox"]):not([type="radio"])')`, 'webview2-form-check');
  pass('native keyboard menu selection and form input');

  native('Select', 2);
  await waitPage(2, '#iframe-shadow-form');
  const shadow = `document.querySelector('#iframe-shadow-form').contentDocument.querySelector('#form-shadow-host').shadowRoot`;
  await until('iframe Shadow DOM form', () => cdp.evaluate(`!!(${shadow})?.querySelector('input:not([disabled]):not([readonly]):not([type="checkbox"]):not([type="radio"])')`));
  await typeInto(`(${shadow}).querySelector('input:not([disabled]):not([readonly]):not([type="checkbox"]):not([type="radio"])')`, 'webview2-iframe-check');
  pass('iframe and Shadow DOM form input');

  const before = await cdp.evaluate('({width:innerWidth,height:innerHeight})');
  native('Resize');
  const after = await until('WebView2 resized with native window', async () => {
    const size = await cdp.evaluate('({width:innerWidth,height:innerHeight})');
    return size.width < before.width && size.height < before.height && size;
  });
  native('MinimizeRestore');
  await until('restored viewport', () => cdp.evaluate(`innerWidth === ${after.width} && innerHeight === ${after.height}`));
  pass('native window resize and minimize/restore');

  await cdp.evaluate(`sessionStorage.setItem('xpath-webview2-verification', 'preserved'); window.__verifyRefresh = true`);
  native('Refresh');
  await until('refresh executed', () => cdp.evaluate(`window.__verifyRefresh === undefined && sessionStorage.getItem('xpath-webview2-verification') === 'preserved'`));
  await waitPage(2, '#iframe-shadow-form');
  pass('native refresh reloads the current route');

  await cdp.call('Network.enable');
  await cdp.call('Network.emulateNetworkConditions', { offline: true, latency: 0, downloadThroughput: 0, uploadThroughput: 0 });
  native('Refresh');
  await until('offline error feedback', () => native().status.includes('失败'));
  assert.equal(native().refreshEnabled, true);
  await cdp.call('Network.emulateNetworkConditions', { offline: false, latency: 0, downloadThroughput: -1, uploadThroughput: -1 });
  native('Refresh');
  await waitPage(2, '#iframe-shadow-form');
  pass('navigation error feedback and refresh recovery');

  const screenshot = await cdp.call('Page.captureScreenshot', { format: 'png' });
  writeFileSync(join(artifacts, 'webview2-iframe.png'), Buffer.from(screenshot.data, 'base64'));
  cdp.socket.close();
  native('Close');
  await new Promise((resolve, reject) => {
    if (app.exitCode !== null) return resolve();
    const timer = setTimeout(() => reject(new Error('Application did not close')), 5000);
    app.once('exit', () => { clearTimeout(timer); resolve(); });
  });
  assert.equal(app.exitCode, 0);
  pass('native close exits cleanly');
  writeFileSync(join(artifacts, 'results.json'), JSON.stringify({ passed: results, timestamp: new Date().toISOString() }, null, 2));
} finally {
  cdp?.socket.close();
  if (app.exitCode === null && !childError) {
    try { native('Close'); } catch { app.kill(); }
    const exited = await Promise.race([new Promise(resolve => app.once('exit', () => resolve(true))), delay(3000).then(() => false)]);
    if (!exited && app.exitCode === null) app.kill();
  }
}
