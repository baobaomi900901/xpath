import { useCallback, useEffect, useRef, useState } from 'react';
import PageLayout from '../components/PageLayout';
import GeometryTestScene, { NestedScene, type SceneEvent, type SceneMode, type TestTab } from './GeometryTestScene';
import './geometry-test.css';

type Point = { x: number; y: number };
type Box = { left: number; top: number; right: number; bottom: number; width: number; height: number };
type Environment = ReturnType<typeof readEnvironment>;
type Snapshot = {
  time: string; mode: SceneMode; tab: TestTab; target: string;
  environment: Environment; browserZoom: number; systemScale: number;
  localViewport: Box; topViewport: Box; iframeOffsets: Point[];
  scroll: ReturnType<typeof scrollValues>[];
};

function readEnvironment() {
  return { dpr: window.devicePixelRatio, width: window.innerWidth, height: window.innerHeight,
    screenX: window.screenX, screenY: window.screenY,
    visualScale: window.visualViewport?.scale ?? 1 };
}
function scrollValues(el: Element, name: string) {
  return { name, left: el.scrollLeft, top: el.scrollTop, width: el.scrollWidth, height: el.scrollHeight,
    clientWidth: el.clientWidth, clientHeight: el.clientHeight,
    maxLeft: Math.max(0, el.scrollWidth - el.clientWidth), maxTop: Math.max(0, el.scrollHeight - el.clientHeight) };
}
function measure(element: HTMLElement) {
  const rect = element.getBoundingClientRect();
  const localViewport: Box = { left: rect.left, top: rect.top, right: rect.right, bottom: rect.bottom, width: rect.width, height: rect.height };
  const topViewport = { ...localViewport };
  const iframeOffsets: Point[] = [];
  let win = element.ownerDocument.defaultView;
  while (win && win !== window.top) {
    const frame = win.frameElement as HTMLElement | null;
    if (!frame) break;
    const box = frame.getBoundingClientRect();
    const offset = { x: box.left + frame.clientLeft, y: box.top + frame.clientTop };
    iframeOffsets.push(offset);
    topViewport.left += offset.x; topViewport.right += offset.x;
    topViewport.top += offset.y; topViewport.bottom += offset.y;
    win = frame.ownerDocument.defaultView;
  }
  const root = element.getRootNode() as Document | ShadowRoot;
  const scroll = ['scroll-outer', 'scroll-inner', 'scroll-child'].flatMap(id => {
    const node = root.getElementById(id);
    return node ? [scrollValues(node, id)] : [];
  });
  scroll.push(scrollValues(element.ownerDocument.documentElement, 'target-document'));
  if (element.ownerDocument !== document) scroll.push(scrollValues(document.documentElement, 'top-document'));
  return { localViewport, topViewport, iframeOffsets, scroll };
}
const anchors = ['左上', '上', '右上', '左', '中心', '右', '左下', '下', '右下', '随机范围'];
function storedNumber(key: string, fallback: number) {
  try { const value = Number(localStorage.getItem(key)); return value > 0 ? value : fallback; } catch { return fallback; }
}

export default function GeometryTestPage() {
  const [mode, setMode] = useState<SceneMode>('plain');
  const [tab, setTab] = useState<TestTab>('geometry');
  const [generation, setGeneration] = useState(0);
  const target = useRef<HTMLElement | null>(null);
  const [snapshot, setSnapshot] = useState<Snapshot | null>(null);
  const [previous, setPrevious] = useState<Snapshot | null>(null);
  const [environment, setEnvironment] = useState(readEnvironment);
  const [browserZoom, setBrowserZoom] = useState(() => storedNumber('geometry-browser-zoom', 100));
  const [systemScale, setSystemScale] = useState(() => storedNumber('geometry-system-scale', 100));
  const [stale, setStale] = useState(true);
  const [events, setEvents] = useState<SceneEvent[]>([]);
  const [anchor, setAnchor] = useState(4);
  const [offset, setOffset] = useState<Point>({ x: 0, y: 0 });
  const [coordinateSpace, setCoordinateSpace] = useState('top');
  const [originX, setOriginX] = useState('');
  const [originY, setOriginY] = useState('');
  const [tolerance, setTolerance] = useState(1);
  const [sdk, setSdk] = useState('');
  const [comparison, setComparison] = useState('');
  const [notice, setNotice] = useState('');
  const [scrollTarget, setScrollTarget] = useState('scroll-outer');
  const [scrollBehavior, setScrollBehavior] = useState<ScrollBehavior>('instant');
  const [scrollPoint, setScrollPoint] = useState<Point>({ x: 100, y: 100 });

  const bindTarget = useCallback((node: HTMLElement | null) => { target.current = node; }, []);
  const addEvent = useCallback((event: SceneEvent) => { setEvents(items => [event, ...items].slice(0, 30)); }, []);
  useEffect(() => {
    let last = JSON.stringify(readEnvironment());
    const check = () => {
      const next = readEnvironment();
      const encoded = JSON.stringify(next);
      if (last === encoded) return;
      last = encoded;
      setStale(true);
      setComparison('');
      setOriginX(''); setOriginY('');
      setEnvironment(next);
    };
    const timer = window.setInterval(check, 750);
    window.addEventListener('resize', check);
    return () => { window.clearInterval(timer); window.removeEventListener('resize', check); };
  }, []);
  useEffect(() => {
    setStale(true); setComparison('');
    setOriginX(''); setOriginY('');
    try {
      localStorage.setItem('geometry-browser-zoom', String(browserZoom));
      localStorage.setItem('geometry-system-scale', String(systemScale));
    } catch { setNotice('浏览器无法保存缩放记录，本次设置仍有效。'); }
  }, [browserZoom, systemScale]);

  function capture() {
    if (!target.current) { setNotice('测试场景尚未加载。'); return; }
    setPrevious(snapshot);
    setSnapshot({ ...measure(target.current), time: new Date().toISOString(), mode, tab,
      target: target.current.id, environment: readEnvironment(), browserZoom, systemScale });
    setStale(false); setComparison(''); setNotice('已读取快照；读取过程未调用滚动或聚焦接口。');
  }
  function reset() { setGeneration(value => value + 1); setSnapshot(null); setPrevious(null); setStale(true); setComparison(''); }
  function changeScene(nextMode: SceneMode, nextTab: TestTab) { setMode(nextMode); setTab(nextTab); reset(); }

  function referenceBox(): Box {
    if (!snapshot || stale) throw new Error('请先重新读取基准快照。');
    const box = coordinateSpace === 'local' ? snapshot.localViewport : snapshot.topViewport;
    if (coordinateSpace === 'local' || coordinateSpace === 'top') return box;
    if (snapshot.environment.visualScale !== 1) throw new Error('当前存在视觉视口缩放；屏幕坐标推算暂不支持此模式，请使用 CSS 视口坐标比较。');
    if (!originX.trim() || !originY.trim() || !Number.isFinite(Number(originX)) || !Number.isFinite(Number(originY))) {
      throw new Error('请填写 SDK 提供的顶层网页视口左上角屏幕物理坐标。');
    }
    const scale = snapshot.environment.dpr;
    const divisor = coordinateSpace === 'dpi96' ? snapshot.systemScale / 100 : 1;
    return {
      left: (Number(originX) + box.left * scale) / divisor,
      right: (Number(originX) + box.right * scale) / divisor,
      top: (Number(originY) + box.top * scale) / divisor,
      bottom: (Number(originY) + box.bottom * scale) / divisor,
      width: box.width * scale / divisor, height: box.height * scale / divisor,
    };
  }
  function compare() {
    try {
      const box = referenceBox();
      const value: unknown = JSON.parse(sdk);
      const actual = Array.isArray(value) ? { x: value[0], y: value[1] } : value;
      if (!actual || typeof actual !== 'object') throw new Error('请输入坐标对象或 [x,y]。');
      const data = actual as Record<string, unknown>;
      const keys: (keyof Box)[] = ['left', 'top', 'right', 'bottom', 'width', 'height'];
      const factor = coordinateSpace === 'screen' ? snapshot!.environment.dpr : coordinateSpace === 'dpi96' ? snapshot!.environment.dpr / (snapshot!.systemScale / 100) : 1;
      let differences: Record<string, number>;
      if ('x' in data && 'y' in data) {
        if (typeof data.x !== 'number' || typeof data.y !== 'number' || !Number.isFinite(data.x) || !Number.isFinite(data.y)) throw new Error('x/y 必须为有限数值。');
        const x = data.x - offset.x * factor; const y = data.y - offset.y * factor;
        if (anchor === 9) {
          setComparison(x >= box.left - tolerance && x <= box.right + tolerance && y >= box.top - tolerance && y <= box.bottom + tolerance ? '通过：随机点位于目标范围内（已扣除偏移）。' : '不通过：随机点超出目标范围。');
          return;
        }
        differences = { x: x - (box.left + box.width * (anchor % 3) / 2), y: y - (box.top + box.height * Math.floor(anchor / 3) / 2) };
      } else {
        const supplied = keys.filter(key => key in data);
        if (!supplied.length) throw new Error('支持 {x,y}、[x,y] 或 left/top/right/bottom/width/height 边界字段。');
        differences = Object.fromEntries(supplied.map(key => {
          const n = data[key];
          if (typeof n !== 'number' || !Number.isFinite(n)) throw new Error(`${key} 必须为有限数值。`);
          return [key, n - box[key]];
        }));
      }
      setComparison(`${Object.values(differences).every(n => Math.abs(n) <= tolerance) ? '通过' : '不通过'}（仅比较提交的字段）：${JSON.stringify(differences)}`);
    } catch (error) { setComparison(error instanceof Error ? error.message : String(error)); }
  }
  function runScroll(location: 'top' | 'bottom' | 'point' | 'one_screen') {
    const node = target.current;
    if (!node) return;
    const root = node.getRootNode() as Document | ShadowRoot;
    const el = scrollTarget === 'document' ? node.ownerDocument.documentElement : scrollTarget === 'top-document' ? document.documentElement : root.getElementById(scrollTarget);
    if (!el) return;
    const before = scrollValues(el, scrollTarget);
    el.scrollTo({ behavior: scrollBehavior,
      left: location === 'point' ? scrollPoint.x : location === 'top' ? 0 : location === 'bottom' ? el.scrollWidth : el.scrollLeft,
      top: location === 'point' ? scrollPoint.y : location === 'top' ? 0 : location === 'bottom' ? el.scrollHeight : el.scrollTop + el.clientHeight });
    addEvent({ time: new Date().toISOString(), type: 'scroll-reference', target: scrollTarget, data: { location, behavior: scrollBehavior, before } });
    setNotice('已执行网页原生滚动参考操作；滚动结束后读取快照比较。此按钮不调用 SDK。');
  }
  async function copy() {
    try {
      await navigator.clipboard.writeText(JSON.stringify({ snapshot, previous, stale, currentEnvironment: environment,
        comparison: { coordinateSpace, anchor: anchors[anchor], offsetCss: offset, tolerance, viewportOriginPhysical: { x: originX, y: originY }, sdk, result: comparison }, events }, null, 2));
      setNotice('已复制 JSON。');
    } catch { setNotice('复制失败，请检查剪贴板权限。'); }
  }

  return <PageLayout title="坐标、滚动与拖拽测试" subtitle="固定 ID · CSS 像素基准 · 缩放环境记录 · SDK 返回值对照" fullWidth>
    <div className="geometry-lab">
      <section className="geometry-env">
        <label>浏览器缩放 %（手填）<input id="browser-zoom" type="number" min={10} value={browserZoom} onChange={e => setBrowserZoom(Math.max(10, Number(e.target.value)))} /></label>
        <label>系统 UI 缩放 %（手填）<input id="system-scale" type="number" min={25} value={systemScale} onChange={e => setSystemScale(Math.max(25, Number(e.target.value)))} /></label>
        <span>DPR <b>{environment.dpr}</b> · 视口 {environment.width} × {environment.height} CSS px · Visual scale {environment.visualScale}</span>
      </section>
      <p className="geometry-hint">DPR 不用于反推两种缩放。切换显示器后请更新系统缩放，并重新读取快照。屏幕原点必须是网页内容视口原点，不是整个浏览器窗口或客户区原点。</p>
      <div className="geometry-toolbar">
        <label>场景 <select aria-label="场景" value={mode} onChange={e => changeScene(e.target.value as SceneMode, tab)}>
          <option value="plain">普通页面</option><option value="iframe">iframe</option><option value="shadow">iframe → Open Shadow</option>
        </select></label>
        <button onClick={reset}>重置场景</button><button id="geometry-capture" onClick={capture}>读取快照</button><button onClick={copy}>复制 JSON</button>
        <strong role="status">{stale ? '请重新读取基准快照' : '快照已记录（场景变化后需重读）'}</strong>
      </div>
      <div className="geometry-tabs" role="tablist" aria-label="测试类型">
        {([['geometry', '坐标与锚点'], ['scroll', '滚动'], ['drag', '拖拽']] as const).map(([key, label]) => <button key={key} role="tab" aria-selected={tab === key} onClick={() => changeScene(mode, key)}>{label}</button>)}
      </div>
      <div className="geometry-layout">
        <section className="geometry-scene" aria-label="测试场景">
          <NestedScene key={`${mode}-${tab}-${generation}`} mode={mode}>
            <GeometryTestScene tab={tab} onTarget={bindTarget} onEvent={addEvent} />
          </NestedScene>
        </section>
        <aside className="geometry-data">
          <h3>当前目标与快照</h3>
          <p>单位：CSS px。快照不随日志自动更新。</p>
          <pre id="geometry-snapshot">{snapshot ? JSON.stringify(snapshot, null, 2) : '请点击“读取快照”'}</pre>
          {snapshot && <details><summary>九宫格锚点（顶层视口，边缘 / 中心基准）</summary><pre>{JSON.stringify(anchors.slice(0, 9).map((name, i) => ({ name,
            x: snapshot.topViewport.left + snapshot.topViewport.width * (i % 3) / 2,
            y: snapshot.topViewport.top + snapshot.topViewport.height * Math.floor(i / 3) / 2 })), null, 2)}</pre></details>}
          {tab === 'scroll' ? <>
            <h3>滚动参考操作</h3>
            <select aria-label="滚动目标" value={scrollTarget} onChange={e => setScrollTarget(e.target.value)}>
              <option value="scroll-outer">外层容器</option><option value="scroll-inner">内层容器</option><option value="document">目标文档</option><option value="top-document">顶层文档</option>
            </select>{' '}
            <select aria-label="滚动行为" value={scrollBehavior} onChange={e => setScrollBehavior(e.target.value as ScrollBehavior)}><option value="instant">instant</option><option value="smooth">smooth</option></select>
            <label>left<input type="number" value={scrollPoint.x} onChange={e => setScrollPoint({ ...scrollPoint, x: Number(e.target.value) })} /></label>
            <label>top<input type="number" value={scrollPoint.y} onChange={e => setScrollPoint({ ...scrollPoint, y: Number(e.target.value) })} /></label>
            <div className="geometry-toolbar">{(['top', 'bottom', 'point', 'one_screen'] as const).map(value => <button key={value} onClick={() => runScroll(value)}>{value}</button>)}</div>
            <p>用 SDK 定位 scroll-child，分别测试 search_up=False / True；该元素本身不滚动。</p>
            <pre id="scroll-difference">{snapshot && previous ? JSON.stringify(snapshot.scroll.map(row => {
              const before = previous.scroll.find(item => item.name === row.name);
              return { name: row.name, deltaTop: row.top - (before?.top ?? row.top), deltaLeft: row.left - (before?.left ?? row.left) };
            }), null, 2) : '读取两次快照后显示滚动差值'}</pre>
          </> : <>
            <h3>SDK 返回值对照</h3>
            <label>坐标系<select value={coordinateSpace} onChange={e => { setCoordinateSpace(e.target.value); setComparison(''); }}>
              <option value="top">顶层视口 · CSS px</option><option value="local">元素所在视口 · CSS px</option><option value="screen">屏幕 · 物理 px（推算）</option><option value="dpi96">屏幕 · 96 DPI（推算）</option>
            </select></label>
            {(coordinateSpace === 'screen' || coordinateSpace === 'dpi96') && <>
              <p className="geometry-hint">推算依赖 SDK 视口原点、DPR 与手填系统缩放，不是独立的系统坐标基准。96 DPI 模式假设整个屏幕坐标按当前显示器缩放归一化；跨显示器需与 SDK 约定一致。</p>
              <label>视口原点物理 X<input type="number" value={originX} onChange={e => { setOriginX(e.target.value); setComparison(''); }} /></label>
              <label>视口原点物理 Y<input type="number" value={originY} onChange={e => { setOriginY(e.target.value); setComparison(''); }} /></label>
            </>}
            <label>锚点<select value={anchor} onChange={e => { setAnchor(Number(e.target.value)); setComparison(''); }}>{anchors.map((name, i) => <option key={name} value={i}>{name}</option>)}</select></label>
            <div className="geometry-toolbar">
              <label>偏移 X（CSS px）<input type="number" value={offset.x} onChange={e => { setOffset({ ...offset, x: Number(e.target.value) }); setComparison(''); }} /></label>
              <label>偏移 Y（CSS px）<input type="number" value={offset.y} onChange={e => { setOffset({ ...offset, y: Number(e.target.value) }); setComparison(''); }} /></label>
            </div>
            <label>容许误差（所选单位）<input type="number" min={0} step={0.1} value={tolerance} onChange={e => { setTolerance(Math.max(0, Number(e.target.value))); setComparison(''); }} /></label>
            <textarea id="sdk-coordinate-result" rows={4} value={sdk} onChange={e => { setSdk(e.target.value); setComparison(''); }} placeholder={'粘贴 {"x":123,"y":456}、[x,y] 或边界字典'} />
            <button id="geometry-compare" disabled={!snapshot || stale} onClick={compare}>比较</button>
            <p id="geometry-comparison" role="status">{comparison}</p>
          </>}
        </aside>
      </div>
      <p role="status">{notice}</p>
      <div className="geometry-toolbar"><h3>事件记录（最近 30 条）</h3><button onClick={() => setEvents([])}>清空记录</button></div>
      <pre id="geometry-events" className="geometry-events">{events.length ? events.map(event => JSON.stringify(event)).join('\n') : '暂无事件'}</pre>
    </div>
  </PageLayout>;
}
