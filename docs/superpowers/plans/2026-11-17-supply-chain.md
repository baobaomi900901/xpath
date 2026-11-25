# Supply Chain GUI Benchmark Implementation Plan

> **For agentic workers:** Use subagent-driven-development for the three independent UI tasks; the root implements the shared service and integration. Work in the current clean workspace; do not commit or create branches during this user-requested implementation.

**Goal:** Deliver a runnable Web → Win32 → Java procurement benchmark for comparing Agents using the user's GUI CLI and SDK.

**Architecture:** Python standard-library local service owns seeded fixture data, XLSX files and persistent orders. Independent native applications consume the fixed contract. An offline evaluator computes expected business results independently of order submission.

**Tech Stack:** Python 3 standard library, HTML/CSS/JS, Win32 C++17/MSVC/CMake, Java 8 Swing.

## Global Constraints

- Binding contract: `SCENARIOS/supply_chain/CONTRACT.md`.
- Web, genuine Win32 and genuine Java Swing; no GUI stack substitution.
- Real XLSX exports, no renamed CSV; no recommendation or answer API.
- Only standard-library runtimes and installed C++ / Java build tools.
- Seeded basic/standard/advanced runs, reset isolation, persisted events and orders.
- Agent-facing task excludes internal interfaces and expected answers.
- No commits, branch/worktree operations or publishing; preserve existing ranges.

## Task 1: Shared service and independent evaluation (root)

Files: `SCENARIOS/supply_chain/{fixtures,domain,workbooks,server,evaluate}.py`, `tests/test_*.py`.

- [x] Write unittest cases for boundary stock, seed reproducibility, real XLSX roundtrip, invalid imports, order validation, duplicate prevention, fail-once, independent grading and HTTP integration.
- [x] Run `python -m unittest discover -s SCENARIOS/supply_chain/tests -v`, verify failure from missing implementation.
- [x] Implement fixture factory `make_fixture(profile,seed)`, run storage `Store(path)`, XLSX writer/reader, service HTTP handlers and offline `evaluate(run_dir)`.
- [x] Re-run tests. Verify wrong procurement is rejected by evaluation even when accepted by normal order validation.

## Task 2: A Web inventory (web worker)

Owned files: `SCENARIOS/supply_chain/web/*`, web-specific tests only.

Read CONTRACT first. Serve index at `/`; same-origin endpoints. Plain HTML/CSS/JS, all business copy Chinese. Implement filters, sorting, pagination8, export complete query, task context, accessible states. Test filter/pagination/export behavior with the installed browser workflow or pure model tests followed by browser checks. No edits to backend/launcher.

## Task 3: B native supplier client (Win32 worker)

Owned files: `SCENARIOS/supply_chain/win32/*`.

Read CONTRACT first. Implement WinHTTP binary/form requests and UTF-8 TSV parsing; native controls and dialogs. Add pure parsing / sorting tests and compile via standalone CMake. App arguments `--url <base>`. Build output `SCENARIOS/supply_chain/build/win32/Release/supply-chain-supplier.exe`. Handle errors visibly and keep data. No edits outside owned files.

## Task 4: C Java purchase client (Java worker)

Owned files: `SCENARIOS/supply_chain/java/*`.

Read CONTRACT first. Implement dependency-free `SupplyChainPurchase` entry class, source8/target8, build classes in `SCENARIOS/supply_chain/build/java`. Use UTF-8 TSV/form HTTP, SwingWorker for I/O. Include headless model tests. Handle business errors and fail-once retry without losing input. No edits outside owned files.

## Task 5: Launcher, docs and full verification (root)

Files: `tools/start_supply_chain.py`, `tools/ranges.json`, `README.md`, `SCENARIOS/supply_chain/{README.md,task.md,.gitignore}`, launcher tests.

- [x] Add tested build/reset/launch/stop/evaluate/task commands, detect installed javac/java and CMake, hide background console windows, preserve all prior runtime paths (no recursive deletion).
- [x] Register scenario in launcher without changing existing options.
- [x] Write operator guide and answer-free task template, CLI/SDK fairness boundary and metrics limitations.
- [x] Build both native apps. Run backend and launcher tests, headless Java/native tests and live UI smoke checks. Export→import real workbook; create and requery an order; verify evaluator pass and negative case.
- [x] Review all changed files for spec and quality, fix important findings, rerun affected checks. Deliver exact launch/evaluation commands and any unverified limitations.

## Verification limits

Web worker completed fixture-based browser smoke (pagination, sorting, filters, reset). Native and Swing builds plus headless tests pass. Initial sandbox Win32 startup produced `0xc0000142` and activation failed. Relaunch from a normal desktop process resolved it. Root then completed the basic business entirely through the installed UIAutoma CLI: browser XLSX download, native import/query/save, Swing editable-cell entry, confirmations, two purchase submissions and order readback. Offline evaluation passed (2 orders, 1700.00). Standard and advanced seeded reference procurement and fail-once recovery pass automated business/integration tests; their full GUI loops were not separately executed. Service/interface reviews and follow-up fixes are complete. See `SCENARIOS/supply_chain/VERIFICATION.md`.
