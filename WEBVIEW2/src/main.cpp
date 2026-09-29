#include <windows.h>
#include <commctrl.h>
#include <shlobj.h>
#include <wrl.h>
#include <WebView2.h>

#include <algorithm>
#include <array>
#include <filesystem>
#include <memory>
#include <string>

using Microsoft::WRL::Callback;
using Microsoft::WRL::ComPtr;

namespace {
constexpr wchar_t kWindowClass[] = L"XPathWebView2Range";
constexpr int kMenuId = 1001;
constexpr int kAddressId = 1002;
constexpr int kRefreshId = 1003;
constexpr int kStatusId = 1004;
constexpr UINT kBrowserExited = WM_APP + 1;
struct Page { const wchar_t* label; const wchar_t* url; };
constexpr std::array<Page, 3> kPages{{
    {L"点击测试", L"https://baobaomi900901.github.io/xpath/#/keys-click-test"},
    {L"表单测试", L"https://baobaomi900901.github.io/xpath/#/form-controls"},
    {L"iframe表单", L"https://baobaomi900901.github.io/xpath/#/iframe-shadow-form"},
}};

std::wstring ErrorCode(HRESULT hr) {
    wchar_t buffer[32]{};
    swprintf_s(buffer, L"0x%08X", static_cast<unsigned int>(hr));
    return buffer;
}

class App : public std::enable_shared_from_this<App> {
public:
    HWND window = nullptr;
    bool closing = false;

    ~App() { if (font_) DeleteObject(font_); }

    bool CreateControls() {
        heading_ = CreateControl(L"STATIC", L"测试菜单", SS_LEFT, 0);
        menu_ = CreateControl(L"LISTBOX", L"测试菜单", LBS_NOTIFY | LBS_NOINTEGRALHEIGHT | WS_TABSTOP | WS_VSCROLL, kMenuId, WS_EX_CLIENTEDGE);
        note_ = CreateControl(L"STATIC", L"原生 Win32 菜单\r\nWebView2 页面内容", SS_LEFT, 0);
        address_ = CreateControl(L"EDIT", kPages[0].url, ES_READONLY | ES_AUTOHSCROLL | WS_TABSTOP, kAddressId, WS_EX_CLIENTEDGE);
        refresh_ = CreateControl(L"BUTTON", L"刷新", BS_PUSHBUTTON | WS_TABSTOP, kRefreshId);
        status_ = CreateControl(L"STATIC", L"正在初始化 WebView2…", SS_LEFT | SS_NOPREFIX, kStatusId);
        placeholder_ = CreateControl(L"STATIC", L"正在初始化 WebView2…", SS_CENTER | SS_NOPREFIX, 0);
        if (!heading_ || !menu_ || !note_ || !address_ || !refresh_ || !status_ || !placeholder_) return false;
        for (const auto& page : kPages) SendMessageW(menu_, LB_ADDSTRING, 0, reinterpret_cast<LPARAM>(page.label));
        SendMessageW(menu_, LB_SETCURSEL, 0, 0);
        EnableWindow(refresh_, FALSE);
        UpdateFont();
        Layout();
        return true;
    }

    void UpdateFont() {
        dpi_ = GetDpiForWindow(window);
        HFONT next = CreateFontW(-Scale(16), 0, 0, 0, FW_NORMAL, FALSE, FALSE, FALSE,
            DEFAULT_CHARSET, OUT_DEFAULT_PRECIS, CLIP_DEFAULT_PRECIS, CLEARTYPE_QUALITY,
            DEFAULT_PITCH | FF_DONTCARE, L"Microsoft YaHei UI");
        if (!next) return;
        for (HWND control : {heading_, menu_, note_, address_, refresh_, status_, placeholder_}) {
            SendMessageW(control, WM_SETFONT, reinterpret_cast<WPARAM>(next), TRUE);
        }
        SendMessageW(menu_, LB_SETITEMHEIGHT, 0, Scale(42));
        if (font_) DeleteObject(font_);
        font_ = next;
    }

    void Layout() {
        RECT client{};
        GetClientRect(window, &client);
        const int width = client.right;
        const int height = client.bottom;
        const int pad = Scale(12);
        const int sidebar = Scale(220);
        const int top = Scale(52);
        const int footer = Scale(34);
        const int rightWidth = std::max(1, width - sidebar - pad);
        MoveWindow(heading_, pad, pad, sidebar - 2 * pad, Scale(24), TRUE);
        MoveWindow(menu_, pad, Scale(48), sidebar - 2 * pad, std::max(1, height - Scale(130)), TRUE);
        MoveWindow(note_, pad, std::max(Scale(100), height - Scale(68)), sidebar - 2 * pad, Scale(50), TRUE);
        const int buttonWidth = Scale(76);
        MoveWindow(address_, sidebar, pad, std::max(1, rightWidth - buttonWidth - pad), Scale(28), TRUE);
        MoveWindow(refresh_, std::max(sidebar, width - pad - buttonWidth), pad, buttonWidth, Scale(28), TRUE);
        MoveWindow(status_, sidebar, std::max(top, height - footer + Scale(6)), rightWidth, Scale(24), TRUE);
        bounds_ = {sidebar, top, std::max(sidebar + 1, width - pad), std::max(top + 1, height - footer)};
        MoveWindow(placeholder_, sidebar + pad, top + Scale(32), std::max(1, rightWidth - 2 * pad), Scale(180), TRUE);
        if (controller_) {
            controller_->put_Bounds(bounds_);
            controller_->put_IsVisible(!IsIconic(window));
            controller_->NotifyParentWindowPositionChanged();
        }
        InvalidateRect(window, nullptr, FALSE);
    }

    void SelectPage() {
        const LRESULT index = SendMessageW(menu_, LB_GETCURSEL, 0, 0);
        if (index < 0 || index >= static_cast<LRESULT>(kPages.size())) return;
        selected_ = static_cast<size_t>(index);
        SetWindowTextW(address_, kPages[selected_].url);
        if (webview_) NavigateSelected();
    }

    void Refresh() {
        if (!webview_) { InitializeBrowser(); return; }
        SetStatus(L"正在加载…");
        const HRESULT hr = webview_->Reload();
        if (FAILED(hr)) SetStatus(L"刷新失败：" + ErrorCode(hr) + L"，请再次刷新重试。");
    }

    void InitializeBrowser() {
        if (initializing_ || closing) return;
        initializing_ = true;
        EnableWindow(refresh_, FALSE);
        SetStatus(L"正在初始化 WebView2…");
        SetWindowTextW(placeholder_, L"正在初始化 WebView2…");
        ShowWindow(placeholder_, SW_SHOW);
        // The official environment-variable overrides are available for verification.
        PWSTR localAppData = nullptr;
        HRESULT hr = SHGetKnownFolderPath(FOLDERID_LocalAppData, 0, nullptr, &localAppData);
        if (FAILED(hr)) { FailInitialization(L"无法读取用户数据目录", hr); return; }
        const auto dataPath = std::filesystem::path(localAppData) / L"XPath" / L"WebView2Range";
        CoTaskMemFree(localAppData);
        std::error_code error;
        std::filesystem::create_directories(dataPath, error);
        if (error) { FailInitialization(L"无法创建用户数据目录", HRESULT_FROM_WIN32(error.value())); return; }
        std::weak_ptr<App> weak = shared_from_this();
        hr = CreateCoreWebView2EnvironmentWithOptions(nullptr, dataPath.c_str(), nullptr,
            Callback<ICoreWebView2CreateCoreWebView2EnvironmentCompletedHandler>(
                [weak](HRESULT result, ICoreWebView2Environment* environment) -> HRESULT {
                    auto app = weak.lock();
                    if (!app || app->closing) return S_OK;
                    if (FAILED(result) || !environment) {
                        app->FailInitialization(L"WebView2 环境创建失败", FAILED(result) ? result : E_FAIL);
                        return S_OK;
                    }
                    app->environment_ = environment;
                    const HRESULT createResult = environment->CreateCoreWebView2Controller(app->window,
                        Callback<ICoreWebView2CreateCoreWebView2ControllerCompletedHandler>(
                            [weak](HRESULT controllerResult, ICoreWebView2Controller* controller) -> HRESULT {
                                auto current = weak.lock();
                                if (!current || current->closing) {
                                    if (controller) controller->Close();
                                    return S_OK;
                                }
                                if (FAILED(controllerResult) || !controller) {
                                    current->FailInitialization(L"WebView2 控件创建失败", FAILED(controllerResult) ? controllerResult : E_FAIL);
                                    return S_OK;
                                }
                                current->controller_ = controller;
                                const HRESULT getResult = controller->get_CoreWebView2(&current->webview_);
                                if (FAILED(getResult) || !current->webview_) {
                                    current->FailInitialization(L"无法获取 WebView2 页面", FAILED(getResult) ? getResult : E_FAIL);
                                    return S_OK;
                                }
                                const HRESULT eventResult = current->RegisterEvents();
                                if (FAILED(eventResult)) {
                                    current->FailInitialization(L"WebView2 事件注册失败", eventResult);
                                    return S_OK;
                                }
                                current->initializing_ = false;
                                EnableWindow(current->refresh_, TRUE);
                                ShowWindow(current->placeholder_, SW_HIDE);
                                current->Layout();
                                current->NavigateSelected();
                                return S_OK;
                            }).Get());
                    if (FAILED(createResult)) app->FailInitialization(L"WebView2 控件创建失败", createResult);
                    return S_OK;
                }).Get());
        if (FAILED(hr)) FailInitialization(L"WebView2 初始化失败", hr);
    }

    void BrowserExited() {
        DisconnectBrowser();
        initializing_ = false;
        const wchar_t* text = L"WebView2 浏览器进程已退出。点击刷新重新初始化。";
        SetStatus(text);
        SetWindowTextW(placeholder_, text);
        ShowWindow(placeholder_, SW_SHOW);
        EnableWindow(refresh_, TRUE);
    }

    void Close() {
        closing = true;
        DisconnectBrowser();
    }

    bool IsNativeControl(HWND target) const {
        return target == window || target == menu_ || target == address_ || target == refresh_;
    }

private:
    HWND heading_ = nullptr, menu_ = nullptr, note_ = nullptr, address_ = nullptr;
    HWND refresh_ = nullptr, status_ = nullptr, placeholder_ = nullptr;
    HFONT font_ = nullptr;
    UINT dpi_ = 96;
    size_t selected_ = 0;
    bool initializing_ = false;
    UINT64 navigationId_ = 0;
    RECT bounds_{};
    ComPtr<ICoreWebView2Environment> environment_;
    ComPtr<ICoreWebView2Controller> controller_;
    ComPtr<ICoreWebView2> webview_;
    EventRegistrationToken starting_{}, completed_{}, source_{}, process_{};

    int Scale(int value) const { return MulDiv(value, static_cast<int>(dpi_), 96); }

    HWND CreateControl(const wchar_t* className, const wchar_t* text, DWORD style, int id, DWORD extended = 0) {
        return CreateWindowExW(extended, className, text, WS_CHILD | WS_VISIBLE | style,
            0, 0, 0, 0, window, reinterpret_cast<HMENU>(static_cast<INT_PTR>(id)),
            GetModuleHandleW(nullptr), nullptr);
    }

    void SetStatus(const std::wstring& text) { if (!closing) SetWindowTextW(status_, text.c_str()); }

    void FailInitialization(const std::wstring& message, HRESULT hr) {
        DisconnectBrowser();
        initializing_ = false;
        const std::wstring text = message + L"（" + ErrorCode(hr) + L"）。\r\n"
            L"请检查 Microsoft Edge WebView2 Runtime 是否已安装，以及用户数据目录是否可写。\r\n"
            L"运行时下载：https://developer.microsoft.com/microsoft-edge/webview2/\r\n"
            L"处理后点击刷新重试。";
        SetWindowTextW(placeholder_, text.c_str());
        ShowWindow(placeholder_, SW_SHOW);
        SetStatus(message + L"：" + ErrorCode(hr) + L"，点击刷新重试。");
        EnableWindow(refresh_, TRUE);
    }

    void NavigateSelected() {
        SetStatus(L"正在加载：" + std::wstring(kPages[selected_].label));
        const HRESULT hr = webview_->Navigate(kPages[selected_].url);
        if (FAILED(hr)) SetStatus(L"页面导航失败：" + ErrorCode(hr) + L"，请点击刷新重试。");
    }

    HRESULT RegisterEvents() {
        std::weak_ptr<App> weak = shared_from_this();
        HRESULT hr = webview_->add_NavigationStarting(
            Callback<ICoreWebView2NavigationStartingEventHandler>(
                [weak](ICoreWebView2*, ICoreWebView2NavigationStartingEventArgs* args) -> HRESULT {
                    if (auto app = weak.lock(); app && !app->closing) {
                        args->get_NavigationId(&app->navigationId_);
                        app->SetStatus(L"正在加载…");
                    }
                    return S_OK;
                }).Get(), &starting_);
        if (FAILED(hr)) return hr;
        hr = webview_->add_NavigationCompleted(
            Callback<ICoreWebView2NavigationCompletedEventHandler>(
                [weak](ICoreWebView2*, ICoreWebView2NavigationCompletedEventArgs* args) -> HRESULT {
                    auto app = weak.lock();
                    if (!app || app->closing) return S_OK;
                    UINT64 id = 0;
                    args->get_NavigationId(&id);
                    if (id != app->navigationId_) return S_OK;
                    BOOL success = FALSE;
                    args->get_IsSuccess(&success);
                    if (success) app->SetStatus(L"就绪");
                    else {
                        COREWEBVIEW2_WEB_ERROR_STATUS error = COREWEBVIEW2_WEB_ERROR_STATUS_UNKNOWN;
                        args->get_WebErrorStatus(&error);
                        app->SetStatus(L"页面加载失败（WebErrorStatus=" + std::to_wstring(static_cast<int>(error)) + L"），请检查网络后点击刷新。");
                    }
                    return S_OK;
                }).Get(), &completed_);
        if (FAILED(hr)) return hr;
        hr = webview_->add_SourceChanged(
            Callback<ICoreWebView2SourceChangedEventHandler>(
                [weak](ICoreWebView2* sender, ICoreWebView2SourceChangedEventArgs* args) -> HRESULT {
                    auto app = weak.lock();
                    if (!app || app->closing) return S_OK;
                    LPWSTR url = nullptr;
                    if (SUCCEEDED(sender->get_Source(&url)) && url) {
                        SetWindowTextW(app->address_, url);
                        for (size_t index = 0; index < kPages.size(); ++index) {
                            if (std::wstring(url) == kPages[index].url) {
                                app->selected_ = index;
                                SendMessageW(app->menu_, LB_SETCURSEL, index, 0);
                                break;
                            }
                        }
                    }
                    CoTaskMemFree(url);
                    BOOL newDocument = TRUE;
                    args->get_IsNewDocument(&newDocument);
                    if (!newDocument) app->SetStatus(L"就绪");
                    return S_OK;
                }).Get(), &source_);
        if (FAILED(hr)) return hr;
        return webview_->add_ProcessFailed(
            Callback<ICoreWebView2ProcessFailedEventHandler>(
                [weak](ICoreWebView2*, ICoreWebView2ProcessFailedEventArgs* args) -> HRESULT {
                    auto app = weak.lock();
                    if (!app || app->closing) return S_OK;
                    COREWEBVIEW2_PROCESS_FAILED_KIND kind{};
                    args->get_ProcessFailedKind(&kind);
                    if (kind == COREWEBVIEW2_PROCESS_FAILED_KIND_BROWSER_PROCESS_EXITED) {
                        PostMessageW(app->window, kBrowserExited, 0, 0);
                    } else app->SetStatus(L"WebView2 页面进程异常，请点击刷新重试。");
                    return S_OK;
                }).Get(), &process_);
    }

    void DisconnectBrowser() {
        if (webview_) {
            webview_->remove_NavigationStarting(starting_);
            webview_->remove_NavigationCompleted(completed_);
            webview_->remove_SourceChanged(source_);
            webview_->remove_ProcessFailed(process_);
        }
        if (controller_) controller_->Close();
        webview_.Reset();
        controller_.Reset();
        environment_.Reset();
        navigationId_ = 0;
        starting_ = {}; completed_ = {}; source_ = {}; process_ = {};
    }
};

LRESULT CALLBACK WindowProc(HWND window, UINT message, WPARAM wParam, LPARAM lParam) {
    App* app = reinterpret_cast<App*>(GetWindowLongPtrW(window, GWLP_USERDATA));
    if (message == WM_NCCREATE) {
        app = static_cast<App*>(reinterpret_cast<CREATESTRUCTW*>(lParam)->lpCreateParams);
        app->window = window;
        SetWindowLongPtrW(window, GWLP_USERDATA, reinterpret_cast<LONG_PTR>(app));
    }
    if (!app) return DefWindowProcW(window, message, wParam, lParam);
    switch (message) {
    case WM_CREATE:
        if (!app->CreateControls()) return -1;
        app->InitializeBrowser();
        return 0;
    case WM_COMMAND:
        if (LOWORD(wParam) == kMenuId && HIWORD(wParam) == LBN_SELCHANGE) app->SelectPage();
        else if (LOWORD(wParam) == kRefreshId && HIWORD(wParam) == BN_CLICKED) app->Refresh();
        return 0;
    case WM_SIZE:
    case WM_MOVE:
        app->Layout();
        return 0;
    case WM_DPICHANGED: {
        const auto* rect = reinterpret_cast<RECT*>(lParam);
        SetWindowPos(window, nullptr, rect->left, rect->top, rect->right - rect->left,
            rect->bottom - rect->top, SWP_NOACTIVATE | SWP_NOZORDER);
        app->UpdateFont();
        app->Layout();
        return 0;
    }
    case WM_GETMINMAXINFO: {
        auto* info = reinterpret_cast<MINMAXINFO*>(lParam);
        const UINT dpi = GetDpiForWindow(window);
        info->ptMinTrackSize = {MulDiv(720, dpi, 96), MulDiv(480, dpi, 96)};
        return 0;
    }
    case kBrowserExited:
        app->BrowserExited();
        return 0;
    case WM_CLOSE:
        app->Close();
        DestroyWindow(window);
        return 0;
    case WM_DESTROY:
        app->Close();
        PostQuitMessage(0);
        return 0;
    case WM_NCDESTROY:
        SetWindowLongPtrW(window, GWLP_USERDATA, 0);
        break;
    }
    return DefWindowProcW(window, message, wParam, lParam);
}
} // namespace

int WINAPI wWinMain(HINSTANCE instance, HINSTANCE, PWSTR, int showCommand) {
    const HRESULT hr = CoInitializeEx(nullptr, COINIT_APARTMENTTHREADED);
    if (FAILED(hr)) {
        MessageBoxW(nullptr, (L"COM 初始化失败：" + ErrorCode(hr)).c_str(), L"WebView2 浏览器靶场", MB_OK | MB_ICONERROR);
        return 1;
    }
    INITCOMMONCONTROLSEX common{sizeof(common), ICC_STANDARD_CLASSES};
    InitCommonControlsEx(&common);
    WNDCLASSEXW windowClass{sizeof(windowClass)};
    windowClass.lpfnWndProc = WindowProc;
    windowClass.hInstance = instance;
    windowClass.hCursor = LoadCursorW(nullptr, IDC_ARROW);
    windowClass.hIcon = LoadIconW(nullptr, IDI_APPLICATION);
    windowClass.hbrBackground = reinterpret_cast<HBRUSH>(COLOR_BTNFACE + 1);
    windowClass.lpszClassName = kWindowClass;
    if (!RegisterClassExW(&windowClass)) { CoUninitialize(); return 1; }
    auto app = std::make_shared<App>();
    const UINT dpi = GetDpiForSystem();
    HWND window = CreateWindowExW(WS_EX_CONTROLPARENT, kWindowClass, L"WebView2 浏览器靶场",
        WS_OVERLAPPEDWINDOW | WS_CLIPCHILDREN, CW_USEDEFAULT, CW_USEDEFAULT,
        MulDiv(1280, dpi, 96), MulDiv(900, dpi, 96), nullptr, nullptr, instance, app.get());
    if (!window) {
        app->Close(); app.reset(); CoUninitialize(); return 1;
    }
    ShowWindow(window, showCommand);
    UpdateWindow(window);
    MSG message{};
    BOOL result;
    while ((result = GetMessageW(&message, nullptr, 0, 0)) > 0) {
        // Leave keys inside the WebView to Chromium, including form Tab/arrow keys.
        if (app->IsNativeControl(message.hwnd) && IsDialogMessageW(window, &message)) continue;
        TranslateMessage(&message);
        DispatchMessageW(&message);
    }
    app.reset();
    CoUninitialize();
    return result == -1 ? 1 : static_cast<int>(message.wParam);
}
