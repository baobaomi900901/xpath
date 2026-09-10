import { Tabs, Typography } from 'antd';
import { useParams } from 'react-router-dom';
import GeometryDragPanel from './GeometryDragPanel';
import GeometryCoordinatesPanel from './GeometryCoordinatesPanel';
import GeometryPageScrollPanel from './GeometryPageScrollPanel';
import GeometryElementPanel from './GeometryElementPanel';

const scenarios = [
  { key: 'drag', label: '拖拽', content: <GeometryDragPanel /> },
  { key: 'coordinates', label: '九宫格(坐标)', content: <GeometryCoordinatesPanel /> },
  { key: 'page-scroll', label: '网页滚动测试', content: <GeometryPageScrollPanel /> },
  { key: 'element-scroll', label: '元素滚动测试', content: <GeometryPageScrollPanel mode="element" /> },
  { key: 'element-geometry', label: '元素几何测试', content: <GeometryElementPanel /> },
];

export function GeometryFrameContent() {
  const { scenario } = useParams();
  const item = scenarios.find(value => value.key === scenario);
  return <div style={{ padding: 20 }}>{item?.content ?? <Typography.Text>未找到测试场景</Typography.Text>}</div>;
}

export default function GeometryIframePanel() {
  const routePrefix = import.meta.env.VITE_GITHUB_PAGES === 'true' ? '#/' : '';
  return (
    <div id="iframe-test-content">
      <Typography.Paragraph type="secondary">
        每个场景位于一层 iframe 内。网页滚动控制 iframe 文档，元素滚动控制其内部容器；
        点击位置和拖拽停止位置以 iframe 可视窗口为原点，几何属性仍相对画板。
      </Typography.Paragraph>
      <Tabs defaultActiveKey="drag" items={scenarios.map(item => ({
        key: item.key,
        label: item.label,
        children: <iframe
          id={`geometry-${item.key}-iframe`}
          title={`iframe ${item.label}`}
          src={`${import.meta.env.BASE_URL}${routePrefix}geometry-frame/${item.key}`}
          style={{ display: 'block', width: '100%', height: 720, border: '1px solid #d9d9d9', borderRadius: 8 }}
        />,
      }))} />
    </div>
  );
}
