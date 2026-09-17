// Excel 插件靶场验收脚本(零依赖):
//   1) 静态契约: 通过 HTTPS 拉取页面, 校验元素契约 / 文案 / 凭据 / 无持久化存储 / manifest
//   2) 真实浏览器: 用 CDP 驱动本机 Chrome 或 Edge, 真实点击走完 登录 -> 已登录 -> 菜单 -> 退出登录
//
// 用法: 先启动服务 `python tools/start_excel_addin.py --no-launch`, 再运行
//   node OFFICE/excel-addin/verify/verify-flow.mjs
// 可用环境变量: XPATH_ADDIN_BASE(默认 https://localhost:7300)、XPATH_ADDIN_BROWSER(浏览器可执行文件)

import { spawn } from 'node:child_process';
import { existsSync, mkdtempSync, rmSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import path from 'node:path';
import process from 'node:process';
import { fileURLToPath } from 'node:url';

const HERE = path.dirname(fileURLToPath(import.meta.url));
const BASE = process.env.XPATH_ADDIN_BASE ?? 'https://localhost:7300';
const DEBUG_PORT = Number(process.env.XPATH_ADDIN_DEBUG_PORT ?? 9333);

// 本脚本只针对本机自签 localhost 服务; 证书已装入 CurrentUser\Root, 这里再兜底一次。
process.env.NODE_TLS_REJECT_UNAUTHORIZED = '0';

const results = [];
let failed = 0;

function check(name, condition, detail = '') {
  const ok = Boolean(condition);
  if (!ok) failed += 1;
  results.push({ name, ok });
  console.log(`${ok ? '  ok  ' : ' FAIL '} ${name}${detail ? `  [${detail}]` : ''}`);
}

const wait = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

// ---------------------------------------------------------------- 静态契约

const REQUIRED_IDS = [
  'login-trigger', 'login-dialog', 'login-form', 'username-input', 'password-input',
  'login-submit', 'login-cancel', 'login-error', 'login-status',
  'user-menu', 'user-menu-trigger', 'user-menu-name', 'logout-item'
];

async function verifyStaticContract() {
  console.log('\n== 静态契约 ==');
  const page = await fetch(`${BASE}/src/taskpane.html`);
  check('taskpane.html 返回 200', page.status === 200, `status=${page.status}`);
  check('taskpane.html 带 Cache-Control: no-store',
    (page.headers.get('cache-control') ?? '').includes('no-store'));

  const html = await page.text();
  for (const id of REQUIRED_IDS) {
    check(`元素契约 ${id}`,
      html.includes(`id="${id}"`) && html.includes(`data-testid="${id}"`));
  }
  for (const text of ['点击登录', '退出登录', '已登录', '账号或密码错误']) {
    check(`文案 ${text}`, html.includes(text));
  }
  check('密码框 type=password', html.includes('type="password"'));

  const script = await (await fetch(`${BASE}/src/taskpane.js`)).text();
  check("凭据 admin", script.includes("EXPECTED_USERNAME = 'admin'"));
  check("凭据 1", script.includes("EXPECTED_PASSWORD = '1'"));
  check('未持久化登录态', !script.includes('localStorage') && !script.includes('sessionStorage'));

  const manifest = await (await fetch(`${BASE}/manifest.xml`)).text();
  for (const text of ['Excel 靶场插件', '登录靶场', '打开面板']) {
    check(`manifest 文案 ${text}`, manifest.includes(text));
  }
  check('manifest 自定义选项卡', manifest.includes('XPathTab') || manifest.includes('XPathRangeTab'));

  for (const asset of ['assets/icon-16.png', 'assets/icon-32.png', 'assets/icon-80.png', 'src/commands.html']) {
    const response = await fetch(`${BASE}/${asset}`);
    check(`资源 ${asset}`, response.ok, `status=${response.status}`);
  }
}

// ---------------------------------------------------------------- CDP 客户端

class Cdp {
  #socket;
  #nextId = 1;
  #pending = new Map();
  #handlers = new Map();
  sessionId = null;

  constructor(socket) {
    this.#socket = socket;
    socket.addEventListener('message', (event) => this.#onMessage(event.data));
  }

  static async connect(url) {
    const socket = new WebSocket(url);
    await new Promise((resolve, reject) => {
      socket.addEventListener('open', resolve, { once: true });
      socket.addEventListener('error', () => reject(new Error(`WebSocket 连接失败: ${url}`)), { once: true });
    });
    return new Cdp(socket);
  }

  #onMessage(raw) {
    const message = JSON.parse(raw);
    if (message.id && this.#pending.has(message.id)) {
      const { resolve, reject } = this.#pending.get(message.id);
      this.#pending.delete(message.id);
      if (message.error) reject(new Error(message.error.message));
      else resolve(message.result);
      return;
    }
    for (const handler of this.#handlers.get(message.method) ?? []) handler(message.params);
  }

  send(method, params = {}, useSession = true) {
    const id = this.#nextId++;
    const payload = { id, method, params };
    if (useSession && this.sessionId) payload.sessionId = this.sessionId;
    return new Promise((resolve, reject) => {
      this.#pending.set(id, { resolve, reject });
      this.#socket.send(JSON.stringify(payload));
    });
  }

  close() {
    this.#socket.close();
  }
}

function findBrowser() {
  const candidates = [
    process.env.XPATH_ADDIN_BROWSER,
    'C:/Program Files/Google/Chrome/Application/chrome.exe',
    'C:/Program Files (x86)/Google/Chrome/Application/chrome.exe',
    process.env.LOCALAPPDATA && path.join(process.env.LOCALAPPDATA, 'Google/Chrome/Application/chrome.exe'),
    'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe',
    'C:/Program Files/Microsoft/Edge/Application/msedge.exe'
  ].filter(Boolean);
  return candidates.find((candidate) => existsSync(candidate)) ?? null;
}

async function waitForDevTools() {
  const deadline = Date.now() + 20000;
  while (Date.now() < deadline) {
    try {
      const response = await fetch(`http://127.0.0.1:${DEBUG_PORT}/json/version`);
      if (response.ok) return await response.json();
    } catch {
      // 浏览器还没起来
    }
    await wait(250);
  }
  throw new Error('等待 DevTools 端口超时');
}

// ---------------------------------------------------------------- 浏览器流程

const SNAPSHOT = `(() => {
  const visible = (el) => {
    if (!el) return false;
    const rect = el.getBoundingClientRect();
    return !el.hidden && rect.width > 0 && rect.height > 0;
  };
  const text = (id) => (document.getElementById(id)?.textContent ?? '').trim();
  const name = document.getElementById('user-menu-name');
  const caret = document.querySelector('#user-menu-trigger .caret');
  return {
    loginTriggerVisible: visible(document.getElementById('login-trigger')),
    loginTriggerText: text('login-trigger'),
    dialogVisible: visible(document.getElementById('login-dialog')),
    statusVisible: visible(document.getElementById('login-status')),
    statusText: text('login-status'),
    userMenuTriggerVisible: visible(document.getElementById('user-menu-trigger')),
    userMenuTriggerText: text('user-menu-trigger'),
    userMenuNameText: text('user-menu-name'),
    userMenuVisible: visible(document.getElementById('user-menu')),
    userMenuText: text('user-menu'),
    errorVisible: visible(document.getElementById('login-error')),
    errorText: text('login-error'),
    ariaExpanded: document.getElementById('user-menu-trigger')?.getAttribute('aria-expanded') ?? null,
    passwordType: document.getElementById('password-input')?.getAttribute('type') ?? null,
    caretRightOfName: Boolean(name && caret)
      && caret.getBoundingClientRect().left >= name.getBoundingClientRect().right - 1,
    state: window.__xpathRange ? window.__xpathRange.getState() : null
  };
})()`;

async function main() {
  await verifyStaticContract();

  const browser = findBrowser();
  if (!browser) {
    throw new Error('找不到 Chrome 或 Edge, 请设置 XPATH_ADDIN_BROWSER 环境变量');
  }
  console.log(`\n== 浏览器流程 (${path.basename(browser)}) ==`);

  const profile = mkdtempSync(path.join(tmpdir(), 'xpath-addin-'));
  const child = spawn(browser, [
    '--headless=new',
    `--remote-debugging-port=${DEBUG_PORT}`,
    `--user-data-dir=${profile}`,
    '--ignore-certificate-errors',
    '--no-first-run',
    '--no-default-browser-check',
    '--disable-extensions',
    '--window-size=420,760',
    'about:blank'
  ], { stdio: 'ignore' });

  let cdp = null;
  try {
    const version = await waitForDevTools();
    cdp = await Cdp.connect(version.webSocketDebuggerUrl);

    const { targetId } = await cdp.send('Target.createTarget', { url: 'about:blank' }, false);
    const attached = await cdp.send('Target.attachToTarget', { targetId, flatten: true }, false);
    cdp.sessionId = attached.sessionId;

    await cdp.send('Page.enable');
    await cdp.send('Runtime.enable');
    await cdp.send('Emulation.setDeviceMetricsOverride',
      { width: 420, height: 760, deviceScaleFactor: 1, mobile: false });
    await cdp.send('Page.navigate', { url: `${BASE}/src/taskpane.html` });

    const deadline = Date.now() + 15000;
    while (Date.now() < deadline) {
      const ready = await evaluate(cdp, 'document.readyState');
      if (ready === 'complete' && await evaluate(cdp, 'Boolean(window.__xpathRange)')) break;
      await wait(150);
    }
    await wait(300);

    const evaluateJson = async (expression) => JSON.parse(await evaluate(cdp, `JSON.stringify(${expression})`));

    const shot = async (name) => {
      const { data } = await cdp.send('Page.captureScreenshot', { format: 'png' });
      writeFileSync(path.join(HERE, name), Buffer.from(data, 'base64'));
      console.log(`  截图 ${name}`);
    };

    // 步骤 1-2: 初始未登录
    let snapshot = await evaluateJson(SNAPSHOT);
    check('初始显示 "点击登录"', snapshot.loginTriggerVisible && snapshot.loginTriggerText === '点击登录',
      snapshot.loginTriggerText);
    check('初始无登录框', !snapshot.dialogVisible);
    check('初始无用户菜单按钮', !snapshot.userMenuTriggerVisible);
    check('初始状态未登录', snapshot.state && snapshot.state.loggedIn === false);

    // 步骤 3-4: 打开登录框
    await clickSelector(cdp, '#login-trigger');
    snapshot = await evaluateJson(SNAPSHOT);
    check('点击后出现登录框', snapshot.dialogVisible);
    check('登录框可输入名称/密码/登录', await evaluate(cdp,
      "['username-input','password-input','login-submit'].every((id) => document.getElementById(id).getBoundingClientRect().width > 0)"));
    check('密码输入框为 password 类型', snapshot.passwordType === 'password', String(snapshot.passwordType));
    await shot('screenshot-login-dialog.png');

    // 步骤 5: 失败分支 admin/2
    await typeInto(cdp, '#username-input', 'admin');
    await typeInto(cdp, '#password-input', '2');
    await clickSelector(cdp, '#login-submit');
    snapshot = await evaluateJson(SNAPSHOT);
    check('错误密码仍在登录框内', snapshot.dialogVisible);
    check('错误提示为 "账号或密码错误"', snapshot.errorVisible && snapshot.errorText === '账号或密码错误',
      snapshot.errorText);
    check('错误密码未登录', snapshot.state && snapshot.state.loggedIn === false);

    // 步骤 6: 取消分支
    await clickSelector(cdp, '#login-cancel');
    snapshot = await evaluateJson(SNAPSHOT);
    check('取消后登录框消失', !snapshot.dialogVisible);
    check('取消后仍显示 "点击登录"', snapshot.loginTriggerVisible);

    // 步骤 7: 正确凭据 admin/1
    await clickSelector(cdp, '#login-trigger');
    await typeInto(cdp, '#username-input', 'admin');
    await typeInto(cdp, '#password-input', '1');
    await clickSelector(cdp, '#login-submit');
    snapshot = await evaluateJson(SNAPSHOT);
    check('登录框消失', !snapshot.dialogVisible);
    check('显示 "已登录"', snapshot.statusVisible && snapshot.statusText === '已登录', snapshot.statusText);
    check('"点击登录" 按钮消失', !snapshot.loginTriggerVisible);
    check('按钮变为 admin', snapshot.userMenuTriggerVisible && snapshot.userMenuNameText === 'admin',
      snapshot.userMenuNameText);
    check('admin 右侧有小箭头', snapshot.caretRightOfName && snapshot.userMenuTriggerText.includes('\u25be'),
      snapshot.userMenuTriggerText);
    check('内部状态已登录', snapshot.state && snapshot.state.loggedIn === true);

    // 步骤 8: 展开用户菜单
    await clickSelector(cdp, '#user-menu-trigger');
    snapshot = await evaluateJson(SNAPSHOT);
    check('出现用户菜单', snapshot.userMenuVisible);
    check('菜单含 "退出登录"', snapshot.userMenuText.includes('退出登录'), snapshot.userMenuText);
    check('菜单展开 aria-expanded=true', snapshot.ariaExpanded === 'true', String(snapshot.ariaExpanded));
    await shot('screenshot-logged-in.png');

    // 步骤 9-10: 退出登录
    await clickSelector(cdp, '#logout-item');
    snapshot = await evaluateJson(SNAPSHOT);
    check('退出后回到 "点击登录"', snapshot.loginTriggerVisible && snapshot.loginTriggerText === '点击登录');
    check('退出后用户菜单按钮消失', !snapshot.userMenuTriggerVisible);
    check('退出后 "已登录" 消失', !snapshot.statusVisible);
    check('退出后状态复位',
      snapshot.state && Object.values(snapshot.state).every((value) => value === false));
    await shot('screenshot-logged-out.png');
  } finally {
    cdp?.close();
    child.kill();
    await wait(300);
    rmSync(profile, { recursive: true, force: true });
  }

  console.log(`\n共 ${results.length} 项断言, 失败 ${failed} 项。`);
  if (failed > 0) process.exitCode = 1;
}

async function evaluate(cdp, expression) {
  const result = await cdp.send('Runtime.evaluate', { expression, returnByValue: true, awaitPromise: true });
  if (result.exceptionDetails) {
    throw new Error(`页面求值失败: ${result.exceptionDetails.exception?.description ?? result.exceptionDetails.text}`);
  }
  return result.result.value;
}

async function clickSelector(cdp, selector) {
  const expression = `(() => {
    const el = document.querySelector(${JSON.stringify(selector)});
    if (!el) return null;
    const rect = el.getBoundingClientRect();
    return { x: rect.left + rect.width / 2, y: rect.top + rect.height / 2, w: rect.width, h: rect.height };
  })()`;
  const box = JSON.parse(await evaluate(cdp, `JSON.stringify(${expression})`));
  if (!box) throw new Error(`找不到元素: ${selector}`);
  if (box.w === 0 || box.h === 0) throw new Error(`元素不可见: ${selector}`);
  for (const type of ['mousePressed', 'mouseReleased']) {
    await cdp.send('Input.dispatchMouseEvent',
      { type, x: box.x, y: box.y, button: 'left', clickCount: 1 });
  }
  await wait(120);
}

async function typeInto(cdp, selector, text) {
  await clickSelector(cdp, selector);
  await cdp.send('Runtime.evaluate',
    { expression: `document.querySelector(${JSON.stringify(selector)}).value = ''` });
  for (const char of text) {
    // 只有 char 事件负责插入文本; keyDown 若也带 text 会重复插入。
    await cdp.send('Input.dispatchKeyEvent', { type: 'keyDown', key: char });
    await cdp.send('Input.dispatchKeyEvent', { type: 'char', key: char, text: char, unmodifiedText: char });
    await cdp.send('Input.dispatchKeyEvent', { type: 'keyUp', key: char });
  }
  const value = await evaluate(cdp, `document.querySelector(${JSON.stringify(selector)}).value`);
  if (value !== text) throw new Error(`输入失败: ${selector} 期望 ${text} 实际 ${value}`);
}

main().catch((error) => {
  console.error(`\n验证失败: ${error.message}`);
  process.exitCode = 1;
});
