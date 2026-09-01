import { useLayoutEffect, useRef, useState } from 'react';
import { Alert, Typography } from 'antd';
import PageLayout from '../components/PageLayout';
import { ensureShadowNestedElements, isShadowMounted, mountShadowRoot } from '../utils/shadowNested';

export default function ShadowNestedTestPage() {
  const openHostRef = useRef<HTMLDivElement>(null);
  const closedHostRef = useRef<HTMLDivElement>(null);
  const [mounted, setMounted] = useState({ open: false, closed: false });

  useLayoutEffect(() => {
    ensureShadowNestedElements();
    mountShadowRoot(openHostRef.current!, 'open-nested-l1', 'open-shadow-root');
    mountShadowRoot(closedHostRef.current!, 'closed-nested-l1', 'closed-shadow-root');

    requestAnimationFrame(() => {
      setMounted({
        open: isShadowMounted('open-shadow-root'),
        closed: isShadowMounted('closed-shadow-root'),
      });
    });
  }, []);

  return (
    <PageLayout
      title="Shadow 嵌套测试"
      subtitle="左侧 Open Shadow 4 层嵌套，右侧 Closed Shadow 4 层嵌套"
      maxWidth={1400}
      inset={24}
    >
      <Alert
        type="info"
        showIcon
        style={{ marginBottom: 16 }}
        message="每层 Shadow 内包含 marker、输入框、按钮；最内层（第 4 层）可提交输入结果"
        description={
          <>
            Open Shadow：DevTools 中可展开 <code>#shadow-root (open)</code> 查看节点。
            Closed Shadow：页面<strong>可见</strong>，但 DevTools 无法展开 shadow 树（这是 Closed 模式的特性，并非页面空白）。
          </>
        }
      />

      <div
        style={{
          display: 'grid',
          gridTemplateColumns: '1fr 1fr',
          gap: 20,
          alignItems: 'start',
        }}
      >
        <section id="open-shadow-section">
          <Typography.Title level={5} style={{ marginTop: 0 }}>
            Open Shadow 嵌套（4 层）
          </Typography.Title>
          <Typography.Paragraph type="secondary">
            元素前缀：<code>open-nested-l1</code> → <code>l4</code>
            {mounted.open ? ' · 已渲染' : ' · 渲染中…'}
          </Typography.Paragraph>
          <div
            ref={openHostRef}
            style={{
              minHeight: 520,
              padding: 12,
              background: '#eff6ff',
              border: '1px solid #bfdbfe',
              borderRadius: 8,
            }}
          />
        </section>

        <section id="closed-shadow-section">
          <Typography.Title level={5} style={{ marginTop: 0 }}>
            Closed Shadow 嵌套（4 层）
          </Typography.Title>
          <Typography.Paragraph type="secondary">
            元素前缀：<code>closed-nested-l1</code> → <code>l4</code>
            {mounted.closed ? ' · 已渲染' : ' · 渲染中…'}
          </Typography.Paragraph>
          <Typography.Paragraph type="warning" style={{ fontSize: 13 }}>
            若 F12 Elements 里看不到节点，属于 Closed Shadow 正常表现；请直接在本页紫色区域内操作控件。
          </Typography.Paragraph>
          <div
            ref={closedHostRef}
            style={{
              minHeight: 520,
              padding: 12,
              background: '#f5f3ff',
              border: '1px solid #ddd6fe',
              borderRadius: 8,
            }}
          />
        </section>
      </div>
    </PageLayout>
  );
}
