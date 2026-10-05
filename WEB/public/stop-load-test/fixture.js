const scopeURL = new URL('./', location.href).href;
const workerURL = new URL('./sw.js', location.href).href;
const ownsController = () => navigator.serviceWorker?.controller?.scriptURL === workerURL;
const element = id => document.getElementById(id);

function waitForController() {
  if (ownsController()) return Promise.resolve();
  return new Promise((resolve, reject) => {
    const timeout = setTimeout(() => finish(new Error('测试环境准备超时，请重新打开准备页。')), 10000);
    const changed = () => { if (ownsController()) finish(); };
    function finish(error) {
      clearTimeout(timeout);
      navigator.serviceWorker.removeEventListener('controllerchange', changed);
      if (error) reject(error); else resolve();
    }
    navigator.serviceWorker.addEventListener('controllerchange', changed);
    changed();
  });
}

async function setup() {
  if (!isSecureContext || !('serviceWorker' in navigator)) {
    throw new Error('浏览器不支持此测试环境，请使用 HTTPS 或 localhost 打开。');
  }
  await navigator.serviceWorker.register('./sw.js', { scope: './', updateViaCache: 'none' });
  await waitForController();
  element('setup-state').dataset.state = 'ready';
  element('setup-state').textContent = '准备完成，可以开始测试。';
  element('start-test').disabled = false;
  element('cleanup-worker').disabled = false;
}

if (document.body.dataset.page === 'setup') {
  element('start-test').addEventListener('click', () => {
    const seconds = Number(element('delay-seconds').value);
    if (!Number.isInteger(seconds) || seconds < 1 || seconds > 120) {
      element('setup-error').textContent = '等待时间须为 1–120 秒的整数。';
      return;
    }
    const destination = new URL('./loading.html', location.href);
    destination.searchParams.set('delay', String(seconds * 1000));
    destination.searchParams.set('run', crypto.randomUUID());
    location.assign(destination.href);
  });
  element('cleanup-worker').addEventListener('click', async () => {
    try {
      const registrations = await navigator.serviceWorker.getRegistrations();
      for (const registration of registrations) {
        if (registration.scope === scopeURL) await registration.unregister();
      }
      element('setup-state').dataset.state = 'removed';
      element('setup-state').textContent = '测试环境已清理。关闭本页释放控制，重新打开可再次准备。';
      element('start-test').disabled = true;
      element('cleanup-worker').disabled = true;
    } catch (error) {
      element('setup-error').textContent = `清理失败：${error.message}`;
    }
  });
  setup().catch(error => {
    element('setup-state').dataset.state = 'error';
    element('setup-state').textContent = '测试环境未准备完成。';
    element('setup-error').textContent = error.message;
  });
} else {
  const parameters = new URLSearchParams(location.search);
  const requestedDelay = Number(parameters.get('delay') ?? 30000);
  const delayMs = Number.isInteger(requestedDelay) && requestedDelay >= 1000 && requestedDelay <= 120000
    ? requestedDelay : 30000;
  const started = performance.now();
  const state = {
    version: 1, runId: parameters.get('run') || crypto.randomUUID(), delayMs,
    controlled: ownsController(), heartbeat: 0, loadEvents: 0,
    resourceStatus: 'pending', resourceLoaded: false, events: [],
  };
  window.stopLoadTest = {
    getState: () => ({ ...state, events: state.events.map(event => ({ ...event })),
      readyState: document.readyState, elapsedMs: Math.round(performance.now() - started) }),
  };
  function record(type, detail = {}) {
    state.events.push({ type, atMs: Math.round(performance.now() - started), ...detail });
    render();
  }
  function render() {
    element('elapsed-seconds').textContent = ((performance.now() - started) / 1000).toFixed(1);
    element('heartbeat').textContent = String(state.heartbeat);
    element('document-state').textContent = document.readyState;
    element('resource-state').textContent = state.resourceStatus;
    element('event-log').textContent = JSON.stringify(window.stopLoadTest.getState(), null, 2);
    element('loading-status').textContent = state.resourceLoaded ? '资源已自然完成。'
      : state.resourceStatus === 'pending' ? `资源等待中，预定 ${delayMs / 1000} 秒后返回。`
      : '资源未完成（中止或失败），请结合网络事件核对。';
  }
  window.addEventListener('load', () => {
    state.loadEvents += 1;
    record('window_load');
  }, { once: true });
  document.addEventListener('DOMContentLoaded', () => record('dom_content_loaded'), { once: true });
  navigator.serviceWorker?.addEventListener('message', event => {
    if (event.data?.runId === state.runId && event.data?.fixture === 'stop-load-test') {
      record(event.data.type);
    }
  });
  setInterval(() => { state.heartbeat += 1; render(); }, 250);
  if (!state.controlled) {
    state.resourceStatus = 'not-prepared';
    element('loading-error').textContent = '请先返回准备页，等待“准备完成”后再开始测试。';
    render();
  } else {
    const resource = document.createElement('img');
    resource.id = 'slow-resource';
    resource.alt = '延迟资源完成后显示';
    resource.addEventListener('load', () => {
      state.resourceLoaded = resource.naturalWidth > 0;
      state.resourceStatus = state.resourceLoaded ? 'loaded' : 'error';
      record('resource_load');
    }, { once: true });
    resource.addEventListener('error', () => { state.resourceStatus = 'error'; record('resource_error'); }, { once: true });
    const url = new URL('./slow.svg', location.href);
    url.searchParams.set('delay', String(delayMs));
    url.searchParams.set('run', state.runId);
    resource.src = url.href;
    // 在模块完成、DOMContentLoaded/load 之前同步插入，使图片阻塞文档 load。
    element('resource-host').append(resource);
    record('resource_requested');
  }
}
