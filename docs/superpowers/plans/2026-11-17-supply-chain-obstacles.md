# Supply-chain optional GUI obstacles

**Goal:** Add one opt-in `--obstacles` flag to the existing launcher and launch-center entry. Default behavior is preserved; business fixtures, exports and grading rules remain the same.

**Global constraints:** Real Win32 / Swing. Actual deferred control construction, not preconstructed controls merely hidden or disabled. No sleeps on the UI thread. Load delay fixed at 1200 ms for comparable trials. Standard labels and accessible names remain meaningful. Record the boolean in context and metadata; an old run without it means false. No commits/branches. Existing uncommitted implementation is the baseline.

## Root: configuration and Web

- [x] Tests first: parser default/flag, persisted fixture context/metadata, desktop command propagation, background serve uses persisted setting, default and obstacle HTTP index, random-ID references and application bindings.
- [x] Add `create_run(..., obstacles=False)` and pass launcher flag. `serve` reads the persisted run setting, not transient command defaults; both desktop command arrays get `--obstacles` only when enabled. Keep business arrays identical for same profile/seed.
- [x] Serve index with `data-obstacles="true"` only in obstacle mode. `obstacles.js` binds private logical DOM references then assigns fresh UUID-based IDs before app bootstrap. Rewrite label-for, datalist-list, ARIA IDREFs and fragment targets. No stable `data-testid` aliases. CSS status/error styles use classes. App holds element references so queries/pagination/reset/export keep working.
- [x] Register optional launch-center boolean, document behavior and fair comparison.

## Win32 worker (owns win32/*)

- [x] Add model regression tests then `--obstacles` option. With flag, startup contains native shell, an `进入报价工作台` button and status; no business Edit/ListView/action HWNDs. User action starts a WM_TIMER, shows loading state, then creates actual existing business controls after1200ms. Prevent duplicate loads and premature menu actions; preserve existing layout, HTTP, menus and default mode. Close cancels pending timer.
- [x] Build/CTest, report verification. Root runs live UI probes.

## Java worker (owns java/*)

- [x] Add headless panel tests then `--obstacles` option. Create only tabs/placeholders at startup; selecting a tab triggers a one-shot Swing Timer, first1200ms shows loading then constructs its business panel/widgets. Initialize each page only once, retain contents across tab switches, no timer duplicates, safely handle close. Default mode eagerly builds existing pages.
- [x] Cache task context independently of lazy form fields; apply context whether it arrives before or after form creation. Exception registration must work even if procurement page was never created. Preserve existing refresh generation guard and row identity fix.
- [x] Build/headless tests, report verification. Root runs live UI probes.

## Root integration

- [x] Review code and fixes; run Python/Node/C++/Java checks.
- [x] From normal desktop launch obstacle mode: verify native initial absence/after-click presence, Java per-tab loading and preserved edits, Web refresh changes IDs while ARIA/datalist/query/reset/export work. Verify default mode remains eager and obstacle metadata reaches reports. Preserve historical runs.
