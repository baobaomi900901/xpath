import assert from 'node:assert/strict';
import { createHmac, randomBytes } from 'node:crypto';
import { mkdir, readFile } from 'node:fs/promises';
import { createRequire } from 'node:module';
import { resolve } from 'node:path';

const require = createRequire(import.meta.url);
const { chromium } = require(process.env.LOGIN_PLAYWRIGHT_MODULE || 'playwright');
const authConfig = JSON.parse(await readFile(new URL('../../fixtures/bank-transfer-auth.json', import.meta.url), 'utf8'));
const base = process.env.LOGIN_TEST_BASE_URL || 'http://127.0.0.1:7199/';
const browser = await chromium.launch({ channel: 'chrome', headless: true });
const page = await browser.newPage({ viewport: { width: 1280, height: 1000 } });
const errors = [];
const writes = [];
page.on('pageerror', error => errors.push(error.message));
page.on('request', request => { if (!['GET', 'HEAD'].includes(request.method())) writes.push(request.url()); });
const frame = page.frameLocator('#registration-frame');
const form = frame.getByRole('form', { name: '登记', exact: true });
const values = {
  '转账账号': '2222222',
  '金额': '1223123',
  '客户名称': '111111222',
  '收款银行': '1231231232',
  '分行支行名称': '33333322',
  '联行号': '',
  '转账用途': '',
};
function signedReference(amount, key = authConfig.sharedKey) {
  const [whole, fraction = ''] = amount.split('.');
  const normalized = `${BigInt(whole)}.${fraction.padEnd(2, '0')}`;
  const nonce = randomBytes(12).toString('base64url');
  const signature = createHmac('sha256', key).update(`${authConfig.payloadPrefix}\n${normalized}\n${nonce}`, 'utf8').digest().subarray(0, 12).toString('base64url');
  return `TR_${nonce}_${signature}`;
}
const references = Array.from({ length: 10 }, () => signedReference(values['金额']));
let passed = 0;
function pass(name) { passed += 1; console.log(`PASS ${name}`); }

async function submitFailure(pattern, enter = false) {
  if (enter) await form.getByLabel('业务流水号', { exact: true }).press('Enter');
  else await form.getByRole('button', { name: '登记', exact: true }).click();
  const dialog = frame.getByRole('dialog', { name: '登记失败', exact: true });
  await dialog.waitFor();
  assert.match(await dialog.getByRole('alert').innerText(), pattern);
  assert.equal(await page.getByRole('dialog').count(), 0, '弹窗必须位于 iframe 中');
  await dialog.getByRole('button', { name: /^确\s*定$/ }).click();
  await dialog.waitFor({ state: 'hidden' });
}

async function fillTransferValues() {
  for (const [label, value] of Object.entries(values)) await form.getByLabel(label, { exact: true }).fill(value);
}

try {
  await page.goto(base);
  await page.waitForLoadState('networkidle');
  assert.equal(await page.locator('#menu-registration-test').count(), 1, '首页应包含登记入口');
  const popupPromise = page.waitForEvent('popup');
  await page.locator('#menu-registration-test').click();
  const popup = await popupPromise;
  await popup.waitForLoadState('domcontentloaded');
  assert.equal(popup.url(), `${base}registration-test`);
  await popup.close();
  pass('首页登记入口可单独打开');

  await page.goto(`${base}registration-test`);
  await form.waitFor();
  assert.equal(await page.title(), '登记');
  assert.equal(await page.getByRole('heading', { name: '登记', exact: true }).count(), 1);
  assert.equal(await page.locator('#registration-frame').getAttribute('title'), '登记表单');
  assert.equal(await page.getByRole('textbox').count(), 0);
  assert.equal(await form.getByRole('textbox').count(), 8);
  assert.equal(await page.locator('#registration-frame').evaluate(element => element.contentDocument !== document), true);
  for (const label of ['业务流水号', ...Object.keys(values)]) assert.equal(await form.getByLabel(label, { exact: true }).inputValue(), '');
  pass('8项输入位于真实 iframe 中，外层标题为登记');

  await submitFailure(/业务流水号/);
  await form.getByLabel('业务流水号', { exact: true }).fill(references[0]);
  await submitFailure(/转账账号.*不能为空/);
  await fillTransferValues();
  pass('空流水号及必填项缺失会在 iframe 内提示');

  for (const reference of [
    'TR_NOT_IN_LIST0',
    'TR_s883X66VL51V',
    references[0].slice(0, -1) + (references[0].endsWith('0') ? '1' : '0'),
    signedReference(values['金额'], 'wrong-key'),
    references[0].toLowerCase(),
    ` ${references[0]}`,
    `${references[0]} `,
  ]) {
    await form.getByLabel('业务流水号', { exact: true }).fill(reference);
    await submitFailure(/流水号/);
    assert.equal(await form.getByLabel('业务流水号', { exact: true }).inputValue(), reference);
  }
  pass('拒绝乱填、旧固定编号、篡改签名、错误密钥、大小写和额外空格');

  await form.getByLabel('业务流水号', { exact: true }).fill(references[0]);
  await form.getByLabel('转账账号', { exact: true }).fill('abc');
  await submitFailure(/转账账号/);
  await form.getByLabel('转账账号', { exact: true }).fill(values['转账账号']);
  await form.getByLabel('金额', { exact: true }).fill('0');
  await submitFailure(/金额/);
  await form.getByLabel('金额', { exact: true }).fill('1.001');
  await submitFailure(/金额/);
  await form.getByLabel('金额', { exact: true }).fill(values['金额']);
  await form.getByLabel('金额', { exact: true }).fill('2');
  await submitFailure(/流水号.*金额/);
  await form.getByLabel('金额', { exact: true }).fill(values['金额']);
  pass('复用转账账号和金额格式校验');

  const bank = await browser.newPage();
  await bank.goto(`${base}login-test`);
  await bank.getByLabel('账号', { exact: true }).fill('admin');
  await bank.getByLabel('密码', { exact: true }).fill('1');
  await bank.getByRole('button', { name: /^登\s*录$/ }).click();
  const bankForm = bank.getByRole('form', { name: '网银转账', exact: true });
  for (const [label, value] of Object.entries(values)) await bankForm.getByLabel(label, { exact: true }).fill(value);
  await bankForm.getByRole('button', { name: '转账', exact: true }).click();
  const bankDialog = bank.getByRole('dialog', { name: '确认转账', exact: true });
  await bankDialog.waitFor();
  const issued = (await bankDialog.innerText()).match(/业务流水号：(TR_[A-Za-z0-9_-]{16}_[A-Za-z0-9_-]{16})/);
  assert(issued);
  references[0] = issued[1];
  await bank.close();
  pass('读取网银二次确认中生成的随机签名编号用于登记');

  for (let index = 0; index < references.length; index += 1) {
    const reference = references[index];
    await form.getByLabel('业务流水号', { exact: true }).fill(reference);
    if (index === 0) await form.getByLabel('业务流水号', { exact: true }).press('Enter');
    else await form.getByRole('button', { name: '登记', exact: true }).click();
    const dialog = frame.getByRole('dialog', { name: '登记成功', exact: true });
    await dialog.waitFor();
    const summary = await dialog.getByRole('status').innerText();
    assert(summary.includes(reference));
    assert(summary.includes(values['转账账号']));
    assert(summary.includes('1223123.00'));
    assert(summary.includes(values['客户名称']));
    assert.equal(await page.getByRole('dialog').count(), 0);
    await dialog.getByRole('button', { name: /^确\s*定$/ }).click();
    await dialog.waitFor({ state: 'hidden' });
  }
  pass('网银和独立HMAC生成的编号全部通过，Enter及空选填项正常');

  await form.getByRole('button', { name: /^重\s*置$/ }).click();
  for (const label of ['业务流水号', ...Object.keys(values)]) assert.equal(await form.getByLabel(label, { exact: true }).inputValue(), '');
  pass('重置清空全部登记信息');

  await form.getByLabel('业务流水号', { exact: true }).fill(references[0]);
  await fillTransferValues();
  if (process.env.LOGIN_TEST_SCREENSHOT_DIR) {
    const directory = resolve(process.env.LOGIN_TEST_SCREENSHOT_DIR);
    await mkdir(directory, { recursive: true });
    await page.screenshot({ path: resolve(directory, 'registration.png'), animations: 'disabled', fullPage: true });
  }
  await page.setViewportSize({ width: 375, height: 812 });
  assert.equal(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth), true);
  assert.equal(await form.evaluate(() => document.documentElement.scrollWidth <= innerWidth), true);
  await form.getByRole('button', { name: '登记', exact: true }).click();
  const success = frame.getByRole('dialog', { name: '登记成功', exact: true });
  await success.waitFor();
  await success.getByRole('button', { name: /^确\s*定$/ }).hover();
  assert.equal(await form.evaluate(() => document.documentElement.scrollWidth <= innerWidth), true);
  if (process.env.LOGIN_TEST_SCREENSHOT_DIR) {
    await page.screenshot({ path: resolve(process.env.LOGIN_TEST_SCREENSHOT_DIR, 'registration-mobile.png'), animations: 'disabled', fullPage: true });
  }
  await success.getByRole('button', { name: /^确\s*定$/ }).click();
  pass('375px窄屏的外层、iframe表单及成功弹窗无横向溢出');

  await page.reload();
  await form.waitFor();
  assert.equal(await form.getByLabel('业务流水号', { exact: true }).inputValue(), '');
  assert.deepEqual(errors, []);
  assert.deepEqual(writes, []);
  pass('刷新不保留登记数据，无未处理异常或写入网络请求');
  console.log(`${passed} registration browser checks passed.`);
} finally {
  await browser.close();
}
