# PowerBuilder Range Implementation Plan

**Goal:** Deliver a real PowerBuilder desktop range with the Win32 form, employee pagination, drag page, menus and one-command launcher.

**Architecture:** Exported PowerScript objects are imported into a generated PBL using the installed OrcaScript 2025 GA compiler. Build output contains the EXE, PBD, matching Runtime XML and accessibility configuration. Source objects remain text and generated files stay under `POWERBUILDER/build`.

**Constraints:** Windows 10/11; PB Runtime 25.0.0.3683; x86 Pcode; no OCR; no database; Python launcher uses only the standard library; no automatic termination of existing range windows; no commits or pushes.

## Tasks

- [x] Verify the installed native OrcaScript compiler with a minimal session before creating application objects.
- [x] Add launcher tests for missing dependencies, Runtime version mismatch, build failure propagation, and skip-build behavior; run and confirm the missing implementation fails.
- [x] Implement `tools/start_powerbuilder.py`: discover explicit/env/registry tools and Runtime, copy exported objects into an isolated build folder, emit PBT/PBG/Orca scripts, compile, write Runtime XML and `pb.ini`, and optionally launch.
- [x] Add `POWERBUILDER/src/pb_range.sra`, `w_main.srw`, `u_form.sru`, `u_table.sru`, `u_drag.sru`, `m_main.srm`, and `m_actions.srm`. Use real PB controls and DataWindow; use deterministic employee rows and five numeric page buttons.
- [x] Compile with the installed OrcaScript tool, inspect every diagnostic, and repair source errors until the real compiler succeeds.
- [x] Include an explicit `--self-test` application mode exercising PB pagination/data rules and control defaults without leaving a manual-testing window open; verify the output and exit status using the actual executable.
- [x] Run launcher unit tests and the real compiler/self-test. Document what was actually verified and leave full desktop interaction to the user.
- [x] Add `POWERBUILDER/README.md`, scoped ignores and root README launcher instructions, and report the exact launch command.

## Verification commands

```powershell
python -m unittest tools.test_start_powerbuilder -v
python .\tools\start_powerbuilder.py --no-launch
python .\tools\start_powerbuilder.py --skip-build --self-test
```

The build command must produce a real PE executable and PBD with successful compiler diagnostics. Self-test must validate 50 pages, first/last record IDs, all seven cells of representative rows, initial form state and reset, and a bounded drag result. It must write a machine-readable report and close its own window. Actual UIA/MSAA tree coverage is not claimed by these checks.

## Result

2026-10-15: Both official installers returned ResultCode=0. OrcaScript built the real x86 PE and PBD successfully. Six launcher tests and 3085 application self-checks passed. Code review findings for dynamic AccessibleName and skip-build Runtime handling were reproduced and fixed. Runtime XML matches the native compiler's Application/RuntimePath schema. Layout is constrained to the actual client area, including at the current machine's DPI. Evidence is in `POWERBUILDER/build/Release/verification.json`; the host is Windows 11 x64, and a separate Windows 10 machine was not tested. No OCR was used, and no user testing window remains open.
