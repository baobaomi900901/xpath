# CEF stale-process cleanup plan

User request: restart the CEF range launcher after automatically terminating old range processes. The pasted log fails copying the CEF 133 runtime while a previous 133 process remains.

## Contract

- Clean selected versions in this repository before any SDK/build work or new launch.
- Match exact canonical executable paths under `CEF/dist/<major>/`; include CEF workers using the same executable. Do not terminate by basename alone or follow unrelated descendants.
- Confirm process image using its process handle before terminating; wait for exit before building. Handle normal exit races and report permission/timeout failures without continuing to build.
- Cancel, invalid arguments and pure `--skip-build --no-launch` validation do not terminate processes.
- A normal restart closes existing windows of the selected versions. Unselected versions remain running.
- Keep Python standard-library-only and Python 3.8 syntax compatibility; keep unrelated WEBVIEW2 work intact.

## Tasks

- [x] Use subagent-driven-development to implement the independent Windows backend in `tools/cef_processes.py` and tests in `tools/test_cef_processes.py`. API: `cleanup_cef_processes(executables: list[Path], timeout: float = 10.0) -> list[int]` returns confirmed exited process IDs. The backend is Windows-only and has no import-time effects.
- [x] Parent adds cleanup dispatch and tests to `tools/start_cef.py` / `tools/test_start_cef.py`, including ordering before build/launch and cleanup-error propagation.
- [x] Reproduce locked DLL access, then verify cleanup releases it and CEF 133 rebuild succeeds. Exercise a real selected-version restart and preserve an unselected test process.
- [x] Update root README and CEF README with automatic restart scope, pure validation behavior and failure messages. Run relevant tests, review and whitespace/syntax checks.

## Evidence

- The original CEF 133 process PID 143092 locked `libcef.dll`; the new launcher cleaned it and `--version 133 --no-launch` rebuilt successfully. Build output: `CEF/.cache/cleanup-rebuild133.log`.
- Real restart initially exposed `TerminateProcess` returning WinError 5 before a worker's exit signal. Instrumentation observed the same held object exit 0.1589 seconds later. The backend now waits within the remaining overall deadline; genuine denial still errors. Four regression tests exercise the production Win32 terminate/wait seam.
- Real restart after the fix replaced 133 PID 8172 with PID 151996, including worker cleanup. Unselected 109 PID 136268 and an owned different-directory executable with the same basename PID 149864 remained alive. Pure validation preserved all three. All test-owned processes were closed afterward. Results: `CEF/.cache/cleanup-smoke/results.json`.
- 67 tests passed: 47 CEF launcher, 18 cleanup, 2 existing Java menu regression tests. The reviewer found no important blockers in the path scope, handle identity, deadlines or exit-race fix. Python 3.8 syntax and whitespace checks are performed before delivery.

No commits or remote publication are requested.
