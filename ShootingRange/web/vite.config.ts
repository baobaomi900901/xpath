import fs from 'node:fs';
import path from 'node:path';
import { defineConfig, type Plugin } from 'vite';
import react from '@vitejs/plugin-react';

const TARGET_LOGICAL_ID = 'uipilot-sdk-web-cookie-target-v1';
const ALLOWED_HOSTS = new Set(['sdk-web.test', 'sub.sdk-web.test']);
const DEFAULT_RANGE_PORT = 7199;

type CookieAllowlist = {
  execution_id: string;
  cookie_name_prefix: string;
  allowed_cookie_names: string[];
};

type TargetSettings = {
  scheme: 'http' | 'https';
  port: number;
  executionId: string;
  observationToken: string;
  allowlist: CookieAllowlist;
  rawEvidenceDir: string | null;
  captureRawHeader: boolean;
  https?: { pfx: Buffer; passphrase: string };
};

function requiredEnv(name: string): string {
  const value = process.env[name]?.trim();
  if (!value) throw new Error(`${name} is required when serving the SDK Web target`);
  return value;
}

function absoluteFileFromEnv(name: string): string {
  const value = requiredEnv(name);
  if (!path.isAbsolute(value) || !fs.statSync(value).isFile()) {
    throw new Error(`${name} must reference an existing absolute file`);
  }
  return value;
}

function absoluteDirectoryFromEnv(name: string): string {
  const value = requiredEnv(name);
  if (!path.isAbsolute(value) || !fs.statSync(value).isDirectory()) {
    throw new Error(`${name} must reference an existing absolute directory`);
  }
  return value;
}

function readSecretFile(envName: string): string {
  const value = fs.readFileSync(absoluteFileFromEnv(envName), 'utf8').trim();
  if (!value) throw new Error(`${envName} must not be empty`);
  return value;
}

function loadAllowlist(filePath: string, executionId: string): CookieAllowlist {
  const value = JSON.parse(fs.readFileSync(filePath, 'utf8')) as Partial<CookieAllowlist>;
  if (value.execution_id !== executionId) throw new Error('Cookie allowlist execution_id mismatch');
  if (typeof value.cookie_name_prefix !== 'string' || !value.cookie_name_prefix) {
    throw new Error('Cookie allowlist cookie_name_prefix is required');
  }
  if (!Array.isArray(value.allowed_cookie_names) || value.allowed_cookie_names.some((name) => typeof name !== 'string')) {
    throw new Error('Cookie allowlist allowed_cookie_names must be a string array');
  }
  if (value.allowed_cookie_names.some((name) => !name.startsWith(value.cookie_name_prefix!))) {
    throw new Error('Every allowed Cookie name must use the execution prefix');
  }
  return {
    execution_id: value.execution_id,
    cookie_name_prefix: value.cookie_name_prefix,
    allowed_cookie_names: [...new Set(value.allowed_cookie_names)].sort(),
  };
}

function loadSettings(): TargetSettings {
  const scheme = requiredEnv('UIPILOT_SDK_WEB_TARGET_SCHEME');
  if (scheme !== 'http' && scheme !== 'https') throw new Error('Target scheme must be http or https');
  const port = Number(requiredEnv('UIPILOT_SDK_WEB_TARGET_PORT'));
  if (!Number.isInteger(port) || port < 1 || port > 65535) throw new Error('Target port is invalid');
  const executionId = requiredEnv('UIPILOT_SDK_WEB_EXECUTION_ID');
  const observationToken = readSecretFile('UIPILOT_SDK_WEB_OBSERVATION_TOKEN_FILE');
  const allowlist = loadAllowlist(
    absoluteFileFromEnv('UIPILOT_SDK_WEB_COOKIE_ALLOWLIST_FILE'),
    executionId,
  );
  const mode = process.env.UIPILOT_SDK_WEB_MODE?.trim() ?? 'verify-only';
  const captureRawHeader = mode === 'diagnose' && process.env.UIPILOT_SDK_WEB_CAPTURE_RAW_COOKIE_HEADER === 'true';
  const rawEvidenceDir = captureRawHeader
    ? absoluteDirectoryFromEnv('UIPILOT_SDK_WEB_RAW_EVIDENCE_DIR')
    : null;
  if (scheme === 'http') {
    return { scheme, port, executionId, observationToken, allowlist, rawEvidenceDir, captureRawHeader };
  }
  return {
    scheme,
    port,
    executionId,
    observationToken,
    allowlist,
    rawEvidenceDir,
    captureRawHeader,
    https: {
      pfx: fs.readFileSync(absoluteFileFromEnv('UIPILOT_SDK_WEB_PFX_FILE')),
      passphrase: readSecretFile('UIPILOT_SDK_WEB_PFX_PASSWORD_FILE'),
    },
  };
}

function parseCookies(header: string): Map<string, string> {
  const cookies = new Map<string, string>();
  for (const part of header.split(';')) {
    const separator = part.indexOf('=');
    if (separator <= 0) continue;
    cookies.set(part.slice(0, separator).trim(), part.slice(separator + 1).trim());
  }
  return cookies;
}

function safeIdentifier(value: string): boolean {
  return /^[A-Za-z0-9._-]{1,128}$/.test(value);
}

function targetPlugin(settings: TargetSettings): Plugin {
  return {
    name: 'uipilot-sdk-web-cookie-target',
    configureServer(server) {
      server.middlewares.use((request, response, next) => {
        const requestUrl = new URL(request.url ?? '/', `${settings.scheme}://sdk-web.test:${settings.port}`);
        if (requestUrl.pathname === '/api/sdk-web/health' && request.method === 'GET') {
          const marker = requestUrl.searchParams.get('uipilot_execution');
          response.setHeader('content-type', 'application/json; charset=utf-8');
          response.end(JSON.stringify({
            logical_id: TARGET_LOGICAL_ID,
            ready: marker === settings.executionId,
            execution_id: marker,
            scheme: settings.scheme,
            port: settings.port,
          }));
          return;
        }
        if (!requestUrl.pathname.endsWith('/api/sdk-web/cookie-observation')) {
          next();
          return;
        }
        if (request.method !== 'POST') {
          response.statusCode = 405;
          response.end();
          return;
        }
        const executionId = String(request.headers['x-uipilot-execution-id'] ?? '');
        const scenarioId = String(request.headers['x-uipilot-scenario-id'] ?? '');
        const token = String(request.headers['x-uipilot-observation-token'] ?? '');
        if (
          executionId !== settings.executionId ||
          executionId !== settings.allowlist.execution_id ||
          token !== settings.observationToken ||
          !safeIdentifier(scenarioId)
        ) {
          response.statusCode = 403;
          response.end();
          return;
        }
        const hostHeader = String(request.headers.host ?? '');
        const host = hostHeader.replace(/^\[|\]$/g, '').split(':')[0].toLowerCase();
        if (!ALLOWED_HOSTS.has(host)) {
          response.statusCode = 400;
          response.end();
          return;
        }
        const rawCookieHeader = String(request.headers.cookie ?? '');
        const parsedCookies = parseCookies(rawCookieHeader);
        const filteredCookies = Object.fromEntries(
          settings.allowlist.allowed_cookie_names
            .filter((name) => name.startsWith(settings.allowlist.cookie_name_prefix))
            .filter((name) => parsedCookies.has(name))
            .map((name) => [name, parsedCookies.get(name)!]),
        );
        if (settings.captureRawHeader && settings.rawEvidenceDir) {
          const evidencePath = path.join(settings.rawEvidenceDir, `cookie-header-${executionId}-${scenarioId}.txt`);
          fs.writeFileSync(evidencePath, rawCookieHeader, { encoding: 'utf8', mode: 0o600, flag: 'wx' });
        }
        response.setHeader('content-type', 'application/json; charset=utf-8');
        response.setHeader('cache-control', 'no-store');
        response.end(JSON.stringify({
          executionId,
          scenarioId,
          actual: {
            cookies: filteredCookies,
            scheme: request.socket.encrypted ? 'https' : 'http',
            host,
            port: settings.port,
            path: requestUrl.pathname,
          },
        }));
      });
    },
  };
}

function samplesAttachmentPlugin(): Plugin {
  return {
    name: 'samples-attachment',
    configureServer(server) {
      server.middlewares.use((request, response, next) => {
        const pathname = (request.url ?? '').split('?')[0];
        if (!pathname.startsWith('/samples/')) {
          next();
          return;
        }
        const originalWriteHead = response.writeHead.bind(response);
        response.writeHead = ((...args: Parameters<typeof response.writeHead>) => {
          const filename = path.basename(pathname);
          response.setHeader('Content-Disposition', `attachment; filename="${filename}"`);
          response.setHeader('Content-Type', 'application/octet-stream');
          return originalWriteHead(...args);
        }) as typeof response.writeHead;
        next();
      });
    },
  };
}

function isSdkWebTargetMode() {
  return Boolean(process.env.UIPILOT_SDK_WEB_TARGET_SCHEME?.trim());
}

export default defineConfig(({ command }) => {
  if (command !== 'serve') return { plugins: [react()] };

  // 普通靶场模式: pnpm dev 直接可用, 无需 SDK 环境变量
  if (!isSdkWebTargetMode()) {
    return {
      plugins: [react(), samplesAttachmentPlugin()],
      server: {
        host: true,
        port: DEFAULT_RANGE_PORT,
        open: true,
      },
    };
  }

  // SDK Cookie 靶场模式: 设置 UIPILOT_SDK_WEB_* 环境变量后启用
  const settings = loadSettings();
  return {
    plugins: [react(), targetPlugin(settings), samplesAttachmentPlugin()],
    server: {
      host: '127.0.0.1',
      port: settings.port,
      strictPort: true,
      open: false,
      allowedHosts: [...ALLOWED_HOSTS],
      https: settings.https,
    },
  };
});
