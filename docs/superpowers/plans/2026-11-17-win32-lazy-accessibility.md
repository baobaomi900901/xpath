# Win32 on-demand accessibility

## Scope and platform interpretation

Target is the current supply-chain supplier application in `SCENARIOS/supply_chain/win32/`, not the unrelated legacy WIN32 shooting ranges. Keep native GUI controls and normal business interaction unchanged. Existing accessibility comes from Windows standard-control proxies, not an application-owned Provider implementation. Add a thin on-demand application adapter which reuses those standard semantics.

Default-silent means zero application Provider objects before valid requests, not an invisible HWND: Windows can expose host/non-client proxies. Inspect/FlaUI tree inspection itself sends activation requests and may explicitly enumerate descendants. `UiaClientsAreListening` means global event subscription, not per-HWND attachment or a reliable count of query-only/MSAA clients. Do not use it for activation or disconnection decisions; retire from actual per-HWND access idle time. Correct virtualization interfaces: IItemContainerProvider::FindItemByProperty and IVirtualizedItemProvider::Realize.

## Required implementation

- [x] Read native implementation and Microsoft primary API documentation; explain plan before implementation.
- [x] Add per-HWND lightweight state and subclass attachment. WM_CREATE/PAINT/control construction attach metadata only; constructors never create descendant Providers. WM_GETOBJECT compares low32-bit object identifier to UiaRootObjectId / OBJID_CLIENT. Other IDs pass through and do not activate.
- [x] Valid root request creates one root under mutex. UIA and MSAA adapters expose standard native names, values, enabled/focus/geometry/actions. Navigation, child access and patterns create only requested nodes and cache them safely. Preserve useful native semantics through CreateStdAccessibleObject/delegation; never hold provider-cache locks across native/COM callbacks.
- [x] Lists expose requested rows/cells lazily. Prefer viewport navigation and ItemContainer/VirtualizedItem for offscreen lookup; constructors must not build all rows. Do not expose fake unsupported patterns.
- [x] Lifetime: reference-counted objects, independent HWND generation, thread-safe factory/cache. Window destruction retires generation; old objects return element-not-available. No forced deletion while references remain. Recovery via released references and documented idle timeout, never treat no listeners alone as no clients. UiaDisconnectProvider runs outside SendMessage/reentrant WM_GETOBJECT, with temporary strong references and no cache locks. Retry gives new epoch.
- [x] No application UiaRaise*/NotifyWinEvent calls during silent mode. Do not claim control over Windows-generated events/non-client/system-owned dialog Providers.
- [x] Add diagnostic counters usable without WM_GETOBJECT: registered/private stats message returns fields; no hidden runtime flags required for normal users. Counters distinguish activation/root/node/live/retirement/epoch.
- [x] Integrate Attach with main and owned controls/header HWNDs, detach/shutdown, COM initialization and CMake. Existing --obstacles GUI construction delay remains independent.
- [x] Tests first for request filtering, single root under concurrency, demand-only child construction, cache identity, stale generation, reference release, timeout and correct native action/value/list behavior. Run real COM UIA/MSAA client probes plus existing native and scenario regression checks. Report platform limitations precisely.

## File ownership

Provider worker: new `win32/lazy_accessibility.h`, `win32/lazy_accessibility.cpp`, `win32/lazy_accessibility_tests.cpp`. Root: main.cpp, CMakeLists.txt, an external operator probe, docs and launcher packaging.

## Integration contract

Namespace `lazy_a11y`. Public `void Attach(HWND)`, `void Shutdown()` (called on UI thread after window message loop, before OleUninitialize), and optional `void Detach(HWND)`; subclass handles NCDESTROY itself. Attach may enumerate existing owned child HWNDs to attach lightweight states, never Provider objects; root also calls Attach on newly created controls. Provider module owns per-HWND request handler, retirement timer and diagnostics.

Also expose `void Invalidate(HWND)` to retire the active generation while preserving hooks and counters. Root calls it before replacing ListView rows/columns, so retained row/cell references cannot silently resolve to a new material. Invalidation of a silent HWND must not allocate Providers.

Diagnostic message `constexpr UINT DiagnosticsMessage = WM_APP + 0x3A`; WPARAM selector: 0 active(0/1), 1 live application nodes, 2 total nodes created, 3 root objects created, 4 activation epochs, 5 retired epochs, 6 current generation, 7 application events raised (silent0), 8 successful native delegate acquisitions (API calls, not unique OS allocations). LPARAM unused. Query is read-only and must not activate. Per-HWND counters persist until destruction. An optional selector >=100 may provide process aggregates for the same fields but document if implemented. Provide `constexpr DWORD IdleTimeoutMs=30000` and `constexpr UINT_PTR RetirementTimerId` with an ID different from business LOAD_TIMER1. Optional native app `--a11y-idle-ms` is not required; tests may call internal retirement function with an injected clock/short timeout.

Selector9 returns protocol magic0xA11 even before activation, so a missing hook cannot be mistaken for all-zero diagnostics. Application/tests delay-load UIAutomationCore.dll and OLEACC.dll through MSVC delayimp to avoid adding eager accessibility DLL imports; system controls can still load system components independently.

Root will integrate without committing or changing branches. No third-party dependencies; use Windows SDK / C++17 / COM. Build with MSVC Release and meaningful assertions enabled. Existing uncommitted scenario is baseline.
