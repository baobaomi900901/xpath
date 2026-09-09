import { useLayoutEffect, useRef, useState } from 'react';
import { createPortal } from 'react-dom';
import { StyleProvider } from '@ant-design/cssinjs';
import { ConfigProvider } from 'antd';
import PageLayout from '../components/PageLayout';
import FormControlsPage from './FormControlsPage';

export function ShadowFormContent() {
  const hostRef = useRef<HTMLDivElement>(null);
  const [shadowRoot, setShadowRoot] = useState<ShadowRoot | null>(null);

  useLayoutEffect(() => {
    const host = hostRef.current!;
    setShadowRoot(host.shadowRoot ?? host.attachShadow({ mode: 'open' }));
  }, []);

  return (
    <div id="form-shadow-host" ref={hostRef}>
      {shadowRoot && createPortal(
        <StyleProvider container={shadowRoot}>
          <div id="shadow-form-content">
            <ConfigProvider getPopupContainer={() => shadowRoot.getElementById('shadow-form-content') as HTMLElement}>
              <FormControlsPage />
            </ConfigProvider>
          </div>
        </StyleProvider>,
        shadowRoot,
      )}
    </div>
  );
}

export default function IframeShadowFormPage() {
  const routePrefix = import.meta.env.VITE_GITHUB_PAGES === 'true' ? '#/' : '';
  const src = `${import.meta.env.BASE_URL}${routePrefix}iframe-shadow-form-content`;

  return (
    <PageLayout
      title="iframe + Shadow 表单测试"
      subtitle="嵌套结构：iframe → Open Shadow DOM → Ant Design / 原生 HTML 表单。动态 ID 开关与原表单页共享浏览器设置。"
      fullWidth
      inset={24}
    >
      <iframe
        id="iframe-shadow-form"
        title="iframe 内的 Shadow 表单"
        src={src}
        style={{ width: '100%', height: '80vh', minHeight: 600, border: '1px solid #d9d9d9', borderRadius: 8 }}
      />
    </PageLayout>
  );
}
