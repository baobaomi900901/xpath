import { useCallback, useState } from 'react';
import { Button, Space, Table, Tag, Typography } from 'antd';
import type { ColumnsType } from 'antd/es/table';
import PageLayout from '../components/PageLayout';

type ClickSource = '真实鼠标' | 'JS/插件模拟';

type InteractionType = 'click' | 'dblclick' | 'contextmenu' | 'hover' | 'focus';

type InteractionLog = {
  key: string;
  buttonId: string;
  buttonLabel: string;
  eventType: InteractionType;
  detectedKeys: string;
  clickSource: ClickSource;
  clickPosition?: string;
  offsetX?: number;
  offsetY?: number;
  isTrusted: boolean;
  time: string;
};

const POSITION_GRID = [
  [
    { value: 'top-left', label: '左上' },
    { value: 'top', label: '上' },
    { value: 'top-right', label: '右上' },
  ],
  [
    { value: 'left', label: '左' },
    { value: 'center', label: '中' },
    { value: 'right', label: '右' },
  ],
  [
    { value: 'bottom-left', label: '左下' },
    { value: 'bottom', label: '下' },
    { value: 'bottom-right', label: '右下' },
  ],
] as const;

const TEST_PANEL_MAX_WIDTH = 420;
const GRID_CELL_SIZE = 100;
const INTERACTION_BOX_SIZE = 100;

type PositionValue = (typeof POSITION_GRID)[number][number]['value'];

function detectKeys(event: MouseEvent): string {
  const parts: string[] = [];
  if (event.altKey) parts.push('alt');
  if (event.ctrlKey) parts.push('ctrl');
  if (event.shiftKey) parts.push('shift');
  if (event.metaKey) parts.push('win');
  return parts.length ? parts.join('+') : 'none';
}

function detectEventSource(event: Event): ClickSource {
  return event.isTrusted ? '真实鼠标' : 'JS/插件模拟';
}

function detectClickSource(event: MouseEvent): ClickSource {
  return detectEventSource(event);
}

function detectClickPosition(event: MouseEvent, element: HTMLElement): PositionValue {
  const rect = element.getBoundingClientRect();
  const x = event.clientX - rect.left;
  const y = event.clientY - rect.top;
  const col = x < rect.width / 3 ? 0 : x < (rect.width * 2) / 3 ? 1 : 2;
  const row = y < rect.height / 3 ? 0 : y < (rect.height * 2) / 3 ? 1 : 2;
  return POSITION_GRID[row][col].value;
}

function getPositionLabel(value: PositionValue) {
  for (const row of POSITION_GRID) {
    for (const cell of row) {
      if (cell.value === value) return cell.label;
    }
  }
  return value;
}

function toPositionCamelCase(value: string) {
  const parts = value.split('-');
  return parts
    .map((part, index) => (index === 0 ? part : part.charAt(0).toUpperCase() + part.slice(1)))
    .join('');
}

function formatClickPosition(value: PositionValue) {
  return `${toPositionCamelCase(value)}-(${getPositionLabel(value)})`;
}

const ANY_EXPECTED = '(任意)';

function getInteractionTypeLabel(eventType: InteractionType) {
  if (eventType === 'dblclick') return '双击';
  if (eventType === 'contextmenu') return '右键';
  if (eventType === 'hover') return '悬停';
  if (eventType === 'focus') return '聚焦';
  return '单击';
}

function formatTime(date: Date) {
  return date.toLocaleTimeString('zh-CN', { hour12: false });
}

export default function KeysClickTestPage() {
  const [logs, setLogs] = useState<InteractionLog[]>([]);
  const [lastResult, setLastResult] = useState('等待交互...');
  const [hoverActive, setHoverActive] = useState(false);
  const [focusActive, setFocusActive] = useState(false);

  const appendLog = useCallback((
    entry: Omit<InteractionLog, 'key' | 'time'>,
    resultMessage: string,
  ) => {
    setLogs((prev) => [
      { ...entry, key: `${entry.buttonId}-${entry.eventType}-${Date.now()}`, time: formatTime(new Date()) },
      ...prev,
    ].slice(0, 20));
    setLastResult(resultMessage);
  }, []);

  const handleInteraction = useCallback((
    buttonId: string,
    buttonLabel: string,
    expected: string,
    event: React.MouseEvent<HTMLElement>,
    eventType: InteractionType,
    extra?: Pick<InteractionLog, 'clickPosition' | 'offsetX' | 'offsetY'>,
  ) => {
    const native = event.nativeEvent;
    const detectedKeys = detectKeys(native);
    const clickSource = detectClickSource(native);
    const matched = expected === ANY_EXPECTED || detectedKeys === expected;
    const typeLabel = getInteractionTypeLabel(eventType);
    const positionText = extra?.clickPosition ? `, 方位=${extra.clickPosition}` : '';

    appendLog(
      {
        buttonId,
        buttonLabel,
        eventType,
        detectedKeys,
        clickSource,
        clickPosition: extra?.clickPosition,
        offsetX: extra?.offsetX,
        offsetY: extra?.offsetY,
        isTrusted: native.isTrusted,
      },
      expected === ANY_EXPECTED
        ? `${buttonLabel}(${typeLabel}): keys=${detectedKeys}, 来源=${clickSource}${positionText}`
        : matched
          ? `✓ ${buttonLabel}(${typeLabel}): keys=${detectedKeys}(符合预期 ${expected}), 来源=${clickSource}${positionText}`
          : `✗ ${buttonLabel}(${typeLabel}): keys=${detectedKeys}, 预期 ${expected}, 来源=${clickSource}${positionText}`,
    );
  }, [appendLog]);

  const handleHover = useCallback((event: React.MouseEvent<HTMLDivElement>) => {
    const native = event.nativeEvent;
    const clickSource = detectEventSource(native);
    appendLog(
      {
        buttonId: 'hover-target',
        buttonLabel: 'Hover 目标',
        eventType: 'hover',
        detectedKeys: '-',
        clickSource,
        isTrusted: native.isTrusted,
      },
      `Hover 目标(悬停): 来源=${clickSource}`,
    );
  }, [appendLog]);

  const handleFocus = useCallback((event: React.FocusEvent<HTMLElement>) => {
    const native = event.nativeEvent;
    const clickSource = detectEventSource(native);
    appendLog(
      {
        buttonId: 'focus-target',
        buttonLabel: 'Focus 目标',
        eventType: 'focus',
        detectedKeys: '-',
        clickSource,
        isTrusted: native.isTrusted,
      },
      `Focus 目标(聚焦): 来源=${clickSource}`,
    );
  }, [appendLog]);

  const handlePositionGridClick = useCallback((event: React.MouseEvent<HTMLDivElement>) => {
    const panel = event.currentTarget;
    const native = event.nativeEvent;
    const position = detectClickPosition(native, panel);
    handleInteraction(
      'position-grid-panel',
      '九宫格方位面板',
      ANY_EXPECTED,
      event,
      'click',
      {
        clickPosition: formatClickPosition(position),
        offsetX: Math.round(native.offsetX),
        offsetY: Math.round(native.offsetY),
      },
    );
  }, [handleInteraction]);

  const handleClick = useCallback((
    buttonId: string,
    buttonLabel: string,
    expected: string,
    event: React.MouseEvent<HTMLElement>,
  ) => handleInteraction(buttonId, buttonLabel, expected, event, 'click'), [handleInteraction]);

  const columns: ColumnsType<InteractionLog> = [
    { title: '时间', dataIndex: 'time', width: 90 },
    {
      title: '事件',
      dataIndex: 'eventType',
      width: 72,
      render: (value: InteractionType) => {
        const color =
          value === 'dblclick' ? 'purple'
            : value === 'contextmenu' ? 'cyan'
              : value === 'hover' ? 'gold'
                : value === 'focus' ? 'green'
                  : 'default';
        return <Tag color={color}>{getInteractionTypeLabel(value)}</Tag>;
      },
    },
    {
      title: '点击来源',
      dataIndex: 'clickSource',
      width: 110,
      render: (value: ClickSource) => (
        <Tag color={value === '真实鼠标' ? 'success' : 'warning'}>{value}</Tag>
      ),
    },
    {
      title: '方位',
      dataIndex: 'clickPosition',
      width: 130,
      render: (value?: string) => (value ? <Tag color="geekblue">{value}</Tag> : '-'),
    },
    {
      title: 'offset',
      width: 96,
      render: (_: unknown, record: InteractionLog) =>
        record.offsetX !== undefined && record.offsetY !== undefined
          ? `${record.offsetX}, ${record.offsetY}`
          : '-',
    },
    {
      title: '检测结果',
      dataIndex: 'detectedKeys',
      width: 100,
      render: (value: string) => <Tag color={value === 'none' ? 'default' : 'processing'}>{value}</Tag>,
    },
  ];

  return (
    <PageLayout
      title="元素点击测试"
      subtitle="测试 click, hover, focus 的 keys, position 等参数"
      fullWidth
      inset={24}
    >
      <div
        style={{
          display: 'flex',
          gap: 24,
          alignItems: 'stretch',
        }}
      >
        <div style={{ flex: 1, minWidth: 0 }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 8 }}>
            <div style={{ display: 'flex', alignItems: 'baseline', gap: 8 }}>
              <Typography.Title level={5} style={{ margin: 0 }}>
                点击记录
              </Typography.Title>
              <Typography.Text type="secondary" style={{ fontSize: 13 }}>
                (仅保留最近 20 条)
              </Typography.Text>
            </div>
            <Button
              id="btn-clear-keys-log"
              size="small"
              disabled={logs.length === 0}
              onClick={() => {
                setLogs([]);
                setLastResult('等待交互...');
              }}
            >
              清除记录
            </Button>
          </div>
          <Table
            id="keys-click-log"
            size="small"
            rowKey="key"
            columns={columns}
            dataSource={logs}
            pagination={false}
            scroll={{ x: 'max-content' }}
            locale={{ emptyText: '暂无记录, 请操作右侧测试区域' }}
          />
        </div>

        <div style={{ flexShrink: 0, width: 1, background: '#EEE' }} aria-hidden />

        <Space
          direction="vertical"
          size={20}
          style={{ flex: '0 0 auto', width: TEST_PANEL_MAX_WIDTH, maxWidth: '100%' }}
        >
          <div>
            <Typography.Title level={5} style={{ marginTop: 0 }}>
              测试按钮
            </Typography.Title>
            <Typography.Paragraph type="secondary">
              单一入口, 可反复用不同 <code>keys</code> 值点击同一元素做回归测试.
            </Typography.Paragraph>
            <Space wrap size={12}>
              <Button
                id="btn-click-target"
                size="large"
                onClick={(event) => handleClick('btn-click-target', '测试按钮', ANY_EXPECTED, event)}
              >
                单击触发
              </Button>
              <Button
                id="btn-dblclick-target"
                size="large"
                onClick={() => setLastResult('双击按钮: 单击未触发, 请双击')}
                onDoubleClick={(event) =>
                  handleInteraction('btn-dblclick-target', '双击触发按钮', ANY_EXPECTED, event, 'dblclick')
                }
              >
                双击触发
              </Button>
              <Button
                id="btn-rightclick-target"
                size="large"
                onClick={() => setLastResult('右键按钮: 左键未触发, 请右键')}
                onContextMenu={(event) => {
                  event.preventDefault();
                  handleInteraction('btn-rightclick-target', '右键触发按钮', ANY_EXPECTED, event, 'contextmenu');
                }}
              >
                右键触发
              </Button>
            </Space>
          </div>

          <div>
            <Typography.Title level={5} style={{ marginTop: 0 }}>
              点击方位测试(九宫格)
            </Typography.Title>
            <Typography.Paragraph type="secondary">每个按钮的尺寸都是 100 * 100</Typography.Paragraph>
            <div
              id="position-grid-panel"
              onClick={handlePositionGridClick}
              style={{
                display: 'grid',
                gridTemplateColumns: `repeat(3, ${GRID_CELL_SIZE}px)`,
                gridTemplateRows: `repeat(3, ${GRID_CELL_SIZE}px)`,
                width: GRID_CELL_SIZE * 3,
                maxWidth: '100%',
                border: '2px solid #1677ff',
                borderRadius: 8,
                overflow: 'hidden',
                cursor: 'crosshair',
                userSelect: 'none',
              }}
            >
              {POSITION_GRID.flat().map((cell) => (
                <div
                  key={cell.value}
                  data-position={cell.value}
                  style={{
                    display: 'flex',
                    flexDirection: 'column',
                    alignItems: 'center',
                    justifyContent: 'center',
                    border: '1px solid #bfdbfe',
                    background: '#eff6ff',
                    fontSize: 15,
                    fontWeight: 600,
                    color: '#1d4ed8',
                    lineHeight: 1.3,
                  }}
                >
                  <span>{cell.label}</span>
                  <span style={{ fontSize: 11, fontWeight: 400, color: '#64748b' }}>{toPositionCamelCase(cell.value)}</span>
                </div>
              ))}
            </div>
            <Typography.Paragraph
              id="keys-click-result"
              style={{
                marginTop: 12,
                marginBottom: 0,
                padding: 12,
                background: '#f8fafc',
                borderRadius: 8,
                whiteSpace: 'pre-wrap',
                lineHeight: 1.5715,
                minHeight: 'calc(1.5715em * 2 + 24px)',
                boxSizing: 'border-box',
              }}
            >
              {lastResult}
            </Typography.Paragraph>
          </div>

          <div>
            <Typography.Title level={5} style={{ marginTop: 0 }}>
              测试 hover() / focus()
            </Typography.Title>
            <Typography.Paragraph type="secondary">
              左测试: <code>hover()</code> 目标, 右测试: <code>focus()</code> 目标
            </Typography.Paragraph>
            <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
              <div
                id="hover-target"
                title="hover-target"
                onMouseEnter={(event) => {
                  setHoverActive(true);
                  handleHover(event);
                }}
                onMouseLeave={() => setHoverActive(false)}
                style={{
                  width: INTERACTION_BOX_SIZE,
                  height: INTERACTION_BOX_SIZE,
                  boxSizing: 'border-box',
                  borderRadius: 8,
                  border: `2px solid ${hoverActive ? '#f59e0b' : '#fcd34d'}`,
                  background: hoverActive ? '#fffbeb' : '#fff',
                  color: hoverActive ? '#b45309' : '#92400e',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  fontSize: 12,
                  fontWeight: 600,
                  cursor: 'default',
                  transition: 'all 0.2s ease',
                  flexShrink: 0,
                  userSelect: 'none',
                }}
              >
                hover()
              </div>
              <button
                id="focus-target"
                type="button"
                title="focus-target"
                onFocus={(event) => {
                  setFocusActive(true);
                  handleFocus(event);
                }}
                onBlur={() => setFocusActive(false)}
                style={{
                  width: INTERACTION_BOX_SIZE,
                  height: INTERACTION_BOX_SIZE,
                  boxSizing: 'border-box',
                  padding: 0,
                  borderRadius: 8,
                  border: `2px solid ${focusActive ? '#22c55e' : '#86efac'}`,
                  background: focusActive ? '#f0fdf4' : '#fff',
                  color: focusActive ? '#15803d' : '#166534',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  fontSize: 12,
                  fontWeight: 600,
                  cursor: 'pointer',
                  outline: 'none',
                  flexShrink: 0,
                }}
              >
                focus()
              </button>
            </div>
          </div>
        </Space>
      </div>
    </PageLayout>
  );
}
