import assert from 'node:assert/strict';
import { spawn, execFileSync } from 'node:child_process';
import { existsSync, mkdirSync, readFileSync, writeFileSync } from 'node:fs';
import { createServer } from 'node:net';
import { join } from 'node:path';
import { fileURLToPath } from 'node:url';

const root = fileURLToPath(new URL('../', import.meta.url));
const manifest = JSON.parse(readFileSync(join(root, 'versions.json'), 'utf8'));
const majors = process.argv.slice(2).length ? process.argv.slice(2) : ['22', '29', '38', '44'];
const useDefault = process.env.XPATH_ELECTRON_DEFAULT === '1';
const base = useDefault ? 'https://baobaomi900901.github.io/xpath/#/' : (process.env.XPATH_ELECTRON_BASE ?? 'http://localhost:7199/');
const routes = ['keys-click-test', 'form-controls', 'iframe-shadow-form'];
const labels = ['点击测试', '表单测试', 'iframe表单'];
const artifacts = join(root, 'verify', 'artifacts');
mkdirSync(artifacts, { recursive: true });
assert.equal(process.platform, 'win32', 'Run on Windows');
const delay = ms => new Promise(resolve => setTimeout(resolve, ms));

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
      value.error ? request.reject(new Error(value.error.message)) : request.resolve(value.result);
    });
    socket.addEventListener('close', () => {
      for (const request of this.pending.values()) { clearTimeout(request.timer); request.reject(new Error('CDP closed')); }
      this.pending.clear();
    });
  }
  static async connect(url) {
    const socket = new WebSocket(url);
    await new Promise((resolve, reject) => {
      const timer = setTimeout(() => { socket.close(); reject(new Error('CDP connect timeout')); }, 10000);
      socket.addEventListener('open', () => { clearTimeout(timer); resolve(); }, { once: true });
      socket.addEventListener('error', error => { clearTimeout(timer); reject(error); }, { once: true });
    });
    return new Cdp(socket);
  }
  call(method, params = {}) {
    const id = ++this.sequence;
    return new Promise((resolve, reject) => {
      const timer = setTimeout(() => { this.pending.delete(id); reject(new Error(`CDP timeout: ${method}`)); }, 15000);
      this.pending.set(id, { resolve, reject, timer });
      this.socket.send(JSON.stringify({ id, method, params }));
    });
  }
  async evaluate(expression) {
    const result = await this.call('Runtime.evaluate', { expression, returnByValue: true, awaitPromise: true });
    if (result.exceptionDetails) throw new Error(JSON.stringify(result.exceptionDetails));
    return result.result.value;
  }
  async click(expression) {
    const point = await this.evaluate(`(() => { const e = ${expression}; if (!e) throw new Error('Missing click target'); e.scrollIntoView({block:'center'}); const r = e.getBoundingClientRect(); return {x:r.x+r.width/2,y:r.y+r.height/2}; })()`);
    await this.call('Input.dispatchMouseEvent', { type: 'mousePressed', ...point, button: 'left', clickCount: 1 });
    await this.call('Input.dispatchMouseEvent', { type: 'mouseReleased', ...point, button: 'left', clickCount: 1 });
  }
}

async function freePort() {
  const server = createServer();
  await new Promise((resolve, reject) => { server.once('error', reject); server.listen(0, '127.0.0.1', resolve); });
  const port = server.address().port;
  await new Promise(resolve => server.close(resolve));
  return port;
}

const reports = [];
for (const major of majors) {
  const entry = manifest[major];
  assert.ok(entry, `Unsupported major ${major}`);
  const exe = join(root, 'dist', major, `electron-shooting-range-${major}.exe`);
  assert.ok(existsSync(exe), `Build this executable first: ${exe}`);
  const runtime = JSON.parse(readFileSync(join(root, 'dist', major, 'version.json'), 'utf8'));
  const port = await freePort();
  const env = { ...process.env };
  delete env.ELECTRON_RUN_AS_NODE;
  const app = spawn(exe, [...(useDefault ? [] : [`--base-url=${base}`]), `--remote-debugging-port=${port}`], {
    cwd: join(root, 'dist', major), stdio: ['ignore', 'ignore', 'pipe'], windowsHide: false, env,
  });
  let processError, stderr = '', host, guest, nativeApi;
  app.on('error', error => { processError = error; });
  app.stderr.on('data', bytes => { stderr = (stderr + bytes.toString()).slice(-10000); });
  const passed = [];
  const suffix = useDefault ? '-hosted' : '';
  const pass = name => { passed.push(name); console.log(`PASS Electron ${major}: ${name}`); };
  async function until(label, predicate, timeout = 45000) {
    const end = Date.now() + timeout;
    let lastError;
    while (Date.now() < end) {
      if (processError) throw processError;
      if (app.exitCode !== null) throw new Error(`Electron ${major} exited ${app.exitCode}: ${stderr}`);
      try { const value = await predicate(); if (value) return value; } catch (error) { lastError = error; }
      await delay(150);
    }
    throw new Error(`Timed out: ${label} ${lastError?.message ?? ''}\n${stderr}`);
  }
  const targets = async () => (await fetch(`http://127.0.0.1:${port}/json/list`, { signal: AbortSignal.timeout(2000) })).json();
  function native(action) {
    const output = execFileSync('powershell.exe', ['-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', join(root, 'verify', 'window.ps1'), '-ProcessId', String(app.pid), '-Action', action], { encoding: 'utf8', timeout: 30000, windowsHide: true });
    return action === 'Close' ? null : JSON.parse(output.trim());
  }
  async function waitPage(index, selector) {
    const url = base + routes[index];
    await until(url, () => guest.evaluate(`location.href === ${JSON.stringify(url)} && !!document.querySelector(${JSON.stringify(selector)})`));
    await until('host address/status', () => host.evaluate(`document.querySelector('#address').value === ${JSON.stringify(url)} && document.querySelector('#menu-${index}').getAttribute('aria-selected') === 'true' && document.querySelector('#status').textContent.startsWith('就绪')`));
  }
  async function typeInto(expression, text) {
    assert.ok(await guest.evaluate(`(() => { const e = ${expression}; if (!e) return false; e.scrollIntoView({block:'center'}); e.focus(); return true; })()`));
    await guest.call('Input.insertText', { text });
    assert.equal(await guest.evaluate(`(${expression}).value`), text);
  }
  async function screenshot(cdp, name) {
    const result = await cdp.call('Page.captureScreenshot', { format: 'png' });
    writeFileSync(join(artifacts, `electron-${major}${suffix}-${name}.png`), Buffer.from(result.data, 'base64'));
  }
  try {
    const hostTarget = await until('shell target', async () => (await targets()).find(t => t.type === 'page' && t.url.endsWith('/shell.html')));
    host = await Cdp.connect(hostTarget.webSocketDebuggerUrl);
    const guestTarget = await until('embedded target', async () => (await targets()).find(t => t.type === 'page' && t.id !== hostTarget.id && t.url.startsWith(base)));
    guest = await Cdp.connect(guestTarget.webSocketDebuggerUrl);
    await guest.call('Page.enable');
    const state = await host.evaluate('window.electronRange.getState()');
    assert.deepEqual(state.runtime, runtime);
    const version = await guest.call('Browser.getVersion');
    assert.ok(version.product.endsWith('/' + runtime.chromium), version.product);
    assert.equal(state.mode, ['22', '29'].includes(major) ? 'BrowserView' : 'WebContentsView');
    assert.deepEqual(await host.evaluate("[...document.querySelectorAll('#menu [data-index]')].map(e=>e.textContent)"), labels);
    const windowInfo = native('Inspect');
    assert.ok(windowInfo.title.includes(`Electron ${major}`), JSON.stringify(windowInfo));
    for (const value of [runtime.electron, runtime.chromium, runtime.node]) assert.ok(windowInfo.title.includes(value), windowInfo.title);
    await waitPage(0, '#btn-click-target');
    pass('exact runtime, embedding mode and default route');
    assert.equal(await guest.evaluate('typeof require'), 'undefined');
    assert.equal(await guest.evaluate('typeof window.electronRange'), 'undefined');
    pass('remote page has no Node or host bridge');
    await guest.click("document.querySelector('#btn-click-target')");
    await until('trusted click', () => guest.evaluate("document.querySelector('tbody')?.innerText.includes('真实鼠标')"));
    pass('trusted mouse click recorded');

    if (!useDefault) {
      const uia = native('Accessibility');
      writeFileSync(join(artifacts, `electron-${major}-uia.json`), JSON.stringify(uia, null, 2));
      assert.ok(uia.nodes.length > 0, 'Native UIA window tree missing');
      let tree = uia;
      nativeApi = 'UIA';
      if (!uia.nodes.some(n => n.name === '单击触发')) {
        tree = native('Msaa');
        nativeApi = 'MSAA';
        writeFileSync(join(artifacts, `electron-${major}-msaa.json`), JSON.stringify(tree, null, 2));
      }
      for (const label of labels) assert.ok(tree.nodes.some(n => n.name === label), `${nativeApi} menu missing ${label}`);
      assert.ok(tree.nodes.some(n => n.name === '单击触发'), `${nativeApi} guest button missing`);
      pass(`Windows ${nativeApi} exposes host menu and guest button`);
    }
    await screenshot(host, 'shell');
    await host.click("document.querySelector('#menu-0')");
    await until('initial route after menu click', () => host.evaluate("document.querySelector('#menu-0').getAttribute('aria-selected') === 'true'"));
    await host.call('Input.dispatchKeyEvent', { type: 'keyDown', key: 'ArrowDown', code: 'ArrowDown', windowsVirtualKeyCode: 40 });
    await host.call('Input.dispatchKeyEvent', { type: 'keyUp', key: 'ArrowDown', code: 'ArrowDown', windowsVirtualKeyCode: 40 });
    const input = 'input:not([disabled]):not([readonly]):not([type="checkbox"]):not([type="radio"])';
    await waitPage(1, input);
    await typeInto(`document.querySelector(${JSON.stringify(input)})`, `electron-${major}-form`);
    pass('keyboard menu navigation and form input');
    await host.click("document.querySelector('#menu-2')");
    await waitPage(2, '#iframe-shadow-form');
    const shadow = "document.querySelector('#iframe-shadow-form').contentDocument.querySelector('#form-shadow-host').shadowRoot";
    await until('iframe Shadow DOM', () => guest.evaluate(`!!(${shadow})?.querySelector(${JSON.stringify(input)})`));
    await typeInto(`(${shadow}).querySelector(${JSON.stringify(input)})`, `electron-${major}-iframe`);
    pass('mouse menu navigation and iframe Shadow DOM input');
    const before = await guest.evaluate('({width:innerWidth,height:innerHeight})');
    native('Resize');
    await until('resize', async () => {
      const after = await guest.evaluate('({width:innerWidth,height:innerHeight})');
      return after.width < before.width && after.height < before.height;
    });
    const bounds = await host.evaluate("(() => { const r = document.querySelector('#browser-placeholder').getBoundingClientRect(); return {width:r.width,height:r.height}; })()");
    const viewport = await guest.evaluate('({width:innerWidth,height:innerHeight})');
    // Windows DPI scaling can produce fractional CSS dimensions; Electron views use integer DIP bounds.
    for (const axis of ['width', 'height']) assert.ok(Math.abs(viewport[axis] - bounds[axis]) <= 1, JSON.stringify({ viewport, bounds }));
    pass('view follows window resizing with matching bounds');
    await guest.evaluate("window.__refreshProbe = true; sessionStorage.setItem('range-refresh', 'kept')");
    await host.click("document.querySelector('#refresh')");
    await until('refresh', () => guest.evaluate("window.__refreshProbe === undefined && sessionStorage.getItem('range-refresh') === 'kept'"));
    await waitPage(2, '#iframe-shadow-form');
    pass('refresh retains route and session');
    await guest.call('Accessibility.enable');
    const ax = await guest.call('Accessibility.getFullAXTree');
    assert.ok(ax.nodes.some(n => n.role?.value === 'RootWebArea'));
    pass('Chromium accessibility tree available');
    await guest.call('Runtime.evaluate', { expression: "window.open('about:blank', '_blank')", userGesture: true });
    await delay(300);
    assert.equal((await targets()).filter(t => t.type === 'page').length, 2);
    pass('extra browser window blocked');
    await screenshot(guest, 'iframe');

    if (!useDefault) {
      const unusedPort = await freePort();
      await guest.call('Page.navigate', { url: `http://127.0.0.1:${unusedPort}/` });
      await until('network error status', () => host.evaluate("document.querySelector('#status').textContent.startsWith('加载失败')"));
      await host.click("document.querySelector('#menu-0')");
      await waitPage(0, '#btn-click-target');
      pass('load failure reported and menu recovers');
    }
    host.socket.close(); guest.socket.close();
    native('Close');
    await new Promise((resolve, reject) => {
      if (app.exitCode !== null) return resolve();
      const timer = setTimeout(() => reject(new Error('Window did not close')), 10000);
      app.once('exit', () => { clearTimeout(timer); resolve(); });
    });
    assert.equal(app.exitCode, 0);
    pass('graceful close');
    reports.push({ major, runtime, mode: state.mode, nativeApi, profile: state.profile, base, passed });
  } catch (error) {
    for (const [cdp, name] of [[host, 'failure-shell'], [guest, 'failure-page']]) {
      if (cdp?.socket.readyState === WebSocket.OPEN) try { await screenshot(cdp, name); } catch { }
    }
    writeFileSync(join(artifacts, `electron-${major}${suffix}-failure.txt`), `${error.stack}\n${stderr}`);
    throw error;
  } finally {
    host?.socket.close(); guest?.socket.close();
    if (app.exitCode === null && !processError) {
      try { native('Close'); } catch { app.kill(); }
      await Promise.race([new Promise(resolve => app.once('exit', resolve)), delay(3000)]);
      if (app.exitCode === null) app.kill();
    }
  }
}
assert.equal(new Set(reports.map(r => r.profile)).size, reports.length);
writeFileSync(join(artifacts, useDefault ? 'results-hosted.json' : 'results.json'), JSON.stringify({ timestamp: new Date().toISOString(), reports }, null, 2));
console.log(`Verified ${reports.length} Electron versions; ${reports.reduce((sum, r) => sum + r.passed.length, 0)} checks passed.`);
