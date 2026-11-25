#include "lazy_accessibility.h"
#include <UIAutomation.h>
#include <algorithm>
#include <atomic>
#include <commctrl.h>
#include <map>
#include <memory>
#include <mutex>
#include <oleacc.h>
#include <string>
#include <tuple>
#include <vector>

namespace lazy_a11y {
namespace {
constexpr UINT_PTR SubclassId = 0xA114;
constexpr UINT CleanupMessage = WM_APP + 0x3B;
constexpr UINT ScheduleMessage = WM_APP + 0x3C;
class Provider;
using Key = std::tuple<unsigned long long, unsigned long long, int, int>;
struct State {
  explicit State(HWND h) : hwnd(h) {
    wchar_t name[128]{};
    GetClassNameW(h, name, 128);
    className = name;
  }
  HWND hwnd;
  std::wstring className;
  std::mutex mutex;
  std::map<Key, Provider *>
      nodes; // Weak: final Release removes under this same mutex.
  Provider *root = nullptr; // Exactly one owning reference while active.
  std::atomic<bool> dead{false}, active{false};
  std::atomic<unsigned long long> epoch{0}, dataVersion{0}, lastUse{0};
  std::atomic<unsigned long long> live{0}, created{0}, roots{0}, retired{0},
      delegates{0};
};
std::mutex statesMutex;
std::map<HWND, std::shared_ptr<State>> states;
std::mutex cleanupMutex;
std::vector<Provider *> pendingCleanup;
HWND cleanupWindow = nullptr;
std::atomic<unsigned long long> nextEpoch{0};

template <class T> struct ComPtr {
  T *p = nullptr;
  ~ComPtr() {
    if (p)
      p->Release();
  }
  T **out() { return &p; }
  T *operator->() const { return p; }
};
VARIANT Child(long id = CHILDID_SELF) {
  VARIANT v{};
  v.vt = VT_I4;
  v.lVal = id;
  return v;
}
std::shared_ptr<State> Lookup(HWND hwnd) {
  std::lock_guard<std::mutex> lock(statesMutex);
  auto it = states.find(hwnd);
  return it == states.end() ? nullptr : it->second;
}
Provider *Acquire(const std::shared_ptr<State> &state, int row = -1,
                  int column = -1);
void Retire(const std::shared_ptr<State> &state);
void DrainCleanup();

class Provider final : public IRawElementProviderSimple,
                       public IRawElementProviderFragment,
                       public IRawElementProviderFragmentRoot,
                       public IAccessible,
                       public IInvokeProvider,
                       public IValueProvider,
                       public IItemContainerProvider,
                       public IVirtualizedItemProvider,
                       public ISelectionProvider,
                       public ISelectionItemProvider,
                       public IScrollItemProvider,
                       public IGridProvider,
                       public IGridItemProvider {
public:
  Provider(std::shared_ptr<State> state, Key key, int row, int column)
      : state_(std::move(state)), key_(key), row_(row), column_(column) {
    ++state_->live;
    ++state_->created;
    if (row_ < 0)
      ++state_->roots;
  }
  HRESULT STDMETHODCALLTYPE QueryInterface(REFIID iid, void **out) override {
    if (!out)
      return E_POINTER;
    *out = nullptr;
    if (iid == IID_IUnknown || iid == __uuidof(IRawElementProviderSimple))
      *out = static_cast<IRawElementProviderSimple *>(this);
    else if (iid == __uuidof(IRawElementProviderFragment))
      *out = static_cast<IRawElementProviderFragment *>(this);
    else if (iid == __uuidof(IRawElementProviderFragmentRoot) && row_ < 0)
      *out = static_cast<IRawElementProviderFragmentRoot *>(this);
    else if (iid == IID_IAccessible || iid == IID_IDispatch)
      *out = static_cast<IAccessible *>(this);
    else if (iid == __uuidof(IInvokeProvider) && (IsButton() || IsHeaderItem()))
      *out = static_cast<IInvokeProvider *>(this);
    else if (iid == __uuidof(IValueProvider) && IsEdit())
      *out = static_cast<IValueProvider *>(this);
    else if (iid == __uuidof(IItemContainerProvider) && IsListRoot())
      *out = static_cast<IItemContainerProvider *>(this);
    else if (iid == __uuidof(IVirtualizedItemProvider) && IsRow())
      *out = static_cast<IVirtualizedItemProvider *>(this);
    else if (iid == __uuidof(ISelectionProvider) && IsListRoot())
      *out = static_cast<ISelectionProvider *>(this);
    else if (iid == __uuidof(ISelectionItemProvider) && IsRow())
      *out = static_cast<ISelectionItemProvider *>(this);
    else if (iid == __uuidof(IScrollItemProvider) && IsRow())
      *out = static_cast<IScrollItemProvider *>(this);
    else if (iid == __uuidof(IGridProvider) && IsListRoot())
      *out = static_cast<IGridProvider *>(this);
    else if (iid == __uuidof(IGridItemProvider) && column_ >= 0)
      *out = static_cast<IGridItemProvider *>(this);
    if (!*out)
      return E_NOINTERFACE;
    AddRef();
    return S_OK;
  }
  ULONG STDMETHODCALLTYPE AddRef() override { return ++refs_; }
  ULONG STDMETHODCALLTYPE Release() override {
    ULONG remaining;
    {
      std::lock_guard<std::mutex> lock(state_->mutex);
      remaining = --refs_;
      if (!remaining) {
        auto it = state_->nodes.find(key_);
        if (it != state_->nodes.end() && it->second == this)
          state_->nodes.erase(it);
      }
    }
    if (!remaining)
      delete this;
    return remaining;
  }
  HRESULT Check() {
    if (state_->dead || !state_->active || state_->epoch != std::get<0>(key_) ||
        (row_ >= 0 && state_->dataVersion != std::get<1>(key_)))
      return UIA_E_ELEMENTNOTAVAILABLE;
    state_->lastUse = GetTickCount64();
    return S_OK;
  }
  bool IsList() const {
    return _wcsicmp(state_->className.c_str(), WC_LISTVIEWW) == 0;
  }
  bool IsListRoot() const { return row_ < 0 && IsList(); }
  bool IsRow() const { return IsList() && row_ >= 0 && column_ < 0; }
  bool IsHeader() const {
    return _wcsicmp(state_->className.c_str(), WC_HEADERW) == 0;
  }
  bool IsHeaderItem() const { return IsHeader() && row_ >= 0; }
  bool IsButton() const {
    return row_ < 0 && _wcsicmp(state_->className.c_str(), L"Button") == 0;
  }
  bool IsEdit() const {
    return row_ < 0 && _wcsicmp(state_->className.c_str(), L"Edit") == 0;
  }
  int Count() const {
    return IsHeader() ? Header_GetItemCount(state_->hwnd)
                      : ListView_GetItemCount(state_->hwnd);
  }
  int Columns() const {
    return Header_GetItemCount(ListView_GetHeader(state_->hwnd));
  }
  std::wstring Text(int row, int col) const {
    if (IsHeader()) {
      wchar_t text[4096]{};
      HDITEMW item{};
      item.mask = HDI_TEXT;
      item.pszText = text;
      item.cchTextMax = 4096;
      SendMessageW(state_->hwnd, HDM_GETITEMW, row,
                   reinterpret_cast<LPARAM>(&item));
      return text;
    }
    std::vector<wchar_t> text(256);
    for (;;) {
      LVITEMW item{};
      item.iSubItem = col;
      item.pszText = text.data();
      item.cchTextMax = static_cast<int>(text.size());
      int n = static_cast<int>(SendMessageW(state_->hwnd, LVM_GETITEMTEXTW, row,
                                            reinterpret_cast<LPARAM>(&item)));
      if (n < static_cast<int>(text.size()) - 1 || text.size() >= 65536)
        return std::wstring(text.data(), n);
      text.resize(text.size() * 2);
    }
  }
  HRESULT Delegate(IAccessible **out) {
    HRESULT hr = Check();
    if (FAILED(hr))
      return hr;
    hr = CreateStdAccessibleObject(state_->hwnd, OBJID_CLIENT, IID_IAccessible,
                                   reinterpret_cast<void **>(out));
    if (SUCCEEDED(hr))
      ++state_->delegates;
    return hr;
  }
  HRESULT String(BSTR *out, const std::wstring &value) {
    if (!out)
      return E_POINTER;
    *out = SysAllocStringLen(value.data(), static_cast<UINT>(value.size()));
    return *out ? S_OK : E_OUTOFMEMORY;
  }
  HRESULT Name(BSTR *out) {
    if (!out)
      return E_POINTER;
    *out = nullptr;
    HRESULT hr = Check();
    if (FAILED(hr))
      return hr;
    if (row_ >= 0)
      return String(out, Text(row_, std::max(0, column_)));
    ComPtr<IAccessible> native;
    hr = Delegate(native.out());
    return FAILED(hr) ? hr : native->get_accName(Child(), out);
  }
  bool ItemBounds(RECT *bounds) const {
    if (IsHeader())
      return !!Header_GetItemRect(state_->hwnd, row_, bounds);
    if (!ListView_GetItemRect(state_->hwnd, row_, bounds, LVIR_BOUNDS))
      return false;
    if (column_ >= 0) {
      // Native subitem zero reports the whole row; header bounds also respect
      // horizontal scrolling and reordered columns.
      HWND header = ListView_GetHeader(state_->hwnd);
      RECT column{};
      if (!Header_GetItemRect(header, column_, &column))
        return false;
      MapWindowPoints(header, state_->hwnd, reinterpret_cast<POINT *>(&column),
                      2);
      bounds->left = column.left;
      bounds->right = column.right;
    }
    return true;
  }
  bool OnScreen() const {
    if (!IsWindowVisible(state_->hwnd))
      return false;
    if (row_ < 0)
      return true;
    RECT item{}, client{}, intersection{};
    if (!ItemBounds(&item))
      return false;
    GetClientRect(state_->hwnd, &client);
    return !!IntersectRect(&intersection, &item, &client);
  }
  HRESULT STDMETHODCALLTYPE get_ProviderOptions(ProviderOptions *out) override {
    if (!out)
      return E_POINTER;
    *out = static_cast<ProviderOptions>(ProviderOptions_ServerSideProvider |
                                        ProviderOptions_UseComThreading);
    return S_OK;
  }
  HRESULT STDMETHODCALLTYPE GetPatternProvider(PATTERNID id,
                                               IUnknown **out) override {
    if (!out)
      return E_POINTER;
    *out = nullptr;
    HRESULT hr = Check();
    if (FAILED(hr))
      return hr;
    if (id == UIA_InvokePatternId && (IsButton() || IsHeaderItem()))
      return QueryInterface(__uuidof(IInvokeProvider),
                            reinterpret_cast<void **>(out));
    if (id == UIA_ValuePatternId && IsEdit())
      return QueryInterface(__uuidof(IValueProvider),
                            reinterpret_cast<void **>(out));
    if (id == UIA_ItemContainerPatternId && IsListRoot())
      return QueryInterface(__uuidof(IItemContainerProvider),
                            reinterpret_cast<void **>(out));
    if (id == UIA_VirtualizedItemPatternId && IsRow())
      return QueryInterface(__uuidof(IVirtualizedItemProvider),
                            reinterpret_cast<void **>(out));
    if (id == UIA_SelectionPatternId && IsListRoot())
      return QueryInterface(__uuidof(ISelectionProvider),
                            reinterpret_cast<void **>(out));
    if (id == UIA_SelectionItemPatternId && IsRow())
      return QueryInterface(__uuidof(ISelectionItemProvider),
                            reinterpret_cast<void **>(out));
    if (id == UIA_ScrollItemPatternId && IsRow())
      return QueryInterface(__uuidof(IScrollItemProvider),
                            reinterpret_cast<void **>(out));
    if (id == UIA_GridPatternId && IsListRoot())
      return QueryInterface(__uuidof(IGridProvider),
                            reinterpret_cast<void **>(out));
    if (id == UIA_GridItemPatternId && column_ >= 0)
      return QueryInterface(__uuidof(IGridItemProvider),
                            reinterpret_cast<void **>(out));
    return S_OK;
  }
  HRESULT STDMETHODCALLTYPE GetPropertyValue(PROPERTYID id,
                                             VARIANT *out) override {
    if (!out)
      return E_POINTER;
    VariantInit(out);
    HRESULT hr = Check();
    if (FAILED(hr))
      return hr;
    auto boolean = [&](bool value) {
      out->vt = VT_BOOL;
      out->boolVal = value ? VARIANT_TRUE : VARIANT_FALSE;
    };
    if (id == UIA_NamePropertyId) {
      out->vt = VT_BSTR;
      return Name(&out->bstrVal);
    }
    if (id == UIA_AutomationIdPropertyId) {
      out->vt = VT_BSTR;
      return String(
          &out->bstrVal,
          row_ < 0
              ? std::to_wstring(GetDlgCtrlID(state_->hwnd))
              : L"row-" + std::to_wstring(row_) +
                    (column_ < 0 ? L"" : L"-cell-" + std::to_wstring(column_)));
    }
    if (id == UIA_ClassNamePropertyId) {
      out->vt = VT_BSTR;
      return String(&out->bstrVal, state_->className);
    }
    if (id == UIA_FrameworkIdPropertyId) {
      out->vt = VT_BSTR;
      return String(&out->bstrVal, L"Win32");
    }
    if (id == UIA_ControlTypePropertyId) {
      out->vt = VT_I4;
      out->lVal =
          row_ < 0 && !(GetWindowLongPtrW(state_->hwnd, GWL_STYLE) & WS_CHILD)
              ? UIA_WindowControlTypeId
          : IsHeaderItem() ? UIA_HeaderItemControlTypeId
          : column_ >= 0   ? UIA_TextControlTypeId
          : IsRow()        ? UIA_DataItemControlTypeId
          : IsListRoot()   ? UIA_DataGridControlTypeId
          : IsButton()     ? UIA_ButtonControlTypeId
          : IsEdit()       ? UIA_EditControlTypeId
          : _wcsicmp(state_->className.c_str(), L"Static") == 0
              ? UIA_TextControlTypeId
          : _wcsicmp(state_->className.c_str(), WC_HEADERW) == 0
              ? UIA_HeaderControlTypeId
              : UIA_PaneControlTypeId;
    } else if (id == UIA_IsEnabledPropertyId)
      boolean(!!IsWindowEnabled(state_->hwnd));
    else if (id == UIA_IsOffscreenPropertyId)
      boolean(!OnScreen());
    else if (id == UIA_IsControlElementPropertyId ||
             id == UIA_IsContentElementPropertyId)
      boolean(true);
    else if (id == UIA_IsKeyboardFocusablePropertyId)
      boolean(column_ < 0 &&
              !!(GetWindowLongPtrW(state_->hwnd, GWL_STYLE) & WS_TABSTOP));
    else if (id == UIA_HasKeyboardFocusPropertyId) {
      GUITHREADINFO info{sizeof(info)};
      GetGUIThreadInfo(GetWindowThreadProcessId(state_->hwnd, nullptr), &info);
      boolean(info.hwndFocus == state_->hwnd &&
              (row_ < 0 ||
               !!ListView_GetItemState(state_->hwnd, row_, LVIS_FOCUSED)));
    } else if (id == UIA_NativeWindowHandlePropertyId && row_ < 0) {
      out->vt = VT_I4;
      out->lVal = static_cast<LONG>(reinterpret_cast<INT_PTR>(state_->hwnd));
    } else if (id == UIA_IsPasswordPropertyId)
      boolean(IsEdit() &&
              !!(GetWindowLongPtrW(state_->hwnd, GWL_STYLE) & ES_PASSWORD));
    else if (id == UIA_SelectionItemIsSelectedPropertyId && IsRow())
      boolean(!!ListView_GetItemState(state_->hwnd, row_, LVIS_SELECTED));
    return S_OK;
  }
  HRESULT STDMETHODCALLTYPE
  get_HostRawElementProvider(IRawElementProviderSimple **out) override {
    if (!out)
      return E_POINTER;
    *out = nullptr;
    HRESULT hr = Check();
    if (FAILED(hr))
      return hr;
    return row_ < 0 ? UiaHostProviderFromHwnd(state_->hwnd, out) : S_OK;
  }
  HRESULT ReturnFragment(Provider *node, IRawElementProviderFragment **out) {
    if (node)
      *out = static_cast<IRawElementProviderFragment *>(node);
    return S_OK;
  }
  HWND ChildHwnd(bool last) const {
    HWND child = GetWindow(state_->hwnd, GW_CHILD);
    if (last && child)
      child = GetWindow(child, GW_HWNDLAST);
    return child;
  }
  HRESULT STDMETHODCALLTYPE Navigate(
      NavigateDirection direction, IRawElementProviderFragment **out) override {
    if (!out)
      return E_POINTER;
    *out = nullptr;
    HRESULT hr = Check();
    if (FAILED(hr))
      return hr;
    if (IsHeader()) {
      int target = -1;
      if (row_ < 0 && (direction == NavigateDirection_FirstChild ||
                       direction == NavigateDirection_LastChild))
        target = direction == NavigateDirection_FirstChild ? 0 : Count() - 1;
      if (row_ >= 0 && direction == NavigateDirection_Parent)
        return ReturnFragment(Acquire(state_), out);
      if (row_ >= 0 && (direction == NavigateDirection_NextSibling ||
                        direction == NavigateDirection_PreviousSibling))
        target = row_ + (direction == NavigateDirection_NextSibling ? 1 : -1);
      if (target >= 0 && target < Count())
        return ReturnFragment(Acquire(state_, target), out);
      return S_OK;
    }
    if (row_ >= 0) {
      if (direction == NavigateDirection_Parent)
        return ReturnFragment(Acquire(state_, column_ < 0 ? -1 : row_), out);
      if (column_ >= 0) {
        int col =
            column_ + (direction == NavigateDirection_NextSibling ? 1 : -1);
        if ((direction == NavigateDirection_NextSibling ||
             direction == NavigateDirection_PreviousSibling) &&
            col >= 0 && col < Columns())
          return ReturnFragment(Acquire(state_, row_, col), out);
      } else if (direction == NavigateDirection_FirstChild ||
                 direction == NavigateDirection_LastChild) {
        if (Columns() > 0)
          return ReturnFragment(
              Acquire(state_, row_,
                      direction == NavigateDirection_FirstChild
                          ? 0
                          : Columns() - 1),
              out);
      } else {
        int row = row_ + (direction == NavigateDirection_NextSibling ? 1 : -1);
        int top = ListView_GetTopIndex(state_->hwnd),
            end = std::min(Count(),
                           top + ListView_GetCountPerPage(state_->hwnd) + 1);
        if ((direction == NavigateDirection_NextSibling ||
             direction == NavigateDirection_PreviousSibling) &&
            row >= top && row < end)
          return ReturnFragment(Acquire(state_, row), out);
      }
    } else if (direction == NavigateDirection_FirstChild ||
               direction == NavigateDirection_LastChild) {
      if (IsListRoot()) {
        if (Count()) {
          int top = ListView_GetTopIndex(state_->hwnd);
          int row =
              direction == NavigateDirection_FirstChild
                  ? top
                  : std::min(Count() - 1,
                             top + ListView_GetCountPerPage(state_->hwnd));
          return ReturnFragment(Acquire(state_, row), out);
        }
      }
    }
    // The native host stitches all HWND boundaries. Fragment navigation is only
    // for this control's windowless rows, cells and header items.
    return S_OK;
  }
  HRESULT STDMETHODCALLTYPE GetRuntimeId(SAFEARRAY **out) override {
    if (!out)
      return E_POINTER;
    *out = nullptr;
    HRESULT hr = Check();
    if (FAILED(hr))
      return hr;
    if (row_ < 0)
      return S_OK;
    int id[]{UiaAppendRuntimeId,
             static_cast<int>(std::get<0>(key_)),
             static_cast<int>(std::get<0>(key_) >> 32),
             static_cast<int>(std::get<1>(key_)),
             row_,
             column_};
    *out = SafeArrayCreateVector(VT_I4, 0, 6);
    if (!*out)
      return E_OUTOFMEMORY;
    for (LONG i = 0; i < 6; ++i)
      SafeArrayPutElement(*out, &i, &id[i]);
    return S_OK;
  }
  HRESULT STDMETHODCALLTYPE get_BoundingRectangle(UiaRect *out) override {
    if (!out)
      return E_POINTER;
    *out = {};
    HRESULT hr = Check();
    if (FAILED(hr))
      return hr;
    RECT r{};
    if (row_ < 0)
      GetWindowRect(state_->hwnd, &r);
    else {
      if (!ItemBounds(&r))
        return UIA_E_ELEMENTNOTAVAILABLE;
      MapWindowPoints(state_->hwnd, nullptr, reinterpret_cast<POINT *>(&r), 2);
    }
    *out = {static_cast<double>(r.left), static_cast<double>(r.top),
            static_cast<double>(r.right - r.left),
            static_cast<double>(r.bottom - r.top)};
    return S_OK;
  }
  HRESULT STDMETHODCALLTYPE GetEmbeddedFragmentRoots(SAFEARRAY **out) override {
    if (!out)
      return E_POINTER;
    *out = nullptr;
    return Check();
  }
  HRESULT STDMETHODCALLTYPE SetFocus() override {
    HRESULT hr = Check();
    if (FAILED(hr))
      return hr;
    if (!IsWindowEnabled(state_->hwnd))
      return UIA_E_ELEMENTNOTENABLED;
    if (IsList() && row_ >= 0) {
      ::SetFocus(state_->hwnd);
      ListView_SetItemState(state_->hwnd, -1, 0, LVIS_FOCUSED);
      ListView_SetItemState(state_->hwnd, row_, LVIS_FOCUSED, LVIS_FOCUSED);
      return S_OK;
    }
    ComPtr<IAccessible> native;
    hr = Delegate(native.out());
    if (FAILED(hr))
      return hr;
    return native->accSelect(SELFLAG_TAKEFOCUS, Child(row_ < 0 ? 0 : row_ + 1));
  }
  HRESULT STDMETHODCALLTYPE
  get_FragmentRoot(IRawElementProviderFragmentRoot **out) override {
    if (!out)
      return E_POINTER;
    *out = nullptr;
    HRESULT hr = Check();
    if (FAILED(hr))
      return hr;
    Provider *root = Acquire(state_);
    if (root)
      *out = static_cast<IRawElementProviderFragmentRoot *>(root);
    return S_OK;
  }
  HRESULT STDMETHODCALLTYPE ElementProviderFromPoint(
      double x, double y, IRawElementProviderFragment **out) override {
    if (!out)
      return E_POINTER;
    *out = nullptr;
    HRESULT hr = Check();
    if (FAILED(hr))
      return hr;
    POINT point{static_cast<LONG>(x), static_cast<LONG>(y)};
    ScreenToClient(state_->hwnd, &point);
    RECT client{};
    GetClientRect(state_->hwnd, &client);
    if (!PtInRect(&client, point))
      return S_OK;
    if (IsHeader() && row_ < 0) {
      HDHITTESTINFO hit{};
      hit.pt = point;
      const int column = static_cast<int>(SendMessageW(
          state_->hwnd, HDM_HITTEST, 0, reinterpret_cast<LPARAM>(&hit)));
      if (column >= 0)
        return ReturnFragment(Acquire(state_, column), out);
    } else if (IsListRoot()) {
      LVHITTESTINFO hit{};
      hit.pt = point;
      int row = ListView_SubItemHitTest(state_->hwnd, &hit);
      if (row >= 0)
        return ReturnFragment(Acquire(state_, row, hit.iSubItem), out);
    }
    AddRef();
    *out = static_cast<IRawElementProviderFragment *>(this);
    return S_OK;
  }
  HRESULT STDMETHODCALLTYPE
  GetFocus(IRawElementProviderFragment **out) override {
    if (!out)
      return E_POINTER;
    *out = nullptr;
    HRESULT hr = Check();
    if (FAILED(hr))
      return hr;
    GUITHREADINFO info{sizeof(info)};
    GetGUIThreadInfo(GetWindowThreadProcessId(state_->hwnd, nullptr), &info);
    if (info.hwndFocus == state_->hwnd) {
      int row = IsListRoot()
                    ? ListView_GetNextItem(state_->hwnd, -1, LVNI_FOCUSED)
                    : -1;
      return ReturnFragment(Acquire(state_, row), out);
    }
    // Focus in a child HWND belongs to a different fragment and its host.
    return S_OK;
  }
  HRESULT STDMETHODCALLTYPE Invoke() override {
    HRESULT hr = Check();
    if (FAILED(hr))
      return hr;
    if (!IsWindowEnabled(state_->hwnd))
      return UIA_E_ELEMENTNOTENABLED;
    if (IsHeaderItem()) {
      RECT r{};
      if (!Header_GetItemRect(state_->hwnd, row_, &r))
        return UIA_E_ELEMENTNOTAVAILABLE;
      LPARAM point = MAKELPARAM((r.left + r.right) / 2, (r.top + r.bottom) / 2);
      if (!PostMessageW(state_->hwnd, WM_LBUTTONDOWN, MK_LBUTTON, point))
        return HRESULT_FROM_WIN32(GetLastError());
      return PostMessageW(state_->hwnd, WM_LBUTTONUP, 0, point)
                 ? S_OK
                 : HRESULT_FROM_WIN32(GetLastError());
    }
    // Post the standard click message so a modal business action cannot block
    // the UIA caller.
    return PostMessageW(state_->hwnd, BM_CLICK, 0, 0)
               ? S_OK
               : HRESULT_FROM_WIN32(GetLastError());
  }
  HRESULT STDMETHODCALLTYPE SetValue(LPCWSTR value) override {
    if (!value)
      return E_INVALIDARG;
    HRESULT hr = Check();
    if (FAILED(hr))
      return hr;
    BOOL readonly = FALSE;
    hr = get_IsReadOnly(&readonly);
    if (FAILED(hr))
      return hr;
    if (readonly)
      return UIA_E_INVALIDOPERATION;
    if (!IsWindowEnabled(state_->hwnd))
      return UIA_E_ELEMENTNOTENABLED;
    ComPtr<IAccessible> native;
    hr = Delegate(native.out());
    if (FAILED(hr))
      return hr;
    BSTR str = SysAllocString(value);
    if (!str)
      return E_OUTOFMEMORY;
    hr = native->put_accValue(Child(), str);
    SysFreeString(str);
    return hr;
  }
  HRESULT STDMETHODCALLTYPE get_Value(BSTR *out) override {
    if (!out)
      return E_POINTER;
    *out = nullptr;
    ComPtr<IAccessible> native;
    HRESULT hr = Delegate(native.out());
    return FAILED(hr) ? hr : native->get_accValue(Child(), out);
  }
  HRESULT STDMETHODCALLTYPE get_IsReadOnly(BOOL *out) override {
    if (!out)
      return E_POINTER;
    HRESULT hr = Check();
    if (FAILED(hr))
      return hr;
    *out = !!(GetWindowLongPtrW(state_->hwnd, GWL_STYLE) & ES_READONLY);
    return S_OK;
  }
  HRESULT STDMETHODCALLTYPE
  FindItemByProperty(IRawElementProviderSimple *after, PROPERTYID property,
                     VARIANT value, IRawElementProviderSimple **out) override {
    if (!out)
      return E_POINTER;
    *out = nullptr;
    HRESULT hr = Check();
    if (FAILED(hr))
      return hr;
    if (property != 0 && property != UIA_NamePropertyId &&
        property != UIA_AutomationIdPropertyId &&
        property != UIA_SelectionItemIsSelectedPropertyId)
      return E_INVALIDARG;
    if ((property == UIA_NamePropertyId ||
         property == UIA_AutomationIdPropertyId) &&
        value.vt != VT_BSTR)
      return E_INVALIDARG;
    if (property == UIA_SelectionItemIsSelectedPropertyId &&
        value.vt != VT_BOOL)
      return E_INVALIDARG;
    int first = 0;
    if (after) {
      // Compare canonical identity without calling client COM while holding the
      // cache lock.
      ComPtr<IUnknown> identity;
      hr = after->QueryInterface(IID_PPV_ARGS(identity.out()));
      if (FAILED(hr))
        return hr;
      bool found = false;
      {
        std::lock_guard<std::mutex> lock(state_->mutex);
        for (const auto &pair : state_->nodes) {
          auto node = pair.second;
          if (static_cast<IUnknown *>(static_cast<IRawElementProviderSimple *>(
                  node)) == identity.p &&
              node->IsRow() && std::get<0>(node->key_) == std::get<0>(key_) &&
              std::get<1>(node->key_) == state_->dataVersion) {
            first = node->row_ + 1;
            found = true;
            break;
          }
        }
      }
      if (!found)
        return E_INVALIDARG;
    }
    for (int i = first, n = Count(); i < n; ++i) {
      bool match = property == 0;
      if (property == UIA_NamePropertyId)
        match = Text(i, 0) == (value.bstrVal ? value.bstrVal : L"");
      if (property == UIA_AutomationIdPropertyId)
        match = L"row-" + std::to_wstring(i) ==
                (value.bstrVal ? value.bstrVal : L"");
      if (property == UIA_SelectionItemIsSelectedPropertyId)
        match = !!ListView_GetItemState(state_->hwnd, i, LVIS_SELECTED) ==
                (value.boolVal != VARIANT_FALSE);
      if (match) {
        Provider *p = Acquire(state_, i);
        if (p)
          *out = static_cast<IRawElementProviderSimple *>(p);
        return S_OK;
      }
    }
    return S_OK;
  }
  HRESULT STDMETHODCALLTYPE Realize() override { return ScrollIntoView(); }
  HRESULT STDMETHODCALLTYPE ScrollIntoView() override {
    HRESULT hr = Check();
    if (FAILED(hr))
      return hr;
    return ListView_EnsureVisible(state_->hwnd, row_, FALSE)
               ? S_OK
               : UIA_E_ELEMENTNOTAVAILABLE;
  }
  HRESULT SelectState(bool selected, bool clear) {
    HRESULT hr = Check();
    if (FAILED(hr))
      return hr;
    if (!IsWindowEnabled(state_->hwnd))
      return UIA_E_ELEMENTNOTENABLED;
    if (clear)
      ListView_SetItemState(state_->hwnd, -1, 0, LVIS_SELECTED);
    ListView_SetItemState(state_->hwnd, row_, selected ? LVIS_SELECTED : 0,
                          LVIS_SELECTED);
    return S_OK;
  }
  HRESULT STDMETHODCALLTYPE Select() override {
    return SelectState(true, true);
  }
  HRESULT STDMETHODCALLTYPE AddToSelection() override {
    HRESULT hr = Check();
    if (FAILED(hr))
      return hr;
    if (GetWindowLongPtrW(state_->hwnd, GWL_STYLE) & LVS_SINGLESEL) {
      int selected = ListView_GetNextItem(state_->hwnd, -1, LVNI_SELECTED);
      if (selected >= 0 && selected != row_)
        return UIA_E_INVALIDOPERATION;
    }
    return SelectState(true, false);
  }
  HRESULT STDMETHODCALLTYPE RemoveFromSelection() override {
    return SelectState(false, false);
  }
  HRESULT STDMETHODCALLTYPE get_IsSelected(BOOL *out) override {
    if (!out)
      return E_POINTER;
    HRESULT hr = Check();
    if (FAILED(hr))
      return hr;
    *out = !!ListView_GetItemState(state_->hwnd, row_, LVIS_SELECTED);
    return S_OK;
  }
  HRESULT STDMETHODCALLTYPE
  get_SelectionContainer(IRawElementProviderSimple **out) override {
    return get_ContainingGrid(out);
  }
  HRESULT STDMETHODCALLTYPE get_CanSelectMultiple(BOOL *out) override {
    if (!out)
      return E_POINTER;
    HRESULT hr = Check();
    if (FAILED(hr))
      return hr;
    *out = !(GetWindowLongPtrW(state_->hwnd, GWL_STYLE) & LVS_SINGLESEL);
    return S_OK;
  }
  HRESULT STDMETHODCALLTYPE get_IsSelectionRequired(BOOL *out) override {
    if (!out)
      return E_POINTER;
    *out = FALSE;
    return Check();
  }
  HRESULT STDMETHODCALLTYPE GetSelection(SAFEARRAY **out) override {
    if (!out)
      return E_POINTER;
    *out = nullptr;
    HRESULT hr = Check();
    if (FAILED(hr))
      return hr;
    std::vector<int> rows;
    for (int row = -1;
         (row = ListView_GetNextItem(state_->hwnd, row, LVNI_SELECTED)) >= 0;)
      rows.push_back(row);
    *out =
        SafeArrayCreateVector(VT_UNKNOWN, 0, static_cast<ULONG>(rows.size()));
    if (!*out)
      return E_OUTOFMEMORY;
    for (LONG i = 0; i < static_cast<LONG>(rows.size()); ++i) {
      Provider *p = Acquire(state_, rows[i]);
      if (p) {
        SafeArrayPutElement(*out, &i,
                            static_cast<IRawElementProviderSimple *>(p));
        p->Release();
      }
    }
    return S_OK;
  }
  HRESULT STDMETHODCALLTYPE GetItem(int row, int column,
                                    IRawElementProviderSimple **out) override {
    if (!out)
      return E_POINTER;
    *out = nullptr;
    HRESULT hr = Check();
    if (FAILED(hr))
      return hr;
    if (row < 0 || row >= Count() || column < 0 || column >= Columns())
      return E_INVALIDARG;
    Provider *p = Acquire(state_, row, column);
    if (p)
      *out = static_cast<IRawElementProviderSimple *>(p);
    return S_OK;
  }
  HRESULT STDMETHODCALLTYPE get_RowCount(int *out) override {
    if (!out)
      return E_POINTER;
    HRESULT hr = Check();
    if (FAILED(hr))
      return hr;
    *out = Count();
    return S_OK;
  }
  HRESULT STDMETHODCALLTYPE get_ColumnCount(int *out) override {
    if (!out)
      return E_POINTER;
    HRESULT hr = Check();
    if (FAILED(hr))
      return hr;
    *out = Columns();
    return S_OK;
  }
  HRESULT STDMETHODCALLTYPE get_Row(int *out) override {
    if (!out)
      return E_POINTER;
    *out = row_;
    return Check();
  }
  HRESULT STDMETHODCALLTYPE get_Column(int *out) override {
    if (!out)
      return E_POINTER;
    *out = column_;
    return Check();
  }
  HRESULT STDMETHODCALLTYPE get_RowSpan(int *out) override {
    if (!out)
      return E_POINTER;
    *out = 1;
    return Check();
  }
  HRESULT STDMETHODCALLTYPE get_ColumnSpan(int *out) override {
    if (!out)
      return E_POINTER;
    *out = 1;
    return Check();
  }
  HRESULT STDMETHODCALLTYPE
  get_ContainingGrid(IRawElementProviderSimple **out) override {
    if (!out)
      return E_POINTER;
    *out = nullptr;
    HRESULT hr = Check();
    if (FAILED(hr))
      return hr;
    Provider *root = Acquire(state_);
    if (root)
      *out = static_cast<IRawElementProviderSimple *>(root);
    return S_OK;
  }

  // IDispatch routes through the IAccessible type library to this adapter,
  // never to an unwrapped delegate.
  HRESULT STDMETHODCALLTYPE GetTypeInfoCount(UINT *out) override {
    if (!out)
      return E_POINTER;
    *out = 1;
    return S_OK;
  }
  HRESULT STDMETHODCALLTYPE GetTypeInfo(UINT index, LCID,
                                        ITypeInfo **out) override {
    if (!out)
      return E_POINTER;
    *out = nullptr;
    if (index)
      return DISP_E_BADINDEX;
    ComPtr<ITypeLib> library;
    HRESULT hr = LoadRegTypeLib(LIBID_Accessibility, 1, 1,
                                LOCALE_SYSTEM_DEFAULT, library.out());
    return FAILED(hr) ? hr : library->GetTypeInfoOfGuid(IID_IAccessible, out);
  }
  HRESULT STDMETHODCALLTYPE GetIDsOfNames(REFIID, LPOLESTR *names, UINT count,
                                          LCID locale, DISPID *out) override {
    ComPtr<ITypeInfo> type;
    HRESULT hr = GetTypeInfo(0, locale, type.out());
    return FAILED(hr) ? hr : DispGetIDsOfNames(type.p, names, count, out);
  }
  HRESULT STDMETHODCALLTYPE Invoke(DISPID id, REFIID, LCID locale, WORD flags,
                                   DISPPARAMS *params, VARIANT *result,
                                   EXCEPINFO *exception, UINT *error) override {
    ComPtr<ITypeInfo> type;
    HRESULT hr = GetTypeInfo(0, locale, type.out());
    return FAILED(hr) ? hr
                      : DispInvoke(static_cast<IAccessible *>(this), type.p, id,
                                   flags, params, result, exception, error);
  }
  HRESULT AccChild(VARIANT child, Provider **out) {
    *out = nullptr;
    HRESULT hr = Check();
    if (FAILED(hr))
      return hr;
    if (child.vt != VT_I4 || child.lVal < 0)
      return E_INVALIDARG;
    if (!child.lVal) {
      AddRef();
      *out = this;
      return S_OK;
    }
    if (IsListRoot() || (IsHeader() && row_ < 0)) {
      if (child.lVal <= Count())
        *out = Acquire(state_, child.lVal - 1);
    } else if (IsRow()) {
      if (child.lVal <= Columns())
        *out = Acquire(state_, row_, child.lVal - 1);
    } else if (row_ < 0) {
      HWND h = ChildHwnd(false);
      for (long i = 1; h && i < child.lVal; ++i)
        h = GetWindow(h, GW_HWNDNEXT);
      if (auto state = Lookup(h))
        *out = Acquire(state);
    }
    return *out ? S_OK : E_INVALIDARG;
  }
  HRESULT STDMETHODCALLTYPE get_accParent(IDispatch **out) override {
    if (!out)
      return E_POINTER;
    *out = nullptr;
    HRESULT hr = Check();
    if (FAILED(hr))
      return hr;
    Provider *parent = nullptr;
    if (row_ >= 0)
      parent = Acquire(state_, column_ < 0 ? -1 : row_);
    else if (auto state = Lookup(GetParent(state_->hwnd)))
      parent = Acquire(state);
    if (parent)
      *out = static_cast<IAccessible *>(parent);
    return S_OK;
  }
  HRESULT STDMETHODCALLTYPE get_accChildCount(long *out) override {
    if (!out)
      return E_POINTER;
    *out = 0;
    HRESULT hr = Check();
    if (FAILED(hr))
      return hr;
    if (IsListRoot() || (IsHeader() && row_ < 0))
      *out = Count();
    else if (IsRow())
      *out = Columns();
    else if (row_ < 0)
      for (HWND h = ChildHwnd(false); h; h = GetWindow(h, GW_HWNDNEXT))
        ++*out;
    return S_OK;
  }
  HRESULT STDMETHODCALLTYPE get_accChild(VARIANT child,
                                         IDispatch **out) override {
    if (!out)
      return E_POINTER;
    *out = nullptr;
    Provider *p = nullptr;
    HRESULT hr = AccChild(child, &p);
    if (SUCCEEDED(hr))
      *out = static_cast<IAccessible *>(p);
    return hr;
  }
  HRESULT STDMETHODCALLTYPE get_accName(VARIANT child, BSTR *out) override {
    if (!out)
      return E_POINTER;
    *out = nullptr;
    ComPtr<Provider> p;
    HRESULT hr = AccChild(child, p.out());
    return FAILED(hr) ? hr : p->Name(out);
  }
  HRESULT STDMETHODCALLTYPE get_accValue(VARIANT child, BSTR *out) override {
    if (!out)
      return E_POINTER;
    *out = nullptr;
    ComPtr<Provider> p;
    HRESULT hr = AccChild(child, p.out());
    if (FAILED(hr))
      return hr;
    if (p->row_ >= 0)
      return p->Name(out);
    ComPtr<IAccessible> native;
    hr = p->Delegate(native.out());
    return FAILED(hr) ? hr : native->get_accValue(Child(), out);
  }
  HRESULT STDMETHODCALLTYPE get_accRole(VARIANT child, VARIANT *out) override {
    if (!out)
      return E_POINTER;
    VariantInit(out);
    ComPtr<Provider> p;
    HRESULT hr = AccChild(child, p.out());
    if (FAILED(hr))
      return hr;
    if (p->row_ >= 0) {
      out->vt = VT_I4;
      out->lVal = p->IsHeaderItem() ? ROLE_SYSTEM_COLUMNHEADER
                  : p->column_ < 0  ? ROLE_SYSTEM_LISTITEM
                                    : ROLE_SYSTEM_CELL;
      return S_OK;
    }
    ComPtr<IAccessible> native;
    hr = p->Delegate(native.out());
    return FAILED(hr) ? hr : native->get_accRole(Child(), out);
  }
  HRESULT STDMETHODCALLTYPE get_accState(VARIANT child, VARIANT *out) override {
    if (!out)
      return E_POINTER;
    VariantInit(out);
    ComPtr<Provider> p;
    HRESULT hr = AccChild(child, p.out());
    if (FAILED(hr))
      return hr;
    if (p->row_ >= 0) {
      out->vt = VT_I4;
      out->lVal =
          STATE_SYSTEM_SELECTABLE |
          (!p->OnScreen() ? STATE_SYSTEM_OFFSCREEN : 0) |
          (!IsWindowEnabled(p->state_->hwnd) ? STATE_SYSTEM_UNAVAILABLE : 0);
      if (ListView_GetItemState(p->state_->hwnd, p->row_, LVIS_SELECTED))
        out->lVal |= STATE_SYSTEM_SELECTED;
      return S_OK;
    }
    ComPtr<IAccessible> native;
    hr = p->Delegate(native.out());
    return FAILED(hr) ? hr : native->get_accState(Child(), out);
  }
#define NATIVE_STRING_METHOD(method)                                           \
  HRESULT STDMETHODCALLTYPE method(VARIANT child, BSTR *out) override {        \
    if (!out)                                                                  \
      return E_POINTER;                                                        \
    *out = nullptr;                                                            \
    ComPtr<Provider> p;                                                        \
    HRESULT hr = AccChild(child, p.out());                                     \
    if (FAILED(hr))                                                            \
      return hr;                                                               \
    if (p->row_ >= 0)                                                          \
      return S_FALSE;                                                          \
    ComPtr<IAccessible> native;                                                \
    hr = p->Delegate(native.out());                                            \
    return FAILED(hr) ? hr : native->method(Child(), out);                     \
  }
  NATIVE_STRING_METHOD(get_accDescription)
  NATIVE_STRING_METHOD(get_accHelp)
  NATIVE_STRING_METHOD(get_accKeyboardShortcut)
  NATIVE_STRING_METHOD(get_accDefaultAction)
#undef NATIVE_STRING_METHOD
  HRESULT STDMETHODCALLTYPE get_accHelpTopic(BSTR *file, VARIANT child,
                                             long *topic) override {
    if (!file || !topic)
      return E_POINTER;
    *file = nullptr;
    *topic = 0;
    ComPtr<Provider> p;
    HRESULT hr = AccChild(child, p.out());
    if (FAILED(hr))
      return hr;
    if (p->row_ >= 0)
      return S_FALSE;
    ComPtr<IAccessible> native;
    hr = p->Delegate(native.out());
    return FAILED(hr) ? hr : native->get_accHelpTopic(file, Child(), topic);
  }
  HRESULT STDMETHODCALLTYPE get_accFocus(VARIANT *out) override {
    if (!out)
      return E_POINTER;
    VariantInit(out);
    HRESULT checked = Check();
    if (FAILED(checked))
      return checked;
    GUITHREADINFO info{sizeof(info)};
    GetGUIThreadInfo(GetWindowThreadProcessId(state_->hwnd, nullptr), &info);
    if (IsChild(state_->hwnd, info.hwndFocus)) {
      if (auto focused = Lookup(info.hwndFocus)) {
        if (Provider *node = Acquire(focused)) {
          out->vt = VT_DISPATCH;
          out->pdispVal = static_cast<IAccessible *>(node);
          return S_OK;
        }
      }
    }
    IRawElementProviderFragment *f = nullptr;
    HRESULT hr = GetFocus(&f);
    if (FAILED(hr) || !f)
      return hr;
    out->vt = VT_DISPATCH;
    hr = f->QueryInterface(IID_IDispatch,
                           reinterpret_cast<void **>(&out->pdispVal));
    f->Release();
    return hr;
  }
  HRESULT STDMETHODCALLTYPE get_accSelection(VARIANT *out) override {
    if (!out)
      return E_POINTER;
    VariantInit(out);
    HRESULT hr = Check();
    if (FAILED(hr))
      return hr;
    if (IsListRoot()) {
      int row = ListView_GetNextItem(state_->hwnd, -1, LVNI_SELECTED);
      if (row >= 0) {
        auto p = Acquire(state_, row);
        if (p) {
          out->vt = VT_DISPATCH;
          out->pdispVal = static_cast<IAccessible *>(p);
        }
      }
    }
    return S_OK;
  }
  HRESULT STDMETHODCALLTYPE accSelect(long flags, VARIANT child) override {
    ComPtr<Provider> p;
    HRESULT hr = AccChild(child, p.out());
    if (FAILED(hr))
      return hr;
    if (p->IsList() && p->row_ >= 0) {
      const long selection =
          flags & (SELFLAG_TAKESELECTION | SELFLAG_ADDSELECTION |
                   SELFLAG_REMOVESELECTION);
      const long supported = SELFLAG_TAKEFOCUS | SELFLAG_TAKESELECTION |
                             SELFLAG_ADDSELECTION | SELFLAG_REMOVESELECTION |
                             SELFLAG_EXTENDSELECTION;
      if ((flags & ~supported) || (selection && (selection & (selection - 1))))
        return E_INVALIDARG;
      if (!IsWindowEnabled(p->state_->hwnd))
        return UIA_E_ELEMENTNOTENABLED;
      if ((flags & SELFLAG_EXTENDSELECTION) &&
          !(GetWindowLongPtrW(p->state_->hwnd, GWL_STYLE) & LVS_SINGLESEL)) {
        int anchor = ListView_GetSelectionMark(p->state_->hwnd);
        if (anchor < 0)
          anchor = p->row_;
        if (!(flags & (SELFLAG_ADDSELECTION | SELFLAG_REMOVESELECTION)))
          ListView_SetItemState(p->state_->hwnd, -1, 0, LVIS_SELECTED);
        const UINT state =
            (flags & SELFLAG_REMOVESELECTION) ? 0 : LVIS_SELECTED;
        for (int index = std::min(anchor, p->row_);
             index <= std::max(anchor, p->row_); ++index)
          ListView_SetItemState(p->state_->hwnd, index, state, LVIS_SELECTED);
      } else {
        if ((flags & SELFLAG_TAKESELECTION) ||
            (flags & SELFLAG_EXTENDSELECTION))
          hr = p->Select();
        else if (flags & SELFLAG_ADDSELECTION)
          hr = p->AddToSelection();
        else if (flags & SELFLAG_REMOVESELECTION)
          hr = p->RemoveFromSelection();
        if (FAILED(hr))
          return hr;
        if (flags & (SELFLAG_TAKESELECTION | SELFLAG_EXTENDSELECTION))
          ListView_SetSelectionMark(p->state_->hwnd, p->row_);
      }
      return (flags & SELFLAG_TAKEFOCUS) ? p->SetFocus() : S_OK;
    }
    ComPtr<IAccessible> native;
    hr = p->Delegate(native.out());
    return FAILED(hr)
               ? hr
               : native->accSelect(flags, Child(p->row_ < 0 ? 0 : p->row_ + 1));
  }
  HRESULT STDMETHODCALLTYPE accLocation(long *x, long *y, long *width,
                                        long *height, VARIANT child) override {
    if (!x || !y || !width || !height)
      return E_POINTER;
    ComPtr<Provider> p;
    HRESULT hr = AccChild(child, p.out());
    if (FAILED(hr))
      return hr;
    UiaRect r{};
    hr = p->get_BoundingRectangle(&r);
    if (SUCCEEDED(hr)) {
      *x = static_cast<long>(r.left);
      *y = static_cast<long>(r.top);
      *width = static_cast<long>(r.width);
      *height = static_cast<long>(r.height);
    }
    return hr;
  }
  HRESULT STDMETHODCALLTYPE accNavigate(long direction, VARIANT child,
                                        VARIANT *out) override {
    if (!out)
      return E_POINTER;
    VariantInit(out);
    ComPtr<Provider> p;
    HRESULT hr = AccChild(child, p.out());
    if (FAILED(hr))
      return hr;
    // MSAA explicitly enumerates all logical rows; UIA fragment navigation only
    // visits the viewport.
    Provider *result = nullptr;
    if (p->IsListRoot() &&
        (direction == NAVDIR_FIRSTCHILD || direction == NAVDIR_LASTCHILD)) {
      if (p->Count())
        result = Acquire(p->state_,
                         direction == NAVDIR_FIRSTCHILD ? 0 : p->Count() - 1);
    } else if (p->IsRow() &&
               (direction == NAVDIR_NEXT || direction == NAVDIR_PREVIOUS)) {
      int row = p->row_ + (direction == NAVDIR_NEXT ? 1 : -1);
      if (row >= 0 && row < p->Count())
        result = Acquire(p->state_, row);
    } else if (p->row_ < 0 &&
               (direction == NAVDIR_NEXT || direction == NAVDIR_PREVIOUS)) {
      auto state = Lookup(GetWindow(p->state_->hwnd, direction == NAVDIR_NEXT
                                                         ? GW_HWNDNEXT
                                                         : GW_HWNDPREV));
      if (state)
        result = Acquire(state);
    } else if (p->row_ < 0 && !p->IsHeader() &&
               (direction == NAVDIR_FIRSTCHILD ||
                direction == NAVDIR_LASTCHILD)) {
      if (auto childState = Lookup(p->ChildHwnd(direction == NAVDIR_LASTCHILD)))
        result = Acquire(childState);
    } else {
      NavigateDirection nav;
      if (direction == NAVDIR_FIRSTCHILD)
        nav = NavigateDirection_FirstChild;
      else if (direction == NAVDIR_LASTCHILD)
        nav = NavigateDirection_LastChild;
      else if (direction == NAVDIR_NEXT)
        nav = NavigateDirection_NextSibling;
      else if (direction == NAVDIR_PREVIOUS)
        nav = NavigateDirection_PreviousSibling;
      else
        return E_INVALIDARG;
      IRawElementProviderFragment *fragment = nullptr;
      hr = p->Navigate(nav, &fragment);
      if (FAILED(hr))
        return hr;
      if (fragment) {
        out->vt = VT_DISPATCH;
        hr = fragment->QueryInterface(
            IID_IDispatch, reinterpret_cast<void **>(&out->pdispVal));
        fragment->Release();
        return hr;
      }
    }
    if (result) {
      out->vt = VT_DISPATCH;
      out->pdispVal = static_cast<IAccessible *>(result);
      return S_OK;
    }
    return S_FALSE;
  }
  HRESULT STDMETHODCALLTYPE accHitTest(long x, long y, VARIANT *out) override {
    if (!out)
      return E_POINTER;
    VariantInit(out);
    HRESULT hr = Check();
    if (FAILED(hr))
      return hr;
    UiaRect rect{};
    hr = get_BoundingRectangle(&rect);
    if (FAILED(hr))
      return hr;
    if (x < rect.left || y < rect.top || x >= rect.left + rect.width ||
        y >= rect.top + rect.height)
      return S_FALSE;
    if (row_ < 0 && !IsListRoot() && !IsHeader()) {
      POINT point{x, y};
      ScreenToClient(state_->hwnd, &point);
      HWND child =
          ChildWindowFromPointEx(state_->hwnd, point, CWP_SKIPINVISIBLE);
      if (child && child != state_->hwnd) {
        if (auto target = Lookup(child)) {
          if (Provider *node = Acquire(target)) {
            out->vt = VT_DISPATCH;
            out->pdispVal = static_cast<IAccessible *>(node);
            return S_OK;
          }
        }
      }
    }
    IRawElementProviderFragment *fragment = nullptr;
    hr = ElementProviderFromPoint(x, y, &fragment);
    if (FAILED(hr) || !fragment)
      return hr;
    out->vt = VT_DISPATCH;
    hr = fragment->QueryInterface(IID_IDispatch,
                                  reinterpret_cast<void **>(&out->pdispVal));
    fragment->Release();
    return hr;
  }
  HRESULT STDMETHODCALLTYPE accDoDefaultAction(VARIANT child) override {
    ComPtr<Provider> p;
    HRESULT hr = AccChild(child, p.out());
    if (FAILED(hr))
      return hr;
    if (p->IsButton() || p->IsHeaderItem())
      return p->Invoke();
    ComPtr<IAccessible> native;
    hr = p->Delegate(native.out());
    return FAILED(hr) ? hr
                      : native->accDoDefaultAction(
                            Child(p->row_ < 0 ? 0 : p->row_ + 1));
  }
  HRESULT STDMETHODCALLTYPE put_accName(VARIANT, BSTR) override {
    HRESULT hr = Check();
    return FAILED(hr) ? hr : E_NOTIMPL;
  }
  HRESULT STDMETHODCALLTYPE put_accValue(VARIANT child, BSTR value) override {
    ComPtr<Provider> p;
    HRESULT hr = AccChild(child, p.out());
    if (FAILED(hr))
      return hr;
    return p->IsEdit() ? p->SetValue(value) : E_NOTIMPL;
  }

private:
  ~Provider() { --state_->live; }
  std::atomic<ULONG> refs_{1};
  std::shared_ptr<State> state_;
  Key key_;
  int row_, column_;
};

Provider *Acquire(const std::shared_ptr<State> &state, int row, int column) {
  if (!state)
    return nullptr;
  std::lock_guard<std::mutex> lock(state->mutex);
  if (state->dead)
    return nullptr;
  if (!state->active) {
    state->epoch = ++nextEpoch;
    state->active = true;
    if (cleanupWindow)
      PostMessageW(cleanupWindow, ScheduleMessage, 0, 0);
  }
  state->lastUse = GetTickCount64();
  Key key{state->epoch.load(), row < 0 ? 0 : state->dataVersion.load(), row,
          column};
  auto it = state->nodes.find(key);
  if (it != state->nodes.end()) {
    it->second->AddRef();
    return it->second;
  }
  Provider *provider = new (std::nothrow) Provider(state, key, row, column);
  if (!provider)
    return nullptr;
  state->nodes.emplace(key, provider);
  if (row < 0) {
    state->root = provider;
    provider->AddRef();
  }
  return provider;
}

void Retire(const std::shared_ptr<State> &state) {
  std::vector<Provider *> nodes;
  Provider *ownedRoot = nullptr;
  {
    std::lock_guard<std::mutex> lock(state->mutex);
    if (!state->active)
      return;
    const auto epoch = state->epoch.load();
    state->active = false;
    ++state->retired;
    ownedRoot = state->root;
    state->root = nullptr;
    for (const auto &pair : state->nodes)
      if (std::get<0>(pair.first) == epoch) {
        pair.second->AddRef();
        nodes.push_back(pair.second);
      }
  }
  // Disconnect later on a posted message, outside any SendMessage call stack.
  {
    std::lock_guard<std::mutex> lock(cleanupMutex);
    pendingCleanup.insert(pendingCleanup.end(), nodes.begin(), nodes.end());
  }
  if (ownedRoot)
    ownedRoot->Release();
  if (cleanupWindow)
    PostMessageW(cleanupWindow, CleanupMessage, 0, 0);
}
void DrainCleanup() {
  if (InSendMessageEx(nullptr) != ISMEX_NOSEND) {
    if (cleanupWindow)
      PostMessageW(cleanupWindow, CleanupMessage, 0, 0);
    return;
  }
  std::vector<Provider *> nodes;
  {
    std::lock_guard<std::mutex> lock(cleanupMutex);
    nodes.swap(pendingCleanup);
  }
  for (Provider *node : nodes) {
    UiaDisconnectProvider(static_cast<IRawElementProviderSimple *>(node));
    node->Release();
  }
}
LRESULT CALLBACK CleanupProc(HWND hwnd, UINT message, WPARAM wp, LPARAM lp) {
  if (message == CleanupMessage) {
    DrainCleanup();
    return 0;
  }
  if (message == ScheduleMessage) {
    SetTimer(hwnd, RetirementTimerId, 1000, nullptr);
    return 0;
  }
  if (message == WM_TIMER && wp == RetirementTimerId) {
    std::vector<std::shared_ptr<State>> snapshot;
    {
      std::lock_guard<std::mutex> lock(statesMutex);
      for (const auto &pair : states)
        snapshot.push_back(pair.second);
    }
    bool active = false;
    const auto now = GetTickCount64();
    for (const auto &state : snapshot) {
      if (state->active && now - state->lastUse.load() >= IdleTimeoutMs)
        Retire(state);
      active = active || state->active.load();
    }
    if (!active)
      KillTimer(hwnd, RetirementTimerId);
    return 0;
  }
  return DefWindowProcW(hwnd, message, wp, lp);
}
LRESULT CALLBACK Subclass(HWND hwnd, UINT message, WPARAM wp, LPARAM lp,
                          UINT_PTR, DWORD_PTR) {
  auto state = Lookup(hwnd);
  if (!state)
    return DefSubclassProc(hwnd, message, wp, lp);
  if (message == DiagnosticsMessage) {
    switch (wp) {
    case 0:
      return state->active;
    case 1:
      return static_cast<LRESULT>(state->live.load());
    case 2:
      return static_cast<LRESULT>(state->created.load());
    case 3:
      return static_cast<LRESULT>(state->roots.load());
    case 4:
      return static_cast<LRESULT>(state->roots.load());
    case 5:
      return static_cast<LRESULT>(state->retired.load());
    case 6:
      return static_cast<LRESULT>(state->epoch.load());
    case 7:
      return 0;
    case 8:
      return static_cast<LRESULT>(state->delegates.load());
    case 9:
      return 0xA11;
    default:
      return 0;
    }
  }
  if (message == WM_GETOBJECT) {
    const DWORD object = static_cast<DWORD>(lp);
    if (object == static_cast<DWORD>(UiaRootObjectId) ||
        object == static_cast<DWORD>(OBJID_CLIENT)) {
      Provider *root = Acquire(state);
      if (!root)
        return 0;
      LRESULT result =
          object == static_cast<DWORD>(UiaRootObjectId)
              ? UiaReturnRawElementProvider(
                    hwnd, wp, lp,
                    static_cast<IRawElementProviderSimple *>(root))
              : LresultFromObject(IID_IAccessible, wp,
                                  static_cast<IAccessible *>(root));
      root->Release();
      return result;
    }
  }
  if (message == WM_NCDESTROY) {
    state->dead = true;
    KillTimer(hwnd, RetirementTimerId);
    RemoveWindowSubclass(hwnd, Subclass, SubclassId);
    {
      std::lock_guard<std::mutex> lock(statesMutex);
      states.erase(hwnd);
    }
    Retire(state);
    return DefSubclassProc(hwnd, message, wp, lp);
  }
  if (_wcsicmp(state->className.c_str(), WC_LISTVIEWW) == 0 &&
      (message == LVM_DELETEALLITEMS || message == LVM_DELETEITEM ||
       message == LVM_INSERTITEMW || message == LVM_INSERTITEMA ||
       message == LVM_SORTITEMS || message == LVM_SORTITEMSEX ||
       message == LVM_SETITEMCOUNT))
    ++state->dataVersion;
  return DefSubclassProc(hwnd, message, wp, lp);
}
} // namespace

void Attach(HWND hwnd) {
  if (!hwnd || !IsWindow(hwnd) ||
      GetWindowThreadProcessId(hwnd, nullptr) != GetCurrentThreadId())
    return;
  if (!cleanupWindow) {
    WNDCLASSW wc{};
    wc.lpfnWndProc = CleanupProc;
    wc.hInstance = GetModuleHandleW(nullptr);
    wc.lpszClassName = L"SupplyChainLazyAccessibilityCleanup";
    RegisterClassW(&wc);
    cleanupWindow =
        CreateWindowExW(0, wc.lpszClassName, L"", 0, 0, 0, 0, 0, HWND_MESSAGE,
                        nullptr, wc.hInstance, nullptr);
  }
  if (!Lookup(hwnd)) {
    auto state = std::make_shared<State>(hwnd);
    if (SetWindowSubclass(hwnd, Subclass, SubclassId, 0)) {
      {
        std::lock_guard<std::mutex> lock(statesMutex);
        states.emplace(hwnd, std::move(state));
      }
    }
  }
  for (HWND child = GetWindow(hwnd, GW_CHILD); child;
       child = GetWindow(child, GW_HWNDNEXT))
    Attach(child);
}
void Detach(HWND hwnd) {
  auto state = Lookup(hwnd);
  if (!state)
    return;
  state->dead = true;
  KillTimer(hwnd, RetirementTimerId);
  RemoveWindowSubclass(hwnd, Subclass, SubclassId);
  {
    std::lock_guard<std::mutex> lock(statesMutex);
    states.erase(hwnd);
  }
  Retire(state);
}
void Invalidate(HWND hwnd) {
  if (auto state = Lookup(hwnd)) {
    ++state->dataVersion;
    Retire(state);
  }
}
void Shutdown() {
  std::vector<HWND> windows;
  {
    std::lock_guard<std::mutex> lock(statesMutex);
    for (const auto &pair : states)
      windows.push_back(pair.first);
  }
  for (HWND hwnd : windows)
    Detach(hwnd);
  DrainCleanup();
  if (cleanupWindow) {
    DestroyWindow(cleanupWindow);
    cleanupWindow = nullptr;
  }
}
} // namespace lazy_a11y
