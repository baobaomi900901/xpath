#include <windows.h>
#include <windowsx.h>
#include <commctrl.h>

#include <algorithm>
#include <array>
#include <string>
#include <vector>

#pragma comment(linker, "/manifestdependency:\"type='win32' name='Microsoft.Windows.Common-Controls' version='6.0.0.0' processorArchitecture='*' publicKeyToken='6595b64144ccf1df' language='*'\"")

namespace {

constexpr wchar_t kMainWindowClass[] = L"XPathWin32ShootingRange";
constexpr wchar_t kPanelWindowClass[] = L"XPathWin32Panel";
constexpr int kPageSize = 20;
constexpr int kDragTargetWidth = 120;
constexpr int kDragTargetHeight = 80;

enum ControlId : int {
    Tab = 100,
    NameEdit,
    PasswordEdit,
    EmailEdit,
    AgeEdit,
    AgeSpin,
    CityCombo,
    CityMultiFirst = 120,
    GenderMale = 130,
    GenderFemale,
    GenderOther,
    HobbyFirst = 140,
    RemarkEdit = 150,
    AgreeCheck,
    SaveButton = 160,
    ResetButton,
    PopupMenuButton = 170,
    EmployeeList = 200,
    FirstPage = 210,
    PreviousPage,
    PageButtonFirst = 220,
    NextPage = 230,
    LastPage,
    DragReset = 300,
    DragCopy,
    DragHide,
    DragArena,
    DragTarget
};

enum MenuCommandId : UINT {
    MenuFileNew = 500,
    MenuFileOpen,
    MenuFileSave,
    MenuEditUndo = 510,
    MenuEditCut,
    MenuEditCopy,
    MenuEditPaste,
    MenuEditSelectAll,
    PopupActionOpen = 520,
    PopupActionCopy,
    PopupActionRename,
    PopupActionDelete,
    PopupActionProperties
};

struct Employee {
    int id;
    std::wstring name;
    std::wstring department;
    std::wstring city;
    std::wstring status;
    std::wstring email;
    std::wstring joinDate;
};

struct AppState {
    HINSTANCE instance{};
    HWND mainWindow{};
    HMENU mainMenu{};
    HWND tab{};
    HWND formPanel{};
    HWND tablePanel{};
    HWND dragPanel{};
    HFONT font{};

    HWND nameEdit{};
    HWND passwordEdit{};
    HWND emailEdit{};
    HWND ageEdit{};
    HWND ageSpin{};
    HWND cityCombo{};
    std::array<HWND, 11> formLabels{};
    std::array<HWND, 5> cityChecks{};
    std::array<HWND, 3> genderRadios{};
    std::array<HWND, 4> hobbyChecks{};
    HWND remarkEdit{};
    HWND agreeCheck{};
    HWND saveButton{};
    HWND resetButton{};
    HWND popupMenuButton{};
    HWND popupMenuStatus{};

    HWND summaryLabel{};
    HWND employeeList{};
    HWND firstButton{};
    HWND previousButton{};
    std::array<HWND, 5> pageButtons{};
    HWND nextButton{};
    HWND lastButton{};
    HWND pageInfoLabel{};

    HWND dragHeading{};
    HWND dragInstructions{};
    HWND dragPositionLabel{};
    HWND dragAnchorLabel{};
    HWND dragResultLabel{};
    HWND dragStatusLabel{};
    HWND dragResetButton{};
    HWND dragCopyButton{};
    HWND dragHideButton{};
    HWND dragArena{};
    HWND dragTarget{};
    bool dragTargetVisible{true};
    bool dragPositionInitialized{};
    bool dragging{};
    int dragLeft{};
    int dragTop{};
    int dragInitialLeft{};
    int dragInitialTop{};
    int dragStartLeft{};
    int dragStartTop{};
    int dragAnchorX{};
    int dragAnchorY{};
    int dragMoveCount{};
    unsigned long long dragStartedAt{};
    unsigned long long dragDuration{};
    std::wstring dragAnchorRegion{L"-"};
    std::wstring dragClipboardStatus;

    std::vector<Employee> employees;
    int currentPage{1};
};

AppState g_app;

HWND CreateControl(
    DWORD extendedStyle,
    const wchar_t* className,
    const wchar_t* text,
    DWORD style,
    HWND parent,
    int id
) {
    HWND control = CreateWindowExW(
        extendedStyle,
        className,
        text,
        WS_CHILD | WS_VISIBLE | style,
        0,
        0,
        0,
        0,
        parent,
        reinterpret_cast<HMENU>(static_cast<INT_PTR>(id)),
        g_app.instance,
        nullptr
    );
    if (control && g_app.font) {
        SendMessageW(control, WM_SETFONT, reinterpret_cast<WPARAM>(g_app.font), TRUE);
    }
    return control;
}

void MoveControl(HWND control, int x, int y, int width, int height) {
    MoveWindow(control, x, y, std::max(0, width), std::max(0, height), TRUE);
}

HWND CreateLabel(HWND parent, const wchar_t* text, int id = 0) {
    return CreateControl(0, WC_STATICW, text, SS_LEFT | SS_CENTERIMAGE, parent, id);
}

HMENU CreateApplicationMenu() {
    HMENU menuBar = CreateMenu();
    HMENU fileMenu = CreatePopupMenu();
    HMENU editMenu = CreatePopupMenu();
    if (!menuBar || !fileMenu || !editMenu) {
        if (fileMenu) {
            DestroyMenu(fileMenu);
        }
        if (editMenu) {
            DestroyMenu(editMenu);
        }
        if (menuBar) {
            DestroyMenu(menuBar);
        }
        return nullptr;
    }

    AppendMenuW(fileMenu, MF_STRING, MenuFileNew, L"新建(&N)");
    AppendMenuW(fileMenu, MF_STRING, MenuFileOpen, L"打开(&O)");
    AppendMenuW(fileMenu, MF_STRING, MenuFileSave, L"保存(&S)");
    AppendMenuW(editMenu, MF_STRING, MenuEditUndo, L"撤销(&U)");
    AppendMenuW(editMenu, MF_SEPARATOR, 0, nullptr);
    AppendMenuW(editMenu, MF_STRING, MenuEditCut, L"剪切(&T)");
    AppendMenuW(editMenu, MF_STRING, MenuEditCopy, L"复制(&C)");
    AppendMenuW(editMenu, MF_STRING, MenuEditPaste, L"粘贴(&P)");
    AppendMenuW(editMenu, MF_SEPARATOR, 0, nullptr);
    AppendMenuW(editMenu, MF_STRING, MenuEditSelectAll, L"全选(&A)");
    AppendMenuW(menuBar, MF_POPUP, reinterpret_cast<UINT_PTR>(fileMenu), L"文件(&F)");
    AppendMenuW(menuBar, MF_POPUP, reinterpret_cast<UINT_PTR>(editMenu), L"编辑(&E)");
    return menuBar;
}

const wchar_t* MenuCommandLabel(UINT command) {
    switch (command) {
        case MenuFileNew: return L"文件 > 新建";
        case MenuFileOpen: return L"文件 > 打开";
        case MenuFileSave: return L"文件 > 保存";
        case MenuEditUndo: return L"编辑 > 撤销";
        case MenuEditCut: return L"编辑 > 剪切";
        case MenuEditCopy: return L"编辑 > 复制";
        case MenuEditPaste: return L"编辑 > 粘贴";
        case MenuEditSelectAll: return L"编辑 > 全选";
        case PopupActionOpen: return L"操作菜单 > 打开";
        case PopupActionCopy: return L"操作菜单 > 复制";
        case PopupActionRename: return L"操作菜单 > 重命名";
        case PopupActionDelete: return L"操作菜单 > 删除";
        case PopupActionProperties: return L"操作菜单 > 属性";
        default: return nullptr;
    }
}

void SetMenuStatus(UINT command) {
    const wchar_t* label = MenuCommandLabel(command);
    if (!label || !g_app.popupMenuStatus) {
        return;
    }
    const std::wstring status = L"最近选择: " + std::wstring(label);
    SetWindowTextW(g_app.popupMenuStatus, status.c_str());
}

void ShowActionPopupMenu() {
    HMENU popup = CreatePopupMenu();
    if (!popup) {
        SetWindowTextW(g_app.popupMenuStatus, L"菜单创建失败");
        return;
    }
    AppendMenuW(popup, MF_STRING, PopupActionOpen, L"打开");
    AppendMenuW(popup, MF_STRING, PopupActionCopy, L"复制");
    AppendMenuW(popup, MF_STRING, PopupActionRename, L"重命名");
    AppendMenuW(popup, MF_STRING, PopupActionDelete, L"删除");
    AppendMenuW(popup, MF_SEPARATOR, 0, nullptr);
    AppendMenuW(popup, MF_STRING, PopupActionProperties, L"属性");

    RECT buttonBounds{};
    GetWindowRect(g_app.popupMenuButton, &buttonBounds);
    const UINT command = static_cast<UINT>(TrackPopupMenuEx(
        popup,
        TPM_LEFTALIGN | TPM_TOPALIGN | TPM_RIGHTBUTTON | TPM_RETURNCMD,
        buttonBounds.left,
        buttonBounds.bottom,
        g_app.mainWindow,
        nullptr
    ));
    DestroyMenu(popup);
    if (command != 0) {
        SetMenuStatus(command);
    }
}

std::wstring DragAnchorRegion(int x, int y) {
    const int column = std::clamp(x * 3 / kDragTargetWidth, 0, 2);
    const int row = std::clamp(y * 3 / kDragTargetHeight, 0, 2);
    constexpr std::array<const wchar_t*, 9> regions = {
        L"topLeft", L"topCenter", L"topRight",
        L"middleLeft", L"middleCenter", L"middleRight",
        L"bottomLeft", L"bottomCenter", L"bottomRight"
    };
    return regions[row * 3 + column];
}

std::wstring DragStateJson() {
    return L"{\"left\":" + std::to_wstring(g_app.dragLeft)
        + L",\"top\":" + std::to_wstring(g_app.dragTop)
        + L",\"initialLeft\":" + std::to_wstring(g_app.dragInitialLeft)
        + L",\"initialTop\":" + std::to_wstring(g_app.dragInitialTop)
        + L",\"deltaLeft\":" + std::to_wstring(g_app.dragLeft - g_app.dragInitialLeft)
        + L",\"deltaTop\":" + std::to_wstring(g_app.dragTop - g_app.dragInitialTop)
        + L",\"startLeft\":" + std::to_wstring(g_app.dragStartLeft)
        + L",\"startTop\":" + std::to_wstring(g_app.dragStartTop)
        + L",\"sessionDeltaLeft\":" + std::to_wstring(g_app.dragLeft - g_app.dragStartLeft)
        + L",\"sessionDeltaTop\":" + std::to_wstring(g_app.dragTop - g_app.dragStartTop)
        + L",\"anchor\":{\"x\":" + std::to_wstring(g_app.dragAnchorX)
        + L",\"y\":" + std::to_wstring(g_app.dragAnchorY)
        + L",\"sudokuPart\":\"" + g_app.dragAnchorRegion
        + L"\"},\"moveCount\":" + std::to_wstring(g_app.dragMoveCount)
        + L",\"durationMs\":" + std::to_wstring(g_app.dragDuration)
        + L",\"dragging\":" + (g_app.dragging ? L"true" : L"false") + L"}";
}

bool CopyUnicodeText(HWND owner, const std::wstring& text) {
    if (!OpenClipboard(owner)) {
        return false;
    }
    if (!EmptyClipboard()) {
        CloseClipboard();
        return false;
    }

    const SIZE_T bytes = (text.size() + 1) * sizeof(wchar_t);
    HGLOBAL memory = GlobalAlloc(GMEM_MOVEABLE, bytes);
    if (!memory) {
        CloseClipboard();
        return false;
    }
    void* destination = GlobalLock(memory);
    if (!destination) {
        GlobalFree(memory);
        CloseClipboard();
        return false;
    }
    CopyMemory(destination, text.c_str(), bytes);
    GlobalUnlock(memory);
    if (!SetClipboardData(CF_UNICODETEXT, memory)) {
        GlobalFree(memory);
        CloseClipboard();
        return false;
    }
    CloseClipboard();
    return true;
}

void UpdateDragLabels();

void CopyDragState() {
    const bool copied = CopyUnicodeText(g_app.mainWindow, DragStateJson());
    g_app.dragClipboardStatus = copied ? L"已复制当前结果" : L"复制失败（剪贴板可能正被占用）";
    UpdateDragLabels();
}

void UpdateDragLabels() {
    if (!g_app.dragPositionLabel) {
        return;
    }

    const int deltaLeft = g_app.dragLeft - g_app.dragInitialLeft;
    const int deltaTop = g_app.dragTop - g_app.dragInitialTop;
    const int sessionDeltaLeft = g_app.dragLeft - g_app.dragStartLeft;
    const int sessionDeltaTop = g_app.dragTop - g_app.dragStartTop;
    const std::wstring position = L"当前位置: left=" + std::to_wstring(g_app.dragLeft)
        + L", top=" + std::to_wstring(g_app.dragTop)
        + L"    相对初始: Δleft=" + std::to_wstring(deltaLeft)
        + L", Δtop=" + std::to_wstring(deltaTop);
    const std::wstring anchor = L"按下锚点: x=" + std::to_wstring(g_app.dragAnchorX)
        + L", y=" + std::to_wstring(g_app.dragAnchorY)
        + L", sudoku_part=" + g_app.dragAnchorRegion;
    const std::wstring result = L"本次拖拽: Δleft=" + std::to_wstring(sessionDeltaLeft)
        + L", Δtop=" + std::to_wstring(sessionDeltaTop)
        + L", move=" + std::to_wstring(g_app.dragMoveCount)
        + L", duration=" + std::to_wstring(g_app.dragDuration) + L"ms";

    SetWindowTextW(g_app.dragPositionLabel, position.c_str());
    SetWindowTextW(g_app.dragAnchorLabel, anchor.c_str());
    SetWindowTextW(g_app.dragResultLabel, result.c_str());
    const std::wstring status = g_app.dragging
        ? L"状态: 拖拽中"
        : (g_app.dragClipboardStatus.empty() ? L"状态: 空闲" : L"状态: " + g_app.dragClipboardStatus);
    SetWindowTextW(g_app.dragStatusLabel, status.c_str());
}

void PositionDragTarget(bool resetToCenter) {
    if (!g_app.dragArena || !g_app.dragTarget) {
        return;
    }

    RECT arena{};
    GetClientRect(g_app.dragArena, &arena);
    const int maxLeft = std::max(0, static_cast<int>(arena.right) - kDragTargetWidth);
    const int maxTop = std::max(0, static_cast<int>(arena.bottom) - kDragTargetHeight);
    if (resetToCenter || !g_app.dragPositionInitialized) {
        g_app.dragLeft = maxLeft / 2;
        g_app.dragTop = maxTop / 2;
        g_app.dragInitialLeft = g_app.dragLeft;
        g_app.dragInitialTop = g_app.dragTop;
        g_app.dragStartLeft = g_app.dragLeft;
        g_app.dragStartTop = g_app.dragTop;
        g_app.dragAnchorX = kDragTargetWidth / 2;
        g_app.dragAnchorY = kDragTargetHeight / 2;
        g_app.dragAnchorRegion = L"middleCenter";
        g_app.dragMoveCount = 0;
        g_app.dragDuration = 0;
        g_app.dragClipboardStatus.clear();
        g_app.dragPositionInitialized = true;
    } else {
        g_app.dragLeft = std::clamp(g_app.dragLeft, 0, maxLeft);
        g_app.dragTop = std::clamp(g_app.dragTop, 0, maxTop);
    }
    MoveControl(g_app.dragTarget, g_app.dragLeft, g_app.dragTop, kDragTargetWidth, kDragTargetHeight);
    UpdateDragLabels();
}

void BeginDragTarget(HWND target, int anchorX, int anchorY) {
    g_app.dragging = true;
    g_app.dragStartLeft = g_app.dragLeft;
    g_app.dragStartTop = g_app.dragTop;
    g_app.dragAnchorX = std::clamp(anchorX, 0, kDragTargetWidth - 1);
    g_app.dragAnchorY = std::clamp(anchorY, 0, kDragTargetHeight - 1);
    g_app.dragAnchorRegion = DragAnchorRegion(g_app.dragAnchorX, g_app.dragAnchorY);
    g_app.dragMoveCount = 0;
    g_app.dragDuration = 0;
    g_app.dragClipboardStatus.clear();
    g_app.dragStartedAt = GetTickCount64();
    SetFocus(target);
    SetCapture(target);
    UpdateDragLabels();
}

void MoveDragTarget(HWND target, int x, int y) {
    if (!g_app.dragging || GetCapture() != g_app.dragTarget) {
        return;
    }

    POINT cursor{x, y};
    ClientToScreen(target, &cursor);
    ScreenToClient(g_app.dragArena, &cursor);
    RECT arena{};
    GetClientRect(g_app.dragArena, &arena);
    const int nextLeft = std::clamp(
        static_cast<int>(cursor.x) - g_app.dragAnchorX,
        0,
        std::max(0, static_cast<int>(arena.right) - kDragTargetWidth)
    );
    const int nextTop = std::clamp(
        static_cast<int>(cursor.y) - g_app.dragAnchorY,
        0,
        std::max(0, static_cast<int>(arena.bottom) - kDragTargetHeight)
    );
    if (nextLeft == g_app.dragLeft && nextTop == g_app.dragTop) {
        return;
    }
    g_app.dragLeft = nextLeft;
    g_app.dragTop = nextTop;
    ++g_app.dragMoveCount;
    MoveControl(g_app.dragTarget, g_app.dragLeft, g_app.dragTop, kDragTargetWidth, kDragTargetHeight);
    UpdateDragLabels();
}

void EndDragTarget() {
    if (!g_app.dragging) {
        return;
    }
    g_app.dragging = false;
    g_app.dragDuration = GetTickCount64() - g_app.dragStartedAt;
    if (GetCapture() == g_app.dragTarget) {
        ReleaseCapture();
    }
    UpdateDragLabels();
}

LRESULT CALLBACK DragTargetSubclass(
    HWND window,
    UINT message,
    WPARAM wParam,
    LPARAM lParam,
    UINT_PTR,
    DWORD_PTR
) {
    switch (message) {
        case WM_LBUTTONDOWN:
            BeginDragTarget(window, GET_X_LPARAM(lParam), GET_Y_LPARAM(lParam));
            return 0;
        case WM_MOUSEMOVE:
            if ((wParam & MK_LBUTTON) != 0) {
                MoveDragTarget(window, GET_X_LPARAM(lParam), GET_Y_LPARAM(lParam));
                return 0;
            }
            break;
        case WM_LBUTTONUP:
            MoveDragTarget(window, GET_X_LPARAM(lParam), GET_Y_LPARAM(lParam));
            EndDragTarget();
            return 0;
        case WM_CAPTURECHANGED:
            EndDragTarget();
            return 0;
        case WM_NCDESTROY:
            RemoveWindowSubclass(window, DragTargetSubclass, 1);
            break;
        default:
            break;
    }
    return DefSubclassProc(window, message, wParam, lParam);
}

bool CreateDragTargetControl() {
    if (g_app.dragTarget) {
        return true;
    }
    g_app.dragTarget = CreateControl(
        0,
        WC_BUTTONW,
        L"drag-target",
        BS_PUSHBUTTON | WS_TABSTOP,
        g_app.dragArena,
        DragTarget
    );
    if (!g_app.dragTarget) {
        g_app.dragTargetVisible = false;
        return false;
    }
    SetWindowSubclass(g_app.dragTarget, DragTargetSubclass, 1, 0);
    g_app.dragTargetVisible = true;
    return true;
}

void HideDragTarget() {
    EndDragTarget();
    if (g_app.dragTarget && !DestroyWindow(g_app.dragTarget)) {
        g_app.dragClipboardStatus = L"隐藏失败";
        UpdateDragLabels();
        return;
    }
    g_app.dragTarget = nullptr;
    g_app.dragTargetVisible = false;
    g_app.dragClipboardStatus = L"元素已隐藏";
    EnableWindow(g_app.dragHideButton, FALSE);
    UpdateDragLabels();
}

void ResetDragTarget() {
    EndDragTarget();
    if (!CreateDragTargetControl()) {
        g_app.dragClipboardStatus = L"恢复失败";
        UpdateDragLabels();
        return;
    }
    EnableWindow(g_app.dragHideButton, TRUE);
    PositionDragTarget(true);
}

void BuildEmployees() {
    constexpr std::array<const wchar_t*, 5> departments = {
        L"研发部", L"产品部", L"市场部", L"销售部", L"人事部"
    };
    constexpr std::array<const wchar_t*, 5> cities = {
        L"北京", L"上海", L"广州", L"深圳", L"杭州"
    };
    constexpr std::array<const wchar_t*, 3> statuses = {
        L"在职", L"离职", L"待入职"
    };

    g_app.employees.reserve(1000);
    for (int id = 1; id <= 1000; ++id) {
        wchar_t date[16]{};
        swprintf_s(date, L"2024-%02d-%02d", (id % 12) + 1, (id % 28) + 1);
        g_app.employees.push_back(Employee{
            id,
            L"用户" + std::to_wstring(id),
            departments[id % departments.size()],
            cities[id % cities.size()],
            statuses[id % statuses.size()],
            L"user" + std::to_wstring(id) + L"@example.com",
            date
        });
    }
}

void CreateFormControls() {
    HWND panel = g_app.formPanel;
    g_app.formLabels[0] = CreateLabel(panel, L"用户信息表单");
    g_app.formLabels[1] = CreateLabel(panel, L"姓名");
    g_app.nameEdit = CreateControl(WS_EX_CLIENTEDGE, WC_EDITW, L"", ES_AUTOHSCROLL | WS_TABSTOP, panel, NameEdit);
    g_app.formLabels[2] = CreateLabel(panel, L"密码");
    g_app.passwordEdit = CreateControl(WS_EX_CLIENTEDGE, WC_EDITW, L"", ES_PASSWORD | ES_AUTOHSCROLL | WS_TABSTOP, panel, PasswordEdit);
    g_app.formLabels[3] = CreateLabel(panel, L"邮箱");
    g_app.emailEdit = CreateControl(WS_EX_CLIENTEDGE, WC_EDITW, L"", ES_AUTOHSCROLL | WS_TABSTOP, panel, EmailEdit);
    g_app.formLabels[4] = CreateLabel(panel, L"年龄");
    g_app.ageEdit = CreateControl(WS_EX_CLIENTEDGE, WC_EDITW, L"25", ES_NUMBER | ES_AUTOHSCROLL | WS_TABSTOP, panel, AgeEdit);
    g_app.ageSpin = CreateControl(0, UPDOWN_CLASSW, L"", UDS_ALIGNRIGHT | UDS_ARROWKEYS | UDS_SETBUDDYINT, panel, AgeSpin);
    SendMessageW(g_app.ageSpin, UDM_SETBUDDY, reinterpret_cast<WPARAM>(g_app.ageEdit), 0);
    SendMessageW(g_app.ageSpin, UDM_SETRANGE32, 18, 80);
    SendMessageW(g_app.ageSpin, UDM_SETPOS32, 0, 25);

    constexpr std::array<const wchar_t*, 5> cities = {L"北京", L"上海", L"广州", L"深圳", L"杭州"};
    g_app.formLabels[5] = CreateLabel(panel, L"城市（单选）");
    g_app.cityCombo = CreateControl(0, WC_COMBOBOXW, L"", CBS_DROPDOWNLIST | WS_VSCROLL | WS_TABSTOP, panel, CityCombo);
    for (const wchar_t* city : cities) {
        SendMessageW(g_app.cityCombo, CB_ADDSTRING, 0, reinterpret_cast<LPARAM>(city));
    }
    SendMessageW(g_app.cityCombo, CB_SETCURSEL, 0, 0);

    g_app.formLabels[6] = CreateLabel(panel, L"城市（多选）");
    for (size_t index = 0; index < cities.size(); ++index) {
        g_app.cityChecks[index] = CreateControl(
            0,
            WC_BUTTONW,
            cities[index],
            BS_AUTOCHECKBOX | WS_TABSTOP,
            panel,
            CityMultiFirst + static_cast<int>(index)
        );
    }

    constexpr std::array<const wchar_t*, 3> genders = {L"男", L"女", L"其他"};
    g_app.formLabels[7] = CreateLabel(panel, L"性别（单选）");
    for (size_t index = 0; index < genders.size(); ++index) {
        DWORD style = BS_AUTORADIOBUTTON | WS_TABSTOP;
        if (index == 0) {
            style |= WS_GROUP;
        }
        g_app.genderRadios[index] = CreateControl(
            0,
            WC_BUTTONW,
            genders[index],
            style,
            panel,
            GenderMale + static_cast<int>(index)
        );
    }
    SendMessageW(g_app.genderRadios[0], BM_SETCHECK, BST_CHECKED, 0);

    constexpr std::array<const wchar_t*, 4> hobbies = {L"阅读", L"运动", L"音乐", L"旅行"};
    g_app.formLabels[8] = CreateLabel(panel, L"兴趣爱好（多选）");
    for (size_t index = 0; index < hobbies.size(); ++index) {
        g_app.hobbyChecks[index] = CreateControl(
            0,
            WC_BUTTONW,
            hobbies[index],
            BS_AUTOCHECKBOX | WS_TABSTOP,
            panel,
            HobbyFirst + static_cast<int>(index)
        );
    }

    g_app.formLabels[9] = CreateLabel(panel, L"备注");
    g_app.remarkEdit = CreateControl(
        WS_EX_CLIENTEDGE,
        WC_EDITW,
        L"",
        ES_MULTILINE | ES_AUTOVSCROLL | ES_WANTRETURN | WS_VSCROLL | WS_TABSTOP,
        panel,
        RemarkEdit
    );
    g_app.formLabels[10] = CreateLabel(panel, L"协议");
    g_app.agreeCheck = CreateControl(0, WC_BUTTONW, L"同意用户协议", BS_AUTOCHECKBOX | WS_TABSTOP, panel, AgreeCheck);
    g_app.saveButton = CreateControl(0, WC_BUTTONW, L"保存", BS_PUSHBUTTON | WS_TABSTOP, panel, SaveButton);
    g_app.resetButton = CreateControl(0, WC_BUTTONW, L"重置", BS_PUSHBUTTON | WS_TABSTOP, panel, ResetButton);
    g_app.popupMenuButton = CreateControl(
        0,
        WC_BUTTONW,
        L"展开原生菜单 ▼",
        BS_PUSHBUTTON | WS_TABSTOP,
        panel,
        PopupMenuButton
    );
    g_app.popupMenuStatus = CreateLabel(panel, L"菜单测试: 尚未选择菜单项");
}

void CreateTableControls() {
    HWND panel = g_app.tablePanel;
    g_app.summaryLabel = CreateLabel(panel, L"共 1000 条数据，每页 20 条");
    g_app.employeeList = CreateControl(
        WS_EX_CLIENTEDGE,
        WC_LISTVIEWW,
        L"员工数据表格",
        LVS_REPORT | LVS_SINGLESEL | LVS_SHOWSELALWAYS | WS_TABSTOP,
        panel,
        EmployeeList
    );
    ListView_SetExtendedListViewStyle(
        g_app.employeeList,
        LVS_EX_FULLROWSELECT | LVS_EX_GRIDLINES | LVS_EX_DOUBLEBUFFER | LVS_EX_LABELTIP
    );

    constexpr std::array<const wchar_t*, 7> columns = {
        L"ID", L"姓名", L"部门", L"城市", L"状态", L"邮箱", L"入职日期"
    };
    constexpr std::array<int, 7> widths = {60, 100, 100, 90, 90, 240, 120};
    for (int index = 0; index < static_cast<int>(columns.size()); ++index) {
        LVCOLUMNW column{};
        column.mask = LVCF_TEXT | LVCF_WIDTH | LVCF_SUBITEM;
        column.pszText = const_cast<wchar_t*>(columns[index]);
        column.cx = widths[index];
        column.iSubItem = index;
        ListView_InsertColumn(g_app.employeeList, index, &column);
    }

    g_app.firstButton = CreateControl(0, WC_BUTTONW, L"首页", BS_PUSHBUTTON | WS_TABSTOP, panel, FirstPage);
    g_app.previousButton = CreateControl(0, WC_BUTTONW, L"上一页", BS_PUSHBUTTON | WS_TABSTOP, panel, PreviousPage);
    for (int index = 0; index < static_cast<int>(g_app.pageButtons.size()); ++index) {
        g_app.pageButtons[index] = CreateControl(
            0,
            WC_BUTTONW,
            L"",
            BS_PUSHBUTTON | WS_TABSTOP,
            panel,
            PageButtonFirst + index
        );
    }
    g_app.nextButton = CreateControl(0, WC_BUTTONW, L"下一页", BS_PUSHBUTTON | WS_TABSTOP, panel, NextPage);
    g_app.lastButton = CreateControl(0, WC_BUTTONW, L"末页", BS_PUSHBUTTON | WS_TABSTOP, panel, LastPage);
    g_app.pageInfoLabel = CreateLabel(panel, L"");
}

void CreateDragControls() {
    HWND panel = g_app.dragPanel;
    g_app.dragHeading = CreateLabel(panel, L"元素拖拽测试");
    g_app.dragInstructions = CreateLabel(
        panel,
        L"拖拽 drag-target 以校验位移、锚点、轨迹数量和耗时；delay_after 需由调用方统计。"
    );
    g_app.dragPositionLabel = CreateLabel(panel, L"");
    g_app.dragAnchorLabel = CreateLabel(panel, L"");
    g_app.dragResultLabel = CreateLabel(panel, L"");
    g_app.dragStatusLabel = CreateLabel(panel, L"");
    g_app.dragResetButton = CreateControl(
        0,
        WC_BUTTONW,
        L"重置位置",
        BS_PUSHBUTTON | WS_TABSTOP,
        panel,
        DragReset
    );
    g_app.dragCopyButton = CreateControl(
        0,
        WC_BUTTONW,
        L"复制当前结果",
        BS_PUSHBUTTON | WS_TABSTOP,
        panel,
        DragCopy
    );
    g_app.dragHideButton = CreateControl(
        0,
        WC_BUTTONW,
        L"隐藏 drag-target",
        BS_PUSHBUTTON | WS_TABSTOP,
        panel,
        DragHide
    );
    g_app.dragArena = CreateControl(
        WS_EX_CLIENTEDGE | WS_EX_CONTROLPARENT,
        kPanelWindowClass,
        L"拖拽区域",
        WS_BORDER | WS_CLIPCHILDREN,
        panel,
        DragArena
    );
    CreateDragTargetControl();
}

void LayoutFormPanel(int width, int height) {
    constexpr int labelX = 28;
    constexpr int fieldX = 172;
    constexpr int labelWidth = 135;
    constexpr int rowHeight = 30;
    const int fieldWidth = std::max(220, std::min(430, width - fieldX - 30));

    MoveControl(g_app.formLabels[0], labelX, 8, 260, 28);
    const std::array<int, 10> rowY = {42, 84, 126, 168, 210, 252, 294, 336, 378, 470};
    for (int index = 0; index < 10; ++index) {
        MoveControl(g_app.formLabels[index + 1], labelX, rowY[index], labelWidth, rowHeight);
    }

    MoveControl(g_app.nameEdit, fieldX, rowY[0], fieldWidth, rowHeight);
    MoveControl(g_app.passwordEdit, fieldX, rowY[1], fieldWidth, rowHeight);
    MoveControl(g_app.emailEdit, fieldX, rowY[2], fieldWidth, rowHeight);
    MoveControl(g_app.ageEdit, fieldX, rowY[3], 140, rowHeight);
    MoveControl(g_app.ageSpin, fieldX + 116, rowY[3], 24, rowHeight);
    MoveControl(g_app.cityCombo, fieldX, rowY[4], 250, 250);

    for (int index = 0; index < static_cast<int>(g_app.cityChecks.size()); ++index) {
        MoveControl(g_app.cityChecks[index], fieldX + index * 78, rowY[5], 74, rowHeight);
    }
    for (int index = 0; index < static_cast<int>(g_app.genderRadios.size()); ++index) {
        MoveControl(g_app.genderRadios[index], fieldX + index * 88, rowY[6], 82, rowHeight);
    }
    for (int index = 0; index < static_cast<int>(g_app.hobbyChecks.size()); ++index) {
        MoveControl(g_app.hobbyChecks[index], fieldX + index * 88, rowY[7], 82, rowHeight);
    }
    MoveControl(g_app.remarkEdit, fieldX, rowY[8], fieldWidth, 76);
    MoveControl(g_app.agreeCheck, fieldX, rowY[9], 180, rowHeight);

    const int actionY = std::max(515, height - 48);
    MoveControl(g_app.saveButton, width / 2 - 104, actionY, 92, 32);
    MoveControl(g_app.resetButton, width / 2 + 12, actionY, 92, 32);
    MoveControl(g_app.popupMenuButton, width - 198, 8, 168, 32);
    MoveControl(g_app.popupMenuStatus, width - 348, 42, 318, 28);
}

void LayoutTablePanel(int width, int height) {
    MoveControl(g_app.summaryLabel, 18, 12, 280, 30);
    MoveControl(g_app.employeeList, 18, 50, width - 36, std::max(180, height - 145));

    constexpr int buttonHeight = 30;
    constexpr int gap = 6;
    constexpr int edgeWidth = 72;
    constexpr int pageWidth = 42;
    const int totalWidth = edgeWidth * 4 + pageWidth * 5 + gap * 8;
    int x = std::max(18, (width - totalWidth) / 2);
    const int y = height - 82;

    MoveControl(g_app.firstButton, x, y, edgeWidth, buttonHeight);
    x += edgeWidth + gap;
    MoveControl(g_app.previousButton, x, y, edgeWidth, buttonHeight);
    x += edgeWidth + gap;
    for (HWND button : g_app.pageButtons) {
        MoveControl(button, x, y, pageWidth, buttonHeight);
        x += pageWidth + gap;
    }
    MoveControl(g_app.nextButton, x, y, edgeWidth, buttonHeight);
    x += edgeWidth + gap;
    MoveControl(g_app.lastButton, x, y, edgeWidth, buttonHeight);
    MoveControl(g_app.pageInfoLabel, 18, height - 44, width - 36, 28);
}

void LayoutDragPanel(int width, int height) {
    constexpr int margin = 24;
    constexpr int detailsWidth = 310;
    const int arenaX = margin + detailsWidth + 24;
    const int arenaWidth = std::max(320, std::min(560, width - arenaX - margin));
    const int arenaHeight = std::max(280, std::min(420, height - 90));

    MoveControl(g_app.dragHeading, margin, 12, detailsWidth, 30);
    MoveControl(g_app.dragInstructions, margin, 45, width - margin * 2, 30);
    MoveControl(g_app.dragPositionLabel, margin, 90, detailsWidth, 48);
    MoveControl(g_app.dragAnchorLabel, margin, 142, detailsWidth, 48);
    MoveControl(g_app.dragResultLabel, margin, 194, detailsWidth, 64);
    MoveControl(g_app.dragStatusLabel, margin, 262, detailsWidth, 32);
    MoveControl(g_app.dragResetButton, margin, 306, 120, 34);
    MoveControl(g_app.dragCopyButton, margin + 132, 306, 150, 34);
    MoveControl(g_app.dragHideButton, margin, 350, 150, 34);
    MoveControl(g_app.dragArena, arenaX, 86, arenaWidth, arenaHeight);
    PositionDragTarget(false);
}

void LayoutMainWindow() {
    RECT client{};
    GetClientRect(g_app.mainWindow, &client);
    MoveControl(g_app.tab, 8, 8, client.right - 16, client.bottom - 16);

    RECT page{};
    GetClientRect(g_app.tab, &page);
    TabCtrl_AdjustRect(g_app.tab, FALSE, &page);
    const int pageWidth = page.right - page.left;
    const int pageHeight = page.bottom - page.top;
    MoveControl(g_app.formPanel, page.left, page.top, pageWidth, pageHeight);
    MoveControl(g_app.tablePanel, page.left, page.top, pageWidth, pageHeight);
    MoveControl(g_app.dragPanel, page.left, page.top, pageWidth, pageHeight);
    LayoutFormPanel(pageWidth, pageHeight);
    LayoutTablePanel(pageWidth, pageHeight);
    LayoutDragPanel(pageWidth, pageHeight);
}

void ResetForm() {
    SetWindowTextW(g_app.nameEdit, L"");
    SetWindowTextW(g_app.passwordEdit, L"");
    SetWindowTextW(g_app.emailEdit, L"");
    SendMessageW(g_app.ageSpin, UDM_SETPOS32, 0, 25);
    SendMessageW(g_app.cityCombo, CB_SETCURSEL, 0, 0);
    for (HWND check : g_app.cityChecks) {
        SendMessageW(check, BM_SETCHECK, BST_UNCHECKED, 0);
    }
    for (HWND radio : g_app.genderRadios) {
        SendMessageW(radio, BM_SETCHECK, BST_UNCHECKED, 0);
    }
    SendMessageW(g_app.genderRadios[0], BM_SETCHECK, BST_CHECKED, 0);
    for (HWND check : g_app.hobbyChecks) {
        SendMessageW(check, BM_SETCHECK, BST_UNCHECKED, 0);
    }
    SetWindowTextW(g_app.remarkEdit, L"");
    SendMessageW(g_app.agreeCheck, BM_SETCHECK, BST_UNCHECKED, 0);
    SetFocus(g_app.nameEdit);
}

void SetListText(int row, int column, const std::wstring& text) {
    ListView_SetItemText(g_app.employeeList, row, column, const_cast<wchar_t*>(text.c_str()));
}

int TotalPages() {
    return std::max(1, (static_cast<int>(g_app.employees.size()) + kPageSize - 1) / kPageSize);
}

void RefreshTable() {
    const int totalPages = TotalPages();
    g_app.currentPage = std::clamp(g_app.currentPage, 1, totalPages);
    const int firstIndex = (g_app.currentPage - 1) * kPageSize;
    const int lastIndex = std::min(firstIndex + kPageSize, static_cast<int>(g_app.employees.size()));

    SendMessageW(g_app.employeeList, WM_SETREDRAW, FALSE, 0);
    ListView_DeleteAllItems(g_app.employeeList);
    for (int index = firstIndex; index < lastIndex; ++index) {
        const Employee& employee = g_app.employees[index];
        const int row = index - firstIndex;
        const std::wstring id = std::to_wstring(employee.id);
        LVITEMW item{};
        item.mask = LVIF_TEXT;
        item.iItem = row;
        item.pszText = const_cast<wchar_t*>(id.c_str());
        ListView_InsertItem(g_app.employeeList, &item);
        SetListText(row, 1, employee.name);
        SetListText(row, 2, employee.department);
        SetListText(row, 3, employee.city);
        SetListText(row, 4, employee.status);
        SetListText(row, 5, employee.email);
        SetListText(row, 6, employee.joinDate);
    }
    SendMessageW(g_app.employeeList, WM_SETREDRAW, TRUE, 0);
    InvalidateRect(g_app.employeeList, nullptr, TRUE);

    const int windowStart = std::clamp(g_app.currentPage - 2, 1, std::max(1, totalPages - 4));
    for (int index = 0; index < static_cast<int>(g_app.pageButtons.size()); ++index) {
        const int page = windowStart + index;
        HWND button = g_app.pageButtons[index];
        if (page <= totalPages) {
            SetWindowTextW(button, std::to_wstring(page).c_str());
            SetWindowLongPtrW(button, GWLP_USERDATA, page);
            EnableWindow(button, page != g_app.currentPage);
            ShowWindow(button, SW_SHOW);
        } else {
            ShowWindow(button, SW_HIDE);
        }
    }

    EnableWindow(g_app.firstButton, g_app.currentPage > 1);
    EnableWindow(g_app.previousButton, g_app.currentPage > 1);
    EnableWindow(g_app.nextButton, g_app.currentPage < totalPages);
    EnableWindow(g_app.lastButton, g_app.currentPage < totalPages);

    const int displayStart = g_app.employees.empty() ? 0 : firstIndex + 1;
    const std::wstring pageInfo = L"第 " + std::to_wstring(g_app.currentPage) + L" / "
        + std::to_wstring(totalPages) + L" 页，当前显示 " + std::to_wstring(displayStart)
        + L" - " + std::to_wstring(lastIndex) + L" 条";
    SetWindowTextW(g_app.pageInfoLabel, pageInfo.c_str());
}

void GoToPage(int page) {
    if (page < 1 || page > TotalPages()) {
        return;
    }
    g_app.currentPage = page;
    RefreshTable();
}

void ShowSelectedTab() {
    const int selected = TabCtrl_GetCurSel(g_app.tab);
    ShowWindow(g_app.formPanel, selected == 0 ? SW_SHOW : SW_HIDE);
    ShowWindow(g_app.tablePanel, selected == 1 ? SW_SHOW : SW_HIDE);
    ShowWindow(g_app.dragPanel, selected == 2 ? SW_SHOW : SW_HIDE);
}

LRESULT CALLBACK PanelWindowProc(HWND window, UINT message, WPARAM wParam, LPARAM lParam) {
    if (GetDlgCtrlID(window) == DragArena && message == WM_PAINT) {
        PAINTSTRUCT paint{};
        HDC context = BeginPaint(window, &paint);
        RECT client{};
        GetClientRect(window, &client);
        FillRect(context, &client, GetSysColorBrush(COLOR_WINDOW));

        HPEN gridPen = CreatePen(PS_SOLID, 1, RGB(232, 232, 232));
        HGDIOBJ oldPen = SelectObject(context, gridPen);
        for (int x = 40; x < client.right; x += 40) {
            MoveToEx(context, x, 0, nullptr);
            LineTo(context, x, client.bottom);
        }
        for (int y = 40; y < client.bottom; y += 40) {
            MoveToEx(context, 0, y, nullptr);
            LineTo(context, client.right, y);
        }
        SelectObject(context, oldPen);
        DeleteObject(gridPen);

        SetBkMode(context, TRANSPARENT);
        SetTextColor(context, RGB(112, 112, 112));
        HGDIOBJ oldFont = SelectObject(context, g_app.font);
        RECT label{10, 8, client.right - 10, 32};
        DrawTextW(context, L"拖拽区域 · 网格 40px", -1, &label, DT_LEFT | DT_SINGLELINE);
        SelectObject(context, oldFont);
        EndPaint(window, &paint);
        return 0;
    }
    if (message == WM_COMMAND || message == WM_NOTIFY) {
        HWND root = GetAncestor(window, GA_ROOT);
        return SendMessageW(root, message, wParam, lParam);
    }
    return DefWindowProcW(window, message, wParam, lParam);
}

LRESULT CALLBACK MainWindowProc(HWND window, UINT message, WPARAM wParam, LPARAM lParam) {
    switch (message) {
        case WM_CREATE: {
            g_app.mainWindow = window;
            g_app.mainMenu = CreateApplicationMenu();
            if (g_app.mainMenu) {
                SetMenu(window, g_app.mainMenu);
            }
            g_app.tab = CreateControl(WS_EX_CONTROLPARENT, WC_TABCONTROLW, L"", WS_TABSTOP | WS_CLIPCHILDREN, window, Tab);
            TCITEMW tabItem{};
            tabItem.mask = TCIF_TEXT;
            tabItem.pszText = const_cast<wchar_t*>(L"表单控件");
            TabCtrl_InsertItem(g_app.tab, 0, &tabItem);
            tabItem.pszText = const_cast<wchar_t*>(L"表格数据");
            TabCtrl_InsertItem(g_app.tab, 1, &tabItem);
            tabItem.pszText = const_cast<wchar_t*>(L"拖拽测试");
            TabCtrl_InsertItem(g_app.tab, 2, &tabItem);

            g_app.formPanel = CreateControl(WS_EX_CONTROLPARENT, kPanelWindowClass, L"表单控件页", WS_CLIPCHILDREN, g_app.tab, 0);
            g_app.tablePanel = CreateControl(WS_EX_CONTROLPARENT, kPanelWindowClass, L"表格数据页", WS_CLIPCHILDREN, g_app.tab, 0);
            g_app.dragPanel = CreateControl(WS_EX_CONTROLPARENT, kPanelWindowClass, L"拖拽测试页", WS_CLIPCHILDREN, g_app.tab, 0);
            CreateFormControls();
            CreateTableControls();
            CreateDragControls();
            BuildEmployees();
            RefreshTable();
            ShowSelectedTab();
            return 0;
        }
        case WM_SIZE:
            LayoutMainWindow();
            return 0;
        case WM_GETMINMAXINFO: {
            auto* info = reinterpret_cast<MINMAXINFO*>(lParam);
            info->ptMinTrackSize.x = 900;
            info->ptMinTrackSize.y = 680;
            return 0;
        }
        case WM_NOTIFY: {
            const auto* header = reinterpret_cast<NMHDR*>(lParam);
            if (header && header->hwndFrom == g_app.tab && header->code == TCN_SELCHANGE) {
                ShowSelectedTab();
                return 0;
            }
            break;
        }
        case WM_COMMAND: {
            const int id = LOWORD(wParam);
            if (MenuCommandLabel(static_cast<UINT>(id))) {
                SetMenuStatus(static_cast<UINT>(id));
                return 0;
            }
            if (id == SaveButton && HIWORD(wParam) == BN_CLICKED) {
                MessageBoxW(window, L"提交成功！", L"提示", MB_OK | MB_ICONINFORMATION);
                return 0;
            }
            if (id == ResetButton && HIWORD(wParam) == BN_CLICKED) {
                ResetForm();
                return 0;
            }
            if (id == PopupMenuButton && HIWORD(wParam) == BN_CLICKED) {
                ShowActionPopupMenu();
                return 0;
            }
            if (id == DragReset && HIWORD(wParam) == BN_CLICKED) {
                ResetDragTarget();
                return 0;
            }
            if (id == DragCopy && HIWORD(wParam) == BN_CLICKED) {
                CopyDragState();
                return 0;
            }
            if (id == DragHide && HIWORD(wParam) == BN_CLICKED) {
                HideDragTarget();
                return 0;
            }
            if (id == FirstPage) {
                GoToPage(1);
                return 0;
            }
            if (id == PreviousPage) {
                GoToPage(g_app.currentPage - 1);
                return 0;
            }
            if (id >= PageButtonFirst && id < PageButtonFirst + static_cast<int>(g_app.pageButtons.size())) {
                const int page = static_cast<int>(GetWindowLongPtrW(reinterpret_cast<HWND>(lParam), GWLP_USERDATA));
                GoToPage(page);
                return 0;
            }
            if (id == NextPage) {
                GoToPage(g_app.currentPage + 1);
                return 0;
            }
            if (id == LastPage) {
                GoToPage(TotalPages());
                return 0;
            }
            break;
        }
        case WM_DESTROY:
            if (g_app.mainMenu) {
                SetMenu(window, nullptr);
                DestroyMenu(g_app.mainMenu);
                g_app.mainMenu = nullptr;
            }
            PostQuitMessage(0);
            return 0;
        default:
            break;
    }
    return DefWindowProcW(window, message, wParam, lParam);
}

bool RegisterWindowClasses(HINSTANCE instance) {
    WNDCLASSEXW mainClass{};
    mainClass.cbSize = sizeof(mainClass);
    mainClass.style = CS_HREDRAW | CS_VREDRAW;
    mainClass.lpfnWndProc = MainWindowProc;
    mainClass.hInstance = instance;
    mainClass.hIcon = LoadIconW(nullptr, IDI_APPLICATION);
    mainClass.hCursor = LoadCursorW(nullptr, IDC_ARROW);
    mainClass.hbrBackground = GetSysColorBrush(COLOR_BTNFACE);
    mainClass.lpszClassName = kMainWindowClass;
    mainClass.hIconSm = LoadIconW(nullptr, IDI_APPLICATION);
    if (!RegisterClassExW(&mainClass)) {
        return false;
    }

    WNDCLASSEXW panelClass{};
    panelClass.cbSize = sizeof(panelClass);
    panelClass.lpfnWndProc = PanelWindowProc;
    panelClass.hInstance = instance;
    panelClass.hCursor = LoadCursorW(nullptr, IDC_ARROW);
    panelClass.hbrBackground = GetSysColorBrush(COLOR_WINDOW);
    panelClass.lpszClassName = kPanelWindowClass;
    return RegisterClassExW(&panelClass) != 0;
}

void CenterWindow(HWND window) {
    RECT windowRect{};
    GetWindowRect(window, &windowRect);
    const int width = windowRect.right - windowRect.left;
    const int height = windowRect.bottom - windowRect.top;
    HMONITOR monitor = MonitorFromWindow(window, MONITOR_DEFAULTTONEAREST);
    MONITORINFO monitorInfo{};
    monitorInfo.cbSize = sizeof(monitorInfo);
    GetMonitorInfoW(monitor, &monitorInfo);
    const int x = monitorInfo.rcWork.left + (monitorInfo.rcWork.right - monitorInfo.rcWork.left - width) / 2;
    const int y = monitorInfo.rcWork.top + (monitorInfo.rcWork.bottom - monitorInfo.rcWork.top - height) / 2;
    SetWindowPos(window, nullptr, x, y, 0, 0, SWP_NOSIZE | SWP_NOZORDER | SWP_NOACTIVATE);
}

}  // namespace

int WINAPI wWinMain(HINSTANCE instance, HINSTANCE, PWSTR, int showCommand) {
    g_app.instance = instance;

    INITCOMMONCONTROLSEX controls{};
    controls.dwSize = sizeof(controls);
    controls.dwICC = ICC_TAB_CLASSES | ICC_LISTVIEW_CLASSES | ICC_UPDOWN_CLASS;
    if (!InitCommonControlsEx(&controls)) {
        return 1;
    }

    g_app.font = CreateFontW(
        -16,
        0,
        0,
        0,
        FW_NORMAL,
        FALSE,
        FALSE,
        FALSE,
        DEFAULT_CHARSET,
        OUT_DEFAULT_PRECIS,
        CLIP_DEFAULT_PRECIS,
        CLEARTYPE_QUALITY,
        DEFAULT_PITCH | FF_DONTCARE,
        L"Microsoft YaHei UI"
    );

    if (!RegisterWindowClasses(instance)) {
        MessageBoxW(nullptr, L"窗口类注册失败。", L"Win32 靶场", MB_OK | MB_ICONERROR);
        return 1;
    }

    HWND window = CreateWindowExW(
        0,
        kMainWindowClass,
        L"Win32 靶场 - UIA",
        WS_OVERLAPPEDWINDOW | WS_CLIPCHILDREN,
        CW_USEDEFAULT,
        CW_USEDEFAULT,
        1024,
        720,
        nullptr,
        nullptr,
        instance,
        nullptr
    );
    if (!window) {
        MessageBoxW(nullptr, L"主窗口创建失败。", L"Win32 靶场", MB_OK | MB_ICONERROR);
        DeleteObject(g_app.font);
        return 1;
    }

    CenterWindow(window);
    ShowWindow(window, showCommand);
    UpdateWindow(window);

    MSG message{};
    while (GetMessageW(&message, nullptr, 0, 0) > 0) {
        if (!IsDialogMessageW(window, &message)) {
            TranslateMessage(&message);
            DispatchMessageW(&message);
        }
    }

    DeleteObject(g_app.font);
    return static_cast<int>(message.wParam);
}
