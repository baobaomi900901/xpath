#include <windows.h>
#include <algorithm>
#include <array>
#include <filesystem>
#include <string>

#include "include/cef_app.h"
#include "include/cef_browser.h"
#include "include/cef_client.h"
#include "include/cef_command_line.h"
#include "include/cef_version.h"
#include "include/wrapper/cef_helpers.h"

namespace {
constexpr wchar_t kWindowClass[] = L"XPathCefRange";
constexpr int kMenuId = 1001;
constexpr int kAddressId = 1002;
constexpr int kRefreshId = 1003;
constexpr int kStatusId = 1004;
constexpr wchar_t kDefaultBase[] = L"https://baobaomi900901.github.io/xpath/#/";
struct Page { const wchar_t* label; const wchar_t* route; };
constexpr std::array<Page, 3> kPages{{
    {L"点击测试", L"keys-click-test"},
    {L"表单测试", L"form-controls"},
    {L"iframe表单", L"iframe-shadow-form"},
}};

std::filesystem::path ExecutableDirectory() {
    std::wstring buffer(32768, L'\0');
    const DWORD length = GetModuleFileNameW(nullptr, buffer.data(), static_cast<DWORD>(buffer.size()));
    if (!length || length >= buffer.size()) return {};
    buffer.resize(length);
    return std::filesystem::path(buffer).parent_path();
}

UINT WindowDpi(HWND window) {
    using GetDpi = UINT(WINAPI*)(HWND);
    const auto getDpi = reinterpret_cast<GetDpi>(GetProcAddress(GetModuleHandleW(L"user32.dll"), "GetDpiForWindow"));
    return getDpi ? getDpi(window) : 96;
}

class App;
class Client final : public CefClient, public CefLifeSpanHandler,
                     public CefLoadHandler, public CefDisplayHandler {
public:
    explicit Client(App* app) : app_(app) {}
    CefRefPtr<CefLifeSpanHandler> GetLifeSpanHandler() override { return this; }
    CefRefPtr<CefLoadHandler> GetLoadHandler() override { return this; }
    CefRefPtr<CefDisplayHandler> GetDisplayHandler() override { return this; }
    void OnAfterCreated(CefRefPtr<CefBrowser> browser) override;
    bool OnBeforePopup(CefRefPtr<CefBrowser>, CefRefPtr<CefFrame>,
#if CEF_VERSION_MAJOR >= 133
                       int,
#endif
                       const CefString&, const CefString&, WindowOpenDisposition, bool,
                       const CefPopupFeatures&, CefWindowInfo&, CefRefPtr<CefClient>&,
                       CefBrowserSettings&, CefRefPtr<CefDictionaryValue>&, bool*) override {
        // This range owns one embedded browser; popups must not replace it.
        return true;
    }
    bool DoClose(CefRefPtr<CefBrowser> browser) override;
    void OnBeforeClose(CefRefPtr<CefBrowser> browser) override;
    void OnLoadingStateChange(CefRefPtr<CefBrowser>, bool loading, bool, bool) override;
    void OnLoadError(CefRefPtr<CefBrowser>, CefRefPtr<CefFrame> frame,
                     ErrorCode code, const CefString& text, const CefString&) override;
    void OnAddressChange(CefRefPtr<CefBrowser> browser, CefRefPtr<CefFrame> frame,
                         const CefString& url) override;
private:
    App* app_;
    IMPLEMENT_REFCOUNTING(Client);
};

class App {
public:
    HWND window = nullptr;
    CefRefPtr<CefBrowser> browser;
    CefRefPtr<Client> client;
    bool closing = false;
    bool closeReady = false;
    bool creating = false;
    bool loadFailed = false;

    explicit App(std::wstring base) : base_(std::move(base)) {
        if (base_.empty()) base_ = kDefaultBase;
        if (base_.back() != L'/') base_ += L'/';
    }
    ~App() { if (font_) DeleteObject(font_); }
    std::wstring SelectedUrl() const { return base_ + kPages[selected_].route; }
    int Scale(int value) const { return MulDiv(value, static_cast<int>(dpi_), 96); }

    HWND Control(const wchar_t* type, const wchar_t* label, DWORD style, int id, DWORD extended = 0) {
        return CreateWindowExW(extended, type, label, WS_CHILD | WS_VISIBLE | style,
            0, 0, 1, 1, window, reinterpret_cast<HMENU>(static_cast<INT_PTR>(id)),
            GetModuleHandleW(nullptr), nullptr);
    }
    bool CreateControls() {
        heading_ = Control(L"STATIC", L"测试菜单", SS_LEFT, 0);
        menu_ = Control(L"LISTBOX", L"测试菜单", LBS_NOTIFY | LBS_NOINTEGRALHEIGHT | WS_TABSTOP | WS_VSCROLL,
            kMenuId, WS_EX_CLIENTEDGE);
        const std::wstring note = L"CEF " + std::to_wstring(CEF_VERSION_MAJOR) + L" / Chromium " +
            std::to_wstring(CHROME_VERSION_MAJOR) + L"\r\n原生窗口嵌入";
        note_ = Control(L"STATIC", note.c_str(), SS_LEFT, 0);
        address_ = Control(L"EDIT", SelectedUrl().c_str(), ES_READONLY | ES_AUTOHSCROLL | WS_TABSTOP,
            kAddressId, WS_EX_CLIENTEDGE);
        refresh_ = Control(L"BUTTON", L"刷新", BS_PUSHBUTTON | WS_TABSTOP, kRefreshId);
        status_ = Control(L"STATIC", L"正在初始化 CEF…", SS_LEFT | SS_NOPREFIX, kStatusId);
        if (!heading_ || !menu_ || !note_ || !address_ || !refresh_ || !status_) return false;
        for (const auto& page : kPages) SendMessageW(menu_, LB_ADDSTRING, 0, reinterpret_cast<LPARAM>(page.label));
        SendMessageW(menu_, LB_SETCURSEL, 0, 0);
        EnableWindow(refresh_, FALSE);
        UpdateFont();
        Layout();
        return true;
    }
    void UpdateFont() {
        dpi_ = WindowDpi(window);
        HFONT next = CreateFontW(-Scale(16), 0, 0, 0, FW_NORMAL, FALSE, FALSE, FALSE,
            DEFAULT_CHARSET, OUT_DEFAULT_PRECIS, CLIP_DEFAULT_PRECIS, CLEARTYPE_QUALITY,
            DEFAULT_PITCH | FF_DONTCARE, L"Microsoft YaHei UI");
        if (!next) return;
        for (HWND control : {heading_, menu_, note_, address_, refresh_, status_}) {
            SendMessageW(control, WM_SETFONT, reinterpret_cast<WPARAM>(next), TRUE);
        }
        SendMessageW(menu_, LB_SETITEMHEIGHT, 0, Scale(42));
        if (font_) DeleteObject(font_);
        font_ = next;
    }
    CefRect BrowserRect() const {
        RECT area{};
        GetClientRect(window, &area);
        const int width = static_cast<int>(area.right);
        const int height = static_cast<int>(area.bottom);
        const int left = Scale(220);
        const int top = Scale(52);
        return CefRect(left, top, std::max(1, width - left - Scale(12)),
            std::max(1, height - top - Scale(34)));
    }
    void Layout() {
        if (!menu_) return;
        RECT area{};
        GetClientRect(window, &area);
        const int width = static_cast<int>(area.right);
        const int height = static_cast<int>(area.bottom);
        const int pad = Scale(12);
        const int sidebar = Scale(220);
        const int contentWidth = std::max(1, width - sidebar - pad);
        MoveWindow(heading_, pad, pad, sidebar - 2 * pad, Scale(24), TRUE);
        MoveWindow(menu_, pad, Scale(48), sidebar - 2 * pad, std::max(1, height - Scale(130)), TRUE);
        MoveWindow(note_, pad, std::max(Scale(48), height - Scale(70)), sidebar - 2 * pad, Scale(56), TRUE);
        MoveWindow(address_, sidebar, pad, std::max(1, contentWidth - Scale(88)), Scale(30), TRUE);
        MoveWindow(refresh_, std::max(sidebar, width - pad - Scale(76)), pad, Scale(76), Scale(30), TRUE);
        MoveWindow(status_, sidebar, std::max(0, height - Scale(28)), contentWidth, Scale(22), TRUE);
        if (browser) {
            const auto bounds = BrowserRect();
            SetWindowPos(browser->GetHost()->GetWindowHandle(), nullptr, bounds.x, bounds.y,
                bounds.width, bounds.height, SWP_NOZORDER | SWP_NOACTIVATE);
            browser->GetHost()->NotifyMoveOrResizeStarted();
        }
    }
    void SetStatus(const std::wstring& value) {
        if (window && status_) SetWindowTextW(status_, value.c_str());
    }
    void Navigate() {
        if (closing) return;
        const auto index = SendMessageW(menu_, LB_GETCURSEL, 0, 0);
        if (index < 0 || index >= static_cast<LRESULT>(kPages.size())) return;
        selected_ = static_cast<size_t>(index);
        SetWindowTextW(address_, SelectedUrl().c_str());
        loadFailed = false;
        SetStatus(L"正在加载…");
        if (browser) browser->GetMainFrame()->LoadURL(SelectedUrl());
    }
    void Refresh() {
        if (!browser || closing) return;
        loadFailed = false;
        SetStatus(L"正在加载…");
        browser->ReloadIgnoreCache();
    }
    bool StartBrowser() {
        client = new Client(this);
        CefWindowInfo info;
        info.SetAsChild(window, BrowserRect());
#if CEF_VERSION_MAJOR >= 125
        info.runtime_style = CEF_RUNTIME_STYLE_ALLOY;
#endif
        CefBrowserSettings settings;
        creating = CefBrowserHost::CreateBrowser(info, client, SelectedUrl(), settings, nullptr, nullptr);
        if (!creating) SetStatus(L"CEF 浏览器创建失败，请查看 cef.log。");
        return creating;
    }
    void BrowserCreated(CefRefPtr<CefBrowser> value) {
        creating = false;
        browser = value;
        browser->GetHost()->SetAccessibilityState(STATE_ENABLED);
        if (closing) { browser->GetHost()->CloseBrowser(true); return; }
        EnableWindow(refresh_, TRUE);
        Layout();
        if (browser->GetMainFrame()->GetURL().ToWString() != SelectedUrl()) Navigate();
    }
    void Close() {
        if (closing) {
            // CEF sends a second WM_CLOSE after DoClose. Destroy the HWND then,
            // and keep the message loop alive until OnBeforeClose.
            if (closeReady && window) DestroyWindow(window);
            return;
        }
        closing = true;
        EnableWindow(menu_, FALSE);
        EnableWindow(refresh_, FALSE);
        if (browser) browser->GetHost()->CloseBrowser(true);
        else if (!creating) DestroyWindow(window);
    }
private:
    std::wstring base_;
    size_t selected_ = 0;
    UINT dpi_ = 96;
    HFONT font_ = nullptr;
    HWND heading_ = nullptr;
    HWND menu_ = nullptr;
    HWND note_ = nullptr;
    HWND address_ = nullptr;
    HWND refresh_ = nullptr;
    HWND status_ = nullptr;
};

void Client::OnAfterCreated(CefRefPtr<CefBrowser> browser) {
    CEF_REQUIRE_UI_THREAD();
    app_->BrowserCreated(browser);
}
bool Client::DoClose(CefRefPtr<CefBrowser> browser) {
    CEF_REQUIRE_UI_THREAD();
    if (app_->browser && app_->browser->IsSame(browser)) {
        app_->closing = true;
        app_->closeReady = true;
    }
    return false;
}
void Client::OnBeforeClose(CefRefPtr<CefBrowser> browser) {
    CEF_REQUIRE_UI_THREAD();
    if (!app_->browser || !app_->browser->IsSame(browser)) return;
    app_->browser = nullptr;
    if (app_->window) DestroyWindow(app_->window);
    else CefQuitMessageLoop();
}
void Client::OnLoadingStateChange(CefRefPtr<CefBrowser>, bool loading, bool, bool) {
    CEF_REQUIRE_UI_THREAD();
    if (loading) { app_->loadFailed = false; app_->SetStatus(L"正在加载…"); }
    else if (!app_->loadFailed) app_->SetStatus(L"加载完成");
}
void Client::OnLoadError(CefRefPtr<CefBrowser>, CefRefPtr<CefFrame> frame,
                         ErrorCode code, const CefString& text, const CefString&) {
    CEF_REQUIRE_UI_THREAD();
    if (!frame->IsMain() || code == ERR_ABORTED) return;
    app_->loadFailed = true;
    app_->SetStatus(L"加载失败（" + std::to_wstring(code) + L"）：" + text.ToWString());
}
void Client::OnAddressChange(CefRefPtr<CefBrowser> browser, CefRefPtr<CefFrame> frame, const CefString& url) {
    CEF_REQUIRE_UI_THREAD();
    if (frame->IsMain() && !browser->IsLoading() && url.ToWString() == app_->SelectedUrl() && !app_->loadFailed) {
        app_->SetStatus(L"加载完成");
    }
}

LRESULT CALLBACK WindowProc(HWND window, UINT message, WPARAM wParam, LPARAM lParam) {
    App* app = reinterpret_cast<App*>(GetWindowLongPtrW(window, GWLP_USERDATA));
    if (message == WM_NCCREATE) {
        app = static_cast<App*>(reinterpret_cast<CREATESTRUCTW*>(lParam)->lpCreateParams);
        app->window = window;
        SetWindowLongPtrW(window, GWLP_USERDATA, reinterpret_cast<LONG_PTR>(app));
    }
    if (!app) return DefWindowProcW(window, message, wParam, lParam);
    switch (message) {
        case WM_COMMAND:
            if (LOWORD(wParam) == kMenuId && HIWORD(wParam) == LBN_SELCHANGE) app->Navigate();
            else if (LOWORD(wParam) == kRefreshId && HIWORD(wParam) == BN_CLICKED) app->Refresh();
            break;
        case WM_SIZE: app->Layout(); break;
        case WM_MOVE:
            if (app->browser) app->browser->GetHost()->NotifyMoveOrResizeStarted();
            break;
        case WM_DPICHANGED: {
            app->UpdateFont();
            const auto* bounds = reinterpret_cast<RECT*>(lParam);
            SetWindowPos(window, nullptr, bounds->left, bounds->top, bounds->right - bounds->left,
                bounds->bottom - bounds->top, SWP_NOZORDER | SWP_NOACTIVATE);
            app->Layout();
            break;
        }
        case WM_GETMINMAXINFO: {
            auto* info = reinterpret_cast<MINMAXINFO*>(lParam);
            info->ptMinTrackSize = {app->Scale(800), app->Scale(600)};
            break;
        }
        case WM_CLOSE: app->Close(); return 0;
        case WM_DESTROY:
            app->window = nullptr;
            if (!app->browser && !app->creating) CefQuitMessageLoop();
            return 0;
        case WM_NCDESTROY: SetWindowLongPtrW(window, GWLP_USERDATA, 0); break;
    }
    return DefWindowProcW(window, message, wParam, lParam);
}
}  // namespace

int APIENTRY wWinMain(HINSTANCE instance, HINSTANCE, LPWSTR, int showCommand) {
    CefMainArgs args(instance);
    const int subprocessCode = CefExecuteProcess(args, nullptr, nullptr);
    if (subprocessCode >= 0) return subprocessCode;
    const auto directory = ExecutableDirectory();
    if (directory.empty()) return 1;
    auto command = CefCommandLine::CreateCommandLine();
    command->InitFromString(GetCommandLineW());
    std::wstring base = command->HasSwitch("base-url") ? command->GetSwitchValue("base-url").ToWString() : kDefaultBase;
    CefSettings settings;
    settings.no_sandbox = true;
#if CEF_VERSION_MAJOR >= 125 && CEF_VERSION_MAJOR < 128
    settings.chrome_runtime = true;
#endif
    const auto profile = directory.parent_path().parent_path() / L".cache" / L"profiles" /
        std::to_wstring(CEF_VERSION_MAJOR) / (std::to_wstring(GetCurrentProcessId()) + L"-" + std::to_wstring(GetTickCount64()));
    std::error_code error;
    std::filesystem::create_directories(profile, error);
    if (error) {
        MessageBoxW(nullptr, L"无法创建 CEF 缓存目录，请确认靶场目录可写。", L"CEF 靶场", MB_OK | MB_ICONERROR);
        return 1;
    }
    CefString(&settings.cache_path) = profile.wstring();
#if CEF_VERSION_MAJOR >= 120
    CefString(&settings.root_cache_path) = profile.wstring();
#endif
    CefString(&settings.log_file) = (profile / L"cef.log").wstring();
    CefString(&settings.resources_dir_path) = directory.wstring();
    CefString(&settings.locales_dir_path) = (directory / L"locales").wstring();
    CefString(&settings.locale) = "zh-CN";
    if (command->HasSwitch("remote-debugging-port")) {
        const auto value = command->GetSwitchValue("remote-debugging-port").ToWString();
        wchar_t* end = nullptr;
        const long port = wcstol(value.c_str(), &end, 10);
        if (end == value.c_str() || *end || port < 1024 || port > 65535) return 2;
        settings.remote_debugging_port = static_cast<int>(port);
    }
    command = nullptr;
    if (!CefInitialize(args, settings, nullptr, nullptr)) {
#if CEF_VERSION_MAJOR >= 120
        return CefGetExitCode();
#else
        return 1;
#endif
    }
    int result = 0;
    {
        App app(std::move(base));
        WNDCLASSEXW windowClass{sizeof(WNDCLASSEXW)};
        windowClass.lpfnWndProc = WindowProc;
        windowClass.hInstance = instance;
        windowClass.hCursor = LoadCursorW(nullptr, IDC_ARROW);
        windowClass.hbrBackground = reinterpret_cast<HBRUSH>(COLOR_WINDOW + 1);
        windowClass.lpszClassName = kWindowClass;
        RegisterClassExW(&windowClass);
        const auto title = L"CEF " + std::to_wstring(CEF_VERSION_MAJOR) + L" 靶场 - Chromium " +
            CefString(MAKE_STRING(CHROME_VERSION_MAJOR) "." MAKE_STRING(CHROME_VERSION_MINOR) "." MAKE_STRING(CHROME_VERSION_BUILD) "." MAKE_STRING(CHROME_VERSION_PATCH)).ToWString();
        HWND window = CreateWindowExW(0, kWindowClass, title.c_str(), WS_OVERLAPPEDWINDOW | WS_CLIPCHILDREN,
            CW_USEDEFAULT, CW_USEDEFAULT, 1440, 960, nullptr, nullptr, instance, &app);
        if (!window || !app.CreateControls()) {
            if (window) DestroyWindow(window);
            result = 1;
        } else {
            ShowWindow(window, showCommand);
            UpdateWindow(window);
            if (app.StartBrowser()) CefRunMessageLoop();
            else { DestroyWindow(window); result = 1; }
        }
        app.browser = nullptr;
        app.client = nullptr;
    }
    CefShutdown();
    return result;
}
