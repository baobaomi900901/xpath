import { randomId, shuffle } from './random';

export type TransferFieldKey = 'account' | 'amount' | 'customer' | 'bank' | 'branch' | 'routing' | 'purpose';
export type TransferValues = Record<TransferFieldKey, string>;

type FieldDefinition = {
  key: TransferFieldKey;
  label: string;
  required: boolean;
  inputMode: 'text' | 'numeric' | 'decimal';
  maxLength: number;
};

export const TRANSFER_FIELDS: FieldDefinition[] = [
  { key: 'account', label: '转账账号', required: true, inputMode: 'numeric', maxLength: 32 },
  { key: 'amount', label: '金额', required: true, inputMode: 'decimal', maxLength: 16 },
  { key: 'customer', label: '客户名称', required: true, inputMode: 'text', maxLength: 60 },
  { key: 'bank', label: '收款银行', required: true, inputMode: 'text', maxLength: 100 },
  { key: 'branch', label: '分行支行名称', required: true, inputMode: 'text', maxLength: 100 },
  { key: 'routing', label: '联行号', required: false, inputMode: 'numeric', maxLength: 12 },
  { key: 'purpose', label: '转账用途', required: false, inputMode: 'text', maxLength: 120 },
];

export type RandomAttributes = { id: string; className: string; name: string };

type FieldLayout = FieldDefinition & {
  container: RandomAttributes;
  labelAttributes: RandomAttributes;
  control: RandomAttributes;
  wrappers: RandomAttributes[];
};

export type TransferLayout = {
  form: RandomAttributes;
  grid: RandomAttributes;
  actions: RandomAttributes;
  fields: FieldLayout[];
  confirm: { control: RandomAttributes; wrappers: RandomAttributes[] };
};

function randomAttributes(): RandomAttributes {
  return { id: randomId(), className: `${randomId('c_')} ${randomId('c_')}`, name: randomId('n_') };
}

function randomWrappers(previousDepth?: number): RandomAttributes[] {
  const depths = [1, 2, 3, 4, 5].filter(depth => depth !== previousDepth);
  const depth = depths[Math.floor(Math.random() * depths.length)];
  return Array.from({ length: depth }, randomAttributes);
}

export function createTransferLayout(previous?: TransferLayout): TransferLayout {
  const fields = shuffle(TRANSFER_FIELDS);
  if (previous && fields.every((field, index) => field.key === previous.fields[index].key)) {
    fields.push(fields.shift()!);
  }
  return {
    form: randomAttributes(),
    grid: randomAttributes(),
    actions: randomAttributes(),
    fields: fields.map(field => ({
      ...field,
      container: randomAttributes(),
      labelAttributes: randomAttributes(),
      control: randomAttributes(),
      wrappers: randomWrappers(previous?.fields.find(item => item.key === field.key)?.wrappers.length),
    })),
    confirm: { control: randomAttributes(), wrappers: randomWrappers(previous?.confirm.wrappers.length) },
  };
}

export function emptyTransferValues(): TransferValues {
  return { account: '', amount: '', customer: '', bank: '', branch: '', routing: '', purpose: '' };
}

export function validateTransfer(values: TransferValues): string | null {
  const missing = TRANSFER_FIELDS.find(field => field.required && !values[field.key].trim());
  if (missing) return `${missing.label}不能为空`;
  if (!/^\d{6,32}$/.test(values.account.trim())) return '转账账号应为6–32位数字';
  if (!/^\d{1,12}(?:\.\d{1,2})?$/.test(values.amount.trim()) || Number(values.amount) <= 0) {
    return '请输入大于0、最多两位小数的有效金额';
  }
  return null;
}

export function formatTransferAmount(amount: string): string {
  const [whole, fraction = ''] = amount.trim().split('.');
  return `${BigInt(whole)}.${fraction.padEnd(2, '0')}`;
}
