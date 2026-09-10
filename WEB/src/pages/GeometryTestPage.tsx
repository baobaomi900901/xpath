import { useEffect, useRef, useState } from 'react';
import { Button, Space, Tabs, Typography } from 'antd';
import PageLayout from '../components/PageLayout';
import GeometryDragPanel from './GeometryDragPanel';
import GeometryCoordinatesPanel from './GeometryCoordinatesPanel';
import GeometryPageScrollPanel from './GeometryPageScrollPanel';

type ScreenDetails = EventTarget & {
  currentScreen: EventTarget & { devicePixelRatio: number };
};
type ScreenWindow = Window & { getScreenDetails?: () => Promise<ScreenDetails> };

export default function GeometryTestPage() {
  const detailsRef = useRef<ScreenDetails | null>(null);
  const [scale, setScale] = useState<{ system: number; browser: number } | null>(null);
  const [status, setStatus] = useState('点击读取后，请允许浏览器访问屏幕信息。');
  const [loading, setLoading] = useState(false);

  const update = () => {
    const system = detailsRef.current?.currentScreen.devicePixelRatio;
    if (!system || !Number.isFinite(system)) {
      setScale(null);
      return;
    }
    setScale({ system: system * 100, browser: window.devicePixelRatio / system * 100 });
  };

  useEffect(() => {
    // 同时捕获浏览器缩放和跨显示器移动导致的像素比例变化。
    const timer = window.setInterval(update, 500);
    window.addEventListener('resize', update);
    return () => {
      window.clearInterval(timer);
      window.removeEventListener('resize', update);
    };
  }, []);

  const read = async () => {
    const screenWindow = window as ScreenWindow;
    if (!screenWindow.getScreenDetails) {
      setStatus('当前浏览器不支持屏幕信息接口，无法自动区分系统缩放和浏览器缩放。');
      return;
    }
    setLoading(true);
    try {
      detailsRef.current = await screenWindow.getScreenDetails();
      update();
      setStatus('系统缩放取当前屏幕像素比例；浏览器缩放由窗口与屏幕像素比例计算。切换屏幕或缩放后自动更新。');
    } catch {
      detailsRef.current = null;
      setScale(null);
      setStatus('未取得屏幕访问权限，请允许后重新读取。');
    } finally {
      setLoading(false);
    }
  };

  const format = (value: number | undefined) => value === undefined ? '未获取' : `${Number(value.toFixed(2))}%`;
  return (
    <PageLayout title="坐标、滚动与拖拽测试" fullWidth>
      <Space size={32} wrap>
        <Typography.Text>系统缩放：<strong id="system-scale">{format(scale?.system)}</strong></Typography.Text>
        <Typography.Text>浏览器缩放：<strong id="browser-zoom">{format(scale?.browser)}</strong></Typography.Text>
        <Button onClick={read} loading={loading}>读取缩放</Button>
      </Space>
      <Typography.Paragraph type="secondary" style={{ marginTop: 12 }} role="status">{status}</Typography.Paragraph>
      <Tabs
        defaultActiveKey="non-iframe"
        items={[
          {
            key: 'non-iframe',
            label: '非iframe',
            children: (
              <div id="non-iframe-test-content">
                <Tabs
                  defaultActiveKey="drag"
                  items={[
                    { key: 'drag', label: '拖拽', children: <GeometryDragPanel /> },
                    { key: 'coordinates', label: '九宫格(坐标)', children: <GeometryCoordinatesPanel /> },
                    { key: 'page-scroll', label: '网页滚动测试', children: <GeometryPageScrollPanel /> },
                    { key: 'element-scroll', label: '元素滚动测试', children: <GeometryPageScrollPanel mode="element" /> },
                  ]}
                />
              </div>
            ),
          },
          { key: 'iframe', label: 'iframe', children: <div id="iframe-test-content" /> },
        ]}
      />
    </PageLayout>
  );
}
