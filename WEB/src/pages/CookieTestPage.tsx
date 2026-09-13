import { useCallback, useEffect, useMemo, useState } from 'react';
import { Alert, Button, Card, Checkbox, Descriptions, Form, Input, InputNumber, Select, Space, Table, Tag, Typography, message } from 'antd';
import type { ColumnsType } from 'antd/es/table';
import PageLayout from '../components/PageLayout';

const OBSERVATION_SUFFIX = '/api/sdk-web/cookie-observation';
const ALLOWED_OBSERVATION_PATHS = new Set([OBSERVATION_SUFFIX, `/cookie-test${OBSERVATION_SUFFIX}`, `/cookie-test/scoped${OBSERVATION_SUFFIX}`, `/outside${OBSERVATION_SUFFIX}`]);
type CookieRow = { key: string; name: string; value: string };
type ServerActual = { executionId: string; scenarioId: string; actual: { cookies: Record<string, string>; scheme: string; host: string; port: number; path: string } };

declare global { interface Window { __UIPILOT_COOKIE_OBSERVATION__?: ServerActual & { documentCookie: Record<string, string> } } }

function readCookies(): CookieRow[] {
  return document.cookie.split(';').map(part => part.trim()).filter(Boolean).map(part => {
    const index = part.indexOf('=');
    const name = index >= 0 ? part.slice(0, index) : part;
    const value = index >= 0 ? part.slice(index + 1) : '';
    return { key: name, name, value };
  });
}
function formDateValue() { const date = new Date(Date.now() + 86400000); return date.toISOString().slice(0, 16); }

export default function CookieTestPage() {
  const params = useMemo(() => new URLSearchParams(window.location.search), []);
  const executionId = params.get('uipilot_execution') ?? '';
  const scenarioId = params.get('uipilot_scenario') ?? 'readiness';
  const observationToken = params.get('uipilot_observation_token') ?? '';
  const observationPath = ALLOWED_OBSERVATION_PATHS.has(params.get('observation_path') ?? '') ? params.get('observation_path')! : OBSERVATION_SUFFIX;
  const [cookies, setCookies] = useState<CookieRow[]>([]);
  const [serverActual, setServerActual] = useState<ServerActual | null>(null);
  const [serverError, setServerError] = useState<string | null>(null);
  const [addForm] = Form.useForm();
  const [deleteForm] = Form.useForm();
  const refresh = useCallback(() => setCookies(readCookies()), []);

  useEffect(() => { refresh(); }, [refresh]);
  useEffect(() => {
    if (!executionId || !observationToken) return;
    const controller = new AbortController();
    fetch(observationPath, { method: 'POST', credentials: 'include', cache: 'no-store', headers: {
      'x-uipilot-execution-id': executionId, 'x-uipilot-scenario-id': scenarioId, 'x-uipilot-observation-token': observationToken,
    }, signal: controller.signal }).then(async response => {
      if (!response.ok) throw new Error(`observation request failed: ${response.status}`);
      return response.json() as Promise<ServerActual>;
    }).then(value => { setServerActual(value); window.__UIPILOT_COOKIE_OBSERVATION__ = { ...value, documentCookie: Object.fromEntries(readCookies().map(row => [row.name, row.value])) }; })
      .catch(error => { if (!controller.signal.aborted) setServerError(error instanceof Error ? error.message : String(error)); });
    return () => controller.abort();
  }, [executionId, observationPath, observationToken, scenarioId]);

  const setCookie = (values: Record<string, unknown>) => {
    const name = String(values.name ?? '').trim();
    const value = String(values.value ?? '');
    const path = String(values.path || '/').trim();
    if (!name || /[=;\s]/.test(name)) { message.error('Cookie 名称不能包含空格、= 或 ;'); return; }
    if (!path.startsWith('/')) { message.error('Path 必须以 / 开头'); return; }
    const parts = [`${encodeURIComponent(name)}=${encodeURIComponent(value)}`, `Path=${path}`];
    if (values.sameSite) parts.push(`SameSite=${values.sameSite}`);
    if (values.secure) parts.push('Secure');
    if (values.maxAge !== undefined && values.maxAge !== null && values.maxAge !== '') parts.push(`Max-Age=${Number(values.maxAge)}`);
    if (values.expires) parts.push(`Expires=${new Date(String(values.expires)).toUTCString()}`);
    document.cookie = parts.join('; ');
    addForm.resetFields();
    addForm.setFieldsValue({ expires: formDateValue(), path: '/', sameSite: 'Lax', secure: window.location.protocol === 'https:' });
    refresh(); message.success('Cookie 已写入');
  };
  const removeCookie = (values: Record<string, unknown>) => {
    const name = String(values.name ?? '').trim(); const path = String(values.path || '/').trim();
    if (!name || /[=;\s]/.test(name)) { message.error('请输入有效的 Cookie 名称'); return; }
    document.cookie = `${encodeURIComponent(name)}=; Path=${path}; Max-Age=0`;
    refresh(); message.success('已发送 Cookie 删除指令');
  };
  const copyVisible = async () => {
    try { await navigator.clipboard.writeText(JSON.stringify(cookies, null, 2)); message.success('当前可见 Cookie 已复制为 JSON'); }
    catch { message.error('复制失败，请检查剪贴板权限'); }
  };
  const columns: ColumnsType<CookieRow> = [
    { title: '名称', dataIndex: 'name', key: 'name' },
    { title: '值（document.cookie 可见）', dataIndex: 'value', key: 'value', render: value => <Typography.Text code>{value}</Typography.Text> },
  ];
  const secureAllowed = window.location.protocol === 'https:';

  return <PageLayout title="Web Cookie 测试" subtitle="使用 JavaScript 管理当前页面可见的 Cookie；HttpOnly 不在本页面设置。" fullWidth>
    <div style={{ display: 'grid', gridTemplateColumns: 'minmax(0, 3fr) minmax(320px, 2fr)', gap: 24, alignItems: 'start' }}>
      <section>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <Typography.Title level={4} style={{ marginTop: 0 }}>当前网页 Cookie</Typography.Title>
          <Space><Button onClick={refresh}>刷新</Button><Button onClick={copyVisible}>复制 JSON</Button></Space>
        </div>
        <Typography.Paragraph type="secondary">这里只能观察当前域名、当前 Path 下 JavaScript 可见的 Cookie。HttpOnly Cookie 不会出现在这里，但可能随请求发送。</Typography.Paragraph>
        <Table<CookieRow> id="cookie-visible-table" size="small" rowKey="key" pagination={false} dataSource={cookies} columns={columns} locale={{ emptyText: '当前没有可见 Cookie' }} />
        {executionId && <Descriptions bordered size="small" column={2} style={{ marginTop: 16 }}>
          <Descriptions.Item label="Execution marker">{executionId}</Descriptions.Item><Descriptions.Item label="Scenario">{scenarioId}</Descriptions.Item>
          <Descriptions.Item label="Observation path">{observationPath}</Descriptions.Item><Descriptions.Item label="服务端观测">{serverActual ? <Tag color="success">已返回</Tag> : serverError ? <Tag color="error">失败</Tag> : <Tag>等待</Tag>}</Descriptions.Item>
        </Descriptions>}
        {serverError && <Alert type="warning" showIcon message={serverError} style={{ marginTop: 12 }} />}
        {serverActual && <Card title="服务端实际收到的 Cookie" style={{ marginTop: 16 }}><Typography.Paragraph code copyable>{JSON.stringify(serverActual.actual, null, 2)}</Typography.Paragraph></Card>}
      </section>
      <section>
        <Card title="添加 Cookie" size="small" style={{ marginBottom: 16 }}>
          <Form form={addForm} layout="vertical" initialValues={{ path: '/', sameSite: 'Lax', secure: secureAllowed, expires: formDateValue() }} onFinish={setCookie}>
            <Form.Item name="name" label="名称" rules={[{ required: true, message: '请输入名称' }]}><Input id="cookie-add-name" /></Form.Item>
            <Form.Item name="value" label="值" rules={[{ required: true, message: '请输入值' }]}><Input id="cookie-add-value" /></Form.Item>
            <Form.Item name="path" label="Path"><Input id="cookie-add-path" /></Form.Item>
            <Form.Item name="sameSite" label="SameSite"><Select id="cookie-add-samesite" options={[{ value: 'Lax', label: 'Lax' }, { value: 'Strict', label: 'Strict' }, { value: 'None', label: 'None' }]} /></Form.Item>
            <Form.Item name="maxAge" label="Max-Age（秒，可选）"><InputNumber id="cookie-add-max-age" min={0} style={{ width: '100%' }} /></Form.Item>
            <Form.Item name="expires" label="Expires（可选）"><Input id="cookie-add-expires" type="datetime-local" /></Form.Item>
            <Form.Item name="secure" valuePropName="checked"><Checkbox id="cookie-add-secure" disabled={!secureAllowed}>Secure{secureAllowed ? '' : '（HTTPS 才可设置）'}</Checkbox></Form.Item>
            <Button id="cookie-add-submit" type="primary" htmlType="submit">添加 Cookie</Button>
          </Form>
        </Card>
        <Card title="删除 Cookie" size="small">
          <Form form={deleteForm} layout="vertical" initialValues={{ path: '/' }} onFinish={removeCookie}>
            <Form.Item name="name" label="名称" rules={[{ required: true, message: '请输入名称' }]}><Input id="cookie-delete-name" /></Form.Item>
            <Form.Item name="path" label="Path（需与添加时一致）"><Input id="cookie-delete-path" /></Form.Item>
            <Button id="cookie-delete-submit" danger type="primary" htmlType="submit">删除 Cookie</Button>
          </Form>
        </Card>
      </section>
    </div>
  </PageLayout>;
}
