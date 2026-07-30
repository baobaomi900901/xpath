import { Alert, Card, Descriptions, Space, Typography } from 'antd';
import { useEffect, useMemo, useState } from 'react';
import PageLayout from '../components/PageLayout';

const { Paragraph, Text } = Typography;
const OBSERVATION_SUFFIX = '/api/sdk-web/cookie-observation';
const ALLOWED_OBSERVATION_PATHS = new Set([
  OBSERVATION_SUFFIX,
  `/cookie-test${OBSERVATION_SUFFIX}`,
  `/cookie-test/scoped${OBSERVATION_SUFFIX}`,
  `/outside${OBSERVATION_SUFFIX}`,
]);

type CookieActual = {
  executionId: string;
  scenarioId: string;
  actual: {
    cookies: Record<string, string>;
    scheme: string;
    host: string;
    port: number;
    path: string;
  };
};

type PageObservation = CookieActual & {
  documentCookie: Record<string, string>;
};

declare global {
  interface Window {
    __UIPILOT_COOKIE_OBSERVATION__?: PageObservation;
  }
}

function filteredDocumentCookie(names: string[]): Record<string, string> {
  const allowed = new Set(names);
  return Object.fromEntries(
    document.cookie
      .split(';')
      .map((part) => part.trim())
      .filter(Boolean)
      .map((part) => {
        const separator = part.indexOf('=');
        return separator > 0 ? [part.slice(0, separator), part.slice(separator + 1)] : ['', ''];
      })
      .filter(([name]) => allowed.has(name)),
  );
}

export default function CookieTestPage() {
  const inputs = useMemo(() => {
    const params = new URLSearchParams(window.location.search);
    const observationPath = params.get('observation_path') ?? OBSERVATION_SUFFIX;
    return {
      executionId: params.get('uipilot_execution') ?? '',
      scenarioId: params.get('uipilot_scenario') ?? 'readiness',
      observationToken: params.get('uipilot_observation_token') ?? '',
      observationPath: ALLOWED_OBSERVATION_PATHS.has(observationPath)
        ? observationPath
        : OBSERVATION_SUFFIX,
    };
  }, []);
  const [observation, setObservation] = useState<PageObservation | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    document.title = `UiPilot SDK Web Test [${inputs.executionId}]`;
    const sanitizedUrl = new URL(window.location.href);
    sanitizedUrl.searchParams.delete('uipilot_observation_token');
    window.history.replaceState(null, '', `${sanitizedUrl.pathname}${sanitizedUrl.search}${sanitizedUrl.hash}`);

    if (!inputs.executionId || !inputs.observationToken) {
      setError('等待 runner 提供 execution marker 与 observation token。');
      return;
    }

    const controller = new AbortController();
    fetch(inputs.observationPath, {
      method: 'POST',
      credentials: 'include',
      cache: 'no-store',
      headers: {
        'x-uipilot-execution-id': inputs.executionId,
        'x-uipilot-scenario-id': inputs.scenarioId,
        'x-uipilot-observation-token': inputs.observationToken,
      },
      signal: controller.signal,
    })
      .then(async (response) => {
        if (!response.ok) throw new Error(`observation request failed: ${response.status}`);
        return response.json() as Promise<CookieActual>;
      })
      .then((actual) => {
        const result: PageObservation = {
          ...actual,
          documentCookie: filteredDocumentCookie(Object.keys(actual.actual.cookies)),
        };
        window.__UIPILOT_COOKIE_OBSERVATION__ = result;
        setObservation(result);
      })
      .catch((reason: unknown) => {
        if (!controller.signal.aborted) {
          setError(reason instanceof Error ? reason.message : String(reason));
        }
      });
    return () => controller.abort();
  }, [inputs]);

  return (
    <PageLayout
      title="SDK Web Cookie 实际观测"
      subtitle={`execution: ${inputs.executionId || 'missing'} / scenario: ${inputs.scenarioId}`}
      fullWidth
    >
      <Space direction="vertical" size={16} style={{ width: '100%' }}>
        {error ? <Alert type="warning" showIcon message={error} /> : null}
        <Descriptions bordered size="small" column={2}>
          <Descriptions.Item label="Execution marker">{inputs.executionId || 'missing'}</Descriptions.Item>
          <Descriptions.Item label="Scenario">{inputs.scenarioId}</Descriptions.Item>
          <Descriptions.Item label="Observation path">{inputs.observationPath}</Descriptions.Item>
          <Descriptions.Item label="Page title">{document.title}</Descriptions.Item>
        </Descriptions>
        <Card title="Filtered server actual" id="cookie-server-actual">
          <Paragraph code copyable>{JSON.stringify(observation?.actual ?? null, null, 2)}</Paragraph>
        </Card>
        <Card title="Filtered document.cookie" id="cookie-document-actual">
          <Paragraph code copyable>{JSON.stringify(observation?.documentCookie ?? {}, null, 2)}</Paragraph>
        </Card>
        <Text type="secondary">本页面只展示实际观测，不计算测试预期或通过结论。</Text>
      </Space>
    </PageLayout>
  );
}
