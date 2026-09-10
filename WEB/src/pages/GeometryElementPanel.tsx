import { useCallback, useLayoutEffect, useRef, useState } from 'react';
import { Button, Table, Typography, message } from 'antd';
import { formatLogTime } from '../utils/formatLogTime';

type GeometryRecord = {
  key: number;
  time: string;
  left: number;
  top: number;
  width: number;
  height: number;
  right: number;
  bottom: number;
};

function randomInteger(min: number, max: number) {
  return min + Math.floor(Math.random() * (max - min + 1));
}

export default function GeometryElementPanel() {
  const canvasRef = useRef<HTMLDivElement>(null);
  const initialized = useRef(false);
  const sequence = useRef(0);
  const [geometry, setGeometry] = useState<GeometryRecord | null>(null);
  const [logs, setLogs] = useState<GeometryRecord[]>([]);

  const copyLogs = async () => {
    try {
      await navigator.clipboard.writeText(JSON.stringify(logs, null, 2));
      message.success('几何日志已复制为 JSON');
    } catch {
      message.error('复制失败，请检查浏览器剪贴板权限');
    }
  };

  const randomize = useCallback(() => {
    const canvas = canvasRef.current;
    if (!canvas || canvas.clientWidth < 200 || canvas.clientHeight < 200) return;
    const width = randomInteger(100, 200);
    const height = randomInteger(100, 200);
    const left = randomInteger(0, canvas.clientWidth - width);
    const top = randomInteger(0, canvas.clientHeight - height);
    const record = { key: ++sequence.current, time: formatLogTime(), left, top, width, height,
      right: left + width, bottom: top + height };
    initialized.current = true;
    setGeometry(record);
    setLogs([record]);
  }, []);

  useLayoutEffect(() => {
    const initialize = () => { if (!initialized.current) randomize(); };
    initialize();
    const observer = new ResizeObserver(initialize);
    observer.observe(canvasRef.current!);
    return () => observer.disconnect();
  }, [randomize]);

  return (
    <div id="non-iframe-element-geometry-content" style={{ display: 'grid', gridTemplateColumns: 'minmax(0, 3fr) minmax(0, 2fr)', gap: 24 }}>
      <section style={{ minWidth: 0 }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 12 }}>
          <Typography.Title level={5} style={{ margin: 0 }}>元素几何画板</Typography.Title>
          <Button id="element-geometry-randomize" size="small" onClick={randomize}>重新随机</Button>
        </div>
        <div style={{ overflowX: 'auto' }}>
          <div id="element-geometry-canvas" ref={canvasRef} style={{ position: 'relative', height: 420, minWidth: 202,
            border: '1px solid #d9d9d9', borderRadius: 8, backgroundColor: '#fafcff',
            backgroundImage: 'linear-gradient(#e8eef7 1px, transparent 1px), linear-gradient(90deg, #e8eef7 1px, transparent 1px)',
            backgroundSize: '20px 20px' }}>
            {geometry && <div id="element-geometry-target" style={{ position: 'absolute', left: geometry.left,
              top: geometry.top, width: geometry.width, height: geometry.height, background: '#1677ff', color: '#fff',
              display: 'grid', placeItems: 'center', borderRadius: 6 }}>
              目标元素
            </div>}
          </div>
        </div>
      </section>
      <section style={{ minWidth: 0 }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 12 }}>
          <Typography.Title level={5} style={{ margin: 0 }}>元素几何记录</Typography.Title>
          <Button id="element-geometry-copy" size="small" onClick={copyLogs}>复制 JSON</Button>
        </div>
        <Typography.Paragraph type="secondary">
          原点为画板内侧左上角，单位 CSS px。宽、高各随机为 100～200px，元素完整位于画板内。
          每次加载和重新随机时更新，仅保留当前元素的几何记录。
        </Typography.Paragraph>
        <Table<GeometryRecord> id="element-geometry-log" size="small" pagination={false} dataSource={logs}
          scroll={{ y: 330, x: 'max-content' }} locale={{ emptyText: '等待生成元素' }}
          columns={[
            { title: '时间', dataIndex: 'time', width: 120 },
            { title: 'X / left', dataIndex: 'left' },
            { title: 'Y / top', dataIndex: 'top' },
            { title: '宽度', dataIndex: 'width' },
            { title: '高度', dataIndex: 'height' },
            { title: 'right', dataIndex: 'right' },
            { title: 'bottom', dataIndex: 'bottom' },
          ]}
        />
      </section>
    </div>
  );
}
