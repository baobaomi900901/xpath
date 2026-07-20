import { RightOutlined, SearchOutlined } from '@ant-design/icons';
import { Card, Empty, Input, Typography } from 'antd';
import { useMemo, useState } from 'react';
import PageLayout from '../components/PageLayout';

const { Paragraph } = Typography;

const menuItems = [
  {
    id: 'menu-slow-load-30s',
    href: '/slow-load-30s.html',
    title: '30秒加载页面',
    description: '测试 load_timeout（默认 20s 超时抛 UIAError）与 stop_if_timeout 行为',
  },
  {
    id: 'menu-anchor-test',
    href: '/anchor-test',
    title: '锚点测试',
    description: '表单顺序与 input 属性每轮随机，仅 label 文字可作为锚点定位',
  },
  {
    id: 'menu-form-controls',
    href: '/form-controls',
    title: '表单控件测试',
    description: '左侧 Ant Design 表单, 右侧原生 HTML 表单, id 每次刷新随机',
  },
  {
    id: 'menu-save-dialog',
    href: '/download-dialog-test',
    title: '下载对话框测试',
    description: '触发浏览器另存为对话框，用于测试 handle_save_dialog()',
  },
  {
    id: 'menu-upload-dialog',
    href: '/upload-dialog-test',
    title: '上传对话框测试',
    description: '触发浏览器打开文件对话框，用于测试 handle_upload_dialog()',
  },
  {
    id: 'menu-web-dialog',
    href: '/web-dialog-test',
    title: '网页对话框测试',
    description: 'alert / confirm / prompt 三种原生对话框处理测试',
  },
  {
    id: 'menu-table-test',
    href: '/table-test',
    title: '表格测试',
    description: 'Ant Design Table，7 列 1000 行数据，支持分页与排序',
  },
  {
    id: 'menu-table-div-test',
    href: '/table-div-test',
    title: '表格测试(div一把梭)',
    description: '纯 div 实现，7 列 1000 行，内容与 Ant Design Table 一致',
  },
  {
    id: 'menu-iframe-nested-test',
    href: '/iframe-nested-test',
    title: 'iframe 嵌套测试',
    description: '4 层 iframe 嵌套，每层含独立锚点与可操作元素',
  },
  {
    id: 'menu-shadow-nested-test',
    href: '/shadow-nested-test',
    title: 'Shadow 嵌套测试',
    description: '左侧 Open Shadow 4 层嵌套，右侧 Closed Shadow 4 层嵌套',
  },
  {
    id: 'menu-keys-click-test',
    href: '/keys-click-test',
    title: '元素点击测试',
    description: '测试 click, hover, focus 的 keys, position 等参数',
  },
];

export default function HomePage() {
  const [search, setSearch] = useState('');

  const filteredItems = useMemo(() => {
    const keyword = search.trim().toLowerCase();
    if (!keyword) return menuItems;
    return menuItems.filter((item) => item.title.toLowerCase().includes(keyword));
  }, [search]);

  return (
    <PageLayout title="Web 靶场" subtitle="选择下方场景进入测试页面" fullWidth>
      <Input
        id="home-search"
        allowClear
        placeholder="搜索标题"
        prefix={<SearchOutlined style={{ color: '#94a3b8' }} />}
        value={search}
        onChange={(event) => setSearch(event.target.value)}
        style={{ marginBottom: 16, maxWidth: 480 }}
      />
      {filteredItems.length === 0 ? (
        <Empty description={search.trim() ? '没有匹配的测试场景' : '暂无测试场景'} />
      ) : (
        <div className="home-menu-grid">
          {filteredItems.map((item) => (
            <Card
              key={item.id}
              id={item.id}
              hoverable
              style={{ width: '100%' }}
              styles={{ body: { padding: 16 } }}
              onClick={() => window.open(item.href, '_blank', 'noopener,noreferrer')}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', gap: 16 }}>
                <div>
                  <Paragraph strong style={{ marginBottom: 4 }}>
                    {item.title}
                  </Paragraph>
                  <Paragraph type="secondary" style={{ marginBottom: 0 }}>
                    {item.description}
                  </Paragraph>
                </div>
                <RightOutlined style={{ color: '#94a3b8', marginTop: 4, flexShrink: 0 }} />
              </div>
            </Card>
          ))}
        </div>
      )}
    </PageLayout>
  );
}
