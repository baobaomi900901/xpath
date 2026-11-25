#define WIN32_LEAN_AND_MEAN
// clang-format off: Windows SDK automation headers require Windows types first.
#include <windows.h>
#include <oleacc.h>
#include <UIAutomation.h>
// clang-format on

#include <array>
#include <cerrno>
#include <cstdlib>
#include <cwchar>
#include <cwctype>
#include <iomanip>
#include <iostream>
#include <limits>
#include <string>

namespace {
// This is the read-only wire contract, deliberately independent of the
// provider.
constexpr UINT DiagnosticsMessage = WM_APP + 0x3A;
constexpr WPARAM DiagnosticsHandshakeSelector = 9;
constexpr DWORD_PTR DiagnosticsHandshakeValue = 0xA11;
constexpr DWORD StatsTimeoutMs = 2000;
constexpr wchar_t DefaultTitle[] = L"供应商报价管理 — 库存补货任务";
constexpr std::array<const char *, 9> CounterNames{"active",
                                                   "live_application_nodes",
                                                   "total_nodes_created",
                                                   "root_objects_created",
                                                   "activation_epochs",
                                                   "retired_epochs",
                                                   "current_generation",
                                                   "application_events_raised",
                                                   "native_delegate_creations"};

template <class T> class ComPtr {
public:
  ~ComPtr() { reset(); }
  ComPtr() = default;
  ComPtr(const ComPtr &) = delete;
  ComPtr &operator=(const ComPtr &) = delete;
  T *get() const { return value_; }
  T *operator->() const { return value_; }
  T **put() {
    reset();
    return &value_;
  }
  void reset() {
    if (value_) {
      value_->Release();
      value_ = nullptr;
    }
  }

private:
  T *value_ = nullptr;
};

struct Options {
  std::wstring title = DefaultTitle;
  std::wstring mode = L"stats";
  HWND hwnd = nullptr;
  DWORD holdMs = 0;
  DWORD waitIdleMs = 0;
};

std::string Utf8(const wchar_t *value, int length = -1) {
  if (!value)
    return "";
  const int size = WideCharToMultiByte(CP_UTF8, 0, value, length, nullptr, 0,
                                       nullptr, nullptr);
  if (size <= 0)
    return "";
  std::string result(size, '\0');
  WideCharToMultiByte(CP_UTF8, 0, value, length, result.data(), size, nullptr,
                      nullptr);
  if (length == -1)
    result.pop_back();
  return result;
}

void PrintHr(const char *operation, HRESULT hr) {
  std::cout << operation << " HRESULT=0x" << std::hex << std::setw(8)
            << std::setfill('0') << static_cast<unsigned long>(hr) << std::dec
            << std::setfill(' ') << '\n';
}

bool ParseNumber(const wchar_t *text, unsigned long long limit, int base,
                 unsigned long long &value) {
  if (!text || !*text || *text == L'-' || *text == L'+' || iswspace(*text))
    return false;
  errno = 0;
  wchar_t *end = nullptr;
  value = std::wcstoull(text, &end, base);
  return !errno && end != text && *end == L'\0' && value <= limit;
}

void Usage() {
  std::cout
      << "Usage: supplier-accessibility-probe [--hwnd DECIMAL_OR_0xHEX | "
         "--title TITLE]\n"
         "       [--mode stats|uia-root|uia-child|msaa-root|msaa-child]\n"
         "       [--hold-ms 0..60000] [--wait-idle-ms 0..60000]\n"
         "Default mode: stats; default title: "
      << Utf8(DefaultTitle) << '\n'
      << "stats uses only the private diagnostics message, never "
         "WM_GETOBJECT.\n"
         "hold-ms retains acquired client references; wait-idle-ms waits after "
         "release.\n"
         "All waits occur in this probe, never on the supplier UI thread.\n";
}

bool ParseOptions(int argc, wchar_t **argv, Options &options) {
  for (int index = 1; index < argc; ++index) {
    const std::wstring arg = argv[index];
    if (index + 1 == argc)
      return false;
    const wchar_t *value = argv[++index];
    if (arg == L"--title") {
      if (!*value)
        return false;
      options.title = value;
    } else if (arg == L"--mode") {
      options.mode = value;
    } else if (arg == L"--hwnd") {
      unsigned long long number = 0;
      const int base =
          value[0] == L'0' && (value[1] == L'x' || value[1] == L'X') ? 16 : 10;
      if (!ParseNumber(value, std::numeric_limits<UINT_PTR>::max(), base,
                       number) ||
          !number)
        return false;
      options.hwnd = reinterpret_cast<HWND>(static_cast<UINT_PTR>(number));
    } else if (arg == L"--hold-ms" || arg == L"--wait-idle-ms") {
      unsigned long long number = 0;
      if (!ParseNumber(value, 60000, 10, number))
        return false;
      if (arg == L"--hold-ms")
        options.holdMs = static_cast<DWORD>(number);
      else
        options.waitIdleMs = static_cast<DWORD>(number);
    } else
      return false;
  }
  return options.mode == L"stats" || options.mode == L"uia-root" ||
         options.mode == L"uia-child" || options.mode == L"msaa-root" ||
         options.mode == L"msaa-child";
}

bool PrintStats(HWND hwnd, const char *phase) {
  DWORD_PTR handshake = 0;
  SetLastError(ERROR_SUCCESS);
  if (!SendMessageTimeoutW(hwnd, DiagnosticsMessage,
                           DiagnosticsHandshakeSelector, 0,
                           SMTO_ABORTIFHUNG | SMTO_BLOCK | SMTO_ERRORONEXIT,
                           StatsTimeoutMs, &handshake)) {
    std::cerr << "stats " << phase
              << " protocol handshake failed, Win32 error=" << GetLastError()
              << '\n';
    return false;
  }
  if (handshake != DiagnosticsHandshakeValue) {
    std::cerr << "stats " << phase
              << " target does not support the application diagnostics protocol"
              << " (selector 9 must return 0xA11).\n";
    return false;
  }
  std::array<DWORD_PTR, CounterNames.size()> counters{};
  for (size_t index = 0; index < counters.size(); ++index) {
    SetLastError(ERROR_SUCCESS);
    if (!SendMessageTimeoutW(hwnd, DiagnosticsMessage,
                             static_cast<WPARAM>(index), 0,
                             SMTO_ABORTIFHUNG | SMTO_BLOCK | SMTO_ERRORONEXIT,
                             StatsTimeoutMs, &counters[index])) {
      std::cerr << "stats " << phase << " selector=" << index
                << " failed, Win32 error=" << GetLastError() << '\n';
      return false;
    }
  }
  std::cout << "stats " << phase;
  for (size_t index = 0; index < counters.size(); ++index)
    std::cout << ' ' << CounterNames[index] << '=' << counters[index];
  std::cout << '\n';
  return true;
}

bool PrintUiaName(IUIAutomationElement *element, const char *label) {
  BSTR name = nullptr;
  const HRESULT hr = element->get_CurrentName(&name);
  PrintHr(label, hr);
  if (SUCCEEDED(hr))
    std::cout << label << " name=\""
              << Utf8(name, static_cast<int>(SysStringLen(name))) << "\"\n";
  SysFreeString(name);
  return SUCCEEDED(hr);
}

bool PrintMsaaName(IAccessible *accessible, LONG childId, const char *label) {
  VARIANT child;
  VariantInit(&child);
  child.vt = VT_I4;
  child.lVal = childId;
  BSTR name = nullptr;
  const HRESULT hr = accessible->get_accName(child, &name);
  PrintHr(label, hr);
  if (SUCCEEDED(hr))
    std::cout << label << " name=\""
              << Utf8(name, static_cast<int>(SysStringLen(name))) << "\"\n";
  SysFreeString(name);
  return SUCCEEDED(hr);
}

bool AcquireUia(HWND hwnd, bool child, ComPtr<IUIAutomation> &automation,
                ComPtr<IUIAutomationElement> &root,
                ComPtr<IUIAutomationElement> &node,
                ComPtr<IUIAutomationTreeWalker> &walker) {
  HRESULT hr =
      CoCreateInstance(CLSID_CUIAutomation, nullptr, CLSCTX_INPROC_SERVER,
                       IID_PPV_ARGS(automation.put()));
  PrintHr("UIA CoCreateInstance(CUIAutomation)", hr);
  if (FAILED(hr))
    return false;
  hr = automation->ElementFromHandle(hwnd, root.put());
  PrintHr("UIA ElementFromHandle", hr);
  if (FAILED(hr) || !root.get())
    return false;
  if (!PrintUiaName(root.get(), "UIA root"))
    return false;
  if (!child)
    return true;
  hr = automation->get_RawViewWalker(walker.put());
  PrintHr("UIA RawViewWalker", hr);
  if (FAILED(hr) || !walker.get())
    return false;
  hr = walker->GetFirstChildElement(root.get(), node.put());
  PrintHr("UIA GetFirstChildElement", hr);
  if (FAILED(hr) || !node.get()) {
    if (SUCCEEDED(hr))
      std::cerr << "UIA root has no first child.\n";
    return false;
  }
  return PrintUiaName(node.get(), "UIA child");
}

bool AcquireMsaa(HWND hwnd, bool child, ComPtr<IAccessible> &root,
                 ComPtr<IDispatch> &dispatch, ComPtr<IAccessible> &node) {
  HRESULT hr = AccessibleObjectFromWindow(
      hwnd, static_cast<DWORD>(OBJID_CLIENT), IID_IAccessible,
      reinterpret_cast<void **>(root.put()));
  PrintHr("MSAA AccessibleObjectFromWindow(OBJID_CLIENT)", hr);
  if (FAILED(hr) || !root.get())
    return false;
  if (!PrintMsaaName(root.get(), CHILDID_SELF, "MSAA root"))
    return false;
  if (!child)
    return true;
  LONG count = 0;
  hr = root->get_accChildCount(&count);
  PrintHr("MSAA get_accChildCount", hr);
  if (FAILED(hr) || count < 1) {
    if (SUCCEEDED(hr))
      std::cerr << "MSAA root has no first child.\n";
    return false;
  }
  VARIANT id;
  VariantInit(&id);
  id.vt = VT_I4;
  id.lVal = 1;
  hr = root->get_accChild(id, dispatch.put());
  PrintHr("MSAA get_accChild(1)", hr);
  if (FAILED(hr))
    return false;
  if (!dispatch.get()) {
    std::cout << "MSAA first child is a simple child ID (held by its root).\n";
    return PrintMsaaName(root.get(), 1, "MSAA child");
  }
  hr = dispatch->QueryInterface(IID_PPV_ARGS(node.put()));
  PrintHr("MSAA child QueryInterface(IAccessible)", hr);
  return SUCCEEDED(hr) && node.get() &&
         PrintMsaaName(node.get(), CHILDID_SELF, "MSAA child");
}
} // namespace

int wmain(int argc, wchar_t **argv) {
  if (argc == 2 &&
      (std::wstring(argv[1]) == L"--help" || std::wstring(argv[1]) == L"-h")) {
    Usage();
    return 0;
  }
  Options options;
  if (!ParseOptions(argc, argv, options)) {
    Usage();
    return 2;
  }
  HWND hwnd =
      options.hwnd ? options.hwnd : FindWindowW(nullptr, options.title.c_str());
  DWORD processId = 0;
  if (!hwnd || !IsWindow(hwnd) || !GetWindowThreadProcessId(hwnd, &processId)) {
    std::cerr << "No valid target window. Start the supplier app or pass "
                 "--hwnd/--title.\n";
    return 3;
  }
  std::cout << "target HWND=0x" << std::hex << reinterpret_cast<UINT_PTR>(hwnd)
            << std::dec << " process_id=" << processId
            << " mode=" << Utf8(options.mode.c_str()) << '\n'
            << "Counters are per target HWND and count application "
               "objects/events only.\n"
               "Windows-owned host/non-client proxies are not counted. "
               "Automatic UIA queries\n"
               "can increase application counters by requesting additional "
               "provider data.\n"
               "Existing assistive clients may already have activated the "
               "target. No zero baseline is assumed.\n"
               "Counters are read separately and may change while other "
               "clients are active.\n";
  if (!PrintStats(hwnd, "before"))
    return 4;
  const HRESULT comHr = CoInitializeEx(nullptr, COINIT_MULTITHREADED);
  PrintHr("CoInitializeEx(MTA)", comHr);
  if (FAILED(comHr))
    return 5;

  bool succeeded = true;
  {
    ComPtr<IUIAutomation> automation;
    ComPtr<IUIAutomationElement> uiaRoot, uiaChild;
    ComPtr<IUIAutomationTreeWalker> walker;
    ComPtr<IAccessible> msaaRoot, msaaChild;
    ComPtr<IDispatch> msaaDispatch;
    if (options.mode == L"uia-root" || options.mode == L"uia-child")
      succeeded = AcquireUia(hwnd, options.mode == L"uia-child", automation,
                             uiaRoot, uiaChild, walker);
    else if (options.mode == L"msaa-root" || options.mode == L"msaa-child")
      succeeded = AcquireMsaa(hwnd, options.mode == L"msaa-child", msaaRoot,
                              msaaDispatch, msaaChild);
    if (options.holdMs) {
      std::cout << "holding client references for " << options.holdMs << " ms\n"
                << std::flush;
      Sleep(options.holdMs);
    }
    if (!PrintStats(hwnd, "held"))
      succeeded = false;
  }
  CoUninitialize();
  std::cout << "client references released; waiting " << options.waitIdleMs
            << " ms\n"
            << std::flush;
  if (options.waitIdleMs)
    Sleep(options.waitIdleMs);
  if (!PrintStats(hwnd, "after"))
    succeeded = false;
  return succeeded ? 0 : 6;
}
