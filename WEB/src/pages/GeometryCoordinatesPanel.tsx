import { useRef, useState, type MouseEvent } from 'react';
import { Button, Table, Typography, message } from 'antd';

type ClickLog = { key: number; time: string; x: number; y: number; deltaX: number; deltaY: number; outside: boolean };

export default function GeometryCoordinatesPanel() {
  const sequence = useRef(0);
  const targetRef = useRef<HTMLDivElement>(null);
  const [logs, setLogs] = useState<ClickLog[]>([]);

  const reset = () => {
    setLogs([]);
    sequence.current = 0;
  };

  const copyLogs = async () => {
    try {
      await navigator.clipboard.writeText(JSON.stringify(logs, null, 2));
      message.success('记录已复制为 JSON');
    } catch {
      message.error('复制失败，请检查浏览器剪贴板权限');
    }
  };

  const recordClick = (event: MouseEvent<HTMLDivElement>) => {
    const target = targetRef.current;
    if (!target) return;
    const bounds = target.getBoundingClientRect();
    const record = {
      key: ++sequence.current,
      time: new Date().toLocaleTimeString('zh-CN', { hour12: false }),
      x: event.clientX,
      y: event.clientY,
      deltaX: event.clientX - (bounds.left + bounds.width / 2),
      deltaY: event.clientY - (bounds.top + bounds.height / 2),
      outside: event.clientX < bounds.left || event.clientX >= bounds.right
        || event.clientY < bounds.top || event.clientY >= bounds.bottom,
    };
    setLogs(previous => [record, ...previous].slice(0, 100));
  };

  return (
    <div id="non-iframe-coordinates-content" style={{ display: 'grid', gridTemplateColumns: 'minmax(0, 3fr) minmax(0, 2fr)', gap: 24 }}>
      <section>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 12 }}>
          <Typography.Title level={5} style={{ margin: 0 }}>坐标画布</Typography.Title>
          <Button id="coordinate-click-reset" size="small" onClick={reset}>重置</Button>
        </div>
        <div id="coordinate-click-canvas" onClick={recordClick} style={{ position: 'relative', height: 420,
          border: '1px solid #d9d9d9', borderRadius: 8, overflow: 'hidden', backgroundColor: '#fafcff',
          backgroundImage: 'linear-gradient(#e8eef7 1px, transparent 1px), linear-gradient(90deg, #e8eef7 1px, transparent 1px)',
          backgroundSize: '20px 20px', cursor: 'crosshair', userSelect: 'none' }}>
          <div id="coordinate-click-target" ref={targetRef} style={{ position: 'absolute', left: '50%', top: '50%',
            transform: 'translate(-50%, -50%)', width: 180, height: 180, maxWidth: '100%',
            display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gridTemplateRows: 'repeat(3, 1fr)',
            background: '#1677ff', color: '#fff' }}>
            {['左上', '上', '右上', '左', '中心', '右', '左下', '下', '右下'].map(label => (
              <span key={label} style={{ display: 'grid', placeItems: 'center', outline: '1px solid #ffffff66', outlineOffset: -1 }}>
                {label}
              </span>
            ))}
          </div>
        </div>
      </section>
      <section style={{ minWidth: 0 }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 12 }}>
          <Typography.Title level={5} style={{ margin: 0 }}>点击位置记录</Typography.Title>
          <Button id="coordinate-click-copy" size="small" onClick={copyLogs}>复制 JSON</Button>
        </div>
        <Typography.Paragraph type="secondary">
          记录点击位置；原点为整个网页可视窗口左上角，单位 CSS px。点击中央元素或画布空白区域均会记录。保留最近 100 条。
          ΔX、ΔY 为点击位置相对中央元素中心点的偏移，向右、向下为正。
        </Typography.Paragraph>
        <Table<ClickLog> id="coordinate-click-log" size="small" pagination={false} dataSource={logs}
          scroll={{ y: 330, x: 'max-content' }} locale={{ emptyText: '点击左侧画布后显示坐标' }}
          columns={[
            { title: '时间', dataIndex: 'time', width: 100 },
            { title: 'X / clientX', dataIndex: 'x', render: (value: number) => value.toFixed(2) },
            { title: 'Y / clientY', dataIndex: 'y', render: (value: number) => value.toFixed(2) },
            { title: '中心偏移 ΔX', dataIndex: 'deltaX', render: (value: number) => value.toFixed(2) },
            { title: '中心偏移 ΔY', dataIndex: 'deltaY', render: (value: number) => value.toFixed(2) },
            { title: '元素外', dataIndex: 'outside', render: (value: boolean) => value ? '是' : '否' },
          ]}
        />
      </section>
    </div>
  );
}
