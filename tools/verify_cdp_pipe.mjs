// Windows CDP pipe acceptance using Chromium's inherited CRT descriptors 3 and 4.
// Run a matching cached Electron positive control before trusting a silent probe.
import { spawn, spawnSync } from 'node:child_process';
import { existsSync, mkdirSync, mkdtempSync, rmSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { setTimeout as delay } from 'node:timers/promises';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const supported = { electron: ['22', '29', '38', '44'], cef: ['109', '125', '128', '133', '154'] };

function parseArgs(argv) {
  const options = { kind: 'electron', versions: null, positiveControl: false, timeoutMs: 6000, output: null };
  for (let index = 0; index < argv.length; index++) {
    const argument = argv[index];
    if (argument === '--positive-control') options.positiveControl = true;
    else if (argument === '--kind') options.kind = argv[++index];
    else if (argument === '--output') options.output = argv[++index];
    else if (argument === '--timeout-ms') options.timeoutMs = Number(argv[++index]);
    else if (argument === '--versions') {
      options.versions = [];
      while (argv[index + 1] && !argv[index + 1].startsWith('--')) options.versions.push(argv[++index]);
    } else if (argument === '--help') {
      console.log('Usage: node tools/verify_cdp_pipe.mjs [--kind electron|cef] [--versions 22 44]');
      console.log('       [--positive-control] [--timeout-ms 6000] [--output results.json]');
      console.log('Positive control runs an untouched cached Electron runtime with a temporary blank app.');
      console.log('No-response results only establish CDP removal when a matching runtime control responds.');
      return null;
    } else throw new Error(`Unknown argument: ${argument}`);
  }
  if (!Object.hasOwn(supported, options.kind)) throw new Error(`Unknown kind: ${options.kind}`);
  if (options.positiveControl && options.kind !== 'electron') throw new Error('Positive controls require --kind electron');
  if (!Number.isInteger(options.timeoutMs) || options.timeoutMs < 1000 || options.timeoutMs > 60000) {
    throw new Error('--timeout-ms must be between 1000 and 60000');
  }
  options.versions ??= supported[options.kind];
  if (!options.versions.length || options.versions.some(version => !supported[options.kind].includes(version))) {
    throw new Error(`Unsupported ${options.kind} versions: ${options.versions.join(', ')}`);
  }
  return options;
}

function makeControlApp(directory) {
  const script = path.join(directory, 'main.cjs');
  writeFileSync(script, `const { app, BrowserWindow } = require('electron');
const path = require('node:path');
app.setPath('userData', path.join(__dirname, 'profile'));
let window;
app.whenReady().then(() => {
  window = new BrowserWindow({ width: 480, height: 300, title: 'CDP pipe positive control' });
  window.loadURL('data:text/html,<title>CDP pipe positive control</title><p>Pipe probe</p>');
});
app.on('window-all-closed', () => app.quit());
`, 'utf8');
  return script;
}

async function verify(options, version) {
  const executable = options.positiveControl
    ? path.join(root, 'ELECTRON', '.cache', 'runtimes', version, 'electron.exe')
    : path.join(root, options.kind.toUpperCase(), 'dist', version, `${options.kind}-shooting-range-${version}.exe`);
  if (!existsSync(executable)) throw new Error(`Missing executable: ${executable}`);
  const temporary = mkdtempSync(path.join(tmpdir(), 'xpath-cdp-pipe-'));
  const args = ['--remote-debugging-pipe'];
  if (options.positiveControl) args.unshift(makeControlApp(temporary));
  const environment = { ...process.env };
  delete environment.ELECTRON_RUN_AS_NODE;
  delete environment.NODE_OPTIONS;
  const processStartedAt = Date.now();
  const child = spawn(executable, args, {
    cwd: path.dirname(executable), env: environment,
    stdio: ['ignore', 'ignore', 'ignore', 'pipe', 'pipe'],
  });
  let childError = null;
  let pipeError = null;
  let responseBytes = 0;
  let pending = '';
  let versionResponse = null;
  child.on('error', error => { childError = error; });
  child.stdio[3].on('error', error => { pipeError = error.code ?? error.message; });
  child.stdio[4].on('error', error => { pipeError = error.code ?? error.message; });
  child.stdio[4].on('data', chunk => {
    responseBytes += chunk.length;
    pending += chunk.toString('utf8');
    let boundary;
    while ((boundary = pending.indexOf('\0')) >= 0) {
      const frame = pending.slice(0, boundary);
      pending = pending.slice(boundary + 1);
      try {
        const message = JSON.parse(frame);
        if (message.id === 1 && typeof message.result?.product === 'string') versionResponse = message;
      } catch { /* Raw output is still recorded and fails a negative probe. */ }
    }
  });
  let nextRequest = 0;
  try {
    while (Date.now() - processStartedAt < options.timeoutMs) {
      if (childError) throw childError;
      if (child.exitCode !== null || child.signalCode !== null) {
        throw new Error(`Main process exited before probe completed: ${child.exitCode ?? child.signalCode}`);
      }
      if (!options.positiveControl && responseBytes) throw new Error(`CDP pipe returned ${responseBytes} bytes`);
      if (options.positiveControl && versionResponse) {
        return { kind: options.kind, version, positiveControl: true, passed: true,
          pid: child.pid, elapsedMs: Date.now() - processStartedAt, response: versionResponse.result };
      }
      if (Date.now() >= nextRequest && !child.stdio[3].destroyed) {
        child.stdio[3].write(JSON.stringify({ id: 1, method: 'Browser.getVersion' }) + '\0');
        nextRequest = Date.now() + 500;
      }
      await delay(50);
    }
    if (childError) throw childError;
    if (child.exitCode !== null || child.signalCode !== null) throw new Error('Main process exited during probe');
    if (options.positiveControl) throw new Error(`Positive control did not answer Browser.getVersion (${responseBytes} bytes; pipe error: ${pipeError ?? 'none'})`);
    if (responseBytes) throw new Error(`CDP pipe returned ${responseBytes} bytes`);
    return { kind: options.kind, version, positiveControl: false, passed: true,
      pid: child.pid, elapsedMs: Date.now() - processStartedAt, responseBytes, pipeError,
      limitation: 'Silence is conclusive only with a responding control for this runtime and transport.' };
  } finally {
    child.stdio[3].destroy();
    child.stdio[4].destroy();
    if (child.pid && child.exitCode === null && child.signalCode === null) {
      spawnSync('taskkill.exe', ['/PID', String(child.pid), '/T', '/F'], { stdio: 'ignore', windowsHide: true });
    }
    // Only remove the fresh temporary directory this invocation created.
    const resolved = path.resolve(temporary);
    if (path.dirname(resolved) === path.resolve(tmpdir()) && path.basename(resolved).startsWith('xpath-cdp-pipe-')) {
      rmSync(resolved, { recursive: true, force: true, maxRetries: 10, retryDelay: 100 });
    }
  }
}

async function main() {
  const options = parseArgs(process.argv.slice(2));
  if (!options) return;
  if (process.platform !== 'win32') throw new Error('This verifier requires Windows');
  const results = [];
  for (const version of options.versions) {
    let result;
    try { result = await verify(options, version); }
    catch (error) { result = { kind: options.kind, version, positiveControl: options.positiveControl, passed: false, error: error.message }; }
    results.push(result);
    console.log(JSON.stringify(result));
    if (options.output) {
      const output = path.resolve(options.output);
      mkdirSync(path.dirname(output), { recursive: true });
      writeFileSync(output, JSON.stringify(results, null, 2) + '\n', 'utf8');
    }
  }
  process.exitCode = Number(results.some(result => !result.passed));
}

main().catch(error => { console.error(error.message); process.exitCode = 1; });
