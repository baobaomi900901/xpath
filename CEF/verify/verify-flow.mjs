import assert from 'node:assert/strict';
import { spawn, execFileSync } from 'node:child_process';
import { existsSync, mkdirSync, readFileSync, writeFileSync } from 'node:fs';
import { createServer } from 'node:net';
import { join } from 'node:path';
import { fileURLToPath } from 'node:url';

const root = fileURLToPath(new URL('../', import.meta.url));
const manifest = JSON.parse(readFileSync(join(root, 'versions.json'), 'utf8'));
const majors = process.argv.slice(2).length ? process.argv.slice(2) : Object.keys(manifest);
const useDefault = process.env.XPATH_CEF_DEFAULT === '1';
const base = useDefault ? 'https://baobaomi900901.github.io/xpath/#/' : (process.env.XPATH_CEF_BASE ?? 'http://localhost:7199/');
const routes = ['keys-click-test', 'form-controls', 'iframe-shadow-form'];
const nativeScript = join(root, 'verify', 'native-controls.ps1');
const artifacts = join(root, 'verify', 'artifacts');
mkdirSync(artifacts, { recursive: true });
const delay = ms => new Promise(resolve => setTimeout(resolve, ms));
assert.equal(process.platform, 'win32', 'Run on Windows');

class Cdp {
  sequence = 0;
  pending = new Map();
  constructor(socket) {
    this.socket = socket;
    socket.addEventListener('message', event => {
      const value = JSON.parse(event.data);
      const request = this.pending.get(value.id);
      if (!request) return;
      clearTimeout(request.timer);
      this.pending.delete(value.id);
      if (value.error) request.reject(new Error(value.error.message));
      else request.resolve(value.result);
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
    const id = ++this.sequence;
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
    const value = await this.call('Runtime.evaluate', { expression, returnByValue: true, awaitPromise: true });
    if (value.exceptionDetails) throw new Error(JSON.stringify(value.exceptionDetails));
    return value.result.value;
  }
}

const reports = [];
for (const major of majors) {
  assert.ok(manifest[major], `Unsupported major: ${major}`);
  const exe = join(root, 'dist', major, `cef-shooting-range-${major}.exe`);
  assert.ok(existsSync(exe), `Build this executable first: ${exe}`);
  const server = createServer();
  await new Promise(resolve => server.listen(0, '127.0.0.1', resolve));
  const port = server.address().port;
  await new Promise(resolve => server.close(resolve));
  const app = spawn(exe, [...(useDefault ? [] : [`--base-url=${base}`]), `--remote-debugging-port=${port}`], {
    cwd: join(root, 'dist', major), stdio: 'ignore', windowsHide: false,
  });
  let childError;
  app.on('error', error => { childError = error; });
  let cdp;
  const passed = [];
  function pass(name) { passed.push(name); console.log(`PASS CEF ${major}: ${name}`); }
  async function until(label, predicate, timeout = 45000) {
    const end = Date.now() + timeout;
    let lastError;
    while (Date.now() < end) {
      if (childError) throw childError;
      if (app.exitCode !== null) throw new Error(`CEF ${major} exited: ${app.exitCode}`);
      try { const result = await predicate(); if (result) return result; }
      catch (error) { lastError = error; }
      await delay(200);
    }
    throw new Error(`Timed out: ${label}${lastError ? ` (${lastError.message})` : ''}`);
  }
  function native(action = 'Inspect', index = 0) {
    const value = execFileSync('powershell.exe', [
      '-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', nativeScript,
      '-ProcessId', String(app.pid), '-Action', action, '-Index', String(index),
    ], { encoding: 'utf8', timeout: 15000, windowsHide: true });
    return action === 'Close' ? null : JSON.parse(value.trim());
  }
  async function waitPage(index, selector) {
    const url = base.replace(/\/?$/, '/') + routes[index];
    await until(url, () => cdp.evaluate(
      `location.href === ${JSON.stringify(url)} && !!document.querySelector(${JSON.stringify(selector)})`,
    ));
    const state = native();
    assert.equal(state.selected, index);
    assert.equal(state.address, url);
    assert.equal(state.refreshEnabled, true);
    assert.ok(!state.status.includes('失败'), state.status);
  }
  async function typeInto(expression, text) {
    assert.ok(await cdp.evaluate(`(() => { const e = ${expression}; if (!e) return false; e.scrollIntoView({block:'center'}); e.focus(); return true; })()`));
    await cdp.call('Input.insertText', { text });
    assert.equal(await cdp.evaluate(`(${expression}).value`), text);
  }
  try {
    const target = await until('CEF CDP target', async () => {
      const response = await fetch(`http://127.0.0.1:${port}/json/list`, { signal: AbortSignal.timeout(2000) });
      const targets = await response.json();
      return targets.find(item => item.type === 'page' && item.webSocketDebuggerUrl);
    });
    cdp = await Cdp.connect(target.webSocketDebuggerUrl);
    await cdp.call('Page.enable');
    const version = await cdp.call('Browser.getVersion');
    assert.ok(version.product.endsWith('/' + manifest[major].chromium_version), version.product);
    await waitPage(0, '#btn-click-target');
    assert.deepEqual(native().items, ['点击测试', '表单测试', 'iframe表单']);
    assert.ok(native().title.includes(`CEF ${major}`));
    pass('exact Chromium version, default route and three native menu items');

    const button = await cdp.evaluate(`(() => {
      const e = document.querySelector('#btn-click-target'); e.scrollIntoView({block:'center'});
      const r = e.getBoundingClientRect(); return {x:r.x+r.width/2,y:r.y+r.height/2};
    })()`);
    await cdp.call('Input.dispatchMouseEvent', { type: 'mousePressed', ...button, button: 'left', clickCount: 1 });
    await cdp.call('Input.dispatchMouseEvent', { type: 'mouseReleased', ...button, button: 'left', clickCount: 1 });
    await until('trusted click log', () => cdp.evaluate(`document.body.innerText.includes('真实鼠标') && document.querySelectorAll('tbody tr').length > 0`));
    pass('trusted click recorded');

    native('KeyNext');
    const inputSelector = 'input:not([disabled]):not([readonly]):not([type="checkbox"]):not([type="radio"])';
    await waitPage(1, inputSelector);
    await typeInto(`document.querySelector(${JSON.stringify(inputSelector)})`, `cef-${major}-form`);
    pass('native keyboard menu and form input');

    native('Select', 2);
    await waitPage(2, '#iframe-shadow-form');
    const shadow = `document.querySelector('#iframe-shadow-form').contentDocument.querySelector('#form-shadow-host').shadowRoot`;
    await until('iframe Shadow DOM', () => cdp.evaluate(`!!(${shadow})?.querySelector(${JSON.stringify(inputSelector)})`));
    await typeInto(`(${shadow}).querySelector(${JSON.stringify(inputSelector)})`, `cef-${major}-iframe`);
    pass('native menu and iframe Shadow DOM form input');

    const before = await cdp.evaluate('({width:innerWidth,height:innerHeight})');
    native('Resize');
    await until('viewport resize', async () => {
      const size = await cdp.evaluate('({width:innerWidth,height:innerHeight})');
      return size.width < before.width && size.height < before.height;
    });
    pass('embedded browser follows native resize');
    await cdp.evaluate("window.__cefRefreshProbe = true; sessionStorage.setItem('cef-refresh-check', 'kept')");
    native('Refresh');
    await until('refresh', () => cdp.evaluate("window.__cefRefreshProbe === undefined && sessionStorage.getItem('cef-refresh-check') === 'kept'"));
    await waitPage(2, '#iframe-shadow-form');
    pass('refresh retains selected route');

    await cdp.call('Accessibility.enable');
    const accessibility = await cdp.call('Accessibility.getFullAXTree');
    assert.ok(accessibility.nodes.some(node => node.role?.value === 'RootWebArea'));
    pass('renderer accessibility tree available');

    await cdp.call('Runtime.evaluate', {
      expression: "window.open('about:blank', '_blank')", userGesture: true,
    });
    await delay(500);
    const popupTargets = await (await fetch(`http://127.0.0.1:${port}/json/list`)).json();
    assert.equal(popupTargets.filter(item => item.type === 'page').length, 1, 'Popup must not replace embedded browser');
    await waitPage(2, '#iframe-shadow-form');
    pass('popup cannot replace the embedded browser');
    const screenshot = await cdp.call('Page.captureScreenshot', { format: 'png' });
    writeFileSync(join(artifacts, `cef-${major}${useDefault ? '-hosted' : ''}-iframe.png`), Buffer.from(screenshot.data, 'base64'));
    cdp.socket.close();
    native('Close');
    await new Promise((resolve, reject) => {
      if (app.exitCode !== null) return resolve();
      const timer = setTimeout(() => reject(new Error('CEF application did not close')), 10000);
      app.once('exit', () => { clearTimeout(timer); resolve(); });
    });
    assert.equal(app.exitCode, 0);
    pass('graceful native close');
    reports.push({ major, product: version.product, base, passed });
  } finally {
    cdp?.socket.close();
    if (app.exitCode === null && !childError) {
      try { native('Close'); } catch { app.kill(); }
      const exited = await Promise.race([new Promise(resolve => app.once('exit', () => resolve(true))), delay(3000).then(() => false)]);
      if (!exited && app.exitCode === null) app.kill();
    }
  }
}
writeFileSync(join(artifacts, useDefault ? 'results-hosted.json' : 'results.json'), JSON.stringify({ timestamp: new Date().toISOString(), reports }, null, 2));
console.log(`Verified ${reports.length} CEF versions; ${reports.reduce((sum, report) => sum + report.passed.length, 0)} checks passed.`);
