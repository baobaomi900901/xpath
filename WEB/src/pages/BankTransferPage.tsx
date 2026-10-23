import { useState, type CSSProperties, type FormEvent, type ReactNode } from 'react';
import { Button, Descriptions, Modal, Result, Tag, Typography } from 'antd';
import PageLayout from '../components/PageLayout';
import { createTransferReference } from '../utils/transferReceipt';
import {
  createTransferLayout,
  emptyTransferValues,
  formatTransferAmount,
  TRANSFER_FIELDS,
  validateTransfer,
  type RandomAttributes,
  type TransferValues,
} from '../utils/transferForm';

type BankTransferPageProps = { identity: string; loginMethod: string; onLogout: () => void };
type Receipt = { values: TransferValues; reference: string };

const inputStyle: CSSProperties = {
  width: '100%', minWidth: 0, boxSizing: 'border-box', height: 42,
  padding: '8px 12px', border: '1px solid #cbd5e1', borderRadius: 6,
  background: '#fff', color: '#0f172a', font: 'inherit',
};

function wrapControl(control: ReactNode, wrappers: RandomAttributes[]): ReactNode {
  return wrappers.reduceRight<ReactNode>((child, attributes) => (
    <div key={attributes.id} {...attributes}>{child}</div>
  ), control);
}

function TransferSummary({ values }: { values: TransferValues }) {
  return (
    <Descriptions
      column={1}
      size="small"
      items={TRANSFER_FIELDS.map(field => ({
        key: field.key,
        label: field.label,
        children: <span style={{ overflowWrap: 'anywhere' }}>
          {field.key === 'amount' ? `${formatTransferAmount(values.amount)} 元` : values[field.key] || '—'}
        </span>,
      }))}
    />
  );
}

export default function BankTransferPage({ identity, loginMethod, onLogout }: BankTransferPageProps) {
  const [layout, setLayout] = useState(() => createTransferLayout());
  const [values, setValues] = useState(emptyTransferValues);
  const [error, setError] = useState<string | null>(null);
  const [pending, setPending] = useState<Receipt | null>(null);
  const [receipt, setReceipt] = useState<Receipt | null>(null);
  const [generating, setGenerating] = useState(false);

  const rebuild = () => {
    setLayout(previous => createTransferLayout(previous));
  };

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (generating) return;
    const message = validateTransfer(values);
    if (message) {
      setError(message);
      return;
    }
    const submitted = Object.fromEntries(Object.entries(values).map(([key, value]) => [key, value.trim()])) as TransferValues;
    setGenerating(true);
    try {
      const reference = await createTransferReference(submitted.amount);
      setPending({ values: submitted, reference });
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : '无法生成业务流水号，请重试');
    } finally {
      setGenerating(false);
    }
  };

  return (
    <PageLayout
      title="网银转账"
      titleExtra={<Tag color="blue">模拟环境</Tag>}
      subtitle="个人网上银行 / 转账汇款 / 单笔转账"
      maxWidth={1000}
      extra={
        <div style={{ display: 'flex', justifyContent: 'space-between', flexWrap: 'wrap', gap: 12, marginBottom: 24 }}>
          <span id="login-status" style={{ color: '#64748b', overflowWrap: 'anywhere' }}>
            当前客户：{identity} · {loginMethod}
          </span>
          <Button id="login-logout" onClick={onLogout}>退出登录</Button>
        </div>
      }
    >
      <div style={{ padding: '20px 24px', background: '#153b70', borderRadius: 8, color: '#fff', marginBottom: 24 }}>
        <div style={{ fontSize: 20, fontWeight: 600, marginBottom: 6 }}>转账汇款</div>
        <div style={{ color: '#dbeafe' }}>人民币 CNY · 本地模拟转账</div>
      </div>

      {receipt ? (
        <>
          <Result status="success" title="转账成功" subTitle="模拟转账已完成" />
          <div role="status" style={{ padding: 20, background: '#f8fafc', borderRadius: 8 }}>
            <Typography.Paragraph style={{ overflowWrap: 'anywhere' }}>业务流水号：{receipt.reference}</Typography.Paragraph>
            <TransferSummary values={receipt.values} />
          </div>
          <Button type="primary" style={{ marginTop: 24 }} onClick={() => {
            setReceipt(null);
            setValues(emptyTransferValues());
            rebuild();
          }}>继续转账</Button>
        </>
      ) : (
        <>
          <Typography.Title level={4} style={{ marginTop: 0, marginBottom: 12 }}>填写转账信息</Typography.Title>
          <Typography.Paragraph type="secondary" style={{ marginBottom: 24 }}>
            带 * 为必填项。点击“重置”会保留已填内容，并重新生成控件特征、顺序和嵌套结构。
          </Typography.Paragraph>
          <form {...layout.form} aria-label="网银转账" autoComplete="off" noValidate onSubmit={handleSubmit}>
            <div {...layout.grid} style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(min(100%, 280px), 1fr))', gap: '24px 32px' }}>
              {layout.fields.map(field => (
                <div key={field.key} {...field.container} style={{ minWidth: 0 }}>
                  <label {...field.labelAttributes} htmlFor={field.control.id} style={{ display: 'inline-block', fontWeight: 500, marginBottom: 8 }}>
                    {field.label}
                  </label>
                  {field.required ? <span aria-hidden="true" style={{ color: '#dc2626', marginLeft: 4 }}>*</span> : null}
                  {wrapControl(
                    <input
                      {...field.control}
                      type="text"
                      required={field.required}
                      disabled={generating}
                      inputMode={field.inputMode}
                      maxLength={field.maxLength}
                      placeholder={field.key === 'amount' ? '请输入金额（元）' : `请输入${field.label}`}
                      value={values[field.key]}
                      onChange={event => setValues(previous => ({ ...previous, [field.key]: event.target.value }))}
                      style={inputStyle}
                    />,
                    field.wrappers,
                  )}
                </div>
              ))}
            </div>
            <div {...layout.actions} style={{ marginTop: 32, paddingTop: 24, borderTop: '1px solid #e2e8f0', display: 'flex', justifyContent: 'center', alignItems: 'center', gap: 12 }}>
              <Button htmlType="button" size="large" style={{ minWidth: 124 }} disabled={generating} onClick={rebuild}>重置</Button>
              {wrapControl(
                <button {...layout.confirm.control} type="submit" disabled={generating} aria-busy={generating} style={{
                  border: 0, borderRadius: 6, background: '#1677ff', color: '#fff', cursor: 'pointer',
                  padding: '10px 48px', font: 'inherit', fontWeight: 500,
                }}>转账</button>,
                layout.confirm.wrappers,
              )}
            </div>
          </form>
        </>
      )}

      <Modal title="填写提示" open={error !== null} centered maskClosable={false} onCancel={() => setError(null)}
        footer={<Button type="primary" onClick={() => setError(null)}>确定</Button>}>
        <p role="alert">{error}</p>
      </Modal>
      <Modal title="确认转账" open={pending !== null} centered maskClosable={false} onCancel={() => setPending(null)}
        footer={[
          <Button key="cancel" onClick={() => setPending(null)}>取消</Button>,
          <Button key="confirm" type="primary" onClick={() => {
            if (!pending) return;
            setReceipt(pending);
            setPending(null);
          }}>确认提交</Button>,
        ]}>
        {pending ? (
          <>
            <Typography.Paragraph style={{ overflowWrap: 'anywhere' }}>业务流水号：{pending.reference}</Typography.Paragraph>
            <TransferSummary values={pending.values} />
          </>
        ) : null}
      </Modal>
    </PageLayout>
  );
}
