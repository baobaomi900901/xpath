import { useEffect, useMemo, useRef, useState } from 'react';
import { Alert, Button, Form, Input, Space, Typography, message } from 'antd';
import PageLayout from '../components/PageLayout';
import { randomStr, shuffle } from '../utils/random';

const LABEL_TEXTS = [
  'First Name',
  'Last Name',
  'Company Name',
  'Role in Company',
  'Address',
  'Email',
  'Phone Number',
];

const MAX_ROUND = 10;

type FieldItem = {
  key: string;
  label: string;
  name: string;
  ngReflectName: string;
};

export default function AnchorTestPage() {
  const [round, setRound] = useState(0);
  const [timer, setTimer] = useState('--');
  const [started, setStarted] = useState(false);
  const [fields, setFields] = useState<FieldItem[]>([]);
  const timerRef = useRef<number | null>(null);

  const initialFields = useMemo(
    () =>
      shuffle(LABEL_TEXTS).map((label) => ({
        key: randomStr(8),
        label,
        name: randomStr(),
        ngReflectName: randomStr(),
      })),
    [],
  );

  useEffect(() => {
    setFields(initialFields);
    return () => {
      if (timerRef.current) window.clearInterval(timerRef.current);
    };
  }, [initialFields]);

  const renderForm = () => {
    setFields(
      shuffle(LABEL_TEXTS).map((label) => ({
        key: randomStr(8),
        label,
        name: randomStr(),
        ngReflectName: randomStr(),
      })),
    );
  };

  const nextRound = () => {
    setRound((current) => {
      const next = current + 1;
      if (next > MAX_ROUND) {
        if (timerRef.current) window.clearInterval(timerRef.current);
        message.success('全部 10 轮完成！');
        setStarted(false);
        return current;
      }
      renderForm();
      return next;
    });
  };

  const handleStart = () => {
    if (started) return;
    setStarted(true);
    setRound(0);
    let sec = 999;
    setTimer(String(sec));
    timerRef.current = window.setInterval(() => {
      sec -= 1;
      setTimer(String(sec));
    }, 1000);
    nextRound();
  };

  return (
    <PageLayout title="锚点测试">
      <Alert
        type="info"
        showIcon
        style={{ marginBottom: 20 }}
        message="测试说明"
        description={
          <ul style={{ margin: 0, paddingLeft: 20 }}>
            <li>每一轮：表单顺序打乱</li>
            <li>每个 input：name、ng-reflect-name 全部随机刷新</li>
            <li>仅 label 文字是业务唯一标识（锚点）</li>
          </ul>
        }
      />

      <Space size={24} style={{ marginBottom: 20, fontWeight: 600 }}>
        <span>
          轮次：{round}/{MAX_ROUND}
        </span>
        <span>计时：{timer}</span>
      </Space>

      <Form layout="vertical">
        {fields.map((field) => (
          <Form.Item key={field.key} label={`${field.label}:`}>
            <Input
              name={field.name}
              data-ng-reflect-name={field.ngReflectName}
              aria-label={field.label}
            />
          </Form.Item>
        ))}
      </Form>

      <Space style={{ marginTop: 16 }}>
        <Button id="btnStart" type="primary" onClick={handleStart}>
          Start 开始
        </Button>
        <Button id="btnSubmit" type="primary" disabled={!started} onClick={nextRound}>
          Submit 提交
        </Button>
      </Space>

      <Typography.Paragraph type="danger" style={{ marginTop: 16, marginBottom: 0 }}>
        F12 打开 Elements 查看，每轮 name 与 ng-reflect-name 全部换新随机字符串
      </Typography.Paragraph>
    </PageLayout>
  );
}
