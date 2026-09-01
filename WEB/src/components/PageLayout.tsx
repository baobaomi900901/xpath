import { Card, Typography } from 'antd';
import { useEffect, type ReactNode } from 'react';

const { Title, Paragraph } = Typography;

type PageLayoutProps = {
  title: string;
  subtitle?: string;
  children: ReactNode;
  extra?: ReactNode;
  maxWidth?: number;
  inset?: number;
  fullWidth?: boolean;
};

export default function PageLayout({
  title,
  subtitle,
  children,
  extra,
  maxWidth = 860,
  inset = 24,
  fullWidth = false,
}: PageLayoutProps) {
  useEffect(() => {
    document.title = title;
  }, [title]);

  return (
    <div style={{ padding: inset, minHeight: '100vh', boxSizing: 'border-box' }}>
      <div
        style={{
          width: '100%',
          maxWidth: fullWidth ? undefined : maxWidth,
          margin: fullWidth ? 0 : '0 auto',
        }}
      >
        <Card>
          <Title level={3} style={{ marginTop: 0 }}>
            {title}
          </Title>
          {subtitle ? (
            <Paragraph type="secondary" style={{ marginBottom: extra ? 12 : 24 }}>
              {subtitle}
            </Paragraph>
          ) : null}
          {extra}
          {children}
        </Card>
      </div>
    </div>
  );
}
