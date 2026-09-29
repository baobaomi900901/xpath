'use strict';
const DEFAULT_BASE_URL = 'https://baobaomi900901.github.io/xpath/#/';
const ROUTES = Object.freeze([
  Object.freeze({ label: '点击测试', path: 'keys-click-test' }),
  Object.freeze({ label: '表单测试', path: 'form-controls' }),
  Object.freeze({ label: 'iframe表单', path: 'iframe-shadow-form' }),
]);

function validateBaseUrl(value) {
  const fail = () => { throw new Error('--base-url 必须是以 / 或 #/ 结尾的 HTTP(S) 根地址，不能包含查询、账号或空白'); };
  if (typeof value !== 'string' || /[\s\\\x00-\x1f\x7f]/.test(value)) fail();
  let url;
  try { url = new URL(value); } catch { fail(); }
  if (!['http:', 'https:'].includes(url.protocol) || !url.hostname || url.username || url.password || value.includes('?')) fail();
  if (url.port === '0' || (value.includes('#') && url.hash !== '#/')) fail();
  // A root must be explicit so appending a route never replaces a path segment.
  if (!(url.hash === '#/' ? value.endsWith('#/') && url.pathname.endsWith('/') : value.endsWith('/'))) fail();
  return value;
}

function pageUrl(baseUrl, index) {
  if (!Number.isInteger(index) || !ROUTES[index]) throw new Error('未知菜单项');
  return validateBaseUrl(baseUrl) + ROUTES[index].path;
}

function parseOptions(argv) {
  const options = { baseUrl: DEFAULT_BASE_URL, debuggingPort: null };
  const seen = new Set();
  for (let i = 0; i < argv.length; i++) {
    const arg = argv[i];
    const name = arg.split('=')[0];
    if (!['--base-url', '--remote-debugging-port'].includes(name)) continue;
    if (seen.has(name)) throw new Error(`重复参数 ${name}`);
    seen.add(name);
    const value = arg.includes('=') ? arg.slice(name.length + 1) : argv[++i];
    if (!value || value.startsWith('--')) throw new Error(`${name} 缺少值`);
    if (name === '--base-url') options.baseUrl = validateBaseUrl(value);
    else {
      if (!/^\d+$/.test(value) || Number(value) < 1024 || Number(value) > 65535) throw new Error('调试端口必须为 1024–65535');
      options.debuggingPort = Number(value);
    }
  }
  return options;
}

function browserBounds(width, height) {
  return { x: 220, y: 52, width: Math.max(1, width - 232), height: Math.max(1, height - 86) };
}

function viewMode(electronVersion) {
  const major = Number(electronVersion.split('.')[0]);
  if ([22, 29].includes(major)) return 'BrowserView';
  if ([38, 44].includes(major)) return 'WebContentsView';
  throw new Error(`不支持的 Electron 主版本 ${major}`);
}

module.exports = { DEFAULT_BASE_URL, ROUTES, validateBaseUrl, pageUrl, parseOptions, browserBounds, viewMode };
