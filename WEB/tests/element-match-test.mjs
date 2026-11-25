import assert from 'node:assert/strict';
import { createRequire } from 'node:module';
import { mkdir } from 'node:fs/promises';
import { resolve } from 'node:path';

const require = createRequire(import.meta.url);
const { chromium } = require(process.env.MATCH_PLAYWRIGHT_MODULE || 'playwright');
const base = process.env.MATCH_TEST_BASE_URL || 'http://127.0.0.1:7199/';
const browser = await chromium.launch({ channel: 'chrome', headless: true });
const page = await browser.newPage({ viewport: { width: 1280, height: 900 } });
const errors = [];
page.on('pageerror', error => errors.push(error.message));

async function targets() {
  return page.locator('#match-targets button[data-sample]').evaluateAll(buttons =>
    Object.fromEntries(buttons.map(button => [button.dataset.sample, {
      id: button.id, value: button.dataset.value, title: button.title, text: button.textContent,
    }])));
}

async function verifyRules(length) {
  const samples = await targets();
  const checks = {
    equals: value => value === 'abc-fixed-xyz',
    'not-equals': value => value !== 'abc-fixed-xyz',
    contains: value => value.includes('-fixed-'),
    'not-contains': value => !value.includes('-fixed-'),
    'starts-with': value => value.startsWith('abc'),
    'not-starts-with': value => !value.startsWith('abc'),
    'ends-with': value => value.endsWith('xyz'),
    'not-ends-with': value => !value.endsWith('xyz'),
    greater: value => Number(value) > 100,
    'greater-equal': value => Number(value) >= 100,
    less: value => Number(value) < 100,
    'less-equal': value => Number(value) <= 100,
    regex: value => new RegExp(`^abc[A-Za-z0-9]{${length}}xyz$`).test(value),
    wildcard: value => /^abc.*xyz$/.test(value),
  };
  const rows = await page.locator('[data-rule]').evaluateAll(elements => elements.map(row => ({
    rule: row.dataset.rule, attribute: row.dataset.attribute,
    positive: row.dataset.positive, negative: row.dataset.negative,
    positiveText: row.querySelector('[data-expect="positive"]').textContent,
    negativeText: row.querySelector('[data-expect="negative"]').textContent,
    pattern: row.querySelectorAll('td')[1].textContent,
  })));
  assert.deepEqual(rows.map(row => row.rule).sort(), Object.keys(checks).sort());
  assert.equal(rows.find(row => row.rule === 'regex').pattern, `^abc[A-Za-z0-9]{${length}}xyz$`);
  assert.equal(rows.find(row => row.rule === 'wildcard').pattern, 'abc*xyz');
  assert.equal(await page.locator('#match-wildcard-single').innerText(), `abc${'?'.repeat(length)}xyz`);
  for (const row of rows) {
    const attribute = row.attribute === 'id' ? 'id' : 'value';
    const positive = samples[row.positive][attribute];
    const negative = samples[row.negative][attribute];
    assert.equal(checks[row.rule](positive), true, `${row.rule} 正例`);
    assert.equal(checks[row.rule](negative), false, `${row.rule} 反例`);
    assert.equal(row.positiveText, positive, `${row.rule} 当前正例值`);
    assert.equal(row.negativeText, negative, `${row.rule} 当前反例值`);
  }
  assert.match(samples.prefix.id, new RegExp(`^abc[A-Za-z0-9]{${length}}$`));
  assert.match(samples.suffix.id, new RegExp(`^[A-Za-z0-9]{${length}}xyz$`));
  assert.match(samples.both.id, new RegExp(`^abc[A-Za-z0-9]{${length}}xyz$`));
  for (const sample of Object.values(samples)) {
    assert.equal(sample.title, sample.value);
    assert.equal(sample.text, sample.value);
  }
  for (const value of [2, 99, 100, 101, 1000]) {
    assert.equal(samples[`number-${value}`].value, String(value));
  }
  assert.equal(new Set(Object.values(samples).map(sample => sample.id)).size, Object.keys(samples).length);
  return samples;
}

try {
  await page.goto(base);
  await page.locator('#home-search').waitFor();
  assert.equal(await page.locator('#menu-element-match-test').count(), 1, '首页应包含元素串匹配测试入口');
  const popupPromise = page.waitForEvent('popup');
  await page.locator('#menu-element-match-test').click();
  const popup = await popupPromise;
  await popup.waitForLoadState('domcontentloaded');
  assert.equal(popup.url(), `${base}element-match-test`);
  await popup.close();
  await page.goto(`${base}element-match-test`);
  await page.locator('#match-targets').waitFor();
  const initial = await verifyRules(8);
  console.log('PASS 首页入口、真实靶元素与 14 种规则正反例');

  await page.locator('[data-sample="both"]').click();
  assert.match(await page.locator('#match-click-result').innerText(), new RegExp(initial.both.id));
  await page.locator('#match-random-length').fill('12');
  assert.deepEqual(await targets(), initial, '编辑位数时样本保持稳定');
  await page.locator('#match-regenerate').click();
  const regenerated = await verifyRules(12);
  for (const key of ['prefix', 'suffix', 'both']) assert.notEqual(regenerated[key].id, initial[key].id);
  for (const key of ['exact', 'other', 'case', 'number-100']) assert.deepEqual(regenerated[key], initial[key]);
  assert.match(await page.locator('#match-click-result').innerText(), /尚未点击/);
  console.log('PASS 点击反馈、编辑稳定性与重新生成');

  for (const length of [1, 32]) {
    await page.locator('#match-random-length').fill(String(length));
    await page.locator('#match-regenerate').click();
    await verifyRules(length);
  }
  for (const invalid of ['', '0', '33', '1.5']) {
    await page.locator('#match-random-length').fill(invalid);
    assert.equal(await page.locator('#match-regenerate').isDisabled(), true, `拒绝非法位数 ${invalid}`);
  }
  console.log('PASS 位数上下限与非法输入');

  const beforeReload = await targets();
  await page.reload();
  await page.locator('#match-targets').waitFor();
  const refreshed = await verifyRules(8);
  assert.notEqual(refreshed.both.id, beforeReload.both.id);
  assert.deepEqual(refreshed.exact, initial.exact);
  if (process.env.MATCH_TEST_SCREENSHOT_DIR) {
    await mkdir(process.env.MATCH_TEST_SCREENSHOT_DIR, { recursive: true });
    await page.screenshot({ path: resolve(process.env.MATCH_TEST_SCREENSHOT_DIR, 'element-match-desktop.png'), fullPage: true });
  }
  await page.setViewportSize({ width: 375, height: 812 });
  await page.locator('#match-random-length').fill('32');
  await page.locator('#match-regenerate').click();
  await verifyRules(32);
  assert.equal(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth), true, '窄屏无页面横向溢出');
  if (process.env.MATCH_TEST_SCREENSHOT_DIR) {
    await page.screenshot({ path: resolve(process.env.MATCH_TEST_SCREENSHOT_DIR, 'element-match-mobile.png'), fullPage: true });
  }
  assert.deepEqual(errors, []);
  console.log('PASS 刷新随机化、窄屏布局、无浏览器异常');
} finally {
  await browser.close();
}
