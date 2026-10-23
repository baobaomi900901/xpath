import { useEffect, useState, type FormEvent } from 'react';
import { Button, Descriptions, Input, Modal, Typography } from 'antd';
import PageLayout from '../components/PageLayout';
import { verifyTransferReference } from '../utils/transferReceipt';
import {
  emptyTransferValues,
  formatTransferAmount,
  TRANSFER_FIELDS,
  validateTransfer,
  type TransferValues,
} from '../utils/transferForm';

type Feedback =
  | { kind: 'error'; message: string }
  | { kind: 'success'; reference: string; values: TransferValues };

export function RegistrationFormContent() {
  const [reference, setReference] = useState('');
  const [values, setValues] = useState(emptyTransferValues);
  const [feedback, setFeedback] = useState<Feedback | null>(null);
  const [checking, setChecking] = useState(false);

  useEffect(() => { document.title = '登记'; }, []);

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (checking) return;
    if (!reference.trim()) {
      setFeedback({ kind: 'error', message: '请输入业务流水号' });
      return;
    }
    const message = validateTransfer(values);
    if (message) {
      setFeedback({ kind: 'error', message });
      return;
    }
    const submitted = Object.fromEntries(Object.entries(values).map(([key, value]) => [key, value.trim()])) as TransferValues;
    setChecking(true);
    try {
      if (!await verifyTransferReference(reference, submitted.amount)) {
        setFeedback({ kind: 'error', message: '业务流水号无效或与金额不匹配，请核对转账确认信息' });
        return;
      }
      setFeedback({ kind: 'success', reference, values: submitted });
    } catch (cause) {
      setFeedback({ kind: 'error', message: cause instanceof Error ? cause.message : '无法校验业务流水号，请重试' });
    } finally {
      setChecking(false);
    }
  };

  return (
    <div style={{ padding: 24, minHeight: '100vh', boxSizing: 'border-box', background: '#fff' }}>
      <Typography.Paragraph type="secondary" style={{ marginBottom: 24 }}>
        请填写转账确认信息，带 * 为必填项。
      </Typography.Paragraph>
      <form aria-label="登记" autoComplete="off" noValidate onSubmit={handleSubmit}>
        <div style={{ marginBottom: 24 }}>
          <label htmlFor="registration-reference" style={{ display: 'inline-block', marginBottom: 8, fontWeight: 500 }}>业务流水号</label>
          <span aria-hidden="true" style={{ color: '#dc2626', marginLeft: 4 }}>*</span>
          <Input
            id="registration-reference"
            name="reference"
            required
            disabled={checking}
            size="large"
            placeholder="请输入转账确认弹窗中的业务流水号"
            value={reference}
            onChange={event => setReference(event.target.value)}
          />
          <Typography.Text type="secondary" style={{ display: 'block', marginTop: 6 }}>
            与转账确认弹窗中显示的流水号保持一致。
          </Typography.Text>
        </div>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(min(100%, 240px), 1fr))', gap: '24px 32px' }}>
          {TRANSFER_FIELDS.map(field => (
            <div key={field.key} style={{ minWidth: 0 }}>
              <label htmlFor={`registration-${field.key}`} style={{ display: 'inline-block', marginBottom: 8, fontWeight: 500 }}>
                {field.label}
              </label>
              {field.required ? <span aria-hidden="true" style={{ color: '#dc2626', marginLeft: 4 }}>*</span> : null}
              <Input
                id={`registration-${field.key}`}
                name={field.key}
                required={field.required}
                disabled={checking}
                size="large"
                inputMode={field.inputMode}
                maxLength={field.maxLength}
                placeholder={field.key === 'amount' ? '请输入金额（元）' : `请输入${field.label}`}
                value={values[field.key]}
                onChange={event => setValues(previous => ({ ...previous, [field.key]: event.target.value }))}
              />
            </div>
          ))}
        </div>
        <div style={{ display: 'flex', justifyContent: 'center', gap: 12, borderTop: '1px solid #e2e8f0', marginTop: 32, paddingTop: 24 }}>
          <Button htmlType="button" size="large" style={{ minWidth: 96 }} disabled={checking} onClick={() => {
            setReference('');
            setValues(emptyTransferValues());
            setFeedback(null);
          }}>重置</Button>
          <Button type="primary" htmlType="submit" aria-label="登记" aria-busy={checking} size="large" style={{ minWidth: 96 }} loading={checking}>登记</Button>
        </div>
      </form>
      <Modal
        title={feedback?.kind === 'success' ? '登记成功' : '登记失败'}
        open={feedback !== null}
        centered
        maskClosable={false}
        onCancel={() => setFeedback(null)}
        footer={<Button type="primary" onClick={() => setFeedback(null)}>确定</Button>}
      >
        {feedback?.kind === 'error' ? <p role="alert">{feedback.message}</p> : null}
        {feedback?.kind === 'success' ? (
          <div role="status">
            <Typography.Paragraph style={{ overflowWrap: 'anywhere' }}>业务流水号：{feedback.reference}</Typography.Paragraph>
            <Descriptions
              column={1}
              size="small"
              items={TRANSFER_FIELDS.map(field => ({
                key: field.key,
                label: field.label,
                children: <span style={{ overflowWrap: 'anywhere' }}>
                  {field.key === 'amount' ? `${formatTransferAmount(feedback.values.amount)} 元` : feedback.values[field.key] || '—'}
                </span>,
              }))}
            />
          </div>
        ) : null}
      </Modal>
    </div>
  );
}

export default function RegistrationPage() {
  const routePrefix = import.meta.env.VITE_GITHUB_PAGES === 'true' ? '#/' : '';
  return (
    <PageLayout title="登记" subtitle="填写转账确认信息并校验业务流水号" maxWidth={1000}>
      <iframe
        id="registration-frame"
        title="登记表单"
        src={`${import.meta.env.BASE_URL}${routePrefix}registration-form-content`}
        style={{ display: 'block', width: '100%', height: '80vh', minHeight: 640, boxSizing: 'border-box', border: '1px solid #e2e8f0', borderRadius: 8, background: '#fff' }}
      />
    </PageLayout>
  );
}
