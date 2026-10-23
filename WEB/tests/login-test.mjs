import assert from 'node:assert/strict';
import { mkdir } from 'node:fs/promises';
import { createRequire } from 'node:module';
import { resolve } from 'node:path';

const require = createRequire(import.meta.url);
const { chromium } = require(process.env.LOGIN_PLAYWRIGHT_MODULE || 'playwright');
// Point this at a running dev server, or /xpath/#/ on a Pages preview.
const base = process.env.LOGIN_TEST_BASE_URL || 'http://127.0.0.1:7199/';
const browser = await chromium.launch({ channel: 'chrome', headless: true });
const page = await browser.newPage({ viewport: { width: 1280, height: 900 } });
const errors = [];
page.on('pageerror', error => errors.push(error.message));
let passed = 0;

function pass(name) {
  passed += 1;
  console.log(`PASS ${name}`);
}

async function fill(identity, secret) {
  const phoneMode = await page.getByRole('tab', { name: '手机验证码登录' }).getAttribute('aria-selected') === 'true';
  await page.getByLabel(phoneMode ? '手机号' : '账号', { exact: true }).fill(identity);
  if (phoneMode) await page.getByRole('button', { name: '发送验证码', exact: true }).click();
  await page.getByLabel(phoneMode ? '验证码' : '密码', { exact: true }).fill(secret);
}

async function expectSendError(identity) {
  await page.getByLabel('手机号', { exact: true }).fill(identity);
  await page.getByRole('button', { name: '发送验证码', exact: true }).click();
  const dialog = page.getByRole('dialog', { name: '登录失败' });
  await dialog.waitFor();
  assert.equal(await dialog.locator('[role="alert"]').innerText(), '手机号错误');
  await dialog.getByRole('button', { name: /^确\s*定$/ }).click();
  await dialog.waitFor({ state: 'hidden' });
  assert.equal(await page.getByLabel('验证码', { exact: true }).isDisabled(), true);
  assert.equal(await page.getByRole('button', { name: /^登\s*录$/ }).isDisabled(), true);
  pass(`发送验证码校验手机号: ${JSON.stringify(identity)}`);
}

async function expectError(identity, secret, message, { enter = false, escape = false } = {}) {
  await fill(identity, secret);
  if (enter) await page.getByLabel('密码', { exact: true }).press('Enter');
  else await page.getByRole('button', { name: /^登\s*录$/ }).click();
  const dialog = page.getByRole('dialog', { name: '登录失败' });
  await dialog.waitFor();
  assert.equal(await dialog.locator('[role="alert"]').innerText(), message);
  assert.equal(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth), true,
    '错误弹窗不能造成横向溢出');
  if (escape) await dialog.getByRole('button', { name: /^确\s*定$/ }).press('Escape');
  else await dialog.getByRole('button', { name: /^确\s*定$/ }).click();
  await dialog.waitFor({ state: 'hidden' });
  const phoneMode = await page.getByRole('tab', { name: '手机验证码登录' }).getAttribute('aria-selected') === 'true';
  assert.equal(await page.getByLabel(phoneMode ? '手机号' : '账号', { exact: true }).inputValue(), identity);
  assert.equal(await page.getByLabel(phoneMode ? '验证码' : '密码', { exact: true }).inputValue(), secret);
  pass(`${message}: ${JSON.stringify([identity, secret])}`);
}

try {
  await page.goto(base);
  await page.waitForLoadState('networkidle');
  assert.equal(await page.locator('#menu-login-test').count(), 1, '首页应包含登录测试入口');
  const popupPromise = page.waitForEvent('popup');
  await page.locator('#menu-login-test').click();
  const popup = await popupPromise;
  await popup.waitForLoadState('domcontentloaded');
  assert.equal(popup.url(), `${base}login-test`);
  await popup.close();
  pass('首页入口打开登录测试');

  await page.goto(`${base}login-test`);
  await page.getByRole('button', { name: /^登\s*录$/ }).waitFor();
  assert.equal(await page.title(), '登录测试');
  assert.equal(await page.getByRole('tab', { name: '账号登录', exact: true }).getAttribute('aria-selected'), 'true');
  assert.equal(await page.getByLabel('密码', { exact: true }).getAttribute('type'), 'password');
  pass('默认账号登录，密码隐藏');

  const loginButton = page.getByRole('button', { name: /^登\s*录$/ });
  assert.equal(await loginButton.isDisabled(), true);
  await fill('admin', '');
  assert.equal(await loginButton.isDisabled(), true);
  await fill('', '1');
  assert.equal(await loginButton.isDisabled(), true);
  await page.getByLabel('密码', { exact: true }).press('Enter');
  await page.locator('#login-form').evaluate(form => form.requestSubmit());
  assert.equal(await page.getByRole('dialog').count(), 0);
  assert.equal(await page.getByRole('form', { name: '网银转账', exact: true }).count(), 0);
  pass('账号或密码为空时登录禁用，Enter 不能绕过');

  await fill('wrong', 'wrong');
  assert.equal(await loginButton.isEnabled(), true);
  pass('账号和密码都有值时启用登录');

  await page.getByLabel('密码', { exact: true }).fill('');
  assert.equal(await loginButton.isDisabled(), true);
  await page.getByLabel('密码', { exact: true }).fill('wrong');
  assert.equal(await loginButton.isEnabled(), true);
  await page.getByLabel('账号', { exact: true }).fill('');
  assert.equal(await loginButton.isDisabled(), true);
  pass('清空任意账号字段都会重新禁用登录');

  await expectError('wrong', 'wrong', '账号错误');
  await expectError('admin', 'wrong', '密码错误', { enter: true, escape: true });
  await expectError('admin ', '1', '账号错误');
  await expectError('admin', '01', '密码错误');

  await fill('admin', '1');
  await page.getByLabel('密码', { exact: true }).press('Enter');
  await page.getByRole('form', { name: '网银转账', exact: true }).waitFor();
  assert.match(await page.locator('#login-status').innerText(), /admin/);
  await page.getByRole('button', { name: '退出登录', exact: true }).click();
  assert.equal(await page.getByLabel('账号', { exact: true }).inputValue(), '');
  assert.equal(await page.getByLabel('密码', { exact: true }).inputValue(), '');
  assert.equal(await loginButton.isDisabled(), true);
  pass('账号登录成功，退出清空表单');

  await fill('admin', '1');
  await page.getByRole('tab', { name: '手机验证码登录' }).click();
  await page.getByLabel('手机号', { exact: true }).waitFor();
  assert.equal(await page.getByLabel('手机号', { exact: true }).inputValue(), '');
  assert.equal(await page.getByLabel('验证码', { exact: true }).inputValue(), '');
  pass('切换到手机验证码登录');

  assert.equal(await page.getByLabel('验证码', { exact: true }).isDisabled(), true);
  assert.equal(await page.getByRole('button', { name: /^登\s*录$/ }).isDisabled(), true);
  const codeBox = await page.getByLabel('验证码', { exact: true }).boundingBox();
  const sendBox = await page.getByRole('button', { name: '发送验证码', exact: true }).boundingBox();
  assert(codeBox && sendBox && sendBox.x >= codeBox.x + codeBox.width, '发送按钮应在验证码输入框右侧');
  pass('验证码输入框和登录默认禁用，发送按钮在右侧');

  await page.getByLabel('手机号', { exact: true }).fill('13922832244');
  assert.equal(await page.getByLabel('验证码', { exact: true }).isDisabled(), true);
  assert.equal(await page.getByRole('button', { name: /^登\s*录$/ }).isDisabled(), true);
  await page.getByLabel('手机号', { exact: true }).press('Enter');
  await page.locator('#login-form').evaluate(form => form.requestSubmit());
  assert.equal(await page.getByRole('form', { name: '网银转账', exact: true }).count(), 0);
  assert.equal(await page.getByRole('dialog').count(), 0);
  pass('仅填写手机号或按 Enter 不会绕过发送步骤');

  await page.getByRole('button', { name: '发送验证码', exact: true }).click();
  assert.equal(await page.getByLabel('验证码', { exact: true }).isEnabled(), true);
  assert.equal(await page.getByRole('button', { name: /^登\s*录$/ }).isEnabled(), true);
  pass('点击发送验证码后解锁输入和登录');

  await page.getByLabel('验证码', { exact: true }).fill('1990');
  await page.getByLabel('手机号', { exact: true }).fill('13922832245');
  assert.equal(await page.getByLabel('验证码', { exact: true }).inputValue(), '');
  assert.equal(await page.getByLabel('验证码', { exact: true }).isDisabled(), true);
  assert.equal(await page.getByRole('button', { name: /^登\s*录$/ }).isDisabled(), true);
  await page.getByLabel('手机号', { exact: true }).fill('13922832244');
  assert.equal(await page.getByLabel('验证码', { exact: true }).isDisabled(), true);
  pass('修改手机号清空验证码并重新禁用，改回仍需重新发送');

  await expectSendError('');
  await expectSendError('13800000000');
  await expectSendError('13922832244 ');
  await expectError('13922832244', '', '验证码错误');
  await expectError('13922832244', '0000', '验证码错误');
  await expectError('13922832244', '01990', '验证码错误');

  await fill('13922832244', '1990');
  await page.getByLabel('验证码', { exact: true }).press('Enter');
  await page.getByRole('form', { name: '网银转账', exact: true }).waitFor();
  assert.match(await page.locator('#login-status').innerText(), /13922832244/);
  await page.getByRole('button', { name: '退出登录', exact: true }).click();
  assert.equal(await page.getByLabel('手机号', { exact: true }).inputValue(), '');
  assert.equal(await page.getByLabel('验证码', { exact: true }).inputValue(), '');
  assert.equal(await page.getByLabel('验证码', { exact: true }).isDisabled(), true);
  assert.equal(await page.getByRole('button', { name: /^登\s*录$/ }).isDisabled(), true);
  pass('手机登录成功，退出清空表单');

  await fill('13922832244', '1990');
  await page.getByRole('tab', { name: '账号登录', exact: true }).click();
  await page.getByLabel('账号', { exact: true }).waitFor();
  assert.equal(await page.getByLabel('账号', { exact: true }).inputValue(), '');
  assert.equal(await page.getByLabel('密码', { exact: true }).inputValue(), '');
  assert.equal(await loginButton.isDisabled(), true);
  await page.getByRole('tab', { name: '手机验证码登录' }).click();
  await page.getByLabel('手机号', { exact: true }).waitFor();
  assert.equal(await page.getByLabel('手机号', { exact: true }).inputValue(), '');
  assert.equal(await page.getByLabel('验证码', { exact: true }).inputValue(), '');
  assert.equal(await page.getByLabel('验证码', { exact: true }).isDisabled(), true);
  assert.equal(await page.getByRole('button', { name: /^登\s*录$/ }).isDisabled(), true);
  pass('往返切换不会保留旧凭据');

  await page.setViewportSize({ width: 375, height: 812 });
  assert.equal(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth), true);
  await expectError('13922832244', 'bad', '验证码错误');
  assert.equal(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth), true);
  pass('手机窄屏页面和弹窗无横向溢出');

  await page.reload();
  await page.getByLabel('账号', { exact: true }).waitFor();
  assert.equal(await page.getByLabel('账号', { exact: true }).inputValue(), '');
  assert.equal(await loginButton.isDisabled(), true);
  pass('刷新回到初始登录状态');

  if (process.env.LOGIN_TEST_SCREENSHOT_DIR) {
    const directory = resolve(process.env.LOGIN_TEST_SCREENSHOT_DIR);
    await mkdir(directory, { recursive: true });
    await page.screenshot({ path: resolve(directory, 'login-mobile.png'), animations: 'disabled', fullPage: true });
    await page.setViewportSize({ width: 1280, height: 900 });
    await page.screenshot({ path: resolve(directory, 'login-account.png'), animations: 'disabled', fullPage: true });
    await page.getByRole('tab', { name: '手机验证码登录' }).click();
    await page.screenshot({ path: resolve(directory, 'login-phone-disabled.png'), animations: 'disabled', fullPage: true });
    await fill('13922832244', 'wrong');
    await page.getByRole('button', { name: /^登\s*录$/ }).click();
    await page.getByRole('dialog', { name: '登录失败' }).getByRole('button', { name: /^确\s*定$/ }).hover();
    await page.screenshot({ path: resolve(directory, 'login-error.png'), animations: 'disabled', fullPage: true });
  }
  assert.deepEqual(errors, [], '页面不能出现未处理的 JavaScript 错误');
  console.log(`${passed} login browser checks passed.`);
} finally {
  await browser.close();
}
