import { useEffect, useRef, useState } from 'react';
import { Button, InputNumber, Space, Table, Typography, message } from 'antd';

type ScrollLog = { key: number; time: string; y: number };

export default function GeometryPageScrollPanel({ mode = 'page' }: { mode?: 'page' | 'element' }) {
  const containerRef = useRef<HTMLDivElement>(null);
  const prefix = `${mode}-scroll`;
  const label = mode === 'page' ? '网页' : '元素';
  const scrollToY = (top: number) => {
    const target = mode === 'page' ? window : containerRef.current;
    target?.scrollTo({ top, behavior: 'instant' });
  };
  const [scrollY, setScrollY] = useState<number | null>(0);
  const [logs, setLogs] = useState<ScrollLog[]>([]);
  const panelRef = useRef<HTMLElement>(null);
  const sequence = useRef(0);
  const resetting = useRef(false);

  useEffect(() => {
    const target = mode === 'page' ? window : containerRef.current!;
    const readY = () => mode === 'page' ? window.scrollY : containerRef.current!.scrollTop;
    let pending = false;
    let timer: number | undefined;
    const supportsScrollEnd = 'onscrollend' in target;
    const visible = () => Boolean(panelRef.current?.getClientRects().length);
    const recordStop = () => {
      if (!pending) return;
      pending = false;
      if (resetting.current && readY() === 0) {
        resetting.current = false;
        return;
      }
      if (!visible()) return;
      const record = { key: ++sequence.current, time: new Date().toLocaleTimeString('zh-CN', { hour12: false }), y: readY() };
      setLogs(previous => [record, ...previous].slice(0, 100));
    };
    const onScroll = () => {
      if (readY() !== 0) resetting.current = false;
      pending = visible();
      if (!supportsScrollEnd) {
        window.clearTimeout(timer);
        timer = window.setTimeout(recordStop, 200);
      }
    };
    target.addEventListener('scroll', onScroll);
    if (supportsScrollEnd) target.addEventListener('scrollend', recordStop);
    return () => {
      window.clearTimeout(timer);
      target.removeEventListener('scroll', onScroll);
      target.removeEventListener('scrollend', recordStop);
    };
  }, [mode]);

  const copyLogs = async () => {
    try {
      await navigator.clipboard.writeText(JSON.stringify(logs, null, 2));
      message.success('滚动日志已复制为 JSON');
    } catch {
      message.error('复制失败，请检查浏览器剪贴板权限');
    }
  };

  return (
    <div id={`non-iframe-${prefix}-content`} style={{ height: mode === 'page' ? 3000 : 420 }}>
      <div id={mode === 'element' ? 'element-scroll-container' : 'page-scroll-surface'} ref={containerRef}
        style={{ width: '60%', height: '100%', borderRadius: 8,
          overflowY: mode === 'element' ? 'auto' : undefined,
          overscrollBehavior: mode === 'element' ? 'contain' : undefined,
          border: mode === 'element' ? '1px solid #d9d9d9' : undefined }}>
        <div id={`${prefix}-gradient`} style={{ height: 3000,
          background: 'linear-gradient(to bottom, #dbeafe 0%, #60a5fa 35%, #8b5cf6 70%, #312e81 100%)' }} />
      </div>
      <section id={`${prefix}-controls`} ref={panelRef} style={{ position: 'fixed', top: '50%', right: 48,
        transform: 'translateY(-50%)', width: 'min(320px, 30vw)', padding: 20, boxSizing: 'border-box',
        background: '#fff', border: '1px solid #d9d9d9', borderRadius: 8, boxShadow: '0 4px 16px #00000014', zIndex: 10,
        maxHeight: '85vh', overflowY: 'auto' }}>
        <Typography.Title level={5} style={{ marginTop: 0 }}>{label}滚动控制</Typography.Title>
        <label htmlFor={`${prefix}-y`} style={{ display: 'block', marginBottom: 8 }}>滚动 Y（CSS px）</label>
        <InputNumber id={`${prefix}-y`} min={0} value={scrollY} onChange={setScrollY} style={{ width: '100%', marginBottom: 12 }} />
        <Space wrap>
          <Button id={`${prefix}-apply`} type="primary" disabled={scrollY === null} onClick={() => {
            if (scrollY !== null) scrollToY(scrollY);
          }}>应用</Button>
          <Button id={`${prefix}-reset`} onClick={() => {
            resetting.current = true;
            setLogs([]);
            sequence.current = 0;
            setScrollY(0);
            scrollToY(0);
          }}>重置</Button>
        </Space>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 8, marginTop: 20, marginBottom: 12 }}>
          <Typography.Text strong>滚动停止日志</Typography.Text>
          <Button id={`${prefix}-copy`} size="small" onClick={copyLogs}>复制 JSON</Button>
        </div>
        <div id={`${prefix}-log-area`} style={{ height: 280, overflow: 'auto' }}>
          <Table<ScrollLog> id={`${prefix}-log`} size="small" pagination={false} dataSource={logs}
            tableLayout="fixed" scroll={{ y: 220, x: 240 }} locale={{ emptyText: `${label}滚动停止后记录，最多 100 条` }}
            columns={[
              { title: '时间', dataIndex: 'time', width: 110 },
              { title: <span style={{ whiteSpace: 'nowrap' }}>Y（CSS px）</span>, dataIndex: 'y', width: 130, render: (value: number) => value.toFixed(2) },
            ]}
          />
        </div>
      </section>
    </div>
  );
}
