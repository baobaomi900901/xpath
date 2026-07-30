import { Alert, Typography } from 'antd';
import PageLayout from '../components/PageLayout';

export default function IframeNestedTestPage() {
  return (
    <PageLayout
      title="iframe 嵌套测试"
      subtitle="4 层 iframe 嵌套场景，用于跨 frame 元素定位测试"
      maxWidth={1400}
      inset={24}
    >
      <Alert
        type="info"
        showIcon
        style={{ marginBottom: 16 }}
        message="结构：第 0 层（本页）→ iframe 第 1 层 → 第 2 层 → 第 3 层 → 第 4 层（最内层）"
      />

      <div
        id="layer-0-panel"
        style={{
          marginBottom: 12,
          padding: '12px 16px',
          background: '#f8fafc',
          borderRadius: 8,
          border: '1px solid #e2e8f0',
        }}
      >
        <Typography.Text strong>第 0 层（入口页）</Typography.Text>
        <Typography.Paragraph type="secondary" style={{ margin: '4px 0 0' }}>
          下方 iframe 加载第 1 层页面
        </Typography.Paragraph>
      </div>

      <iframe
        id="iframe-layer-1"
        title="iframe 第 1 层"
        src="/iframes/level-1.html"
        style={{
          width: '100%',
          height: 720,
          border: '1px solid #cbd5e1',
          borderRadius: 8,
          background: '#fff',
        }}
      />
    </PageLayout>
  );
}
