import { useState } from 'react';
import { Alert, Button, Space, Tag, Typography } from 'antd';
import PageLayout from '../components/PageLayout';

export default function WebDialogTestPage() {
  const [status, setStatus] = useState('等待触发对话框…');

  const stamp = () => `\n时间：${new Date().toLocaleString()}`;

  return (
    <PageLayout
      title="网页对话框测试"
      subtitle="触发浏览器原生对话框（alert / confirm / prompt），用于测试对话框处理"
    >
      <Alert
        type="info"
        showIcon
        style={{ marginBottom: 24 }}
        message="三种对话框类型"
        description={
          <ul style={{ margin: 0, paddingLeft: 20 }}>
            <li>alert — 仅确认按钮，调用 web.dialog.accept</li>
            <li>confirm — 确认 / 取消，调用 accept 或 dismiss</li>
            <li>prompt — 确认 / 取消 + 输入框，调用 prompt(text) 或 dismiss</li>
          </ul>
        }
      />

      <Space direction="vertical" size={24} style={{ width: '100%' }}>
        <div>
          <Tag color="blue">类型 1</Tag>
          <Typography.Title level={5}>Alert — 只有确认按钮</Typography.Title>
          <Typography.Paragraph type="secondary">对应 window.alert()，只有一个「确定」按钮。</Typography.Paragraph>
          <Button
            id="btn-alert"
            type="primary"
            onClick={() => {
              setStatus('已触发 Alert，等待处理…');
              window.alert('这是一条 Alert 消息，请点击确定关闭。');
              setStatus(`Alert 已关闭（用户点击了确定）${stamp()}`);
            }}
          >
            触发 Alert 对话框
          </Button>
        </div>

        <div>
          <Tag color="blue">类型 2</Tag>
          <Typography.Title level={5}>Confirm — 确认与取消</Typography.Title>
          <Typography.Paragraph type="secondary">对应 window.confirm()，包含「确定」和「取消」。</Typography.Paragraph>
          <Button
            id="btn-confirm"
            type="primary"
            onClick={() => {
              setStatus('已触发 Confirm，等待处理…');
              const result = window.confirm('是否确认执行此操作？');
              setStatus(`Confirm 结果：${result ? '确定（true）' : '取消（false）'}${stamp()}`);
            }}
          >
            触发 Confirm 对话框
          </Button>
        </div>

        <div>
          <Tag color="blue">类型 3</Tag>
          <Typography.Title level={5}>Prompt — 确认、取消与输入框</Typography.Title>
          <Typography.Paragraph type="secondary">对应 window.prompt()，包含输入框及「确定」「取消」。</Typography.Paragraph>
          <Button
            id="btn-prompt"
            type="primary"
            onClick={() => {
              setStatus('已触发 Prompt，等待处理…');
              const result = window.prompt('请输入您的名称：', 'UiPilot');
              setStatus(
                result === null
                  ? `Prompt 结果：取消（null）${stamp()}`
                  : `Prompt 结果：确定，输入值为「${result}」${stamp()}`,
              );
            }}
          >
            触发 Prompt 对话框
          </Button>
        </div>
      </Space>

      <Typography.Paragraph id="status" style={{ marginTop: 24, padding: 12, background: '#f8fafc', borderRadius: 8, whiteSpace: 'pre-wrap' }}>
        {status}
      </Typography.Paragraph>
    </PageLayout>
  );
}
