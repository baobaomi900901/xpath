import assert from 'node:assert/strict';
import { mkdir } from 'node:fs/promises';
import { createRequire } from 'node:module';
import { resolve } from 'node:path';

const require = createRequire(import.meta.url);
const { chromium } = require(process.env.LOGIN_PLAYWRIGHT_MODULE || 'playwright');
const referencePattern = /^TR_[A-Za-z0-9_-]{16}_[A-Za-z0-9_-]{16}$/;
const base = process.env.LOGIN_TEST_BASE_URL || 'http://127.0.0.1:7199/';
const browser = await chromium.launch({ channel: 'chrome', headless: true });
const page = await browser.newPage({ viewport: { width: 1280, height: 1000 } });
const errors = [];
const writes = [];
page.on('pageerror', error => errors.push(error.message));
page.on('request', request => { if (!['GET', 'HEAD'].includes(request.method())) writes.push(request.url()); });
let passed = 0;
const form = page.getByRole('form', { name: '网银转账', exact: true });
const values = {
  '转账账号': '6222021234567890123',
  '金额': '1234.56',
  '客户名称': '测试客户',
  '收款银行': '测试银行',
  '分行支行名称': '测试银行深圳科技支行',
  '联行号': '123456789012',
  '转账用途': '自动化测试款项',
};

function pass(name) { passed += 1; console.log(`PASS ${name}`); }

async function snapshot() {
  return form.evaluate(element => {
    function describe(control) {
      const parents = [];
      for (let parent = control.parentElement; parent && parent !== element; parent = parent.parentElement) {
        parents.push({ id: parent.id, className: parent.className });
      }
      return { id: control.id, className: control.className, name: control.getAttribute('name'), parents };
    }
    return {
      id: element.id,
      fields: Array.from(element.querySelectorAll('input')).map(input => ({
        label: input.labels[0]?.textContent.trim(), ...describe(input),
      })),
      confirm: describe(Array.from(element.querySelectorAll('button')).find(button => button.textContent.trim() === '转账')),
    };
  });
}

async function fillValues() {
  for (const [label, value] of Object.entries(values)) await form.getByLabel(label, { exact: true }).fill(value);
}

async function verifyValues() {
  for (const [label, value] of Object.entries(values)) assert.equal(await form.getByLabel(label, { exact: true }).inputValue(), value);
}

async function checkError(message) {
  await form.getByRole('button', { name: '转账', exact: true }).click();
  const dialog = page.getByRole('dialog', { name: '填写提示', exact: true });
  await dialog.waitFor();
  assert.match(await dialog.innerText(), message);
  await dialog.getByRole('button', { name: /^确\s*定$/ }).click();
  await dialog.waitFor({ state: 'hidden' });
}

async function receiptReference() {
  const status = await page.getByRole('status').innerText();
  const match = status.match(/业务流水号：(TR_[A-Za-z0-9_-]{16}_[A-Za-z0-9_-]{16})/);
  assert(match, '回执应显示业务流水号');
  return match[1];
}

async function confirmationReference() {
  const text = await page.getByRole('dialog', { name: '确认转账', exact: true }).innerText();
  const match = text.match(/业务流水号：(TR_[A-Za-z0-9_-]{16}_[A-Za-z0-9_-]{16})/);
  assert(match, '二次确认弹窗应显示业务流水号');
  return match[1];
}

try {
  await page.goto(`${base}login-test`);
  await page.getByLabel('账号', { exact: true }).fill('admin');
  await page.getByLabel('密码', { exact: true }).fill('1');
  await page.getByRole('button', { name: /^登\s*录$/ }).click();
  assert.equal(await form.count(), 1, '登录成功后应显示网银转账表单');
  assert.equal(await page.title(), '网银转账');
  assert.match(await page.locator('#login-status').innerText(), /admin/);
  assert.equal(await form.locator('input').count(), 7);
  for (const label of Object.keys(values)) assert.equal(await form.getByLabel(label, { exact: true }).count(), 1);
  pass('账号登录进入网银转账，七项表单均可按中文标签定位');

  let before = await snapshot();
  const ids = await form.locator('[id]').evaluateAll(elements => elements.map(element => element.id));
  assert.equal(new Set(ids).size, ids.length, '随机 id 不能重复');
  assert(before.fields.every(field => field.id && field.className && field.name));
  assert(before.fields.every(field => field.parents.every(parent => parent.id && parent.className)));
  assert(before.confirm.id && before.confirm.className);
  pass('字段、容器和转账按钮具备独立随机属性');

  await checkError(/不能为空/);
  await fillValues();
  assert.deepEqual(await snapshot(), before, '输入及校验不能改变结构');
  pass('输入和错误弹窗不会导致随机结构变化');

  for (let round = 0; round < 4; round += 1) {
    await form.getByRole('button', { name: /^重\s*置$/ }).click();
    const after = await snapshot();
    assert.notEqual(after.id, before.id);
    assert.notDeepEqual(after.fields.map(field => field.label), before.fields.map(field => field.label));
    for (const field of after.fields) {
      const previous = before.fields.find(item => item.label === field.label);
      assert.notEqual(field.id, previous.id);
      assert.notEqual(field.className, previous.className);
      assert.notEqual(field.name, previous.name);
      assert.notEqual(field.parents.length, previous.parents.length);
    }
    assert.notEqual(after.confirm.id, before.confirm.id);
    assert.notEqual(after.confirm.className, before.confirm.className);
    assert.notEqual(after.confirm.parents.length, before.confirm.parents.length);
    await verifyValues();
    before = after;
  }
  pass('连续四轮重建改变 id/class/name、字段顺序及嵌套深度，并保留全部输入');

  for (const amount of ['0', '-1', 'abc', '1.001', '1e3']) {
    await form.getByLabel('金额', { exact: true }).fill(amount);
    await checkError(/金额/);
  }
  await form.getByLabel('金额', { exact: true }).fill(values['金额']);
  await form.getByLabel('转账账号', { exact: true }).fill('bad-account');
  await checkError(/转账账号/);
  await form.getByLabel('转账账号', { exact: true }).fill(values['转账账号']);
  pass('金额和转账账号校验通过模态框反馈');

  await form.getByRole('button', { name: '转账', exact: true }).click();
  const confirmation = page.getByRole('dialog', { name: '确认转账', exact: true });
  await confirmation.waitFor();
  const previewReference = await confirmationReference();
  assert.match(previewReference, referencePattern);
  for (const value of Object.values(values)) assert((await confirmation.innerText()).includes(value));
  await confirmation.getByRole('button', { name: /^取\s*消$/ }).click();
  await confirmation.waitFor({ state: 'hidden' });
  await verifyValues();
  assert.deepEqual(await snapshot(), before);
  pass('确认摘要与输入一致，取消后数据和随机结构不变');

  if (process.env.LOGIN_TEST_SCREENSHOT_DIR) {
    const directory = resolve(process.env.LOGIN_TEST_SCREENSHOT_DIR);
    await mkdir(directory, { recursive: true });
    await page.screenshot({ path: resolve(directory, 'bank-transfer.png'), animations: 'disabled', fullPage: true });
    await page.setViewportSize({ width: 375, height: 812 });
    await page.screenshot({ path: resolve(directory, 'bank-transfer-mobile.png'), animations: 'disabled', fullPage: true });
  } else await page.setViewportSize({ width: 375, height: 812 });
  assert.equal(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth), true);
  await form.getByRole('button', { name: '转账', exact: true }).click();
  await confirmation.waitFor();
  const confirmedReference = await confirmationReference();
  assert.notEqual(confirmedReference, previewReference, '重新发起转账应生成新的随机流水号');
  assert.equal(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth), true);
  if (process.env.LOGIN_TEST_SCREENSHOT_DIR) {
    await confirmation.getByRole('button', { name: '确认提交', exact: true }).hover();
    await page.waitForFunction(element => getComputedStyle(element).opacity === '1', await confirmation.elementHandle());
    await page.screenshot({ path: resolve(process.env.LOGIN_TEST_SCREENSHOT_DIR, 'bank-transfer-confirmation-mobile.png'), animations: 'disabled', fullPage: true });
  }
  await confirmation.getByRole('button', { name: '确认提交', exact: true }).click();
  await page.getByText('转账成功', { exact: true }).waitFor();
  assert.equal(await form.count(), 0);
  assert((await page.getByRole('status').innerText()).includes(values['转账账号']));
  assert.match(await receiptReference(), referencePattern);
  assert.equal(await receiptReference(), confirmedReference, '最终回执必须与二次确认弹窗的流水号一致');
  pass('窄屏表单及确认无溢出，提交后显示成功回执');

  await page.getByRole('button', { name: '继续转账', exact: true }).click();
  for (const label of Object.keys(values)) assert.equal(await form.getByLabel(label, { exact: true }).inputValue(), '');
  assert.notEqual((await snapshot()).id, before.id);
  pass('继续转账清空业务值并生成新一轮随机结构');

  const issued = [previewReference, confirmedReference];
  for (let index = 0; index < 3; index += 1) {
    await fillValues();
    await form.getByRole('button', { name: '转账', exact: true }).click();
    await confirmation.waitFor();
    const pendingReference = await confirmationReference();
    assert.match(pendingReference, referencePattern);
    await confirmation.getByRole('button', { name: '确认提交', exact: true }).click();
    await page.getByText('转账成功', { exact: true }).waitFor();
    const reference = await receiptReference();
    assert.equal(reference, pendingReference);
    issued.push(reference);
    await page.getByRole('button', { name: '继续转账', exact: true }).click();
  }
  assert.equal(new Set(issued).size, issued.length);
  pass('同一金额的多笔转账生成不同随机签名流水号，弹窗与回执编号一致');

  const accountLayout = await snapshot();
  await page.getByRole('button', { name: '退出登录', exact: true }).click();
  await page.getByRole('tab', { name: '手机验证码登录', exact: true }).click();
  await page.getByLabel('手机号', { exact: true }).fill('13922832244');
  await page.getByRole('button', { name: '发送验证码', exact: true }).click();
  await page.getByLabel('验证码', { exact: true }).fill('1990');
  await page.getByRole('button', { name: /^登\s*录$/ }).click();
  await form.waitFor();
  assert.match(await page.locator('#login-status').innerText(), /13922832244/);
  assert.notEqual((await snapshot()).id, accountLayout.id);
  pass('手机登录也进入转账页，并为新会话重新生成结构');

  await page.reload();
  await page.getByRole('tab', { name: '账号登录', exact: true }).waitFor();
  assert.equal(await form.count(), 0);
  assert.deepEqual(errors, []);
  assert.deepEqual(writes, [], '转账模拟不能发出支付或其他写入网络请求');
  pass('刷新退出会话，全流程无异常及写入网络请求');
  console.log(`${passed} bank transfer browser checks passed.`);
} finally {
  await browser.close();
}
