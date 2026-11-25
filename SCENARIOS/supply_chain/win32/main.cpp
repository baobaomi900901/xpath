#include <windows.h>

#include "model.h"
#include "lazy_accessibility.h"
#include <ole2.h>
#include <commctrl.h>
#include <commdlg.h>
#include <fstream>
#include <memory>
#include <set>
#include <shellapi.h>
#include <thread>

#include <winhttp.h>
#pragma comment(lib, "comctl32.lib")
constexpr UINT DONE = WM_APP + 1;
constexpr UINT_PTR LOAD_TIMER = 1;
constexpr int ENTER = 106;
WorkspaceLoad workspace;
HWND enterBtn;
constexpr int IMPORT = 101, QUERY = 102, EXPORT = 103, DETAIL = 104, EXIT = 105;
HWND win, inventory, quotes, material, status, importBtn, queryBtn, exportBtn,
    detailBtn, invLabel, quoteLabel, materialLabel;
HFONT font;
std::wstring base = L"http://127.0.0.1:8765";
Table stock, offers;
std::set<std::string> queried;
std::thread worker;
bool busy = false, ascending = true;
UINT dpi = 96;
std::wstring wide(const std::string &s) {
  if (s.empty())
    return {};
  int n = MultiByteToWideChar(CP_UTF8, MB_ERR_INVALID_CHARS, s.data(),
                              (int)s.size(), nullptr, 0);
  if (!n)
    throw std::runtime_error("Invalid UTF-8 response");
  std::wstring r(n, 0);
  MultiByteToWideChar(CP_UTF8, 0, s.data(), (int)s.size(), r.data(), n);
  return r;
}
std::string utf8(const std::wstring &s) {
  int n = WideCharToMultiByte(CP_UTF8, 0, s.data(), (int)s.size(), nullptr, 0,
                              nullptr, nullptr);
  std::string r(n, 0);
  WideCharToMultiByte(CP_UTF8, 0, s.data(), (int)s.size(), r.data(), n, nullptr,
                      nullptr);
  return r;
}
struct Internet {
  HINTERNET h = nullptr;
  Internet(HINTERNET p) : h(p) {
    if (!h)
      throw std::runtime_error("WinHTTP initialization failed");
  }
  ~Internet() {
    if (h)
      WinHttpCloseHandle(h);
  }
  operator HINTERNET() const { return h; }
};
std::string request(const std::wstring &path, const std::string &body = {},
                    bool post = false) {
  URL_COMPONENTS u{};
  u.dwStructSize = sizeof(u);
  u.dwHostNameLength = u.dwUrlPathLength = (DWORD)-1;
  if (!WinHttpCrackUrl(base.c_str(), 0, 0, &u))
    throw std::runtime_error("Invalid service URL");
  std::wstring host(u.lpszHostName, u.dwHostNameLength);
  if (host != L"127.0.0.1" && host != L"localhost" && host != L"::1")
    throw std::runtime_error("Service must use loopback host");
  Internet session(WinHttpOpen(L"SupplyChainSupplier/1.0",
                               WINHTTP_ACCESS_TYPE_NO_PROXY, nullptr, nullptr,
                               0));
  WinHttpSetTimeouts(session, 5000, 5000, 10000, 20000);
  Internet connection(WinHttpConnect(session, host.c_str(), u.nPort, 0));
  Internet req(WinHttpOpenRequest(
      connection, post ? L"POST" : L"GET", path.c_str(), nullptr,
      WINHTTP_NO_REFERER, WINHTTP_DEFAULT_ACCEPT_TYPES,
      u.nScheme == INTERNET_SCHEME_HTTPS ? WINHTTP_FLAG_SECURE : 0));
  const wchar_t *header =
      L"Content-Type: "
      L"application/vnd.openxmlformats-officedocument.spreadsheetml.sheet\r\n";
  if (!WinHttpSendRequest(req, post ? header : WINHTTP_NO_ADDITIONAL_HEADERS,
                          post ? (DWORD)-1 : 0,
                          body.empty() ? WINHTTP_NO_REQUEST_DATA
                                       : (LPVOID)body.data(),
                          (DWORD)body.size(), (DWORD)body.size(), 0) ||
      !WinHttpReceiveResponse(req, nullptr))
    throw std::runtime_error("无法连接业务服务，请检查服务后重试。");
  DWORD code = 0, len = sizeof(code);
  WinHttpQueryHeaders(
      req, WINHTTP_QUERY_STATUS_CODE | WINHTTP_QUERY_FLAG_NUMBER,
      WINHTTP_HEADER_NAME_BY_INDEX, &code, &len, WINHTTP_NO_HEADER_INDEX);
  std::string result;
  DWORD available = 0, read = 0;
  do {
    if (!WinHttpQueryDataAvailable(req, &available))
      throw std::runtime_error("Response read failed");
    if (!available)
      break;
    if (result.size() + available > 64 * 1024 * 1024)
      throw std::runtime_error("Response too large");
    size_t off = result.size();
    result.resize(off + available);
    if (!WinHttpReadData(req, result.data() + off, available, &read))
      throw std::runtime_error("Response read failed");
    result.resize(off + read);
  } while (available);
  if (code < 200 || code >= 300)
    throw std::runtime_error("HTTP " + std::to_string(code) + ": " + result);
  return result;
}
struct Result {
  int kind;
  Table table;
  std::string id, error;
  std::wstring path;
};
void enabled(bool on) {
  for (HWND h : {importBtn, queryBtn, exportBtn, detailBtn, material})
    if (h)
      EnableWindow(h, on);
  HMENU menu = GetMenu(win);
  for (int id : {IMPORT, QUERY, EXPORT, DETAIL})
    EnableMenuItem(menu, id, MF_BYCOMMAND | (on ? MF_ENABLED : MF_GRAYED));
}
void start(int kind, std::wstring path = {}, std::string id = {}) {
  if (busy || !workspace.ready())
    return;
  if (worker.joinable())
    worker.join();
  busy = true;
  enabled(false);
  SetWindowTextW(status, L"正在处理，请稍候…");
  worker = std::thread([kind, path, id] {
    auto r = std::make_unique<Result>();
    r->kind = kind;
    r->path = path;
    r->id = id;
    try {
      if (kind == IMPORT) {
        std::ifstream f(path, std::ios::binary);
        if (!f)
          throw std::runtime_error("无法打开库存文件");
        std::string bytes((std::istreambuf_iterator<char>(f)), {});
        if (bytes.size() > 32 * 1024 * 1024)
          throw std::runtime_error("库存文件过大");
        r->table = parseTsv(request(L"/api/import/inventory", bytes, true));
        r->table.column("material_id");
      } else if (kind == QUERY) {
        r->table = parseTsv(request(L"/api/quotes?material_id=" +
                                    wide(urlEncode(id)) + L"&format=tsv"));
        r->table.column("unit_price");
      } else {
        std::string ids;
        for (auto &x : queried) {
          if (!ids.empty())
            ids += ',';
          ids += x;
        }
        auto data =
            request(L"/api/export/quotes?material_ids=" + wide(urlEncode(ids)));
        if (data.size() < 4 || data.substr(0, 2) != "PK")
          throw std::runtime_error("服务未返回有效 XLSX 文件");
        saveBinaryFile(path, data);
        try {
          request(L"/api/confirm/quotes", data, true);
        } catch (const std::exception &e) {
          throw std::runtime_error(
              std::string(
                  "报价文件已保存，但保存确认失败；可以安全重试导出。\n") +
              e.what());
        }
      }
    } catch (const std::exception &e) {
      r->error = e.what();
    }
    PostMessageW(win, DONE, 0, (LPARAM)r.release());
  });
}
std::wstring label(const std::string &key) {
  static const std::vector<std::pair<std::string, std::wstring>> names = {
      {"batch_id", L"批次"},
      {"material_id", L"物料编码"},
      {"name", L"物料名称"},
      {"unit", L"单位"},
      {"plant", L"工厂"},
      {"warehouse", L"仓库"},
      {"current", L"当前库存"},
      {"safety", L"安全库存"},
      {"target", L"目标库存"},
      {"enabled", L"启用"},
      {"quote_id", L"报价编号"},
      {"supplier_id", L"供应商编码"},
      {"supplier_name", L"供应商名称"},
      {"unit_price", L"含税单价"},
      {"available", L"可供数量"},
      {"moq", L"最小起订量"},
      {"lead_days", L"交期天数"},
      {"valid_until", L"有效期至"},
      {"active", L"启用"},
      {"currency", L"币种"}};
  for (auto &n : names)
    if (n.first == key)
      return n.second;
  return wide(key);
}
void fill(HWND list, const Table &t) {
  lazy_a11y::Invalidate(list);
  lazy_a11y::Invalidate(ListView_GetHeader(list));
  ListView_DeleteAllItems(list);
  while (ListView_DeleteColumn(list, 0)) {
  }
  for (size_t c = 0; c < t.headers.size(); ++c) {
    auto text = label(t.headers[c]);
    LVCOLUMNW col{};
    col.mask = LVCF_TEXT | LVCF_WIDTH | LVCF_SUBITEM;
    col.pszText = text.data();
    col.cx = MulDiv(c == 3 ? 150 : 110, dpi, 96);
    col.iSubItem = (int)c;
    ListView_InsertColumn(list, (int)c, &col);
  }
  for (size_t i = 0; i < t.rows.size(); ++i)
    for (size_t j = 0; j < t.rows[i].size(); ++j) {
      auto text = wide(t.rows[i][j]);
      if (j == 0) {
        LVITEMW item{};
        item.mask = LVIF_TEXT;
        item.iItem = (int)i;
        item.pszText = text.data();
        ListView_InsertItem(list, &item);
      } else
        ListView_SetItemText(list, (int)i, (int)j, text.data());
    }
}
bool fileDialog(bool save, std::wstring &path) {
  wchar_t filename[32768] = L"";
  if (save)
    wcscpy_s(filename, L"供应商报价.xlsx");
  OPENFILENAMEW f{};
  f.lStructSize = sizeof(f);
  f.hwndOwner = win;
  f.lpstrFilter = L"Excel 工作簿 (*.xlsx)\0*.xlsx\0\0";
  f.lpstrFile = filename;
  f.nMaxFile = 32768;
  f.lpstrDefExt = L"xlsx";
  f.Flags = OFN_EXPLORER | OFN_NOCHANGEDIR | OFN_PATHMUSTEXIST |
            (save ? OFN_OVERWRITEPROMPT : OFN_FILEMUSTEXIST);
  if (!(save ? GetSaveFileNameW(&f) : GetOpenFileNameW(&f)))
    return false;
  path = filename;
  return true;
}
void detail() {
  int n = ListView_GetNextItem(quotes, -1, LVNI_SELECTED);
  if (n < 0) {
    MessageBoxW(win, L"请先选择一条报价。", L"报价详情", MB_OK);
    return;
  }
  std::wstring text;
  for (size_t i = 0; i < offers.headers.size(); ++i)
    text +=
        label(offers.headers[i]) + L"：" + wide(offers.rows[n][i]) + L"\r\n";
  MessageBoxW(win, text.c_str(), L"报价详情", MB_OK | MB_ICONINFORMATION);
}
void command(int id) {
  if (id == EXIT) {
    SendMessageW(win, WM_CLOSE, 0, 0);
    return;
  }
  if (busy || !workspace.ready())
    return;
  try {
    if (id == IMPORT) {
      std::wstring path;
      if (fileDialog(false, path))
        start(IMPORT, path);
    } else if (id == QUERY) {
      wchar_t value[256];
      GetWindowTextW(material, value, 256);
      std::wstring v = value;
      if (v.empty()) {
        MessageBoxW(win, L"请输入物料编码。", L"查询", MB_OK);
        return;
      }
      start(QUERY, {}, utf8(v));
    } else if (id == EXPORT) {
      if (queried.empty()) {
        MessageBoxW(win, L"请先查询需要导出的物料。", L"导出", MB_OK);
        return;
      }
      std::wstring path;
      if (fileDialog(true, path))
        start(EXPORT, path);
    } else if (id == DETAIL)
      detail();
  } catch (const std::exception &e) {
    MessageBoxW(win, wide(e.what()).c_str(), L"操作失败", MB_OK | MB_ICONERROR);
  }
}
int px(int n) { return MulDiv(n, dpi, 96); }
void layout() {
  RECT r;
  GetClientRect(win, &r);
  int w = r.right, h = r.bottom, p = px(12), row = px(30), top = px(62),
      mid = std::max(top + px(100), h * 44 / 100);
  MoveWindow(status, 0, h - px(28), w, px(28), TRUE);
  if (!workspace.ready()) {
    MoveWindow(enterBtn, p, p, px(210), row, TRUE);
    return;
  }
  MoveWindow(importBtn, p, p, px(150), row, TRUE);
  MoveWindow(materialLabel, px(180), p + px(5), px(85), row, TRUE);
  MoveWindow(material, px(268), p, px(160), row, TRUE);
  MoveWindow(queryBtn, px(440), p, px(90), row, TRUE);
  MoveWindow(exportBtn, px(545), p, px(210), row, TRUE);
  MoveWindow(invLabel, p, top - px(18), w - 2 * p, px(20), TRUE);
  MoveWindow(inventory, p, top, w - 2 * p, mid - top, TRUE);
  MoveWindow(quoteLabel, p, mid + px(10), w - px(160), px(22), TRUE);
  MoveWindow(detailBtn, w - px(140), mid + px(5), px(125), row, TRUE);
  MoveWindow(quotes, p, mid + px(42), w - 2 * p,
             std::max(px(40), h - mid - px(82)), TRUE);
}
HWND control(const wchar_t *cls, const wchar_t *text, DWORD style, int id = 0) {
  HWND h = CreateWindowExW(0, cls, text, WS_CHILD | WS_VISIBLE | style, 0, 0, 0,
                           0, win, (HMENU)(INT_PTR)id,
                           GetModuleHandleW(nullptr), nullptr);
  if (h)
    lazy_a11y::Attach(h);
  SendMessageW(h, WM_SETFONT, (WPARAM)font, TRUE);
  return h;
}
void setFont() {
  if (font)
    DeleteObject(font);
  font = CreateFontW(-px(14), 0, 0, 0, FW_NORMAL, FALSE, FALSE, FALSE,
                     DEFAULT_CHARSET, 0, 0, CLEARTYPE_QUALITY, 0,
                     L"Microsoft YaHei UI");
  for (HWND h : {inventory, quotes, material, status, importBtn, queryBtn,
                 exportBtn, detailBtn, invLabel, quoteLabel, materialLabel, enterBtn})
    if (h)
      SendMessageW(h, WM_SETFONT, (WPARAM)font, TRUE);
}
void createBusinessControls() {
  importBtn = control(L"BUTTON", L"导入库存文件…", BS_PUSHBUTTON | WS_TABSTOP,
                      IMPORT);
  materialLabel = control(L"STATIC", L"物料编码：", 0);
  material =
      control(L"EDIT", L"", WS_BORDER | ES_AUTOHSCROLL | WS_TABSTOP, 110);
  SendMessageW(material, EM_SETLIMITTEXT, 64, 0);
  queryBtn =
      control(L"BUTTON", L"查询报价", BS_PUSHBUTTON | WS_TABSTOP, QUERY);
  exportBtn = control(L"BUTTON", L"导出已查询物料报价…",
                      BS_PUSHBUTTON | WS_TABSTOP, EXPORT);
  detailBtn =
      control(L"BUTTON", L"报价详情", BS_PUSHBUTTON | WS_TABSTOP, DETAIL);
  invLabel = control(L"STATIC", L"已导入库存（双击行可填入物料编码）", 0);
  inventory =
      control(WC_LISTVIEWW, L"导入库存列表",
              LVS_REPORT | LVS_SINGLESEL | WS_BORDER | WS_TABSTOP, 111);
  quoteLabel = control(L"STATIC", L"供应商原始报价（点击单价列排序）", 0);
  quotes = control(WC_LISTVIEWW, L"供应商报价列表",
                   LVS_REPORT | LVS_SINGLESEL | WS_BORDER | WS_TABSTOP, 112);
  for (HWND list : {inventory, quotes})
    ListView_SetExtendedListViewStyle(
        list, LVS_EX_FULLROWSELECT | LVS_EX_GRIDLINES | LVS_EX_DOUBLEBUFFER);
  SetWindowTextW(status, L"就绪：请导入库存工作簿，然后自行选择物料查询。");
}
LRESULT CALLBACK proc(HWND h, UINT m, WPARAM wp, LPARAM lp) {
  switch (m) {
  case WM_CREATE: {
    win = h;
    lazy_a11y::Attach(h);
    dpi = GetDpiForWindow(h);
    setFont();
    HMENU menu = CreateMenu(), file = CreatePopupMenu();
    AppendMenuW(file, MF_STRING, IMPORT, L"导入库存文件…");
    AppendMenuW(file, MF_STRING, EXPORT, L"导出已查询物料报价…");
    AppendMenuW(file, MF_SEPARATOR, 0, nullptr);
    AppendMenuW(file, MF_STRING, EXIT, L"退出");
    AppendMenuW(menu, MF_POPUP, (UINT_PTR)file, L"文件(&F)");
    AppendMenuW(menu, MF_STRING, QUERY, L"查询(&Q)");
    AppendMenuW(menu, MF_STRING, DETAIL, L"报价详情(&D)");
    SetMenu(h, menu);
    status = control(L"STATIC", L"请进入报价工作台。", SS_SUNKEN);
    if (workspace.ready()) {
      createBusinessControls();
    } else {
      enterBtn = control(L"BUTTON", L"进入报价工作台",
                         BS_PUSHBUTTON | WS_TABSTOP, ENTER);
      enabled(false);
    }
    layout();
    return 0;
  }
  case WM_COMMAND:
    if (LOWORD(wp) == ENTER) {
      if (workspace.begin()) {
        if (!SetTimer(h, LOAD_TIMER, 1200, nullptr)) {
          workspace = WorkspaceLoad(true);
          SetWindowTextW(status, L"无法开始加载，请重试。");
          return 0;
        }
        EnableWindow(enterBtn, FALSE);
        SetWindowTextW(status, L"正在加载报价工作台，请稍候…");
      }
      return 0;
    }
    command(LOWORD(wp));
    return 0;
  case WM_TIMER:
    if (wp == LOAD_TIMER) {
      KillTimer(h, LOAD_TIMER);
      if (workspace.complete()) {
        DestroyWindow(enterBtn);
        enterBtn = nullptr;
        createBusinessControls();
        enabled(true);
        layout();
        SetFocus(material);
      }
      return 0;
    }
    break;
  case WM_SIZE:
    layout();
    return 0;
  case WM_GETMINMAXINFO:
    ((MINMAXINFO *)lp)->ptMinTrackSize = {px(820), px(540)};
    return 0;
  case WM_DPICHANGED:
    dpi = HIWORD(wp);
    setFont();
    {
      RECT *r = (RECT *)lp;
      SetWindowPos(h, nullptr, r->left, r->top, r->right - r->left,
                   r->bottom - r->top, SWP_NOZORDER);
    }
    layout();
    return 0;
  case WM_NOTIFY: {
    if (!workspace.ready()) return 0;
    auto n = (NMHDR *)lp;
    if (n->hwndFrom == inventory && n->code == NM_DBLCLK && !busy) {
      int i = ListView_GetNextItem(inventory, -1, LVNI_SELECTED);
      if (i >= 0)
        SetWindowTextW(
            material, wide(stock.rows[i][stock.column("material_id")]).c_str());
    }
    if (n->hwndFrom == quotes && n->code == NM_DBLCLK)
      detail();
    if (n->hwndFrom == quotes && n->code == LVN_COLUMNCLICK && !busy) {
      int col = ((NMLISTVIEW *)lp)->iSubItem;
      if (offers.headers[col] == "unit_price") {
        try {
          std::stable_sort(
              offers.rows.begin(), offers.rows.end(), [col](auto &a, auto &b) {
                return ascending ? priceCents(a[col]) < priceCents(b[col])
                                 : priceCents(a[col]) > priceCents(b[col]);
              });
          ascending = !ascending;
          fill(quotes, offers);
        } catch (const std::exception &e) {
          MessageBoxW(h, wide(e.what()).c_str(), L"排序失败",
                      MB_OK | MB_ICONERROR);
        }
      }
    }
    return 0;
  }
  case DONE: {
    std::unique_ptr<Result> r((Result *)lp);
    if (worker.joinable())
      worker.join();
    busy = false;
    enabled(true);
    if (!r->error.empty()) {
      SetWindowTextW(status, L"操作失败，现有数据已保留；可以重试。");
      MessageBoxW(h, wide(r->error).c_str(), L"操作失败", MB_OK | MB_ICONERROR);
    } else {
      if (r->kind == IMPORT) {
        stock = std::move(r->table);
        if (!stock.rows.empty()) {
          try {
            SetWindowTextW(invLabel,
                           (L"已导入库存 — 批次：" +
                            wide(stock.rows[0][stock.column("batch_id")]) +
                            L"（双击行填入编码）")
                               .c_str());
          } catch (...) {
          }
        }
        offers = {};
        queried.clear();
        fill(inventory, stock);
        fill(quotes, offers);
        SetWindowTextW(material, L"");
      } else if (r->kind == QUERY) {
        offers = std::move(r->table);
        queried.insert(r->id);
        fill(quotes, offers);
      }
      std::wstring msg =
          r->kind == EXPORT
              ? L"报价工作簿已保存。"
              : L"完成。库存行数：" + std::to_wstring(stock.rows.size()) +
                    L"；当前报价：" + std::to_wstring(offers.rows.size()) +
                    L"；已查询物料：" + std::to_wstring(queried.size());
      SetWindowTextW(status, msg.c_str());
    }
    return 0;
  }
  case WM_CLOSE:
    if (busy) {
      SetWindowTextW(status,
                     L"正在完成请求，请稍后关闭（网络超时最多约 40 秒）。");
      return 0;
    }
    KillTimer(h, LOAD_TIMER);
    workspace.cancel();
    DestroyWindow(h);
    return 0;
  case WM_DESTROY:
    KillTimer(h, LOAD_TIMER);
    workspace.cancel();
    if (worker.joinable())
      worker.join();
    DeleteObject(font);
    PostQuitMessage(0);
    return 0;
  }
  return DefWindowProcW(h, m, wp, lp);
}
int WINAPI wWinMain(HINSTANCE instance, HINSTANCE, LPWSTR, int show) {
  const HRESULT oleResult = OleInitialize(nullptr);
  if (FAILED(oleResult)) {
    MessageBoxW(nullptr, L"无法初始化无障碍 COM 运行环境。", L"启动失败", MB_OK | MB_ICONERROR);
    return 1;
  }
  int argc;
  LPWSTR *args = CommandLineToArgvW(GetCommandLineW(), &argc);
  for (int i = 1; i < argc; ++i)
    if (std::wstring(args[i]) == L"--url" && i + 1 < argc)
      base = args[++i];
    else if (std::wstring(args[i]) == L"--obstacles")
      workspace = WorkspaceLoad(true);
  LocalFree(args);
  while (!base.empty() && base.back() == L'/')
    base.pop_back();
  INITCOMMONCONTROLSEX ic{sizeof(ic),
                          ICC_LISTVIEW_CLASSES | ICC_STANDARD_CLASSES};
  InitCommonControlsEx(&ic);
  WNDCLASSW wc{};
  wc.lpfnWndProc = proc;
  wc.hInstance = instance;
  wc.lpszClassName = L"SupplyChainSupplier";
  wc.hCursor = LoadCursorW(nullptr, IDC_ARROW);
  wc.hbrBackground = (HBRUSH)(COLOR_BTNFACE + 1);
  wc.hIcon = LoadIconW(nullptr, IDI_APPLICATION);
  RegisterClassW(&wc);
  HWND h =
      CreateWindowExW(0, wc.lpszClassName, L"供应商报价管理 — 库存补货任务",
                      WS_OVERLAPPEDWINDOW, CW_USEDEFAULT, CW_USEDEFAULT, 1180,
                      780, nullptr, nullptr, instance, nullptr);
  if (!h) {
    lazy_a11y::Shutdown();
    OleUninitialize();
    return 1;
  }
  ShowWindow(h, show);
  MSG msg;
  while (GetMessageW(&msg, nullptr, 0, 0) > 0) {
    if (!IsDialogMessageW(h, &msg)) {
      TranslateMessage(&msg);
      DispatchMessageW(&msg);
    }
  }
  lazy_a11y::Shutdown();
  OleUninitialize();
  return (int)msg.wParam;
}

