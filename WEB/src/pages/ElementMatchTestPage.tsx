import { useState } from 'react';
import { Alert, Button, Card, Input, Space, Typography } from 'antd';
import PageLayout from '../components/PageLayout';
import { randomStr } from '../utils/random';

type Sample = { key: string; label: string; id: string; value: string; group: 'string' | 'number' };
type Rule = {
  key: string;
  name: string;
  attribute: 'id' | 'data-value';
  pattern: string;
  positive: string;
  negative: string;
};

const FIXED_SAMPLES: Sample[] = [
  { key: 'exact', label: '固定字符串', id: 'abc-fixed-xyz', value: 'abc-fixed-xyz', group: 'string' },
  { key: 'other', label: '不同前后缀', id: 'def-fixed-uvw', value: 'def-fixed-uvw', group: 'string' },
  { key: 'case', label: '大小写对照', id: 'Abc-fixed-XYZ', value: 'Abc-fixed-XYZ', group: 'string' },
  ...[2, 99, 100, 101, 1000].map(value => ({
    key: `number-${value}`, label: `数值 ${value}`, id: `match-number-${value}`, value: String(value), group: 'number' as const,
  })),
];

function createGeneration(length: number) {
  const prefix = `abc${randomStr(length)}`;
  const suffix = `${randomStr(length)}xyz`;
  const both = `abc${randomStr(length)}xyz`;
  const samples: Sample[] = [
    { key: 'prefix', label: '固定开头 + 随机码', id: prefix, value: prefix, group: 'string' },
    { key: 'suffix', label: '随机码 + 固定结尾', id: suffix, value: suffix, group: 'string' },
    { key: 'both', label: '固定开头 + 随机码 + 固定结尾', id: both, value: both, group: 'string' },
    ...FIXED_SAMPLES,
  ];
  return { length, samples };
}

function createRules(length: number): Rule[] {
  return [
    { key: 'equals', name: '等于', attribute: 'id', pattern: 'abc-fixed-xyz', positive: 'exact', negative: 'other' },
    { key: 'not-equals', name: '不等于', attribute: 'id', pattern: 'abc-fixed-xyz', positive: 'other', negative: 'exact' },
    { key: 'contains', name: '包含', attribute: 'id', pattern: '-fixed-', positive: 'exact', negative: 'both' },
    { key: 'not-contains', name: '不包含', attribute: 'id', pattern: '-fixed-', positive: 'both', negative: 'exact' },
    { key: 'starts-with', name: '开头为', attribute: 'id', pattern: 'abc', positive: 'prefix', negative: 'other' },
    { key: 'not-starts-with', name: '开头不为', attribute: 'id', pattern: 'abc', positive: 'other', negative: 'prefix' },
    { key: 'ends-with', name: '结尾为', attribute: 'id', pattern: 'xyz', positive: 'suffix', negative: 'other' },
    { key: 'not-ends-with', name: '结尾不为', attribute: 'id', pattern: 'xyz', positive: 'other', negative: 'suffix' },
    { key: 'greater', name: '大于', attribute: 'data-value', pattern: '100', positive: 'number-101', negative: 'number-100' },
    { key: 'greater-equal', name: '大于等于', attribute: 'data-value', pattern: '100', positive: 'number-100', negative: 'number-99' },
    { key: 'less', name: '小于', attribute: 'data-value', pattern: '100', positive: 'number-99', negative: 'number-100' },
    { key: 'less-equal', name: '小于等于', attribute: 'data-value', pattern: '100', positive: 'number-100', negative: 'number-101' },
    { key: 'regex', name: '正则', attribute: 'id', pattern: `^abc[A-Za-z0-9]{${length}}xyz$`, positive: 'both', negative: 'exact' },
    { key: 'wildcard', name: '通配符', attribute: 'id', pattern: 'abc*xyz', positive: 'both', negative: 'other' },
  ];
}

export default function ElementMatchTestPage() {
  const [lengthInput, setLengthInput] = useState('8');
  const [generation, setGeneration] = useState(() => createGeneration(8));
  const [clickResult, setClickResult] = useState('尚未点击靶元素');
  const length = Number(lengthInput);
  const validLength = lengthInput.trim() !== '' && Number.isInteger(length) && length >= 1 && length <= 32;
  const byKey = Object.fromEntries(generation.samples.map(sample => [sample.key, sample]));
  const rules = createRules(generation.length);

  return (
    <PageLayout title="元素串匹配测试" subtitle="使用真实按钮的 id、title、data-value 和文本，验证元素定位时的匹配规则" fullWidth>
      <Space direction="vertical" size={20} style={{ width: '100%', minWidth: 0 }}>
        <Card title="随机样本设置">
          <div className="match-settings">
            <label htmlFor="match-random-length">随机码位数（1–32）</label>
            <Input
              id="match-random-length"
              type="number"
              min={1}
              max={32}
              step={1}
              value={lengthInput}
              status={validLength ? undefined : 'error'}
              aria-invalid={!validLength}
              aria-describedby="match-length-help"
              onChange={event => setLengthInput(event.target.value)}
              style={{ width: 120 }}
            />
            <Button id="match-regenerate" type="primary" disabled={!validLength} onClick={() => {
              setGeneration(createGeneration(length));
              setClickResult('尚未点击靶元素');
            }}>重新生成</Button>
          </div>
          <Typography.Paragraph id="match-length-help" type={validLength ? 'secondary' : 'danger'} style={{ margin: '12px 0 0' }}>
            {validLength
              ? `当前样本随机码为 ${generation.length} 位，字符为 A–Z、a–z、0–9。修改位数后点击重新生成；刷新页面恢复 8 位并生成新值。`
              : '请输入 1 到 32 之间的整数，点击重新生成后应用。'}
          </Typography.Paragraph>
        </Card>

        <Card title="靶元素" id="match-targets">
          <Typography.Paragraph type="secondary">
            按钮文字、title、data-value 均为下方显示的值；字符串按钮的 id 也为该值。固定样本不会随重新生成而变化。
          </Typography.Paragraph>
          <div className="match-sample-grid">
            {generation.samples.map(sample => (
              <div key={sample.key} className="match-sample" data-sample-group={sample.group}>
                <div className="match-sample-label">{sample.label}</div>
                <button
                  type="button"
                  className="match-target"
                  id={sample.id}
                  title={sample.value}
                  data-value={sample.value}
                  data-sample={sample.key}
                  onClick={() => setClickResult(`已点击「${sample.label}」：id=${sample.id}，data-value=${sample.value}`)}
                >{sample.value}</button>
                <div className="match-sample-id">id：<code>{sample.id}</code></div>
              </div>
            ))}
          </div>
          <div id="match-click-result" role="status" className="match-click-result">{clickResult}</div>
        </Card>

        <Card title="14 种规则参考">
          <Alert
            type="info"
            showIcon
            message="使用你的自动化工具执行匹配，对照下表检查结果"
            description="字符串示例区分大小写；数值示例将 data-value 按数值比较，阈值为 100。请将查找范围限定在对应的字符串或数值靶元素内，否定规则可能命中多个元素。表中每行各列出一个正例和反例。"
          />
          <div className="match-rule-scroll" role="region" aria-label="匹配规则参考表" tabIndex={0}>
            <table className="match-rule-table">
              <thead>
                <tr><th scope="col">规则</th><th scope="col">比较属性</th><th scope="col">条件值</th><th scope="col">应命中的值（正例）</th><th scope="col">不应命中的值（反例）</th></tr>
              </thead>
              <tbody>
                {rules.map(rule => {
                  const positive = byKey[rule.positive];
                  const negative = byKey[rule.negative];
                  return (
                    <tr key={rule.key} data-rule={rule.key} data-attribute={rule.attribute} data-positive={rule.positive} data-negative={rule.negative}>
                      <th scope="row">{rule.name}</th>
                      <td><code>{rule.attribute}</code></td>
                      <td><code>{rule.pattern}</code></td>
                      <td><code data-expect="positive">{rule.attribute === 'id' ? positive.id : positive.value}</code></td>
                      <td><code data-expect="negative">{rule.attribute === 'id' ? negative.id : negative.value}</code></td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
          <Typography.Paragraph type="secondary" style={{ marginBottom: 0 }}>
            通配符按整串匹配：<code>*</code> 代表任意长度字符，<code>?</code> 代表单个字符。
            还可用 <code id="match-wildcard-single">{`abc${'?'.repeat(generation.length)}xyz`}</code> 匹配「固定开头 + 随机码 + 固定结尾」。
            数值 2 和 1000 可用于区分数值比较与字符串字典序比较；大小写对照样本可验证工具的大小写设置。
          </Typography.Paragraph>
        </Card>
      </Space>
    </PageLayout>
  );
}
