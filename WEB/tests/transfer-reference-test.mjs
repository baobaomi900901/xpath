import assert from 'node:assert/strict';
import { createHmac } from 'node:crypto';
import { readFile } from 'node:fs/promises';
import test from 'node:test';
import { createTransferReference, verifyTransferReference } from '../shared/transferReference.mjs';

const config = JSON.parse(await readFile(new URL('../../fixtures/bank-transfer-auth.json', import.meta.url), 'utf8'));
const { sharedKey, payloadPrefix } = config;
const create = amount => createTransferReference(amount, sharedKey, payloadPrefix);
const verify = (reference, amount, key = sharedKey) => verifyTransferReference(reference, amount, key, payloadPrefix);

test('签名与独立Node HMAC计算一致，金额统一到两位小数', async () => {
  const reference = await create('00100.0');
  assert.equal(reference.length, 36);
  assert.match(reference, /^TR_[A-Za-z0-9_-]{16}_[A-Za-z0-9_-]{16}$/);
  const nonce = reference.slice(3, 19);
  const signature = reference.slice(20);
  assert.equal(signature, createHmac('sha256', sharedKey).update(`${payloadPrefix}\n100.00\n${nonce}`, 'utf8').digest().subarray(0, 12).toString('base64url'));
  assert.equal(await verify(reference, '100'), true);
  assert.equal(await verify(reference, '100.00'), true);
  assert.equal(await verify(reference, ' 0100.0 '), true);
});

test('篡改编号、随机因子、金额或密钥均无法通过', async () => {
  const reference = await create('1234.56');
  const altered = reference.slice(0, -1) + (reference.endsWith('0') ? '1' : '0');
  assert.equal(await verify(altered, '1234.56'), false);
  const alteredNonce = reference.slice(0, 3) + (reference[3] === '0' ? '1' : '0') + reference.slice(4);
  assert.equal(await verify(alteredNonce, '1234.56'), false);
  assert.equal(await verify(reference, '1234.57'), false);
  assert.equal(await verify(reference, '1234.56', 'different-key'), false);
});

test('Base64URL随机因子含下划线和连字符时仍能验签', async () => {
  const nonce = '_-'.repeat(8);
  const signature = createHmac('sha256', sharedKey).update(`${payloadPrefix}\n1.00\n${nonce}`, 'utf8').digest().subarray(0, 12).toString('base64url');
  assert.equal(await verify(`TR_${nonce}_${signature}`, '1'), true);
});

test('旧固定编号、乱填及前后空格不能通过', async () => {
  const reference = await create('100');
  for (const invalid of ['TR_s883X66VL51V', `TR_${'a'.repeat(32)}_${'b'.repeat(64)}`, 'anything', ` ${reference}`, `${reference} `, reference.toUpperCase()]) {
    assert.equal(await verify(invalid, '100'), false);
  }
});

test('相同金额连续256次生成不同随机编号', async () => {
  const references = await Promise.all(Array.from({ length: 256 }, () => create('100.00')));
  assert.equal(new Set(references).size, 256);
});

test('非法金额不能签名或通过验签', async () => {
  const reference = await create('100');
  for (const amount of ['', '0', '-1', 'abc', '1e2', '1.001']) {
    await assert.rejects(() => create(amount), /金额/);
    assert.equal(await verify(reference, amount), false);
  }
});
