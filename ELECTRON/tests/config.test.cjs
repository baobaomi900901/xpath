'use strict';
const test = require('node:test');
const assert = require('node:assert/strict');
const { DEFAULT_BASE_URL, ROUTES, validateBaseUrl, pageUrl, parseOptions, browserBounds, viewMode } = require('../src/config.cjs');

test('same routes work with Pages hash routing and local browser routing', () => {
  assert.equal(pageUrl(DEFAULT_BASE_URL, 0), 'https://baobaomi900901.github.io/xpath/#/keys-click-test');
  assert.equal(pageUrl('http://localhost:7199/', 2), 'http://localhost:7199/iframe-shadow-form');
  assert.equal(ROUTES.length, 3);
  assert.throws(() => pageUrl(DEFAULT_BASE_URL, 3));
});

test('reject ambiguous or unsafe base URLs even when launching EXE directly', () => {
  for (const url of ['file:///tmp/', 'https://x/a', 'https://u:p@x/', 'https://x/?a=b', 'https://x/#foo', 'https://x/#', 'https://x/\\a/', ' https://x/', 'https://x:99999/', 'https://x:0/', 'https://x/%20/?']) {
    assert.throws(() => validateBaseUrl(url), url);
  }
  for (const url of ['https://x/', 'http://127.0.0.1:7199/', 'https://x/path/#/']) assert.equal(validateBaseUrl(url), url);
});

test('direct launch arguments validate base URL and debugging port', () => {
  assert.deepEqual(parseOptions([]), { baseUrl: DEFAULT_BASE_URL, debuggingPort: null });
  assert.deepEqual(parseOptions(['--base-url', 'http://localhost:7199/', '--remote-debugging-port=9222']), { baseUrl: 'http://localhost:7199/', debuggingPort: 9222 });
  assert.throws(() => parseOptions(['--base-url']));
  assert.throws(() => parseOptions(['--remote-debugging-port=1023']));
  assert.throws(() => parseOptions(['--remote-debugging-port=65536']));
  assert.throws(() => parseOptions(['--remote-debugging-port=9222x']));
  assert.throws(() => parseOptions(['--base-url=https://x/', '--base-url=https://y/']));
});

test('independent view occupies CEF content bounds and follows resize', () => {
  assert.deepEqual(browserBounds(1280, 900), { x: 220, y: 52, width: 1048, height: 814 });
  assert.deepEqual(browserBounds(960, 640), { x: 220, y: 52, width: 728, height: 554 });
  assert.deepEqual(browserBounds(100, 40), { x: 220, y: 52, width: 1, height: 1 });
});

test('chosen versions use the intended embedding implementations', () => {
  assert.equal(viewMode('22.3.27'), 'BrowserView');
  assert.equal(viewMode('29.4.6'), 'BrowserView');
  assert.equal(viewMode('38.8.6'), 'WebContentsView');
  assert.equal(viewMode('44.4.5'), 'WebContentsView');
  assert.throws(() => viewMode('0.0.0'));
});
