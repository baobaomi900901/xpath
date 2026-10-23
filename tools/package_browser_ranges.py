"""Package rebuilt Windows browser ranges with CDP verification evidence."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import zipfile

ROOT = Path(__file__).resolve().parents[1]
VERSIONS = {'cef': ['109', '125', '128', '133', '154'],
            'electron': ['22', '29', '38', '44'], 'webview2': ['Release']}


def package(kind: str, version: str, output: Path, results: list[dict]) -> dict:
    source = (ROOT / 'WEBVIEW2/build/Release' if kind == 'webview2'
              else ROOT / kind.upper() / 'dist' / version)
    executable = ('webview2-shooting-range.exe' if kind == 'webview2'
                  else f'{kind}-shooting-range-{version}.exe')
    assert (source / executable).is_file(), f'Missing {source / executable}'
    evidence = [item for item in results if item['kind'] == kind and item['version'] == version]
    required = {'normal', 'port', 'split', 'duplicate', 'zero', 'pipe'}
    if kind == 'webview2':
        required |= {'environment', 'nested'}
    assert required <= {item['scenario'] for item in evidence}, f'Missing verification: {kind} {version}'
    assert all(item['passed'] for item in evidence), f'Failed verification: {kind} {version}'
    pipe_evidence = {}
    if kind in ('cef', 'electron'):
        names = ['no-cdp-pipe-results.json']
        if kind == 'electron':
            names.append('cdp-pipe-positive-results.json')
        for name in names:
            records = json.loads((ROOT / kind.upper() / 'verify/artifacts' / name).read_text(encoding='utf-8'))
            matching = [item for item in records if str(item['version']) == version]
            assert matching and all(item['passed'] for item in matching), f'Missing pipe evidence: {kind} {version}'
            pipe_evidence[name] = matching
    folder = f'{kind}-{version}-no-cdp'
    archive = output / f'{folder}-windows-x64.zip'
    files = sorted(path for path in source.rglob('*') if path.is_file()
                   and '.cache' not in path.relative_to(source).parts
                   and path.suffix.lower() not in ('.pdb', '.log'))
    with zipfile.ZipFile(archive, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=5) as bundle:
        for path in files:
            bundle.write(path, f'{folder}/{path.relative_to(source).as_posix()}')
        bundle.writestr(f'{folder}/NO-CDP-README.txt',
                        f'{kind.upper()} {version} - Windows x64\n'
                        f'Extract the entire folder, then run {executable}.\n'
                        'CDP startup flags are ignored; no remote-debugging port or pipe is enabled.\n'
                        'Do not copy only the EXE for CEF/Electron: keep DLLs and resources together.\n'
                        'WebView2 requires Microsoft Edge WebView2 Runtime and the Visual C++ Runtime.\n'
                        'Default pages require access to the project GitHub Pages website.\n'
                        'Verification covers browser-window startup, owned-process TCP listeners and CDP flags.\n'
                        'Legacy CDP DOM interaction tests are not included in this verification.\n')
        bundle.writestr(f'{folder}/no-cdp-results.json', json.dumps(evidence, ensure_ascii=False, indent=2))
        for name, records in pipe_evidence.items():
            bundle.writestr(f'{folder}/{name}', json.dumps(records, ensure_ascii=False, indent=2))
    with zipfile.ZipFile(archive) as bundle:
        assert f'{folder}/{executable}' in bundle.namelist()
        bad = bundle.testzip()
        assert bad is None, f'Corrupt ZIP member: {bad}'
    digest = hashlib.sha256()
    with archive.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(chunk)
    return {'kind': kind, 'version': version, 'file': archive.name, 'bytes': archive.stat().st_size,
            'sha256': digest.hexdigest(), 'runtime_files': len(files), 'checks': len(evidence)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=ROOT / 'artifacts/no-cdp-2026-10-23')
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    results = []
    for kind in VERSIONS:
        results.extend(json.loads((ROOT / kind.upper() / 'verify/artifacts/no-cdp-results.json').read_text(encoding='utf-8')))
    manifest = []
    for kind, versions in VERSIONS.items():
        for version in versions:
            item = package(kind, version, args.output, results)
            manifest.append(item)
            print(json.dumps(item), flush=True)
            (args.output / 'manifest.json').write_text(json.dumps(manifest, indent=2), encoding='utf-8')
    (args.output / 'SHA256SUMS.txt').write_text(''.join(f"{item['sha256']}  {item['file']}\n" for item in manifest), encoding='utf-8')
    (args.output / 'no-cdp-results.json').write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding='utf-8')
    (args.output / 'README.txt').write_text(
        'Windows x64 browser ranges - CDP disabled - 2026-10-23\n\n'
        'CEF: 109, 125, 128, 133, 154. Electron: 22, 29, 38, 44. WebView2: Release.\n'
        'Extract each complete ZIP and run the EXE inside. Keep runtime files together.\n'
        'WebView2 requires Microsoft Edge WebView2 Runtime and Visual C++ Runtime.\n'
        'Default pages require access to the project GitHub Pages website.\n\n'
        '62 real-window startup checks passed, including CDP port/pipe flags.\n'
        'WebView2 also passed injected environment and nested command-line checks.\n'
        'Supplemental CRT pipe probes: 9 passed; 4 unmodified Electron controls responded.\n'
        'CEF has no matching unmodified pipe control; its pipe silence is supplemental evidence.\n'
        'The checks do not cover full page interaction or UIA regression.\n'
        'See per-package JSON evidence, manifest.json and SHA256SUMS.txt.\n', encoding='utf-8')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
