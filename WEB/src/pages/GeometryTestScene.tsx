import { useEffect, useRef, useState, type ReactNode } from 'react';
import { createPortal } from 'react-dom';

export type SceneMode = 'plain' | 'iframe' | 'shadow';
export type TestTab = 'geometry' | 'scroll' | 'drag';
export type SceneEvent = { time: string; type: string; target: string; data: Record<string, unknown> };

export function NestedScene({ mode, children }: { mode: SceneMode; children: ReactNode }) {
  const [mount, setMount] = useState<HTMLElement | ShadowRoot | null>(null);
  if (mode === 'plain') return <>{children}</>;
  return <>
    <iframe id="geometry-frame" title="坐标测试 iframe" style={{ width: '100%', height: 650, border: '4px solid #93c5fd' }}
      srcDoc={'<!doctype html><html><head><meta charset="utf-8"></head><body style="margin:0"><div id="geometry-shadow-host"></div></body></html>'}
      onLoad={event => {
        const host = event.currentTarget.contentDocument!.getElementById('geometry-shadow-host')!;
        setMount(mode === 'shadow' ? host.shadowRoot ?? host.attachShadow({ mode: 'open' }) : host);
      }} />
    {mount && createPortal(children, mount)}
  </>;
}

export default function GeometryTestScene({ tab, onTarget, onEvent }: {
  tab: TestTab;
  onTarget: (element: HTMLElement | null) => void;
  onEvent: (event: SceneEvent) => void;
}) {
  const root = useRef<HTMLDivElement>(null);
  const [covered, setCovered] = useState(false);
  const [farAway, setFarAway] = useState(false);
  const [bounded, setBounded] = useState(true);
  const [position, setPosition] = useState({ x: 40, y: 40 });
  const positionRef = useRef(position);
  const session = useRef<{ x: number; y: number; left: number; top: number } | null>(null);
  const emit = (type: string, target: string, data: Record<string, unknown>) => onEvent({ time: new Date().toISOString(), type, target, data });

  useEffect(() => {
    const doc = root.current!.ownerDocument;
    const win = doc.defaultView!;
    const record = () => onEvent({ time: new Date().toISOString(), type: 'document-scroll', target: 'target-document',
      data: { top: doc.documentElement.scrollTop, left: doc.documentElement.scrollLeft } });
    win.addEventListener('scroll', record);
    return () => win.removeEventListener('scroll', record);
  }, [onEvent]);

  useEffect(() => {
    const win = root.current!.ownerDocument.defaultView!;
    const move = (event: MouseEvent) => {
      const start = session.current;
      if (!start) return;
      let x = start.left + event.clientX - start.x;
      let y = start.top + event.clientY - start.y;
      if (bounded) { x = Math.max(0, Math.min(440, x)); y = Math.max(0, Math.min(320, y)); }
      positionRef.current = { x, y };
      setPosition({ x, y });
    };
    const end = (event: MouseEvent) => {
      const start = session.current;
      if (!start) return;
      move(event);
      session.current = null;
      onEvent({ time: new Date().toISOString(), type: 'drag-end', target: 'geometry-drag-target', data: {
        clientX: event.clientX, clientY: event.clientY, screenX: event.screenX, screenY: event.screenY,
        left: positionRef.current.x, top: positionRef.current.y,
        deltaX: positionRef.current.x - start.left, deltaY: positionRef.current.y - start.top,
        isTrusted: event.isTrusted,
      } });
    };
    win.addEventListener('mousemove', move);
    win.addEventListener('mouseup', end);
    return () => { win.removeEventListener('mousemove', move); win.removeEventListener('mouseup', end); };
  }, [bounded, onEvent]);

  return <div ref={root} style={{ padding: 20, font: '14px system-ui', color: '#172554', background: '#f8fafc', minHeight: 560 }}>
    {tab === 'geometry' && <>
      <p>目标尺寸 160 × 100 CSS px；九宫格标记方位，坐标基准使用边缘与中心。</p>
      <label><input type="checkbox" checked={covered} onChange={e => setCovered(e.target.checked)} /> 遮罩覆盖目标</label>{' '}
      <label><input type="checkbox" checked={farAway} onChange={e => setFarAway(e.target.checked)} /> 将目标放到视口下方</label>
      <div style={{ height: farAway ? 1000 : 90 }} />
      <div style={{ position: 'relative', width: 160, height: 100, marginLeft: 35 }}>
        <div id="geometry-target" ref={onTarget}
          onClick={e => emit('click', e.currentTarget.id, { clientX: e.clientX, clientY: e.clientY, isTrusted: e.nativeEvent.isTrusted })}
          style={{ width: 160, height: 100, display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gridTemplateRows: 'repeat(3, 1fr)', background: '#dbeafe', cursor: 'crosshair' }}>
          {['左上', '上', '右上', '左', '中心', '右', '左下', '下', '右下'].map(label => <span key={label}
            style={{ display: 'grid', placeItems: 'center', outline: '1px solid #93c5fd', outlineOffset: -1 }}>{label}</span>)}
        </div>
        {covered && <div id="geometry-cover" style={{ position: 'absolute', inset: -8, background: '#64748bf0', color: 'white', display: 'grid', placeItems: 'center' }}>遮罩</div>}
      </div>
      <div style={{ height: 100 }} />
    </>}
    {tab === 'scroll' && <>
      <p>外层 520 × 320，内容 1100 × 900；内层 300 × 160，内容 700 × 500（CSS px）。</p>
      <div id="scroll-outer" ref={onTarget} onScroll={e => emit('scroll', e.currentTarget.id, { top: e.currentTarget.scrollTop, left: e.currentTarget.scrollLeft })}
        style={{ width: 520, height: 320, overflow: 'scroll', border: '2px solid #60a5fa' }}>
        <div style={{ width: 1100, height: 900, position: 'relative', background: 'repeating-linear-gradient(0deg,#eff6ff 0 99px,#bfdbfe 99px 100px)' }}>
          <strong style={{ position: 'absolute', top: 0, left: 0 }}>顶部 / 左端 (0, 0)</strong>
          <div id="scroll-inner" onScroll={e => { e.stopPropagation(); emit('scroll', e.currentTarget.id, { top: e.currentTarget.scrollTop, left: e.currentTarget.scrollLeft }); }}
            style={{ position: 'absolute', left: 150, top: 150, width: 300, height: 160, overflow: 'scroll', border: '2px solid #a78bfa' }}>
            <div style={{ width: 700, height: 500, background: '#ede9fe', position: 'relative' }}>
              内层顶部
              <span id="scroll-child" style={{ position: 'absolute', left: 350, top: 250, padding: 8, background: '#fef3c7' }}>普通子元素（search_up）</span>
              <span style={{ position: 'absolute', right: 0, bottom: 0 }}>内层底部 / 右端</span>
            </div>
          </div>
          <span style={{ position: 'absolute', left: 550, top: 450 }}>中部 (550, 450)</span>
          <strong style={{ position: 'absolute', bottom: 0, right: 0 }}>底部 / 右端</strong>
        </div>
      </div>
      <p>页面滚动标记：下方留白供 WebBrowser.get_scroll 测试。</p>
      <div style={{ width: 1200, height: 900, background: 'linear-gradient(#f8fafc,#dbeafe)', display: 'flex', alignItems: 'end', justifyContent: 'end' }}>当前文档底部 / 右端</div>
    </>}
    {tab === 'drag' && <>
      <p>拖拽块 120 × 80，画布 560 × 400 CSS px；十字为目标落点。</p>
      <label><input type="checkbox" checked={bounded} onChange={e => setBounded(e.target.checked)} /> 限制在画布内</label>
      <p id="drag-position">left={position.x}, top={position.y}；中心误差 Δx={position.x + 60 - 380}, Δy={position.y + 40 - 240}</p>
      <div id="geometry-drag-arena" style={{ position: 'relative', width: 560, height: 400, marginTop: 16, outline: '1px solid #93c5fd', background: 'repeating-linear-gradient(0deg,#eff6ff 0 39px,#bfdbfe 39px 40px)' }}>
        <span id="drag-destination" style={{ position: 'absolute', left: 380, top: 240, transform: 'translate(-50%,-50%)', color: '#dc2626', fontSize: 28, pointerEvents: 'none' }}>＋</span>
        <div id="geometry-drag-target" ref={onTarget} role="button" tabIndex={0} aria-label="坐标拖拽目标"
          data-left={position.x} data-top={position.y}
          onMouseDown={e => {
            if (e.button !== 0) return;
            e.preventDefault();
            session.current = { x: e.clientX, y: e.clientY, left: positionRef.current.x, top: positionRef.current.y };
            emit('drag-start', e.currentTarget.id, { clientX: e.clientX, clientY: e.clientY, isTrusted: e.nativeEvent.isTrusted });
          }}
          style={{ position: 'absolute', left: position.x, top: position.y, width: 120, height: 80, background: '#2563eb', color: 'white', display: 'grid', placeItems: 'center', cursor: 'grab', userSelect: 'none' }}>拖拽目标</div>
      </div>
    </>}
  </div>;
}
