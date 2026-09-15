import { useState } from 'react';
import { Button, Card, Input, Space, Typography } from 'antd';
import PageLayout from '../components/PageLayout';

const DEFAULT_HTML = '等待渲染 HTML…';

export default function ElementHtmlTestPage() {
  const [input, setInput] = useState('');
  const [html, setHtml] = useState(DEFAULT_HTML);

  const reset = () => {
    setInput('');
    setHtml(DEFAULT_HTML);
  };

  return (
    <PageLayout title="元素 HTML 测试" subtitle="输入文本或 HTML，渲染到固定靶元素后测试元素 HTML 获取接口" fullWidth>
      <div style={{ display: 'grid', gridTemplateColumns: 'minmax(0, 1fr) minmax(0, 1fr)', gap: 24, alignItems: 'start' }}>
        <Card title="HTML 输入">
          <Input.TextArea
            id="element-html-input"
            value={input}
            onChange={event => setInput(event.target.value)}
            placeholder={'例如：<span>str</span>'}
            autoSize={{ minRows: 8, maxRows: 16 }}
          />
          <Space style={{ marginTop: 16 }}>
            <Button id="element-html-apply" type="primary" onClick={() => setHtml(input)}>确定</Button>
            <Button id="element-html-reset" onClick={reset}>重置</Button>
          </Space>
        </Card>
        <Card title="靶元素">
          <div
            id="element-html-target"
            dangerouslySetInnerHTML={{ __html: html }}
            style={{ minHeight: 120, padding: 16, border: '1px dashed #1677ff', borderRadius: 8, background: '#f8fbff' }}
          />
          <Typography.Text type="secondary" style={{ display: 'block', marginTop: 16 }}>当前 innerHTML：</Typography.Text>
          <pre id="element-html-result" style={{ whiteSpace: 'pre-wrap', overflowWrap: 'anywhere', padding: 12, background: '#f5f5f5', borderRadius: 6 }}>{html}</pre>
        </Card>
      </div>
    </PageLayout>
  );
}
