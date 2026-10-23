const encoder = new TextEncoder();

function canonicalAmount(value) {
  const text = typeof value === 'string' ? value.trim() : '';
  if (!/^\d{1,12}(?:\.\d{1,2})?$/.test(text) || Number(text) <= 0) {
    throw new Error('请输入大于0、最多两位小数的有效金额');
  }
  const [whole, fraction = ''] = text.split('.');
  return `${BigInt(whole)}.${fraction.padEnd(2, '0')}`;
}

function cryptoEngine() {
  if (!globalThis.crypto?.subtle) {
    throw new Error('当前环境无法进行流水号校验，请使用 localhost 或 HTTPS 页面');
  }
  return globalThis.crypto;
}

function toBase64Url(bytes) {
  return btoa(String.fromCharCode(...bytes)).replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, '');
}

async function createSignature(amount, nonce, secret, prefix) {
  if (typeof secret !== 'string' || secret.length === 0) throw new Error('未配置流水号共享密钥');
  const engine = cryptoEngine();
  const key = await engine.subtle.importKey(
    'raw', encoder.encode(secret), { name: 'HMAC', hash: 'SHA-256' }, false, ['sign'],
  );
  const payload = encoder.encode(`${prefix}\n${amount}\n${nonce}`);
  const signature = await engine.subtle.sign('HMAC', key, payload);
  return toBase64Url(new Uint8Array(signature).subarray(0, 12));
}

export async function createTransferReference(amount, secret, prefix = 'bank-transfer:v2') {
  const normalized = canonicalAmount(amount);
  const nonce = toBase64Url(cryptoEngine().getRandomValues(new Uint8Array(12)));
  const signature = await createSignature(normalized, nonce, secret, prefix);
  return `TR_${nonce}_${signature}`;
}

export async function verifyTransferReference(reference, amount, secret, prefix = 'bank-transfer:v2') {
  const match = typeof reference === 'string' ? reference.match(/^TR_([A-Za-z0-9_-]{16})_([A-Za-z0-9_-]{16})$/) : null;
  if (!match) return false;
  let normalized;
  try { normalized = canonicalAmount(amount); } catch { return false; }
  const signature = await createSignature(normalized, match[1], secret, prefix);
  let difference = 0;
  for (let index = 0; index < signature.length; index += 1) {
    difference |= signature.charCodeAt(index) ^ match[2].charCodeAt(index);
  }
  return difference === 0;
}
