// Compatibility entry point: distributed builds no longer expose CDP.
import { spawnSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';
const versions = process.argv.slice(2);
const result = spawnSync(process.env.PYTHON || 'python', [
  fileURLToPath(new URL('../../tools/verify_no_cdp.py', import.meta.url)),
  '--kind', 'electron', '--output',
  fileURLToPath(new URL('./artifacts/no-cdp-results.json', import.meta.url)),
  ...(versions.length ? ['--versions', ...versions] : []),
], { stdio: 'inherit' });
if (result.error) throw result.error;
process.exitCode = result.status ?? 1;
