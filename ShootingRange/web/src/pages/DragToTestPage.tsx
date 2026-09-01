import { Button, Space, Table, Tag, Typography, message } from 'antd';
import type { ColumnsType } from 'antd/es/table';
import { useCallback, useEffect, useRef, useState } from 'react';
import PageLayout from '../components/PageLayout';

const TARGET_ID = 'drag-target';
const ARENA_ID = 'drag-arena';
const INITIAL_LEFT = 40;
const INITIAL_TOP = 40;
const TARGET_WIDTH = 120;
const TARGET_HEIGHT = 80;
const ARENA_WIDTH = 560;
const ARENA_HEIGHT = 420;
const MAX_LOGS = 20;

type DragPhase = 'start' | 'move' | 'end';

type DragLog = {
  key: string;
  time: string;
  phase: DragPhase;
  deltaLeft: number;
  deltaTop: number;
  left: number;
  top: number;
  clientX: number;
  clientY: number;
  pageX: number;
  pageY: number;
  isTrusted: boolean;
};

type DragSession = {
  startClientX: number;
  startClientY: number;
  startLeft: number;
  startTop: number;
};

function formatTime(date: Date) {
  return date.toLocaleTimeString('zh-CN', { hour12: false });
}

function clamp(value: number, min: number, max: number) {
  return Math.min(max, Math.max(min, value));
}

export default function DragToTestPage() {
  const [logs, setLogs] = useState<DragLog[]>([]);
  const [left, setLeft] = useState(INITIAL_LEFT);
  const [top, setTop] = useState(INITIAL_TOP);
  const [dragging, setDragging] = useState(false);
  const sessionRef = useRef<DragSession | null>(null);
  const posRef = useRef({ left: INITIAL_LEFT, top: INITIAL_TOP });
  const lastMoveDeltaRef = useRef<{ deltaLeft: number; deltaTop: number } | null>(null);

  const appendLog = useCallback((
    entry: Omit<DragLog, 'key' | 'time'>,
    resultMessage: string,
  ) => {
    const record: DragLog = {
      ...entry,
      key: `${entry.phase}-${Date.now()}-${Math.random().toString(36).slice(2, 7)}`,
      time: formatTime(new Date()),
    };
    console.log('[拖拽测试]', resultMessage, record);
    setLogs((prev) => [record, ...prev].slice(0, MAX_LOGS));
  }, []);

  const updatePosition = useCallback((nextLeft: number, nextTop: number) => {
    const maxLeft = ARENA_WIDTH - TARGET_WIDTH;
    const maxTop = ARENA_HEIGHT - TARGET_HEIGHT;
    const clampedLeft = clamp(Math.round(nextLeft), 0, maxLeft);
    const clampedTop = clamp(Math.round(nextTop), 0, maxTop);
    posRef.current = { left: clampedLeft, top: clampedTop };
    setLeft(clampedLeft);
    setTop(clampedTop);
    return { left: clampedLeft, top: clampedTop };
  }, []);

  const endDrag = useCallback((event: MouseEvent) => {
    const session = sessionRef.current;
    if (!session) return;

    const deltaLeft = posRef.current.left - session.startLeft;
    const deltaTop = posRef.current.top - session.startTop;
    sessionRef.current = null;
    setDragging(false);

    appendLog(
      {
        phase: 'end',
        deltaLeft,
        deltaTop,
        left: posRef.current.left,
        top: posRef.current.top,
        clientX: Math.round(event.clientX),
        clientY: Math.round(event.clientY),
        pageX: Math.round(event.pageX),
        pageY: Math.round(event.pageY),
        isTrusted: event.isTrusted,
      },
      `结束拖拽: deltaLeft=${deltaLeft}, deltaTop=${deltaTop}, left=${posRef.current.left}, top=${posRef.current.top}`,
    );
  }, [appendLog]);

  const moveDrag = useCallback((event: MouseEvent) => {
    const session = sessionRef.current;
    if (!session) return;

    const next = updatePosition(
      session.startLeft + (event.clientX - session.startClientX),
      session.startTop + (event.clientY - session.startClientY),
    );
    const deltaLeft = next.left - session.startLeft;
    const deltaTop = next.top - session.startTop;

    const last = lastMoveDeltaRef.current;
    if (last && last.deltaLeft === deltaLeft && last.deltaTop === deltaTop) {
      return;
    }
    lastMoveDeltaRef.current = { deltaLeft, deltaTop };

    appendLog(
      {
        phase: 'move',
        deltaLeft,
        deltaTop,
        left: next.left,
        top: next.top,
        clientX: Math.round(event.clientX),
        clientY: Math.round(event.clientY),
        pageX: Math.round(event.pageX),
        pageY: Math.round(event.pageY),
        isTrusted: event.isTrusted,
      },
      `拖拽中: deltaLeft=${deltaLeft}, deltaTop=${deltaTop}`,
    );
  }, [appendLog, updatePosition]);

  useEffect(() => {
    if (!dragging) return undefined;

    const onMove = (event: MouseEvent) => moveDrag(event);
    const onUp = (event: MouseEvent) => endDrag(event);

    window.addEventListener('mousemove', onMove);
    window.addEventListener('mouseup', onUp);
    return () => {
      window.removeEventListener('mousemove', onMove);
      window.removeEventListener('mouseup', onUp);
    };
  }, [dragging, endDrag, moveDrag]);

  const handleMouseDown = useCallback((event: React.MouseEvent<HTMLDivElement>) => {
    if (event.button !== 0) return;
    event.preventDefault();

    sessionRef.current = {
      startClientX: event.clientX,
      startClientY: event.clientY,
      startLeft: posRef.current.left,
      startTop: posRef.current.top,
    };
    setDragging(true);
    lastMoveDeltaRef.current = null;

    appendLog(
      {
        phase: 'start',
        deltaLeft: 0,
        deltaTop: 0,
        left: posRef.current.left,
        top: posRef.current.top,
        clientX: Math.round(event.clientX),
        clientY: Math.round(event.clientY),
        pageX: Math.round(event.pageX),
        pageY: Math.round(event.pageY),
        isTrusted: event.isTrusted,
      },
      `开始拖拽: left=${posRef.current.left}, top=${posRef.current.top}, isTrusted=${event.isTrusted}`,
    );
  }, [appendLog]);

  const handleReset = useCallback(() => {
    sessionRef.current = null;
    setDragging(false);
    updatePosition(INITIAL_LEFT, INITIAL_TOP);
    message.success('已重置拖拽块位置');
  }, [updatePosition]);

  const offsetFromSpawn = {
    deltaLeft: left - INITIAL_LEFT,
    deltaTop: top - INITIAL_TOP,
  };

  const columns: ColumnsType<DragLog> = [
    { title: '时间', dataIndex: 'time', width: 90 },
    {
      title: '阶段',
      dataIndex: 'phase',
      width: 72,
      render: (value: DragPhase) => {
        const color = value === 'start' ? 'blue' : value === 'end' ? 'green' : 'default';
        const label = value === 'start' ? '开始' : value === 'end' ? '结束' : '移动';
        return <Tag color={color}>{label}</Tag>;
      },
    },
    {
      title: 'Δleft',
      dataIndex: 'deltaLeft',
      width: 72,
      render: (value: number) => <Tag color="geekblue">{value}</Tag>,
    },
    {
      title: 'Δtop',
      dataIndex: 'deltaTop',
      width: 72,
      render: (value: number) => <Tag color="geekblue">{value}</Tag>,
    },
    {
      title: 'left/top',
      width: 100,
      render: (_: unknown, record: DragLog) => `${record.left}, ${record.top}`,
    },
    {
      title: 'client',
      width: 110,
      render: (_: unknown, record: DragLog) => `${record.clientX}, ${record.clientY}`,
    },
    {
      title: 'isTrusted',
      dataIndex: 'isTrusted',
      width: 90,
      render: (value: boolean) => (
        <Tag color={value ? 'success' : 'warning'}>{value ? 'true' : 'false'}</Tag>
      ),
    },
  ];

  return (
    <PageLayout
      title="元素拖拽测试"
      subtitle="测试 drag_to(left, top) 相对像素偏移; 拖拽块 id=drag-target"
      fullWidth
      inset={24}
    >
      <div style={{ display: 'flex', gap: 24, alignItems: 'stretch' }}>
        <div style={{ flex: 1, minWidth: 0 }}>
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              marginBottom: 8,
            }}
          >
            <div style={{ display: 'flex', alignItems: 'baseline', gap: 8 }}>
              <Typography.Title level={5} style={{ margin: 0 }}>
                拖拽记录
              </Typography.Title>
              <Typography.Text type="secondary" style={{ fontSize: 13 }}>
                (仅保留最近 {MAX_LOGS} 条)
              </Typography.Text>
            </div>
            <Space size={8}>
              <Button
                id="btn-copy-latest-drag-log"
                size="small"
                disabled={logs.length === 0}
                onClick={async () => {
                  const latest = logs[0];
                  const payload = {
                    phase: latest.phase,
                    deltaLeft: latest.deltaLeft,
                    deltaTop: latest.deltaTop,
                    left: latest.left,
                    top: latest.top,
                    clientX: latest.clientX,
                    clientY: latest.clientY,
                    pageX: latest.pageX,
                    pageY: latest.pageY,
                    isTrusted: latest.isTrusted,
                    time: latest.time,
                    offsetFromSpawn,
                  };
                  try {
                    await navigator.clipboard.writeText(JSON.stringify(payload, null, 2));
                    message.success('已复制最近一条记录');
                  } catch {
                    message.error('复制失败, 请检查浏览器剪贴板权限');
                  }
                }}
              >
                复制最近的一条记录
              </Button>
              <Button
                id="btn-clear-drag-log"
                size="small"
                disabled={logs.length === 0}
                onClick={() => setLogs([])}
              >
                清除记录
              </Button>
            </Space>
          </div>
          <Table
            id="drag-to-log"
            size="small"
            rowKey="key"
            columns={columns}
            dataSource={logs}
            pagination={false}
            scroll={{ x: 'max-content' }}
            locale={{ emptyText: '暂无记录, 请拖拽右侧目标块' }}
          />
        </div>

        <div style={{ flexShrink: 0, width: 1, background: '#EEE' }} aria-hidden />

        <div style={{ flex: '0 0 auto', width: ARENA_WIDTH + 32 }}>
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              marginBottom: 8,
            }}
          >
            <Typography.Title level={5} style={{ margin: 0 }}>
              拖拽区域
            </Typography.Title>
            <Button id="btn-reset-drag-target" size="small" onClick={handleReset}>
              重置位置
            </Button>
          </div>

          <Typography.Paragraph type="secondary" style={{ marginBottom: 12 }}>
            SDK 用法示例: <code>element.drag_to(left=100, top=50)</code>
            {' '}→ 期望相对起点约 Δleft=100, Δtop=50。
            当前相对初始位置:{' '}
            <Tag color="processing">Δleft={offsetFromSpawn.deltaLeft}</Tag>
            <Tag color="processing">Δtop={offsetFromSpawn.deltaTop}</Tag>
            <Tag>{dragging ? '拖拽中' : '空闲'}</Tag>
          </Typography.Paragraph>

          <div
            id={ARENA_ID}
            style={{
              position: 'relative',
              width: ARENA_WIDTH,
              height: ARENA_HEIGHT,
              border: '1px solid #D9D9D9',
              borderRadius: 8,
              backgroundColor: '#FAFAFA',
              backgroundImage:
                'linear-gradient(#EEE 1px, transparent 1px), linear-gradient(90deg, #EEE 1px, transparent 1px)',
              backgroundSize: '40px 40px',
              overflow: 'hidden',
              userSelect: 'none',
            }}
          >
            <div
              style={{
                position: 'absolute',
                left: INITIAL_LEFT,
                top: 0,
                bottom: 0,
                width: 1,
                background: 'rgba(22, 119, 255, 0.25)',
                pointerEvents: 'none',
              }}
            />
            <div
              style={{
                position: 'absolute',
                top: INITIAL_TOP,
                left: 0,
                right: 0,
                height: 1,
                background: 'rgba(22, 119, 255, 0.25)',
                pointerEvents: 'none',
              }}
            />
            <div
              style={{
                position: 'absolute',
                left: 8,
                top: 8,
                fontSize: 12,
                color: '#8C8C8C',
                pointerEvents: 'none',
              }}
            >
              初始原点 ({INITIAL_LEFT}, {INITIAL_TOP}) · 网格 40px
            </div>

            <div
              id={TARGET_ID}
              role="button"
              tabIndex={0}
              aria-label="拖拽目标"
              data-left={left}
              data-top={top}
              data-delta-left={offsetFromSpawn.deltaLeft}
              data-delta-top={offsetFromSpawn.deltaTop}
              onMouseDown={handleMouseDown}
              style={{
                position: 'absolute',
                left,
                top,
                width: TARGET_WIDTH,
                height: TARGET_HEIGHT,
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
                justifyContent: 'center',
                gap: 4,
                background: dragging ? '#1677FF' : '#4096FF',
                color: '#FFF',
                borderRadius: 8,
                boxShadow: '0 2px 8px rgba(0,0,0,0.15)',
                cursor: dragging ? 'grabbing' : 'grab',
                fontWeight: 600,
                fontSize: 13,
                zIndex: 1,
              }}
            >
              <span>drag-target</span>
              <span style={{ fontWeight: 400, fontSize: 12, opacity: 0.9 }}>
                {left}, {top}
              </span>
            </div>
          </div>

          <Typography.Paragraph type="secondary" style={{ marginTop: 12, marginBottom: 0 }}>
            稳定选择器建议: <code>//*[@id=&apos;drag-target&apos;]</code>
            {' '}或读取属性 <code>data-delta-left</code> / <code>data-delta-top</code> 做断言。
          </Typography.Paragraph>
        </div>
      </div>
    </PageLayout>
  );
}
