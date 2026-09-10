import { useEffect, useRef, useState, type MouseEvent as ReactMouseEvent } from 'react';
import { Button, Table, Typography, message } from 'antd';

type DragLog = { key: number; time: string; left: number; top: number };

export default function GeometryDragPanel() {
  const canvasRef = useRef<HTMLDivElement>(null);
  const targetRef = useRef<HTMLDivElement>(null);
  const cleanupRef = useRef<(() => void) | null>(null);
  const sequence = useRef(0);
  const [dragging, setDragging] = useState(false);
  const [logs, setLogs] = useState<DragLog[]>([]);

  useEffect(() => () => cleanupRef.current?.(), []);

  const resetPosition = () => {
    cleanupRef.current?.();
    setDragging(false);
    setLogs([]);
    sequence.current = 0;
    const target = targetRef.current!;
    target.style.left = '50%';
    target.style.top = '50%';
    target.style.transform = 'translate(-50%, -50%)';
  };

  const copyLogs = async () => {
    try {
      await navigator.clipboard.writeText(JSON.stringify(logs, null, 2));
      message.success('记录已复制为 JSON');
    } catch {
      message.error('复制失败，请检查浏览器剪贴板权限');
    }
  };

  const startDrag = (event: ReactMouseEvent<HTMLDivElement>) => {
    if (event.button !== 0) return;
    event.preventDefault();
    cleanupRef.current?.();
    const target = targetRef.current!;
    const canvas = canvasRef.current!;
    const bounds = target.getBoundingClientRect();
    const grabX = event.clientX - bounds.left;
    const grabY = event.clientY - bounds.top;
    setDragging(true);

    const move = (mouse: MouseEvent) => {
      const area = canvas.getBoundingClientRect();
      const left = Math.max(0, Math.min(canvas.clientWidth - target.offsetWidth,
        mouse.clientX - area.left - canvas.clientLeft - grabX));
      const top = Math.max(0, Math.min(canvas.clientHeight - target.offsetHeight,
        mouse.clientY - area.top - canvas.clientTop - grabY));
      target.style.left = `${left}px`;
      target.style.top = `${top}px`;
      target.style.transform = 'none';
    };
    const cleanup = () => {
      window.removeEventListener('mousemove', move);
      window.removeEventListener('mouseup', stop);
      window.removeEventListener('blur', cancel);
      cleanupRef.current = null;
    };
    const stop = (mouse: MouseEvent) => {
      move(mouse);
      const final = target.getBoundingClientRect();
      const record = { key: ++sequence.current, time: new Date().toLocaleTimeString('zh-CN', { hour12: false }),
        left: final.left, top: final.top };
      setLogs(previous => [record, ...previous].slice(0, 100));
      setDragging(false);
      cleanup();
    };
    const cancel = () => { setDragging(false); cleanup(); };
    window.addEventListener('mousemove', move);
    window.addEventListener('mouseup', stop);
    window.addEventListener('blur', cancel);
    cleanupRef.current = cleanup;
  };

  return (
    <div id="non-iframe-drag-content" style={{ display: 'grid', gridTemplateColumns: 'minmax(0, 3fr) minmax(0, 2fr)', gap: 24 }}>
      <section>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 12 }}>
          <Typography.Title level={5} style={{ margin: 0 }}>拖拽画布</Typography.Title>
          <Button id="coordinate-drag-reset" size="small" onClick={resetPosition}>重置</Button>
        </div>
        <div id="coordinate-drag-canvas" ref={canvasRef} style={{ position: 'relative', height: 420,
          border: '1px solid #d9d9d9', borderRadius: 8, overflow: 'hidden', backgroundColor: '#fafcff',
          backgroundImage: 'linear-gradient(#e8eef7 1px, transparent 1px), linear-gradient(90deg, #e8eef7 1px, transparent 1px)',
          backgroundSize: '20px 20px' }}>
          <div id="coordinate-drag-target" ref={targetRef} onMouseDown={startDrag}
            style={{ position: 'absolute', left: '50%', top: '50%', transform: 'translate(-50%, -50%)', width: 100, height: 64, maxWidth: '100%',
              display: 'grid', placeItems: 'center', borderRadius: 6, color: '#fff', background: '#1677ff',
              cursor: dragging ? 'grabbing' : 'grab', userSelect: 'none' }}>
            拖拽元素
          </div>
        </div>
      </section>
      <section style={{ minWidth: 0 }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 12 }}>
          <Typography.Title level={5} style={{ margin: 0 }}>拖动停止坐标</Typography.Title>
          <Button id="coordinate-drag-copy" size="small" onClick={copyLogs}>复制 JSON</Button>
        </div>
        <Typography.Paragraph type="secondary">
          记录元素左上角；原点为整个网页可视窗口左上角，单位 CSS px（非画布坐标、非屏幕坐标）。保留最近 100 条。
        </Typography.Paragraph>
        <Table<DragLog> id="coordinate-drag-log" size="small" pagination={false} dataSource={logs}
          scroll={{ y: 330, x: 'max-content' }} locale={{ emptyText: '拖动左侧元素，松开后显示坐标' }}
          columns={[
            { title: '时间', dataIndex: 'time', width: 100 },
            { title: 'X / left', dataIndex: 'left', render: (value: number) => value.toFixed(2) },
            { title: 'Y / top', dataIndex: 'top', render: (value: number) => value.toFixed(2) },
          ]}
        />
      </section>
    </div>
  );
}
