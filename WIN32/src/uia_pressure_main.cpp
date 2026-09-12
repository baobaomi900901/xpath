#include <windows.h>
#include <commctrl.h>
#include <string>

#pragma comment(linker, "/manifestdependency:\"type='win32' name='Microsoft.Windows.Common-Controls' version='6.0.0.0' processorArchitecture='*' publicKeyToken='6595b64144ccf1df' language='*'\"")

namespace {
constexpr wchar_t kWindowClass[] = L"XPathUiAPressureRange";
HWND g_tree{};
int g_depth{};

int ParseDepth(LPWSTR text) {
    wchar_t* end = nullptr;
    const long value = text ? wcstol(text, &end, 10) : 500;
    return (end != text && (value == 500 || value == 1000 || value == 2000)) ? static_cast<int>(value) : 500;
}

HTREEITEM InsertLevel(HTREEITEM parent, int level) {
    const std::wstring name = L"uia-pressure-level-" + std::to_wstring(level);
    TVINSERTSTRUCTW insert{};
    insert.hParent = parent;
    insert.hInsertAfter = TVI_LAST;
    insert.item.mask = TVIF_TEXT | TVIF_PARAM;
    insert.item.pszText = const_cast<wchar_t*>(name.c_str());
    insert.item.lParam = level;
    HTREEITEM item = TreeView_InsertItem(g_tree, &insert);
    if (!item || level >= g_depth) return item;
    HTREEITEM deepest = InsertLevel(item, level + 1);
    TreeView_Expand(g_tree, item, TVE_EXPAND);
    return deepest;
}

LRESULT CALLBACK WindowProc(HWND window, UINT message, WPARAM wParam, LPARAM lParam) {
    if (message == WM_NOTIFY && g_tree) {
        auto* draw = reinterpret_cast<NMTVCUSTOMDRAW*>(lParam);
        if (draw->nmcd.hdr.hwndFrom == g_tree && draw->nmcd.hdr.code == NM_CUSTOMDRAW) {
            if (draw->nmcd.dwDrawStage == CDDS_PREPAINT) return CDRF_NOTIFYITEMDRAW;
            if (draw->nmcd.dwDrawStage == CDDS_ITEMPREPAINT && draw->nmcd.lItemlParam == g_depth) {
                draw->clrText = RGB(180, 0, 0);
                draw->clrTextBk = RGB(255, 220, 220);
                return CDRF_DODEFAULT;
            }
        }
    }
    if (message == WM_DESTROY) { PostQuitMessage(0); return 0; }
    return DefWindowProcW(window, message, wParam, lParam);
}

int Run(HINSTANCE instance, int depth) {
    g_depth = depth;
    INITCOMMONCONTROLSEX common{sizeof(common), ICC_TREEVIEW_CLASSES};
    InitCommonControlsEx(&common);
    WNDCLASSW klass{};
    klass.hInstance = instance; klass.lpfnWndProc = WindowProc;
    klass.hCursor = LoadCursorW(nullptr, IDC_ARROW); klass.hbrBackground = GetSysColorBrush(COLOR_WINDOW);
    klass.lpszClassName = kWindowClass;
    if (!RegisterClassW(&klass)) return 1;
    const std::wstring title = L"Win32 UIA 压力靶场 - " + std::to_wstring(depth) + L"层";
    HWND root = CreateWindowExW(0, kWindowClass, title.c_str(), WS_OVERLAPPEDWINDOW,
        CW_USEDEFAULT, CW_USEDEFAULT, 720, 720, nullptr, nullptr, instance, nullptr);
    if (!root) return 1;
    g_tree = CreateWindowExW(WS_EX_CLIENTEDGE, WC_TREEVIEWW, L"",
        WS_CHILD | WS_VISIBLE | WS_TABSTOP | TVS_HASBUTTONS | TVS_HASLINES | TVS_LINESATROOT,
        8, 8, 680, 650, root, reinterpret_cast<HMENU>(1), instance, nullptr);
    if (!g_tree) { DestroyWindow(root); return 1; }
    InsertLevel(TVI_ROOT, 1);
    TreeView_Expand(g_tree, TreeView_GetRoot(g_tree), TVE_EXPAND);
    ShowWindow(root, SW_SHOW); UpdateWindow(root);
    MSG message{};
    while (GetMessageW(&message, nullptr, 0, 0) > 0) { TranslateMessage(&message); DispatchMessageW(&message); }
    return static_cast<int>(message.wParam);
}
}

int WINAPI wWinMain(HINSTANCE instance, HINSTANCE, PWSTR commandLine, int) { return Run(instance, ParseDepth(commandLine)); }
