import { useRef, useState } from 'react';
import { Alert, Button, Form, Space, Typography } from 'antd';
import PageLayout from '../components/PageLayout';

function formatFiles(files: FileList | null) {
  if (!files?.length) return '未选择文件';
  return Array.from(files)
    .map((file) => `${file.name} (${file.size} bytes)`)
    .join('\n');
}

function NativeFileInput({
  id,
  multiple,
  accept,
  title,
  onStatus,
}: {
  id: string;
  multiple?: boolean;
  accept?: string;
  title: string;
  onStatus: (text: string) => void;
}) {
  return (
    <input
      id={id}
      type="file"
      multiple={multiple}
      accept={accept}
      style={{ display: 'block', marginTop: 8 }}
      onClick={() => onStatus('已点击上传控件，等待 handle_upload_dialog 处理…')}
      onChange={(event) => {
        onStatus(`${title}\n${formatFiles(event.target.files)}\n时间：${new Date().toLocaleString()}`);
      }}
    />
  );
}

export default function UploadDialogTestPage() {
  const [status, setStatus] = useState('等待选择文件…');
  const hiddenInputRef = useRef<HTMLInputElement>(null);

  return (
    <PageLayout
      title="上传对话框测试"
      subtitle="点击文件选择控件，触发浏览器「打开文件」对话框，用于测试 handle_upload_dialog()"
    >
      <Alert
        type="info"
        showIcon
        style={{ marginBottom: 24 }}
        message="测试步骤"
        description={
          <ol style={{ margin: 0, paddingLeft: 20 }}>
            <li>调用 web.handle_upload_dialog(filenames, dialog_result=&quot;ok&quot;)</li>
            <li>再点击下方的上传控件，触发文件选择对话框</li>
            <li>测试文件位于 samples/ 目录：demo.txt、report.csv、data.json</li>
          </ol>
        }
      />

      <Form layout="vertical">
        <Form.Item label="单文件上传">
          <NativeFileInput id="input-upload-single" title="单文件上传：" onStatus={setStatus} />
        </Form.Item>
        <Form.Item label="多文件上传">
          <NativeFileInput id="input-upload-multiple" multiple title="多文件上传：" onStatus={setStatus} />
        </Form.Item>
        <Form.Item label="仅文本文件（.txt,.csv）">
          <NativeFileInput
            id="input-upload-text"
            accept=".txt,.csv,text/plain,text/csv"
            title="文本文件上传："
            onStatus={setStatus}
          />
        </Form.Item>
        <Form.Item label="仅 JSON 文件（.json）">
          <NativeFileInput
            id="input-upload-json"
            accept=".json,application/json"
            title="JSON 文件上传："
            onStatus={setStatus}
          />
        </Form.Item>
        <Form.Item label="按钮触发上传">
          <input
            ref={hiddenInputRef}
            id="input-upload-hidden"
            type="file"
            hidden
            onClick={() => setStatus('已点击上传控件，等待 handle_upload_dialog 处理…')}
            onChange={(event) => {
              setStatus(`按钮触发上传：\n${formatFiles(event.target.files)}\n时间：${new Date().toLocaleString()}`);
            }}
          />
          <Button id="btn-trigger-upload" type="primary" onClick={() => hiddenInputRef.current?.click()}>
            点击选择文件
          </Button>
        </Form.Item>
        <Form.Item label="表单内文件上传">
          <form
            id="upload-form"
            onSubmit={(event) => {
              event.preventDefault();
              const input = event.currentTarget.querySelector('#input-upload-form') as HTMLInputElement | null;
              setStatus(`表单已提交：\n${formatFiles(input?.files ?? null)}\n时间：${new Date().toLocaleString()}`);
            }}
          >
            <NativeFileInput id="input-upload-form" title="表单文件上传：" onStatus={setStatus} />
            <Space style={{ marginTop: 12 }}>
              <Button id="btn-upload-submit" type="primary" htmlType="submit">
                提交表单
              </Button>
              <Button id="btn-upload-reset" htmlType="reset">
                重置
              </Button>
            </Space>
          </form>
        </Form.Item>
      </Form>

      <Typography.Paragraph id="status" style={{ padding: 12, background: '#f8fafc', borderRadius: 8, whiteSpace: 'pre-wrap' }}>
        {status}
      </Typography.Paragraph>
    </PageLayout>
  );
}
