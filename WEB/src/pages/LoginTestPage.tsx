import { useState, type FormEvent } from 'react';
import { Button, Input, Modal, Tabs } from 'antd';
import PageLayout from '../components/PageLayout';
import BankTransferPage from './BankTransferPage';

type LoginMode = 'account' | 'phone';

type LoginFormProps = {
  mode: LoginMode;
  onSuccess: () => void;
};

function LoginForm({ mode, onSuccess }: LoginFormProps) {
  const [identity, setIdentity] = useState('');
  const [secret, setSecret] = useState('');
  const [codeSent, setCodeSent] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const isPhone = mode === 'phone';
  const identityLabel = isPhone ? '手机号' : '账号';
  const secretLabel = isPhone ? '验证码' : '密码';
  const identityId = isPhone ? 'login-phone' : 'login-account';
  const secretId = isPhone ? 'login-code' : 'login-password';
  const submitDisabled = isPhone ? !codeSent : identity.length === 0 || secret.length === 0;

  const handleSubmit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (submitDisabled) return;
    if (identity !== (isPhone ? '13922832244' : 'admin')) {
      setError(`${identityLabel}错误`);
      return;
    }
    if (secret !== (isPhone ? '1990' : '1')) {
      setError(`${secretLabel}错误`);
      return;
    }
    onSuccess();
  };

  const handleSendCode = () => {
    if (identity !== '13922832244') {
      setError('手机号错误');
      return;
    }
    setCodeSent(true);
  };

  return (
    <>
      <form id="login-form" noValidate onSubmit={handleSubmit}>
        <div style={{ marginBottom: 24 }}>
          <label htmlFor={identityId} style={{ display: 'block', marginBottom: 8, fontWeight: 500 }}>
            {identityLabel}
          </label>
          <Input
            id={identityId}
            name={isPhone ? 'phone' : 'account'}
            type={isPhone ? 'tel' : 'text'}
            autoComplete={isPhone ? 'tel' : 'username'}
            placeholder={`请输入${identityLabel}`}
            size="large"
            required
            value={identity}
            onChange={event => {
              setIdentity(event.target.value);
              if (isPhone) {
                setCodeSent(false);
                setSecret('');
              }
            }}
          />
        </div>
        <div style={{ marginBottom: 24 }}>
          <label htmlFor={secretId} style={{ display: 'block', marginBottom: 8, fontWeight: 500 }}>
            {secretLabel}
          </label>
          {isPhone ? (
            <div style={{ display: 'flex', gap: 8 }}>
              <Input
                id={secretId}
                name="code"
                inputMode="numeric"
                autoComplete="one-time-code"
                placeholder="请输入验证码"
                size="large"
                required
                disabled={!codeSent}
                value={secret}
                onChange={event => setSecret(event.target.value)}
                style={{ flex: 1, minWidth: 0 }}
              />
              <Button
                id="login-send-code"
                htmlType="button"
                size="large"
                onClick={handleSendCode}
                style={{ flexShrink: 0 }}
              >
                发送验证码
              </Button>
            </div>
          ) : (
            <Input.Password
              id={secretId}
              name="password"
              autoComplete="current-password"
              placeholder="请输入密码"
              size="large"
              required
              value={secret}
              onChange={event => setSecret(event.target.value)}
            />
          )}
        </div>
        <Button id="login-submit" type="primary" htmlType="submit" size="large" block disabled={submitDisabled}>
          登录
        </Button>
      </form>
      <Modal
        title="登录失败"
        open={error !== null}
        centered
        maskClosable={false}
        onCancel={() => setError(null)}
        footer={
          <Button id="login-error-ok" type="primary" onClick={() => setError(null)}>
            确定
          </Button>
        }
      >
        <p id="login-error-message" role="alert">{error}</p>
      </Modal>
    </>
  );
}

export default function LoginTestPage() {
  const [mode, setMode] = useState<LoginMode>('account');
  const [session, setSession] = useState<LoginMode | null>(null);

  if (session) {
    return (
      <BankTransferPage
        identity={session === 'account' ? 'admin' : '13922832244'}
        loginMethod={session === 'account' ? '账号登录' : '手机验证码登录'}
        onLogout={() => setSession(null)}
      />
    );
  }

  return (
    <PageLayout title="登录测试" subtitle="选择登录方式，填写信息后登录" maxWidth={520}>
      <Tabs
        id="login-tabs"
        activeKey={mode}
        onChange={key => setMode(key === 'phone' ? 'phone' : 'account')}
        items={[
          {
            key: 'account',
            label: '账号登录',
            children: mode === 'account' ? <LoginForm mode="account" onSuccess={() => setSession('account')} /> : null,
          },
          {
            key: 'phone',
            label: '手机验证码登录',
            children: mode === 'phone' ? <LoginForm mode="phone" onSuccess={() => setSession('phone')} /> : null,
          },
        ]}
      />
    </PageLayout>
  );
}
