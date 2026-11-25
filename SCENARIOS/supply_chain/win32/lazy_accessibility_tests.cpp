#include "lazy_accessibility.h"
#include <UIAutomation.h>
#include <atomic>
#include <commctrl.h>
#include <cstdio>
#include <cstdlib>
#include <oleacc.h>
#include <string>
#include <thread>
#include <vector>
// Compile the implementation into this native harness to exercise direct
// provider interfaces and the factory race. MSAA client proxies intentionally
// expose only MSAA interfaces; cross-process UIA is verified by the separate
// operator probe.
#include "lazy_accessibility.cpp"

void check(bool ok, const char *name) {
  if (!ok) {
    std::fprintf(stderr, "FAIL: %s\n", name);
    std::exit(1);
  }
}
LRESULT stat(HWND h, WPARAM field) {
  return SendMessageW(h, lazy_a11y::DiagnosticsMessage, field, 0);
}
template <class T> struct Ptr {
  T *p = nullptr;
  ~Ptr() {
    if (p)
      p->Release();
  }
  void reset() {
    if (p)
      p->Release();
    p = nullptr;
  }
  T **out() { return &p; }
  T *operator->() const { return p; }
};
VARIANT self() {
  VARIANT v{};
  v.vt = VT_I4;
  v.lVal = CHILDID_SELF;
  return v;
}
void pump() {
  MSG msg;
  while (PeekMessageW(&msg, nullptr, 0, 0, PM_REMOVE)) {
    TranslateMessage(&msg);
    DispatchMessageW(&msg);
  }
}
int headerClicks = 0;
LRESULT CALLBACK recordClick(HWND h, UINT m, WPARAM wp, LPARAM lp, UINT_PTR,
                             DWORD_PTR data) {
  if (m == WM_COMMAND && LOWORD(wp) == 102 && HIWORD(wp) == BN_CLICKED)
    ++*reinterpret_cast<int *>(data);
  if (m == WM_NOTIFY && reinterpret_cast<NMHDR *>(lp)->code == LVN_COLUMNCLICK)
    ++headerClicks;
  return DefSubclassProc(h, m, wp, lp);
}
int runTests() {
  INITCOMMONCONTROLSEX ic{sizeof(ic), ICC_LISTVIEW_CLASSES};
  InitCommonControlsEx(&ic);
  HWND window =
      CreateWindowW(L"STATIC", L"test window", WS_OVERLAPPEDWINDOW, 0, 0, 500,
                    400, nullptr, nullptr, GetModuleHandleW(nullptr), nullptr);
  HWND edit =
      CreateWindowW(L"EDIT", L"initial", WS_CHILD | ES_AUTOHSCROLL, 10, 10, 200,
                    30, window, (HMENU)101, GetModuleHandleW(nullptr), nullptr);
  HWND button =
      CreateWindowW(L"BUTTON", L"Action", WS_CHILD | BS_PUSHBUTTON, 10, 45, 100,
                    30, window, (HMENU)102, GetModuleHandleW(nullptr), nullptr);
  HWND list = CreateWindowW(
      WC_LISTVIEWW, L"Rows", WS_CHILD | LVS_REPORT | LVS_SINGLESEL, 10, 80, 400,
      200, window, (HMENU)103, GetModuleHandleW(nullptr), nullptr);
  LVCOLUMNW col{};
  col.mask = LVCF_WIDTH | LVCF_TEXT;
  col.cx = 100;
  col.pszText = const_cast<wchar_t *>(L"Name");
  ListView_InsertColumn(list, 0, &col);
  ListView_InsertColumn(list, 1, &col);
  for (int i = 0; i < 1000; ++i) {
    std::wstring text = L"Row " + std::to_wstring(i);
    LVITEMW item{};
    item.mask = LVIF_TEXT;
    item.iItem = i;
    item.pszText = text.data();
    ListView_InsertItem(list, &item);
    ListView_SetItemText(list, i, 1, const_cast<wchar_t *>(L"cell"));
  }
  lazy_a11y::Attach(window);
  check(stat(window, 9) == 0xA11 && stat(edit, 9) == 0xA11 &&
            stat(list, 9) == 0xA11,
        "diagnostics handshake proves attachment");
  check(stat(window, 1) == 0 && stat(edit, 1) == 0 && stat(list, 1) == 0,
        "attachment allocates zero providers");
  check(stat(edit, 7) == 0 && stat(edit, 8) == 0,
        "silent state raises no application events and creates no delegates");
  SendMessageW(edit, WM_GETOBJECT, 0, static_cast<LPARAM>(OBJID_NATIVEOM));
  check(stat(edit, 0) == 0, "unrelated object ID stays silent");
  Ptr<IAccessible> accessible;
  check(SUCCEEDED(AccessibleObjectFromWindow(
            edit, OBJID_CLIENT, IID_IAccessible,
            reinterpret_cast<void **>(accessible.out()))),
        "MSAA root acquisition");
  check(stat(edit, 0) == 1 && stat(edit, 3) == 1 && stat(edit, 1) == 1,
        "valid request creates exactly one root");
  check(stat(window, 0) == 0 && stat(button, 0) == 0 && stat(list, 0) == 0,
        "HWND roots remain independent");
  // Consume each LresultFromObject token: sign- and zero-extended IDs both
  // request the same root.
  for (LPARAM id : {static_cast<LPARAM>(static_cast<LONG>(OBJID_CLIENT)),
                    static_cast<LPARAM>(static_cast<DWORD>(OBJID_CLIENT))}) {
    LRESULT result = SendMessageW(edit, WM_GETOBJECT, 0, id);
    Ptr<IAccessible> normalized;
    check(SUCCEEDED(
              ObjectFromLresult(result, IID_IAccessible, 0,
                                reinterpret_cast<void **>(normalized.out()))),
          "low32 object ID normalization");
  }
  check(stat(edit, 3) == 1, "repeat valid requests reuse one root");
  Ptr<IRawElementProviderSimple> simple;
  simple.p = static_cast<IRawElementProviderSimple *>(
      lazy_a11y::Acquire(lazy_a11y::Lookup(edit)));
  check(simple.p != nullptr, "same cached adapter exposes direct UIA");
  Ptr<IUnknown> pattern;
  check(SUCCEEDED(
            simple->GetPatternProvider(UIA_ValuePatternId, pattern.out())) &&
            pattern.p,
        "edit value pattern");
  Ptr<IValueProvider> value;
  check(SUCCEEDED(pattern->QueryInterface(IID_PPV_ARGS(value.out()))),
        "value QI");
  check(SUCCEEDED(value->SetValue(L"changed")), "value action");
  wchar_t text[100]{};
  GetWindowTextW(edit, text, 100);
  check(std::wstring(text) == L"changed", "native edit changed");
  BSTR actual = nullptr;
  check(SUCCEEDED(accessible->get_accValue(self(), &actual)),
        "native MSAA value");
  check(actual && std::wstring(actual) == L"changed",
        "MSAA observes same value");
  SysFreeString(actual);
  Ptr<IUnknown> unsupported;
  check(SUCCEEDED(simple->GetPatternProvider(UIA_InvokePatternId,
                                             unsupported.out())) &&
            !unsupported.p,
        "unsupported pattern is absent");
  int clicks = 0;
  SetWindowSubclass(window, recordClick, 77,
                    reinterpret_cast<DWORD_PTR>(&clicks));
  Ptr<IAccessible> buttonAcc;
  check(SUCCEEDED(AccessibleObjectFromWindow(
            button, OBJID_CLIENT, IID_IAccessible,
            reinterpret_cast<void **>(buttonAcc.out()))),
        "button acquisition");
  {
    auto root = lazy_a11y::Acquire(lazy_a11y::Lookup(button));
    check(SUCCEEDED(root->Invoke()), "button Invoke");
    root->Release();
  }
  pump();
  check(clicks == 1, "native button delivers real command");
  Ptr<IAccessible> listAcc;
  check(SUCCEEDED(AccessibleObjectFromWindow(
            list, OBJID_CLIENT, IID_IAccessible,
            reinterpret_cast<void **>(listAcc.out()))),
        "list root acquisition");
  check(stat(list, 1) == 1 && stat(list, 2) == 1,
        "1000 rows create only list root");
  Ptr<IItemContainerProvider> container;
  {
    auto root = lazy_a11y::Acquire(lazy_a11y::Lookup(list));
    check(SUCCEEDED(root->QueryInterface(IID_PPV_ARGS(container.out()))),
          "list item container");
    root->Release();
  }
  VARIANT name{};
  name.vt = VT_BSTR;
  name.bstrVal = SysAllocString(L"Row 900");
  Ptr<IRawElementProviderSimple> row;
  check(SUCCEEDED(container->FindItemByProperty(nullptr, UIA_NamePropertyId,
                                                name, row.out())) &&
            row.p,
        "offscreen named row lookup");
  VariantClear(&name);
  check(stat(list, 1) == 2 && stat(list, 2) == 2,
        "lookup constructs only requested row");
  Ptr<IRawElementProviderSimple> rowAgain;
  VARIANT index{};
  index.vt = VT_BSTR;
  index.bstrVal = SysAllocString(L"row-900");
  check(SUCCEEDED(container->FindItemByProperty(
            nullptr, UIA_AutomationIdPropertyId, index, rowAgain.out())),
        "row ID lookup");
  VariantClear(&index);
  check(rowAgain.p == row.p && stat(list, 2) == 2, "live row cache identity");
  Ptr<IVirtualizedItemProvider> virtualized;
  check(SUCCEEDED(row->QueryInterface(IID_PPV_ARGS(virtualized.out()))),
        "offscreen row supports Realize");
  check(SUCCEEDED(virtualized->Realize()), "Realize scrolls native list");
  check(ListView_GetTopIndex(list) > 0, "realization changes viewport");
  Ptr<IRawElementProviderFragment> fragment;
  check(SUCCEEDED(row->QueryInterface(IID_PPV_ARGS(fragment.out()))),
        "row fragment");
  Ptr<IRawElementProviderFragment> cell;
  check(
      SUCCEEDED(fragment->Navigate(NavigateDirection_FirstChild, cell.out())) &&
          cell.p,
      "requested first cell");
  check(stat(list, 1) == 3, "cell navigation adds one node");
  Ptr<IRawElementProviderSimple> cellSimple;
  check(SUCCEEDED(cell->QueryInterface(IID_PPV_ARGS(cellSimple.out()))),
        "cell simple");
  VARIANT cellName{};
  check(SUCCEEDED(cellSimple->GetPropertyValue(UIA_NamePropertyId, &cellName)),
        "cell name");
  check(cellName.vt == VT_BSTR && std::wstring(cellName.bstrVal) == L"Row 900",
        "native cell text");
  VariantClear(&cellName);
  UiaRect firstCellRect{};
  check(SUCCEEDED(cell->get_BoundingRectangle(&firstCellRect)),
        "cell rectangle");
  check(firstCellRect.width <= 100,
        "first cell bounds do not include other columns");
  Ptr<IAccessible> rowAcc;
  check(SUCCEEDED(row->QueryInterface(IID_PPV_ARGS(rowAcc.out()))), "row MSAA");
  // Native accessibility does not transfer keyboard focus into hidden controls.
  ShowWindow(edit, SW_SHOWNA);
  ShowWindow(button, SW_SHOWNA);
  ShowWindow(list, SW_SHOWNA);
  ShowWindow(window, SW_SHOWNOACTIVATE);
  SetActiveWindow(window);
  SetFocus(edit);
  check(SUCCEEDED(rowAcc->accSelect(SELFLAG_TAKEFOCUS | SELFLAG_TAKESELECTION,
                                    self())),
        "combined selection and focus flags");
  check(GetFocus() == list &&
            (ListView_GetItemState(list, 900, LVIS_FOCUSED) & LVIS_FOCUSED),
        "combined flags apply native focus too");
  rowAcc.reset();
  cellSimple.reset();
  cell.reset();
  check(stat(list, 1) == 2, "released cell immediately leaves weak cache");
  {
    auto state = lazy_a11y::Lookup(list);
    std::vector<lazy_a11y::Provider *> requested(24, nullptr);
    std::vector<std::thread> workers;
    std::atomic<bool> go{false};
    for (int i = 0; i < 24; ++i)
      workers.emplace_back([&, i] {
        while (!go.load())
          std::this_thread::yield();
        requested[i] = lazy_a11y::Acquire(state, 700);
      });
    auto before = stat(list, 2);
    go = true;
    for (auto &worker : workers)
      worker.join();
    for (auto p : requested)
      check(p == requested[0], "concurrent requests share node identity");
    check(stat(list, 2) == before + 1,
          "concurrent factory creates exactly one node");
    for (auto p : requested)
      p->Release();
    check(stat(list, 1) == 2,
          "concurrent references release without a strong cache cycle");
  }
  HWND header = ListView_GetHeader(list);
  check(stat(header, 9) == 0xA11 && stat(header, 2) == 0,
        "header attaches silently");
  Ptr<IAccessible> headerAcc;
  check(SUCCEEDED(AccessibleObjectFromWindow(
            header, OBJID_CLIENT, IID_IAccessible,
            reinterpret_cast<void **>(headerAcc.out()))),
        "header root acquisition");
  long columns = 0;
  check(SUCCEEDED(headerAcc->get_accChildCount(&columns)) && columns == 2,
        "native header exposes logical column items");
  VARIANT headerChild = self();
  headerChild.lVal = 1;
  BSTR headerName = nullptr;
  check(SUCCEEDED(headerAcc->get_accName(headerChild, &headerName)) &&
            headerName && std::wstring(headerName) == L"Name",
        "header column name preserved");
  SysFreeString(headerName);
  {
    auto headerRoot = lazy_a11y::Acquire(lazy_a11y::Lookup(header));
    RECT r{};
    Header_GetItemRect(header, 1, &r);
    MapWindowPoints(header, nullptr, reinterpret_cast<POINT *>(&r), 2);
    Ptr<IRawElementProviderFragment> hit;
    check(SUCCEEDED(headerRoot->ElementProviderFromPoint(
              (r.left + r.right) / 2, (r.top + r.bottom) / 2, hit.out())) &&
              hit.p,
          "header point hit");
    Ptr<IRawElementProviderSimple> hitSimple;
    hit->QueryInterface(IID_PPV_ARGS(hitSimple.out()));
    VARIANT type{};
    hitSimple->GetPropertyValue(UIA_ControlTypePropertyId, &type);
    check(type.vt == VT_I4 && type.lVal == UIA_HeaderItemControlTypeId,
          "header hit returns logical item");
    headerRoot->Release();
  }
  {
    auto headerItem = lazy_a11y::Acquire(lazy_a11y::Lookup(header), 0);
    check(SUCCEEDED(headerItem->Invoke()), "header item Invoke");
    headerItem->Release();
    pump();
  }
  check(headerClicks == 1,
        "header action delivers native column-click notification");
  auto previousEpoch = stat(list, 6);
  lazy_a11y::Invalidate(list);
  VARIANT retired{};
  check(row->GetPropertyValue(UIA_NamePropertyId, &retired) ==
            UIA_E_ELEMENTNOTAVAILABLE,
        "rebuild invalidates retained row");
  check(stat(list, 0) == 0, "invalidation retires without reactivation");
  Ptr<IAccessible> newList;
  check(SUCCEEDED(AccessibleObjectFromWindow(
            list, OBJID_CLIENT, IID_IAccessible,
            reinterpret_cast<void **>(newList.out()))),
        "reacquire after rebuild");
  check(stat(list, 6) > previousEpoch && stat(list, 3) == 2,
        "reacquisition creates one new epoch");
  newList.reset();
  listAcc.reset();
  container.reset();
  rowAgain.reset();
  virtualized.reset();
  fragment.reset();
  row.reset();
  pump();
  check(stat(list, 1) == 1, "old epoch releases while new root remains");
  auto state = lazy_a11y::Lookup(list);
  state->lastUse = GetTickCount64() - lazy_a11y::IdleTimeoutMs - 1;
  PostMessageW(lazy_a11y::cleanupWindow, WM_TIMER, lazy_a11y::RetirementTimerId,
               0);
  pump();
  check(stat(list, 0) == 0 && stat(list, 1) == 0,
        "idle expiration disconnects and returns to zero providers");
  lazy_a11y::Invalidate(list);
  check(stat(list, 0) == 0 && stat(list, 1) == 0,
        "invalidating silent list allocates nothing");
  Ptr<IAccessible> afterIdle;
  check(SUCCEEDED(AccessibleObjectFromWindow(
            list, OBJID_CLIENT, IID_IAccessible,
            reinterpret_cast<void **>(afterIdle.out()))),
        "recovery after idle");
  check(stat(list, 3) == 3 && stat(list, 1) == 1,
        "recovery creates only new root");
  {
    auto frame = lazy_a11y::Acquire(lazy_a11y::Lookup(window));
    Ptr<IRawElementProviderFragment> child;
    check(
        SUCCEEDED(frame->Navigate(NavigateDirection_FirstChild, child.out())) &&
            !child.p,
        "HWND fragment stitching belongs to the native host");
    VARIANT controlType{};
    check(SUCCEEDED(frame->GetPropertyValue(UIA_ControlTypePropertyId,
                                            &controlType)) &&
              controlType.vt == VT_I4 &&
              controlType.lVal == UIA_WindowControlTypeId,
          "top-level application window keeps Window control type");
    long count = 0;
    check(SUCCEEDED(frame->get_accChildCount(&count)) && count == 3,
          "MSAA still exposes owned HWND children explicitly");
    VARIANT firstMsaaChild{};
    check(SUCCEEDED(
              frame->accNavigate(NAVDIR_FIRSTCHILD, self(), &firstMsaaChild)) &&
              firstMsaaChild.vt == VT_DISPATCH,
          "MSAA first-child navigation preserves HWND hierarchy");
    VariantClear(&firstMsaaChild);
    SetFocus(edit);
    Ptr<IRawElementProviderFragment> focus;
    check(SUCCEEDED(frame->GetFocus(focus.out())) && !focus.p,
          "UIA focus does not cross fragment roots");
    VARIANT msaaFocus{};
    check(SUCCEEDED(frame->get_accFocus(&msaaFocus)) &&
              msaaFocus.vt == VT_DISPATCH,
          "MSAA focus preserves child HWND semantics");
    VariantClear(&msaaFocus);
    frame->Release();
  }
  DestroyWindow(window);
  VARIANT stale{};
  check(simple->GetPropertyValue(UIA_NamePropertyId, &stale) ==
            UIA_E_ELEMENTNOTAVAILABLE,
        "destroyed HWND root safely stale");
  lazy_a11y::Shutdown();
  std::puts("PASS: silent attachment, object-ID normalization, native "
            "actions/value/header, lazy rows/cells, concurrent factory "
            "identity, weak cache release, invalidation, idle "
            "cleanup/recovery, stale references");
  return 0;
}
int main() {
  check(SUCCEEDED(OleInitialize(nullptr)), "OLE initializes");
  int result = runTests();
  OleUninitialize();
  return result;
}
