#ifndef WIN32_SHOOTING_RANGE_ENABLE_MSAA
#define WIN32_SHOOTING_RANGE_ENABLE_MSAA 1
#endif

#include <windows.h>
#include <windowsx.h>
#include <oleacc.h>
#if WIN32_SHOOTING_RANGE_ENABLE_MSAA
#include <oleauto.h>
#endif

#include <algorithm>
#include <array>
#include <atomic>
#include <cwchar>
#include <string>
#include <vector>

namespace {

#if WIN32_SHOOTING_RANGE_ENABLE_MSAA
constexpr wchar_t kWindowClass[] = L"XPathWin32MsaaOnlyShootingRange";
constexpr wchar_t kWindowTitle[] = L"Win32 靶场 - MSAA Only";
#else
constexpr wchar_t kWindowClass[] = L"XPathWin32CanvasShootingRange";
constexpr wchar_t kWindowTitle[] = L"Win32 靶场 - Canvas Only";
#endif
constexpr int kPageSize = 20;
constexpr int kTotalRows = 1000;

enum ElementKey : int {
    TabForm = 1000,
    TabTable,
    FormHeading = 1010,
    NameEdit = 101,
    PasswordEdit,
    EmailEdit,
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
    EmployeeTable = 200,
    FirstPage = 210,
    PreviousPage,
    PageButtonFirst = 220,
    NextPage = 230,
    LastPage,
    FormLabelFirst = 3000,
    SummaryLabel = 3100,
    HeaderFirst = 3200,
    PageInfoLabel = 3300,
    StatusLabel = 3400,
    CellFirst = 10000
};

enum class ElementKind {
    StaticText,
    Tab,
    Edit,
    Password,
    Spinner,
    ComboBox,
    CheckBox,
    RadioButton,
    Button,
    Table,
    Header,
    Cell
};

struct Element {
    int key;
    RECT bounds;
    std::wstring name;
    std::wstring value;
    long role;
    long state;
    std::wstring defaultAction;
    ElementKind kind;
};

struct AppState {
    HINSTANCE instance{};
    HWND window{};
    HFONT font{};
#if WIN32_SHOOTING_RANGE_ENABLE_MSAA
    IAccessible* accessible{};
#endif
    bool tableTab{};
    int focusedKey{NameEdit};
    int age{25};
    int city{};
    int gender{};
    int currentPage{1};
    std::wstring name;
    std::wstring password;
    std::wstring email;
    std::wstring remark;
    std::wstring status;
    std::array<bool, 5> cityChecks{};
    std::array<bool, 4> hobbyChecks{};
    bool agreed{};
};

AppState g_app;

constexpr std::array<const wchar_t*, 5> kCities = {L"北京", L"上海", L"广州", L"深圳", L"杭州"};
constexpr std::array<const wchar_t*, 4> kHobbies = {L"阅读", L"运动", L"音乐", L"旅行"};
constexpr std::array<const wchar_t*, 3> kGenders = {L"男", L"女", L"其他"};
constexpr std::array<const wchar_t*, 7> kHeaders = {
    L"ID", L"姓名", L"部门", L"城市", L"状态", L"邮箱", L"入职日期"
};
constexpr std::array<const wchar_t*, 5> kDepartments = {
    L"研发部", L"产品部", L"市场部", L"销售部", L"人事部"
};
constexpr std::array<const wchar_t*, 3> kStatuses = {L"在职", L"离职", L"待入职"};

RECT MakeRect(int left, int top, int right, int bottom) {
    return RECT{left, top, right, bottom};
}

void AddElement(
    std::vector<Element>& elements,
    int key,
    RECT bounds,
    std::wstring name,
    std::wstring value,
    long role,
    ElementKind kind,
    bool focusable = false,
    bool checked = false,
    bool selected = false,
    bool unavailable = false,
    std::wstring defaultAction = L""
) {
    long state = 0;
    if (focusable) {
        state |= STATE_SYSTEM_FOCUSABLE;
    }
    if (key == g_app.focusedKey) {
        state |= STATE_SYSTEM_FOCUSED;
    }
    if (checked) {
        state |= STATE_SYSTEM_CHECKED;
    }
    if (selected) {
        state |= STATE_SYSTEM_SELECTED;
    }
    if (unavailable) {
        state |= STATE_SYSTEM_UNAVAILABLE;
    }
    if (kind == ElementKind::Password) {
        state |= STATE_SYSTEM_PROTECTED;
    }
    if (kind == ElementKind::Cell || kind == ElementKind::Tab) {
        state |= STATE_SYSTEM_SELECTABLE;
    }
    elements.push_back(Element{
        key,
        bounds,
        std::move(name),
        std::move(value),
        role,
        state,
        std::move(defaultAction),
        kind
    });
}

std::array<std::wstring, 7> EmployeeValues(int id) {
    wchar_t date[16]{};
    swprintf_s(date, L"2024-%02d-%02d", (id % 12) + 1, (id % 28) + 1);
    return {
        std::to_wstring(id),
        L"用户" + std::to_wstring(id),
        kDepartments[id % kDepartments.size()],
        kCities[id % kCities.size()],
        kStatuses[id % kStatuses.size()],
        L"user" + std::to_wstring(id) + L"@example.com",
        date
    };
}

std::vector<Element> BuildElements(HWND window) {
    RECT client{};
    GetClientRect(window, &client);
    const int width = client.right;
    const int height = client.bottom;
    std::vector<Element> elements;
    elements.reserve(g_app.tableTab ? 160 : 40);

    AddElement(
        elements,
        TabForm,
        MakeRect(10, 10, 110, 44),
        L"表单控件",
        L"",
        ROLE_SYSTEM_PAGETAB,
        ElementKind::Tab,
        true,
        false,
        !g_app.tableTab,
        false,
        L"切换"
    );
    AddElement(
        elements,
        TabTable,
        MakeRect(110, 10, 210, 44),
        L"表格数据",
        L"",
        ROLE_SYSTEM_PAGETAB,
        ElementKind::Tab,
        true,
        false,
        g_app.tableTab,
        false,
        L"切换"
    );

    if (!g_app.tableTab) {
        constexpr int labelX = 30;
        constexpr int fieldX = 180;
        constexpr int labelWidth = 140;
        const int fieldWidth = std::max(240, std::min(430, width - fieldX - 30));
        const std::array<int, 10> rowY = {76, 116, 156, 196, 236, 276, 316, 356, 396, 484};
        constexpr std::array<const wchar_t*, 10> labels = {
            L"姓名", L"密码", L"邮箱", L"年龄", L"城市（单选）", L"城市（多选）",
            L"性别（单选）", L"兴趣爱好（多选）", L"备注", L"协议"
        };

        AddElement(elements, FormHeading, MakeRect(30, 50, 300, 74), L"用户信息表单", L"",
                   ROLE_SYSTEM_STATICTEXT, ElementKind::StaticText);
        for (int index = 0; index < static_cast<int>(labels.size()); ++index) {
            AddElement(elements, FormLabelFirst + index, MakeRect(labelX, rowY[index], labelX + labelWidth, rowY[index] + 30),
                       labels[index], L"", ROLE_SYSTEM_STATICTEXT, ElementKind::StaticText);
        }

        AddElement(elements, NameEdit, MakeRect(fieldX, rowY[0], fieldX + fieldWidth, rowY[0] + 30), L"姓名", g_app.name,
                   ROLE_SYSTEM_TEXT, ElementKind::Edit, true);
        AddElement(elements, PasswordEdit, MakeRect(fieldX, rowY[1], fieldX + fieldWidth, rowY[1] + 30), L"密码", L"",
                   ROLE_SYSTEM_TEXT, ElementKind::Password, true);
        AddElement(elements, EmailEdit, MakeRect(fieldX, rowY[2], fieldX + fieldWidth, rowY[2] + 30), L"邮箱", g_app.email,
                   ROLE_SYSTEM_TEXT, ElementKind::Edit, true);
        AddElement(elements, AgeSpin, MakeRect(fieldX, rowY[3], fieldX + 140, rowY[3] + 30), L"年龄", std::to_wstring(g_app.age),
                   ROLE_SYSTEM_SPINBUTTON, ElementKind::Spinner, true, false, false, false, L"增加");
        AddElement(elements, CityCombo, MakeRect(fieldX, rowY[4], fieldX + 250, rowY[4] + 30), L"城市（单选）", kCities[g_app.city],
                   ROLE_SYSTEM_COMBOBOX, ElementKind::ComboBox, true, false, false, false, L"切换选项");

        for (int index = 0; index < static_cast<int>(kCities.size()); ++index) {
            AddElement(elements, CityMultiFirst + index, MakeRect(fieldX + index * 78, rowY[5], fieldX + index * 78 + 74, rowY[5] + 30),
                       kCities[index], L"", ROLE_SYSTEM_CHECKBUTTON, ElementKind::CheckBox, true, g_app.cityChecks[index],
                       false, false, g_app.cityChecks[index] ? L"取消选中" : L"选中");
        }
        for (int index = 0; index < static_cast<int>(kGenders.size()); ++index) {
            AddElement(elements, GenderMale + index, MakeRect(fieldX + index * 88, rowY[6], fieldX + index * 88 + 82, rowY[6] + 30),
                       kGenders[index], L"", ROLE_SYSTEM_RADIOBUTTON, ElementKind::RadioButton, true, g_app.gender == index,
                       g_app.gender == index, false, L"选择");
        }
        for (int index = 0; index < static_cast<int>(kHobbies.size()); ++index) {
            AddElement(elements, HobbyFirst + index, MakeRect(fieldX + index * 88, rowY[7], fieldX + index * 88 + 82, rowY[7] + 30),
                       kHobbies[index], L"", ROLE_SYSTEM_CHECKBUTTON, ElementKind::CheckBox, true, g_app.hobbyChecks[index],
                       false, false, g_app.hobbyChecks[index] ? L"取消选中" : L"选中");
        }
        AddElement(elements, RemarkEdit, MakeRect(fieldX, rowY[8], fieldX + fieldWidth, rowY[8] + 76), L"备注", g_app.remark,
                   ROLE_SYSTEM_TEXT, ElementKind::Edit, true);
        AddElement(elements, AgreeCheck, MakeRect(fieldX, rowY[9], fieldX + 180, rowY[9] + 30), L"同意用户协议", L"",
                   ROLE_SYSTEM_CHECKBUTTON, ElementKind::CheckBox, true, g_app.agreed, false, false,
                   g_app.agreed ? L"取消选中" : L"选中");

        const int actionY = std::max(530, height - 52);
        AddElement(elements, SaveButton, MakeRect(width / 2 - 104, actionY, width / 2 - 12, actionY + 32), L"保存", L"",
                   ROLE_SYSTEM_PUSHBUTTON, ElementKind::Button, true, false, false, false, L"按下");
        AddElement(elements, ResetButton, MakeRect(width / 2 + 12, actionY, width / 2 + 104, actionY + 32), L"重置", L"",
                   ROLE_SYSTEM_PUSHBUTTON, ElementKind::Button, true, false, false, false, L"按下");
        if (!g_app.status.empty()) {
            AddElement(elements, StatusLabel, MakeRect(width / 2 + 125, actionY, width - 20, actionY + 32), g_app.status, L"",
                       ROLE_SYSTEM_STATICTEXT, ElementKind::StaticText);
        }
    } else {
        const int tableLeft = 18;
        const int tableRight = width - 18;
        const int headerTop = 82;
        const int headerHeight = 26;
        const int rowHeight = 22;
        std::array<int, 7> columnWidths = {60, 105, 105, 85, 85, 0, 120};
        const int fixedWidth = columnWidths[0] + columnWidths[1] + columnWidths[2] + columnWidths[3]
            + columnWidths[4] + columnWidths[6];
        columnWidths[5] = std::max(180, tableRight - tableLeft - fixedWidth);

        AddElement(elements, SummaryLabel, MakeRect(18, 50, 310, 78), L"共 1000 条数据，每页 20 条", L"",
                   ROLE_SYSTEM_STATICTEXT, ElementKind::StaticText);
        AddElement(elements, EmployeeTable, MakeRect(tableLeft, headerTop, tableRight, headerTop + headerHeight + rowHeight * kPageSize),
                   L"员工数据表格", L"", ROLE_SYSTEM_TABLE, ElementKind::Table);

        int x = tableLeft;
        for (int column = 0; column < static_cast<int>(kHeaders.size()); ++column) {
            AddElement(elements, HeaderFirst + column, MakeRect(x, headerTop, x + columnWidths[column], headerTop + headerHeight),
                       kHeaders[column], L"", ROLE_SYSTEM_COLUMNHEADER, ElementKind::Header);
            x += columnWidths[column];
        }

        const int firstId = (g_app.currentPage - 1) * kPageSize + 1;
        for (int row = 0; row < kPageSize; ++row) {
            const int id = firstId + row;
            const auto values = EmployeeValues(id);
            x = tableLeft;
            for (int column = 0; column < static_cast<int>(values.size()); ++column) {
                const int key = CellFirst + id * 10 + column;
                const int top = headerTop + headerHeight + row * rowHeight;
                const std::wstring accessibleName = L"第 " + std::to_wstring(id) + L" 行 " + kHeaders[column];
                AddElement(elements, key, MakeRect(x, top, x + columnWidths[column], top + rowHeight), accessibleName, values[column],
                           ROLE_SYSTEM_CELL, ElementKind::Cell, true);
                x += columnWidths[column];
            }
        }

        constexpr int edgeWidth = 72;
        constexpr int pageWidth = 42;
        constexpr int gap = 6;
        const int totalWidth = edgeWidth * 4 + pageWidth * 5 + gap * 8;
        x = std::max(18, (width - totalWidth) / 2);
        const int buttonY = height - 70;
        const int totalPages = kTotalRows / kPageSize;
        const int windowStart = std::clamp(g_app.currentPage - 2, 1, totalPages - 4);

        AddElement(elements, FirstPage, MakeRect(x, buttonY, x + edgeWidth, buttonY + 30), L"首页", L"",
                   ROLE_SYSTEM_PUSHBUTTON, ElementKind::Button, true, false, false, g_app.currentPage == 1, L"按下");
        x += edgeWidth + gap;
        AddElement(elements, PreviousPage, MakeRect(x, buttonY, x + edgeWidth, buttonY + 30), L"上一页", L"",
                   ROLE_SYSTEM_PUSHBUTTON, ElementKind::Button, true, false, false, g_app.currentPage == 1, L"按下");
        x += edgeWidth + gap;
        for (int index = 0; index < 5; ++index) {
            const int page = windowStart + index;
            AddElement(elements, PageButtonFirst + index, MakeRect(x, buttonY, x + pageWidth, buttonY + 30), std::to_wstring(page),
                       std::to_wstring(page), ROLE_SYSTEM_PUSHBUTTON, ElementKind::Button, true, false,
                       page == g_app.currentPage, page == g_app.currentPage, L"按下");
            x += pageWidth + gap;
        }
        AddElement(elements, NextPage, MakeRect(x, buttonY, x + edgeWidth, buttonY + 30), L"下一页", L"",
                   ROLE_SYSTEM_PUSHBUTTON, ElementKind::Button, true, false, false, g_app.currentPage == totalPages, L"按下");
        x += edgeWidth + gap;
        AddElement(elements, LastPage, MakeRect(x, buttonY, x + edgeWidth, buttonY + 30), L"末页", L"",
                   ROLE_SYSTEM_PUSHBUTTON, ElementKind::Button, true, false, false, g_app.currentPage == totalPages, L"按下");

        const int displayStart = (g_app.currentPage - 1) * kPageSize + 1;
        const std::wstring pageInfo = L"第 " + std::to_wstring(g_app.currentPage) + L" / " + std::to_wstring(totalPages)
            + L" 页，当前显示 " + std::to_wstring(displayStart) + L" - "
            + std::to_wstring(displayStart + kPageSize - 1) + L" 条";
        AddElement(elements, PageInfoLabel, MakeRect(18, height - 36, width - 18, height - 10), pageInfo, L"",
                   ROLE_SYSTEM_STATICTEXT, ElementKind::StaticText);
    }
    return elements;
}

int ChildIdForKey(const std::vector<Element>& elements, int key) {
    for (int index = 0; index < static_cast<int>(elements.size()); ++index) {
        if (elements[index].key == key) {
            return index + 1;
        }
    }
    return CHILDID_SELF;
}

int ChildIdForKey(int key) {
    return ChildIdForKey(BuildElements(g_app.window), key);
}

void NotifyElement(long eventId, int key) {
#if WIN32_SHOOTING_RANGE_ENABLE_MSAA
    NotifyWinEvent(eventId, g_app.window, OBJID_CLIENT, ChildIdForKey(key));
#else
    static_cast<void>(eventId);
    static_cast<void>(key);
#endif
}

void NotifyRoot(long eventId) {
#if WIN32_SHOOTING_RANGE_ENABLE_MSAA
    NotifyWinEvent(eventId, g_app.window, OBJID_CLIENT, CHILDID_SELF);
#else
    static_cast<void>(eventId);
#endif
}

void SetFocusedKey(int key) {
    if (g_app.focusedKey == key) {
        return;
    }
    g_app.focusedKey = key;
    SetFocus(g_app.window);
    NotifyElement(EVENT_OBJECT_FOCUS, key);
    InvalidateRect(g_app.window, nullptr, FALSE);
}

void ResetForm() {
    g_app.name.clear();
    g_app.password.clear();
    g_app.email.clear();
    g_app.remark.clear();
    g_app.status.clear();
    g_app.age = 25;
    g_app.city = 0;
    g_app.gender = 0;
    g_app.cityChecks.fill(false);
    g_app.hobbyChecks.fill(false);
    g_app.agreed = false;
    g_app.focusedKey = NameEdit;
    NotifyRoot(EVENT_OBJECT_REORDER);
    InvalidateRect(g_app.window, nullptr, FALSE);
}

void ChangePage(int page) {
    const int newPage = std::clamp(page, 1, kTotalRows / kPageSize);
    if (newPage == g_app.currentPage) {
        return;
    }
    g_app.currentPage = newPage;
    g_app.focusedKey = EmployeeTable;
    NotifyRoot(EVENT_OBJECT_REORDER);
    InvalidateRect(g_app.window, nullptr, FALSE);
}

void ActivateElement(int key) {
    if (key == TabForm || key == TabTable) {
        const bool newTableTab = key == TabTable;
        if (newTableTab != g_app.tableTab) {
            g_app.tableTab = newTableTab;
            g_app.focusedKey = key;
            NotifyRoot(EVENT_OBJECT_REORDER);
            InvalidateRect(g_app.window, nullptr, FALSE);
        }
        return;
    }
    if (key >= CityMultiFirst && key < CityMultiFirst + static_cast<int>(g_app.cityChecks.size())) {
        const int index = key - CityMultiFirst;
        g_app.cityChecks[index] = !g_app.cityChecks[index];
        NotifyElement(EVENT_OBJECT_STATECHANGE, key);
    } else if (key >= GenderMale && key <= GenderOther) {
        g_app.gender = key - GenderMale;
        NotifyElement(EVENT_OBJECT_SELECTION, key);
    } else if (key >= HobbyFirst && key < HobbyFirst + static_cast<int>(g_app.hobbyChecks.size())) {
        const int index = key - HobbyFirst;
        g_app.hobbyChecks[index] = !g_app.hobbyChecks[index];
        NotifyElement(EVENT_OBJECT_STATECHANGE, key);
    } else if (key == AgreeCheck) {
        g_app.agreed = !g_app.agreed;
        NotifyElement(EVENT_OBJECT_STATECHANGE, key);
    } else if (key == AgeSpin) {
        g_app.age = std::min(80, g_app.age + 1);
        NotifyElement(EVENT_OBJECT_VALUECHANGE, key);
    } else if (key == CityCombo) {
        g_app.city = (g_app.city + 1) % static_cast<int>(kCities.size());
        NotifyElement(EVENT_OBJECT_VALUECHANGE, key);
    } else if (key == SaveButton) {
        g_app.status = L"提交成功！";
        NotifyRoot(EVENT_OBJECT_NAMECHANGE);
    } else if (key == ResetButton) {
        ResetForm();
        return;
    } else if (key == FirstPage) {
        ChangePage(1);
        return;
    } else if (key == PreviousPage) {
        ChangePage(g_app.currentPage - 1);
        return;
    } else if (key >= PageButtonFirst && key < PageButtonFirst + 5) {
        const auto elements = BuildElements(g_app.window);
        const auto element = std::find_if(elements.begin(), elements.end(), [key](const Element& item) { return item.key == key; });
        if (element != elements.end()) {
            ChangePage(std::stoi(element->value));
        }
        return;
    } else if (key == NextPage) {
        ChangePage(g_app.currentPage + 1);
        return;
    } else if (key == LastPage) {
        ChangePage(kTotalRows / kPageSize);
        return;
    }
    InvalidateRect(g_app.window, nullptr, FALSE);
}

bool PutElementValue(int key, const std::wstring& value) {
    if (key == NameEdit) {
        g_app.name = value;
    } else if (key == PasswordEdit) {
        g_app.password = value;
    } else if (key == EmailEdit) {
        g_app.email = value;
    } else if (key == RemarkEdit) {
        g_app.remark = value;
    } else if (key == AgeSpin) {
        try {
            g_app.age = std::clamp(std::stoi(value), 18, 80);
        } catch (...) {
            return false;
        }
    } else if (key == CityCombo) {
        const auto city = std::find(kCities.begin(), kCities.end(), value);
        if (city == kCities.end()) {
            return false;
        }
        g_app.city = static_cast<int>(std::distance(kCities.begin(), city));
    } else {
        return false;
    }
    NotifyElement(EVENT_OBJECT_VALUECHANGE, key);
    InvalidateRect(g_app.window, nullptr, FALSE);
    return true;
}

#if WIN32_SHOOTING_RANGE_ENABLE_MSAA
HRESULT CopyBstr(const std::wstring& value, BSTR* output) {
    if (!output) {
        return E_INVALIDARG;
    }
    *output = SysAllocStringLen(value.data(), static_cast<UINT>(value.size()));
    return *output ? S_OK : E_OUTOFMEMORY;
}

class MsaaAccessible final : public IAccessible {
public:
    explicit MsaaAccessible(HWND window) : window_(window) {}

    HRESULT STDMETHODCALLTYPE QueryInterface(REFIID interfaceId, void** object) override {
        if (!object) {
            return E_INVALIDARG;
        }
        *object = nullptr;
        if (interfaceId == IID_IUnknown || interfaceId == IID_IDispatch || interfaceId == IID_IAccessible) {
            *object = static_cast<IAccessible*>(this);
            AddRef();
            return S_OK;
        }
        return E_NOINTERFACE;
    }

    ULONG STDMETHODCALLTYPE AddRef() override {
        return ++references_;
    }

    ULONG STDMETHODCALLTYPE Release() override {
        const ULONG count = --references_;
        if (count == 0) {
            delete this;
        }
        return count;
    }

    HRESULT STDMETHODCALLTYPE GetTypeInfoCount(UINT* count) override {
        if (!count) {
            return E_INVALIDARG;
        }
        *count = 0;
        return S_OK;
    }

    HRESULT STDMETHODCALLTYPE GetTypeInfo(UINT, LCID, ITypeInfo**) override {
        return E_NOTIMPL;
    }

    HRESULT STDMETHODCALLTYPE GetIDsOfNames(REFIID, LPOLESTR*, UINT, LCID, DISPID*) override {
        return DISP_E_UNKNOWNNAME;
    }

    HRESULT STDMETHODCALLTYPE Invoke(DISPID, REFIID, LCID, WORD, DISPPARAMS*, VARIANT*, EXCEPINFO*, UINT*) override {
        return DISP_E_MEMBERNOTFOUND;
    }

    HRESULT STDMETHODCALLTYPE get_accParent(IDispatch** parent) override {
        if (!parent) {
            return E_INVALIDARG;
        }
        *parent = nullptr;
        IAccessible* accessible = nullptr;
        const HRESULT result = AccessibleObjectFromWindow(
            window_, OBJID_WINDOW, IID_IAccessible, reinterpret_cast<void**>(&accessible)
        );
        if (SUCCEEDED(result)) {
            *parent = accessible;
        }
        return result;
    }

    HRESULT STDMETHODCALLTYPE get_accChildCount(long* count) override {
        if (!count) {
            return E_INVALIDARG;
        }
        *count = static_cast<long>(BuildElements(window_).size());
        return S_OK;
    }

    HRESULT STDMETHODCALLTYPE get_accChild(VARIANT, IDispatch** child) override {
        if (!child) {
            return E_INVALIDARG;
        }
        *child = nullptr;
        return S_FALSE;
    }

    HRESULT STDMETHODCALLTYPE get_accName(VARIANT child, BSTR* name) override {
        if (IsSelf(child)) {
            return CopyBstr(L"Win32 靶场 - MSAA Only", name);
        }
        const auto elements = BuildElements(window_);
        const Element* element = Resolve(child, elements);
        return element ? CopyBstr(element->name, name) : E_INVALIDARG;
    }

    HRESULT STDMETHODCALLTYPE get_accValue(VARIANT child, BSTR* value) override {
        if (!value) {
            return E_INVALIDARG;
        }
        *value = nullptr;
        if (IsSelf(child)) {
            return S_FALSE;
        }
        const auto elements = BuildElements(window_);
        const Element* element = Resolve(child, elements);
        if (!element || element->value.empty()) {
            return S_FALSE;
        }
        return CopyBstr(element->value, value);
    }

    HRESULT STDMETHODCALLTYPE get_accDescription(VARIANT child, BSTR* description) override {
        if (!description) {
            return E_INVALIDARG;
        }
        *description = nullptr;
        if (IsSelf(child)) {
            return CopyBstr(L"仅实现 IAccessible 的 Win32 靶场", description);
        }
        const auto elements = BuildElements(window_);
        const Element* element = Resolve(child, elements);
        if (!element) {
            return E_INVALIDARG;
        }
        return CopyBstr(L"MSAA 元素编号 " + std::to_wstring(element->key), description);
    }

    HRESULT STDMETHODCALLTYPE get_accRole(VARIANT child, VARIANT* role) override {
        if (!role) {
            return E_INVALIDARG;
        }
        VariantInit(role);
        role->vt = VT_I4;
        if (IsSelf(child)) {
            role->lVal = ROLE_SYSTEM_CLIENT;
            return S_OK;
        }
        const auto elements = BuildElements(window_);
        const Element* element = Resolve(child, elements);
        if (!element) {
            return E_INVALIDARG;
        }
        role->lVal = element->role;
        return S_OK;
    }

    HRESULT STDMETHODCALLTYPE get_accState(VARIANT child, VARIANT* state) override {
        if (!state) {
            return E_INVALIDARG;
        }
        VariantInit(state);
        state->vt = VT_I4;
        if (IsSelf(child)) {
            state->lVal = 0;
            return S_OK;
        }
        const auto elements = BuildElements(window_);
        const Element* element = Resolve(child, elements);
        if (!element) {
            return E_INVALIDARG;
        }
        state->lVal = element->state;
        return S_OK;
    }

    HRESULT STDMETHODCALLTYPE get_accHelp(VARIANT, BSTR* help) override {
        if (!help) {
            return E_INVALIDARG;
        }
        *help = nullptr;
        return S_FALSE;
    }

    HRESULT STDMETHODCALLTYPE get_accHelpTopic(BSTR* helpFile, VARIANT, long* topicId) override {
        if (!helpFile || !topicId) {
            return E_INVALIDARG;
        }
        *helpFile = nullptr;
        *topicId = -1;
        return S_FALSE;
    }

    HRESULT STDMETHODCALLTYPE get_accKeyboardShortcut(VARIANT, BSTR* shortcut) override {
        if (!shortcut) {
            return E_INVALIDARG;
        }
        *shortcut = nullptr;
        return S_FALSE;
    }

    HRESULT STDMETHODCALLTYPE get_accFocus(VARIANT* focus) override {
        if (!focus) {
            return E_INVALIDARG;
        }
        VariantInit(focus);
        focus->vt = VT_I4;
        focus->lVal = ChildIdForKey(BuildElements(window_), g_app.focusedKey);
        return S_OK;
    }

    HRESULT STDMETHODCALLTYPE get_accSelection(VARIANT* selection) override {
        if (!selection) {
            return E_INVALIDARG;
        }
        VariantInit(selection);
        return S_FALSE;
    }

    HRESULT STDMETHODCALLTYPE get_accDefaultAction(VARIANT child, BSTR* action) override {
        if (!action) {
            return E_INVALIDARG;
        }
        *action = nullptr;
        if (IsSelf(child)) {
            return S_FALSE;
        }
        const auto elements = BuildElements(window_);
        const Element* element = Resolve(child, elements);
        if (!element || element->defaultAction.empty()) {
            return S_FALSE;
        }
        return CopyBstr(element->defaultAction, action);
    }

    HRESULT STDMETHODCALLTYPE accSelect(long flags, VARIANT child) override {
        if ((flags & SELFLAG_TAKEFOCUS) == 0) {
            return E_NOTIMPL;
        }
        const auto elements = BuildElements(window_);
        const Element* element = Resolve(child, elements);
        if (!element || (element->state & STATE_SYSTEM_FOCUSABLE) == 0) {
            return E_INVALIDARG;
        }
        SetFocusedKey(element->key);
        return S_OK;
    }

    HRESULT STDMETHODCALLTYPE accLocation(long* left, long* top, long* width, long* height, VARIANT child) override {
        if (!left || !top || !width || !height) {
            return E_INVALIDARG;
        }
        RECT bounds{};
        if (IsSelf(child)) {
            GetClientRect(window_, &bounds);
        } else {
            const auto elements = BuildElements(window_);
            const Element* element = Resolve(child, elements);
            if (!element) {
                return E_INVALIDARG;
            }
            bounds = element->bounds;
        }
        POINT origin{bounds.left, bounds.top};
        ClientToScreen(window_, &origin);
        *left = origin.x;
        *top = origin.y;
        *width = bounds.right - bounds.left;
        *height = bounds.bottom - bounds.top;
        return S_OK;
    }

    HRESULT STDMETHODCALLTYPE accNavigate(long direction, VARIANT start, VARIANT* destination) override {
        if (!destination) {
            return E_INVALIDARG;
        }
        VariantInit(destination);
        const auto elements = BuildElements(window_);
        long childId = 0;
        if (IsSelf(start) && direction == NAVDIR_FIRSTCHILD && !elements.empty()) {
            childId = 1;
        } else if (IsSelf(start) && direction == NAVDIR_LASTCHILD && !elements.empty()) {
            childId = static_cast<long>(elements.size());
        } else if (start.vt == VT_I4 && direction == NAVDIR_NEXT && start.lVal < static_cast<long>(elements.size())) {
            childId = start.lVal + 1;
        } else if (start.vt == VT_I4 && direction == NAVDIR_PREVIOUS && start.lVal > 1) {
            childId = start.lVal - 1;
        } else {
            return S_FALSE;
        }
        destination->vt = VT_I4;
        destination->lVal = childId;
        return S_OK;
    }

    HRESULT STDMETHODCALLTYPE accHitTest(long screenX, long screenY, VARIANT* child) override {
        if (!child) {
            return E_INVALIDARG;
        }
        VariantInit(child);
        POINT point{screenX, screenY};
        ScreenToClient(window_, &point);
        const auto elements = BuildElements(window_);
        for (int index = static_cast<int>(elements.size()) - 1; index >= 0; --index) {
            if (PtInRect(&elements[index].bounds, point)) {
                child->vt = VT_I4;
                child->lVal = index + 1;
                return S_OK;
            }
        }
        child->vt = VT_I4;
        child->lVal = CHILDID_SELF;
        return S_OK;
    }

    HRESULT STDMETHODCALLTYPE accDoDefaultAction(VARIANT child) override {
        const auto elements = BuildElements(window_);
        const Element* element = Resolve(child, elements);
        if (!element || element->defaultAction.empty() || (element->state & STATE_SYSTEM_UNAVAILABLE) != 0) {
            return E_INVALIDARG;
        }
        ActivateElement(element->key);
        return S_OK;
    }

    HRESULT STDMETHODCALLTYPE put_accName(VARIANT, BSTR) override {
        return E_NOTIMPL;
    }

    HRESULT STDMETHODCALLTYPE put_accValue(VARIANT child, BSTR value) override {
        if (!value) {
            return E_INVALIDARG;
        }
        const auto elements = BuildElements(window_);
        const Element* element = Resolve(child, elements);
        if (!element) {
            return E_INVALIDARG;
        }
        return PutElementValue(element->key, value) ? S_OK : E_INVALIDARG;
    }

private:
    static bool IsSelf(const VARIANT& child) {
        return child.vt == VT_I4 && child.lVal == CHILDID_SELF;
    }

    static const Element* Resolve(const VARIANT& child, const std::vector<Element>& elements) {
        if (child.vt != VT_I4 || child.lVal < 1 || child.lVal > static_cast<long>(elements.size())) {
            return nullptr;
        }
        return &elements[child.lVal - 1];
    }

    std::atomic<ULONG> references_{1};
    HWND window_;
};
#endif

void DrawTextInRect(HDC context, const std::wstring& text, RECT bounds, UINT format, COLORREF color = RGB(32, 32, 32)) {
    SetTextColor(context, color);
    SetBkMode(context, TRANSPARENT);
    bounds.left += 5;
    bounds.right -= 5;
    DrawTextW(context, text.c_str(), static_cast<int>(text.size()), &bounds, format);
}

void DrawElement(HDC context, const Element& element) {
    RECT bounds = element.bounds;
    const bool focused = (element.state & STATE_SYSTEM_FOCUSED) != 0;
    const bool checked = (element.state & STATE_SYSTEM_CHECKED) != 0;
    const bool selected = (element.state & STATE_SYSTEM_SELECTED) != 0;
    const bool unavailable = (element.state & STATE_SYSTEM_UNAVAILABLE) != 0;

    switch (element.kind) {
        case ElementKind::StaticText:
            DrawTextInRect(context, element.name, bounds, DT_LEFT | DT_VCENTER | DT_SINGLELINE);
            break;
        case ElementKind::Tab: {
            FillRect(context, &bounds, GetSysColorBrush(selected ? COLOR_WINDOW : COLOR_BTNFACE));
            FrameRect(context, &bounds, GetSysColorBrush(COLOR_3DSHADOW));
            DrawTextInRect(context, element.name, bounds, DT_CENTER | DT_VCENTER | DT_SINGLELINE);
            break;
        }
        case ElementKind::Edit:
        case ElementKind::Password:
        case ElementKind::Spinner:
        case ElementKind::ComboBox: {
            FillRect(context, &bounds, GetSysColorBrush(COLOR_WINDOW));
            FrameRect(context, &bounds, GetSysColorBrush(COLOR_3DSHADOW));
            std::wstring display = element.value;
            if (element.kind == ElementKind::Password) {
                display.assign(g_app.password.size(), L'\x2022');
            }
            RECT textBounds = bounds;
            if (element.kind == ElementKind::Spinner || element.kind == ElementKind::ComboBox) {
                textBounds.right -= 22;
            }
            const UINT format = element.key == RemarkEdit ? DT_LEFT | DT_TOP | DT_WORDBREAK : DT_LEFT | DT_VCENTER | DT_SINGLELINE;
            DrawTextInRect(context, display, textBounds, format);
            if (element.kind == ElementKind::Spinner) {
                RECT up = MakeRect(bounds.right - 22, bounds.top, bounds.right, (bounds.top + bounds.bottom) / 2);
                RECT down = MakeRect(bounds.right - 22, (bounds.top + bounds.bottom) / 2, bounds.right, bounds.bottom);
                DrawFrameControl(context, &up, DFC_SCROLL, DFCS_SCROLLUP);
                DrawFrameControl(context, &down, DFC_SCROLL, DFCS_SCROLLDOWN);
            } else if (element.kind == ElementKind::ComboBox) {
                RECT arrow = MakeRect(bounds.right - 22, bounds.top, bounds.right, bounds.bottom);
                DrawFrameControl(context, &arrow, DFC_SCROLL, DFCS_SCROLLCOMBOBOX);
            }
            break;
        }
        case ElementKind::CheckBox:
        case ElementKind::RadioButton: {
            RECT mark = MakeRect(bounds.left + 2, bounds.top + 7, bounds.left + 18, bounds.top + 23);
            UINT style = element.kind == ElementKind::RadioButton ? DFCS_BUTTONRADIO : DFCS_BUTTONCHECK;
            if (checked) {
                style |= DFCS_CHECKED;
            }
            DrawFrameControl(context, &mark, DFC_BUTTON, style);
            RECT text = MakeRect(bounds.left + 22, bounds.top, bounds.right, bounds.bottom);
            DrawTextInRect(context, element.name, text, DT_LEFT | DT_VCENTER | DT_SINGLELINE);
            break;
        }
        case ElementKind::Button: {
            UINT style = DFCS_BUTTONPUSH;
            if (unavailable) {
                style |= DFCS_INACTIVE;
            }
            DrawFrameControl(context, &bounds, DFC_BUTTON, style);
            DrawTextInRect(context, element.name, bounds, DT_CENTER | DT_VCENTER | DT_SINGLELINE,
                           unavailable ? GetSysColor(COLOR_GRAYTEXT) : GetSysColor(COLOR_BTNTEXT));
            break;
        }
        case ElementKind::Table:
            FillRect(context, &bounds, GetSysColorBrush(COLOR_WINDOW));
            FrameRect(context, &bounds, GetSysColorBrush(COLOR_3DSHADOW));
            break;
        case ElementKind::Header:
            FillRect(context, &bounds, GetSysColorBrush(COLOR_BTNFACE));
            FrameRect(context, &bounds, GetSysColorBrush(COLOR_3DSHADOW));
            DrawTextInRect(context, element.name, bounds, DT_CENTER | DT_VCENTER | DT_SINGLELINE);
            break;
        case ElementKind::Cell:
            FillRect(context, &bounds, GetSysColorBrush(COLOR_WINDOW));
            FrameRect(context, &bounds, GetSysColorBrush(COLOR_BTNFACE));
            DrawTextInRect(context, element.value, bounds, DT_LEFT | DT_VCENTER | DT_SINGLELINE);
            break;
    }
    if (focused) {
        InflateRect(&bounds, -2, -2);
        DrawFocusRect(context, &bounds);
    }
}

void PaintWindow(HWND window) {
    PAINTSTRUCT paint{};
    HDC target = BeginPaint(window, &paint);
    RECT client{};
    GetClientRect(window, &client);
    HDC buffer = CreateCompatibleDC(target);
    HBITMAP bitmap = CreateCompatibleBitmap(target, client.right, client.bottom);
    HGDIOBJ oldBitmap = SelectObject(buffer, bitmap);
    HGDIOBJ oldFont = SelectObject(buffer, g_app.font);
    FillRect(buffer, &client, GetSysColorBrush(COLOR_WINDOW));

    const auto elements = BuildElements(window);
    for (const Element& element : elements) {
        DrawElement(buffer, element);
    }

    BitBlt(target, 0, 0, client.right, client.bottom, buffer, 0, 0, SRCCOPY);
    SelectObject(buffer, oldFont);
    SelectObject(buffer, oldBitmap);
    DeleteObject(bitmap);
    DeleteDC(buffer);
    EndPaint(window, &paint);
}

const Element* FindElementByKey(const std::vector<Element>& elements, int key) {
    const auto found = std::find_if(elements.begin(), elements.end(), [key](const Element& element) {
        return element.key == key;
    });
    return found == elements.end() ? nullptr : &*found;
}

void HandleClick(HWND window, int x, int y) {
    POINT point{x, y};
    const auto elements = BuildElements(window);
    for (auto element = elements.rbegin(); element != elements.rend(); ++element) {
        if (!PtInRect(&element->bounds, point)) {
            continue;
        }
        if ((element->state & STATE_SYSTEM_FOCUSABLE) != 0) {
            SetFocusedKey(element->key);
        }
        if (element->key == AgeSpin && x >= element->bounds.right - 22) {
            if (y < (element->bounds.top + element->bounds.bottom) / 2) {
                g_app.age = std::min(80, g_app.age + 1);
            } else {
                g_app.age = std::max(18, g_app.age - 1);
            }
            NotifyElement(EVENT_OBJECT_VALUECHANGE, AgeSpin);
            InvalidateRect(window, nullptr, FALSE);
        } else if (!element->defaultAction.empty() && (element->state & STATE_SYSTEM_UNAVAILABLE) == 0) {
            ActivateElement(element->key);
        }
        return;
    }
}

void MoveFocus(bool backwards) {
    const auto elements = BuildElements(g_app.window);
    std::vector<int> focusable;
    for (const Element& element : elements) {
        if ((element.state & STATE_SYSTEM_FOCUSABLE) != 0 && (element.state & STATE_SYSTEM_UNAVAILABLE) == 0) {
            focusable.push_back(element.key);
        }
    }
    if (focusable.empty()) {
        return;
    }
    const auto current = std::find(focusable.begin(), focusable.end(), g_app.focusedKey);
    int index = current == focusable.end() ? 0 : static_cast<int>(std::distance(focusable.begin(), current));
    index = backwards ? (index - 1 + static_cast<int>(focusable.size())) % static_cast<int>(focusable.size())
                      : (index + 1) % static_cast<int>(focusable.size());
    SetFocusedKey(focusable[index]);
}

void HandleCharacter(wchar_t character) {
    std::wstring* target = nullptr;
    if (g_app.focusedKey == NameEdit) {
        target = &g_app.name;
    } else if (g_app.focusedKey == PasswordEdit) {
        target = &g_app.password;
    } else if (g_app.focusedKey == EmailEdit) {
        target = &g_app.email;
    } else if (g_app.focusedKey == RemarkEdit) {
        target = &g_app.remark;
    }
    if (!target) {
        return;
    }
    if (character == L'\b') {
        if (!target->empty()) {
            target->pop_back();
        }
    } else if (character >= L' ' || (character == L'\r' && g_app.focusedKey == RemarkEdit)) {
        target->push_back(character == L'\r' ? L'\n' : character);
    } else {
        return;
    }
    NotifyElement(EVENT_OBJECT_VALUECHANGE, g_app.focusedKey);
    InvalidateRect(g_app.window, nullptr, FALSE);
}

LRESULT CALLBACK WindowProc(HWND window, UINT message, WPARAM wParam, LPARAM lParam) {
    switch (message) {
        case WM_CREATE:
            g_app.window = window;
#if WIN32_SHOOTING_RANGE_ENABLE_MSAA
            g_app.accessible = new MsaaAccessible(window);
#endif
            return 0;
#if WIN32_SHOOTING_RANGE_ENABLE_MSAA
        case WM_GETOBJECT:
            if (static_cast<DWORD>(lParam) == static_cast<DWORD>(OBJID_CLIENT)) {
                return LresultFromObject(IID_IAccessible, wParam, g_app.accessible);
            }
            break;
#endif
        case WM_PAINT:
            PaintWindow(window);
            return 0;
        case WM_ERASEBKGND:
            return 1;
        case WM_LBUTTONDOWN:
            HandleClick(window, GET_X_LPARAM(lParam), GET_Y_LPARAM(lParam));
            return 0;
        case WM_CHAR:
            HandleCharacter(static_cast<wchar_t>(wParam));
            return 0;
        case WM_KEYDOWN: {
            if (wParam == VK_TAB) {
                MoveFocus((GetKeyState(VK_SHIFT) & 0x8000) != 0);
                return 0;
            }
            if (wParam == VK_RETURN || wParam == VK_SPACE) {
                const auto elements = BuildElements(window);
                const Element* element = FindElementByKey(elements, g_app.focusedKey);
                if (element && !element->defaultAction.empty() && (element->state & STATE_SYSTEM_UNAVAILABLE) == 0) {
                    ActivateElement(element->key);
                }
                return 0;
            }
            if (g_app.focusedKey == AgeSpin && (wParam == VK_UP || wParam == VK_DOWN)) {
                g_app.age = std::clamp(g_app.age + (wParam == VK_UP ? 1 : -1), 18, 80);
                NotifyElement(EVENT_OBJECT_VALUECHANGE, AgeSpin);
                InvalidateRect(window, nullptr, FALSE);
                return 0;
            }
            if (g_app.focusedKey == CityCombo && (wParam == VK_UP || wParam == VK_DOWN)) {
                const int delta = wParam == VK_DOWN ? 1 : -1;
                g_app.city = (g_app.city + delta + static_cast<int>(kCities.size())) % static_cast<int>(kCities.size());
                NotifyElement(EVENT_OBJECT_VALUECHANGE, CityCombo);
                InvalidateRect(window, nullptr, FALSE);
                return 0;
            }
            break;
        }
        case WM_SIZE:
            InvalidateRect(window, nullptr, FALSE);
            return 0;
        case WM_GETMINMAXINFO: {
            auto* info = reinterpret_cast<MINMAXINFO*>(lParam);
            info->ptMinTrackSize.x = 900;
            info->ptMinTrackSize.y = 680;
            return 0;
        }
        case WM_DESTROY:
#if WIN32_SHOOTING_RANGE_ENABLE_MSAA
            if (g_app.accessible) {
                g_app.accessible->Release();
                g_app.accessible = nullptr;
            }
#endif
            PostQuitMessage(0);
            return 0;
        default:
            break;
    }
    return DefWindowProcW(window, message, wParam, lParam);
}

void CenterWindow(HWND window) {
    RECT windowRect{};
    GetWindowRect(window, &windowRect);
    MONITORINFO monitorInfo{};
    monitorInfo.cbSize = sizeof(monitorInfo);
    GetMonitorInfoW(MonitorFromWindow(window, MONITOR_DEFAULTTONEAREST), &monitorInfo);
    const int width = windowRect.right - windowRect.left;
    const int height = windowRect.bottom - windowRect.top;
    const int x = monitorInfo.rcWork.left + (monitorInfo.rcWork.right - monitorInfo.rcWork.left - width) / 2;
    const int y = monitorInfo.rcWork.top + (monitorInfo.rcWork.bottom - monitorInfo.rcWork.top - height) / 2;
    SetWindowPos(window, nullptr, x, y, 0, 0, SWP_NOSIZE | SWP_NOZORDER | SWP_NOACTIVATE);
}

}  // namespace

int WINAPI wWinMain(HINSTANCE instance, HINSTANCE, PWSTR, int showCommand) {
    g_app.instance = instance;
#if WIN32_SHOOTING_RANGE_ENABLE_MSAA
    if (FAILED(OleInitialize(nullptr))) {
        return 1;
    }
#endif

    g_app.font = CreateFontW(
        -16, 0, 0, 0, FW_NORMAL, FALSE, FALSE, FALSE, DEFAULT_CHARSET, OUT_DEFAULT_PRECIS,
        CLIP_DEFAULT_PRECIS, CLEARTYPE_QUALITY, DEFAULT_PITCH | FF_DONTCARE, L"Microsoft YaHei UI"
    );

    WNDCLASSEXW windowClass{};
    windowClass.cbSize = sizeof(windowClass);
    windowClass.style = CS_HREDRAW | CS_VREDRAW;
    windowClass.lpfnWndProc = WindowProc;
    windowClass.hInstance = instance;
    windowClass.hIcon = LoadIconW(nullptr, IDI_APPLICATION);
    windowClass.hCursor = LoadCursorW(nullptr, IDC_ARROW);
    windowClass.hbrBackground = GetSysColorBrush(COLOR_WINDOW);
    windowClass.lpszClassName = kWindowClass;
    windowClass.hIconSm = LoadIconW(nullptr, IDI_APPLICATION);
    if (!RegisterClassExW(&windowClass)) {
        DeleteObject(g_app.font);
#if WIN32_SHOOTING_RANGE_ENABLE_MSAA
        OleUninitialize();
#endif
        return 1;
    }

    HWND window = CreateWindowExW(
        0,
        kWindowClass,
        kWindowTitle,
        WS_OVERLAPPEDWINDOW,
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
        DeleteObject(g_app.font);
#if WIN32_SHOOTING_RANGE_ENABLE_MSAA
        OleUninitialize();
#endif
        return 1;
    }

    CenterWindow(window);
    ShowWindow(window, showCommand);
    UpdateWindow(window);

    MSG message{};
    while (GetMessageW(&message, nullptr, 0, 0) > 0) {
        TranslateMessage(&message);
        DispatchMessageW(&message);
    }

    DeleteObject(g_app.font);
#if WIN32_SHOOTING_RANGE_ENABLE_MSAA
    OleUninitialize();
#endif
    return static_cast<int>(message.wParam);
}
