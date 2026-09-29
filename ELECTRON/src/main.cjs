'use strict';
const { app, BrowserWindow, BrowserView, WebContentsView, ipcMain, Menu, dialog } = require('electron');
const fs = require('node:fs');
const path = require('node:path');
const { randomBytes } = require('node:crypto');
const { ROUTES, parseOptions, pageUrl, browserBounds, viewMode } = require('./config.cjs');

let options, runtime, mode;
try {
  runtime = require('./runtime.json');
  const actual = { electron: process.versions.electron, chromium: process.versions.chrome, node: process.versions.node };
  for (const name of Object.keys(actual)) {
    if (runtime[name] !== actual[name]) throw new Error(`${name} 版本不匹配：需要 ${runtime[name]}，实际 ${actual[name]}`);
  }
  if (String(runtime.major) !== actual.electron.split('.')[0]) throw new Error('运行时主版本不匹配');
  mode = viewMode(actual.electron);
  options = parseOptions(process.argv.slice(app.isPackaged ? 1 : 2));
} catch (error) {
  dialog.showErrorBox('Electron 靶场启动失败', error.message);
  app.exit(1);
}

if (options) {
  if (options.debuggingPort) {
    app.commandLine.appendSwitch('remote-debugging-address', '127.0.0.1');
    app.commandLine.appendSwitch('remote-debugging-port', String(options.debuggingPort));
  }
  const exeDirectory = path.dirname(process.execPath);
  const rangeRoot = path.basename(path.dirname(exeDirectory)) === 'dist' ? path.resolve(exeDirectory, '../..') : exeDirectory;
  const profile = path.join(rangeRoot, '.cache', 'profiles', String(runtime.major), `${process.pid}-${randomBytes(6).toString('hex')}`);
  fs.mkdirSync(path.join(profile, 'session'), { recursive: true });
  app.setPath('userData', profile);
  app.setPath('sessionData', path.join(profile, 'session'));
  app.setAppUserModelId(`xpath.electron.range.${runtime.major}`);

  let win = null, view = null;
  let hostReady = false;
  let selected = 0;
  const state = {
    revision: 0, selected, address: pageUrl(options.baseUrl, selected), loading: true,
    error: '', status: '正在初始化浏览器…', runtime, mode, profile, routes: ROUTES,
  };
  function publish(patch = {}) {
    Object.assign(state, patch);
    state.revision++;
    if (hostReady && win && !win.isDestroyed()) win.webContents.send('range:state', state);
  }
  function fromHost(event) {
    return win && !win.isDestroyed() && event.sender === win.webContents && event.senderFrame === win.webContents.mainFrame;
  }
  function updateBounds() {
    if (!win || win.isDestroyed() || !view) return;
    const [width, height] = win.getContentSize();
    view.setBounds(browserBounds(width, height));
  }
  function navigate(index) {
    if (!view || view.webContents.isDestroyed() || !Number.isInteger(index) || !ROUTES[index]) return;
    selected = index;
    const url = pageUrl(options.baseUrl, index);
    publish({ selected, address: url, loading: true, error: '', status: `正在加载 ${ROUTES[index].label}…` });
    // did-fail-load reports failures, including aborted loads from fast menu switching.
    view.webContents.loadURL(url).catch(() => {});
  }
  ipcMain.handle('range:get-state', event => {
    if (!fromHost(event)) throw new Error('拒绝非宿主请求');
    return state;
  });
  ipcMain.on('range:select', (event, index) => { if (fromHost(event)) navigate(index); });
  ipcMain.on('range:refresh', event => {
    if (!fromHost(event) || !view || view.webContents.isDestroyed()) return;
    publish({ loading: true, error: '', status: '正在刷新…' });
    // On an initial network failure Chromium may still report about:blank.
    if (!/^https?:/.test(view.webContents.getURL())) navigate(selected);
    else view.webContents.reloadIgnoringCache();
  });

  app.whenReady().then(async () => {
    Menu.setApplicationMenu(null);
    app.setAccessibilitySupportEnabled(true);
    const title = `Electron ${runtime.major} 靶场 | ${runtime.electron} | Chromium ${runtime.chromium} | Node ${runtime.node} | ${mode}`;
    win = new BrowserWindow({
      width: 1280, height: 900, minWidth: 960, minHeight: 640, title, show: false,
      backgroundColor: '#f0f0f0', autoHideMenuBar: true,
      webPreferences: { preload: path.join(__dirname, 'preload.cjs'), nodeIntegration: false, contextIsolation: true, sandbox: true },
    });
    win.on('page-title-updated', event => event.preventDefault());
    win.webContents.on('will-navigate', event => event.preventDefault());
    win.webContents.setWindowOpenHandler(() => ({ action: 'deny' }));
    view = new (mode === 'BrowserView' ? BrowserView : WebContentsView)({
      webPreferences: { nodeIntegration: false, contextIsolation: true, sandbox: true },
    });
    if (mode === 'BrowserView') win.setBrowserView(view);
    else win.contentView.addChildView(view);
    updateBounds();
    win.on('resize', updateBounds);
    view.webContents.setWindowOpenHandler(() => ({ action: 'deny' }));
    view.webContents.on('will-navigate', (event, url) => { if (!/^https?:/.test(url)) event.preventDefault(); });
    view.webContents.on('did-start-loading', () => publish({ loading: true, error: '', status: `正在加载 ${ROUTES[selected].label}…` }));
    view.webContents.on('did-navigate', (_event, url) => publish({ address: url }));
    view.webContents.on('did-navigate-in-page', (_event, url, isMainFrame) => { if (isMainFrame) publish({ address: url }); });
    view.webContents.on('did-fail-load', (_event, code, description, url, isMainFrame) => {
      if (!isMainFrame || code === -3) return;
      publish({ loading: false, address: url, error: `${description} (${code})`, status: `加载失败：${description} (${code})；可刷新重试` });
    });
    view.webContents.on('did-stop-loading', () => {
      if (!state.error) publish({ loading: false, status: `就绪 · ${ROUTES[selected].label}` });
    });
    view.webContents.on('render-process-gone', (_event, details) => publish({ loading: false, error: details.reason, status: `网页进程退出：${details.reason}；可刷新重试` }));
    win.once('closed', () => {
      // WebContentsView is not automatically destroyed with its owner window.
      if (view && !view.webContents.isDestroyed()) view.webContents.close({ waitForBeforeUnload: false });
      view = null;
      win = null;
      hostReady = false;
    });
    await win.loadFile(path.join(__dirname, 'shell.html'));
    hostReady = true;
    publish();
    win.show();
    navigate(0);
  }).catch(error => {
    dialog.showErrorBox('Electron 靶场初始化失败', error.message);
    app.exit(1);
  });
  app.on('window-all-closed', () => app.quit());
}
