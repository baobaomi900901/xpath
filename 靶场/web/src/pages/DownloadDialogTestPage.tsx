import { useState } from 'react';
import { Alert, Button, Input, Space, Typography } from 'antd';
import PageLayout from '../components/PageLayout';
import { downloadBlob } from '../utils/random';

export default function DownloadDialogTestPage() {
  const [status, setStatus] = useState('等待触发下载…');
  const [filename, setFilename] = useState('custom-download.txt');

  const markDownload = (name: string) => {
    setStatus(`已触发下载：${name}\n时间：${new Date().toLocaleString()}`);
  };

  return (
    <PageLayout
      title="下载对话框测试"
      subtitle="点击下载按钮或链接，触发浏览器「另存为」对话框，用于测试 handle_save_dialog()"
    >
      <Alert
        type="info"
        showIcon
        style={{ marginBottom: 24 }}
        message="测试步骤"
        description={
          <ol style={{ margin: 0, paddingLeft: 20 }}>
            <li>先调用 web.handle_save_dialog(file_folder, file_name=...)</li>
            <li>再点击下方的下载按钮，触发保存对话框</li>
            <li>可通过 dialog_result=&quot;cancel&quot; 测试取消保存</li>
          </ol>
        }
      />

      <Typography.Title level={5}>静态文件下载</Typography.Title>
      <Space wrap style={{ marginBottom: 24 }}>
        <Button id="link-download-txt" type="primary" href="/samples/demo.txt" download="demo.txt" onClick={() => markDownload('demo.txt')}>
          下载 demo.txt
        </Button>
        <Button id="link-download-csv" href="/samples/report.csv" download="report.csv" onClick={() => markDownload('report.csv')}>
          下载 report.csv
        </Button>
        <Button id="link-download-json" href="/samples/data.json" download="data.json" onClick={() => markDownload('data.json')}>
          下载 data.json
        </Button>
      </Space>

      <Typography.Title level={5}>动态生成下载（Blob）</Typography.Title>
      <Space wrap style={{ marginBottom: 24 }}>
        <Button
          id="btn-download-blob-txt"
          type="primary"
          onClick={() => {
            downloadBlob(
              'notes.txt',
              `UiPilot 下载对话框测试\n生成时间：${new Date().toISOString()}\n`,
              'text/plain;charset=utf-8',
            );
            markDownload('notes.txt');
          }}
        >
          下载生成的 notes.txt
        </Button>
        <Button
          id="btn-download-blob-json"
          onClick={() => {
            const payload = { source: 'blob', createdAt: new Date().toISOString(), items: ['alpha', 'beta', 'gamma'] };
            downloadBlob('export.json', JSON.stringify(payload, null, 2), 'application/json;charset=utf-8');
            markDownload('export.json');
          }}
        >
          下载生成的 export.json
        </Button>
        <Button
          id="btn-download-blob-csv"
          onClick={() => {
            downloadBlob('users.csv', 'id,name\n1,Alice\n2,Bob\n3,Carol\n', 'text/csv;charset=utf-8');
            markDownload('users.csv');
          }}
        >
          下载生成的 users.csv
        </Button>
      </Space>

      <Typography.Title level={5}>自定义文件名</Typography.Title>
      <Space wrap style={{ marginBottom: 24 }}>
        <Input id="input-filename" value={filename} onChange={(e) => setFilename(e.target.value)} style={{ width: 260 }} />
        <Button
          id="btn-download-custom"
          type="primary"
          onClick={() => {
            const name = filename.trim() || 'custom-download.txt';
            downloadBlob(name, '自定义文件名下载测试\n', 'text/plain;charset=utf-8');
            markDownload(name);
          }}
        >
          下载自定义文件
        </Button>
      </Space>

      <Typography.Paragraph id="status" style={{ padding: 12, background: '#f8fafc', borderRadius: 8, whiteSpace: 'pre-wrap' }}>
        {status}
      </Typography.Paragraph>
    </PageLayout>
  );
}
