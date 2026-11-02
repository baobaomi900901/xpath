#pragma once

#include <windows.h>
#include <commctrl.h>
#include <algorithm>
#include <array>
#include <string>
#include <vector>

namespace win32_samples {

using CreateControlFn = HWND (*)(DWORD, const wchar_t*, const wchar_t*, DWORD, HWND, int);
using MoveControlFn = void (*)(HWND, int, int, int, int);

enum Id : int {
    SingleList = 400, MultipleList, EmptyList, WritableText, ReadonlyText, DisabledText,
    HiddenText, ChangeEnabled, ChangeVisible, Slider, Progress, Toggle, TriState,
    Execute, ResetControls, ExtendedList = 450,
    DynamicInput = 600, ReplaceInput, AddChoice, RemoveChoice, ReplaceChoice,
    MixedTable, ReplaceModel, ReplaceTable, SortTable, SampleTree, AddTreeNode,
    ResetDynamic, DynamicChoiceFirst = 2000
};

struct Controls {
    HWND parent{};
    CreateControlFn create{};
    MoveControlFn move{};
    HWND Add(const wchar_t* type, const wchar_t* text, DWORD style, int id, DWORD ex = 0) const {
        return create(ex, type, text, style | WS_TABSTOP, parent, id);
    }
    HWND Label(const wchar_t* text) const {
        return create(0, WC_STATICW, text, SS_LEFT | SS_CENTERIMAGE, parent, 0);
    }
};

inline std::wstring LongContent() {
    std::wstring text;
    for (int i = 1; i <= 360; ++i) {
        text += L"第 " + std::to_wstring(i) + L" 行：中文与 Unicode 文本，表情 🙂，可以读取、选择和复制。\r\n";
    }
    return text;
}

struct SelectionPage {
    Controls ui;
    std::array<HWND, 4> listLabels{};
    std::array<HWND, 4> lists{};
    std::array<HWND, 4> textLabels{};
    std::array<HWND, 4> texts{};
    HWND heading{}, instructions{}, enableButton{}, visibleButton{}, numericLabel{}, slider{}, progress{};
    HWND toggle{}, triState{}, execute{}, executions{}, longLabel{}, longText{}, resetButton{};
    int executionCount{};
    bool hiddenVisible{true};

    void Create(HWND parent, CreateControlFn create, MoveControlFn move) {
        ui = {parent, create, move};
        heading = ui.Label(L"列表、文本状态与数值控件");
        instructions = ui.Label(L"普通多选点击切换；扩展多选使用 Ctrl / Shift；两个同名项是独立项目。");
        constexpr std::array<const wchar_t*, 4> names = {L"示例单选列表", L"示例多选列表", L"示例空列表", L"扩展多选列表"};
        constexpr std::array<const wchar_t*, 5> options = {L"北京", L"上海", L"广州", L"同名", L"同名"};
        for (int i = 0; i < 4; ++i) {
            listLabels[i] = ui.Label(names[i]);
            lists[i] = ui.Add(WC_LISTBOXW, names[i], LBS_NOTIFY | WS_VSCROLL | LBS_NOINTEGRALHEIGHT |
                (i == 0 ? 0 : i == 3 ? LBS_EXTENDEDSEL : LBS_MULTIPLESEL),
                i == 3 ? ExtendedList : SingleList + i, WS_EX_CLIENTEDGE);
            if (i != 2) for (const auto* option : options) {
                SendMessageW(lists[i], LB_ADDSTRING, 0, reinterpret_cast<LPARAM>(option));
            }
        }
        constexpr std::array<const wchar_t*, 4> textNames = {L"可编辑文本", L"只读文本", L"禁用文本", L"显隐文本"};
        for (int i = 0; i < 4; ++i) {
            textLabels[i] = ui.Label(textNames[i]);
            texts[i] = ui.Add(WC_EDITW, L"", ES_AUTOHSCROLL | (i == 1 ? ES_READONLY : 0),
                WritableText + i, WS_EX_CLIENTEDGE);
        }
        enableButton = ui.Add(WC_BUTTONW, L"切换禁用状态", BS_PUSHBUTTON, ChangeEnabled);
        visibleButton = ui.Add(WC_BUTTONW, L"显示 / 隐藏输入", BS_PUSHBUTTON, ChangeVisible);
        numericLabel = ui.Label(L"");
        slider = ui.Add(TRACKBAR_CLASSW, L"示例滑块", TBS_AUTOTICKS, Slider);
        SendMessageW(slider, TBM_SETRANGE, TRUE, MAKELPARAM(0, 100));
        SendMessageW(slider, TBM_SETTICFREQ, 25, 0);
        progress = ui.Add(PROGRESS_CLASSW, L"示例进度", 0, Progress);
        SendMessageW(progress, PBM_SETRANGE, 0, MAKELPARAM(0, 100));
        toggle = ui.Add(WC_BUTTONW, L"示例开关", BS_AUTOCHECKBOX | BS_PUSHLIKE, Toggle);
        triState = ui.Add(WC_BUTTONW, L"三态复选框", BS_AUTO3STATE, TriState);
        execute = ui.Add(WC_BUTTONW, L"执行一次", BS_PUSHBUTTON, Execute);
        executions = ui.Label(L"");
        longLabel = ui.Label(L"长文本（中文、换行与表情，可滚动选择和复制）");
        longText = ui.Add(WC_EDITW, LongContent().c_str(), ES_MULTILINE | ES_READONLY |
            ES_AUTOVSCROLL | WS_VSCROLL, 0, WS_EX_CLIENTEDGE);
        resetButton = ui.Add(WC_BUTTONW, L"重置选择与状态", BS_PUSHBUTTON, ResetControls);
        Reset();
    }

    void UpdateNumber() {
        const int value = static_cast<int>(SendMessageW(slider, TBM_GETPOS, 0, 0));
        SendMessageW(progress, PBM_SETPOS, value, 0);
        SetWindowTextW(numericLabel, (L"示例滑块 / 进度：" + std::to_wstring(value)).c_str());
    }
    void Reset() {
        SendMessageW(lists[0], LB_SETCURSEL, 0, 0);
        SendMessageW(lists[1], LB_SETSEL, FALSE, -1);
        SendMessageW(lists[1], LB_SETSEL, TRUE, 0); SendMessageW(lists[1], LB_SETSEL, TRUE, 1);
        SendMessageW(lists[3], LB_SETSEL, FALSE, -1);
        SendMessageW(lists[3], LB_SETSEL, TRUE, 0); SendMessageW(lists[3], LB_SETSEL, TRUE, 1);
        constexpr std::array<const wchar_t*, 4> values = {L"可编辑内容", L"只读内容", L"禁用内容", L"显隐内容"};
        for (int i = 0; i < 4; ++i) SetWindowTextW(texts[i], values[i]);
        EnableWindow(texts[2], FALSE); hiddenVisible = true; ShowWindow(texts[3], SW_SHOW);
        SendMessageW(slider, TBM_SETPOS, TRUE, 35); UpdateNumber();
        SendMessageW(toggle, BM_SETCHECK, BST_UNCHECKED, 0);
        SendMessageW(triState, BM_SETCHECK, BST_INDETERMINATE, 0);
        executionCount = 0; SetWindowTextW(executions, L"已执行：0 次");
    }
    bool Command(int id, int notification) {
        if (notification != BN_CLICKED) return false;
        if (id == ChangeEnabled) EnableWindow(texts[2], !IsWindowEnabled(texts[2]));
        else if (id == ChangeVisible) { hiddenVisible = !hiddenVisible; ShowWindow(texts[3], hiddenVisible ? SW_SHOW : SW_HIDE); }
        else if (id == Execute) SetWindowTextW(executions, (L"已执行：" + std::to_wstring(++executionCount) + L" 次").c_str());
        else if (id == ResetControls) Reset();
        else return false;
        return true;
    }
    void Layout(int width, int height) const {
        const auto move = ui.move;
        constexpr int margin = 20, gap = 20;
        const int column = (width - margin * 2 - gap) / 2;
        const int right = margin + column + gap;
        move(heading, margin, 8, width - margin * 2, 26);
        move(instructions, margin, 36, width - margin * 2, 24);
        const int listWidth = (width - margin * 2 - gap * 3) / 4;
        const int listHeight = std::clamp((height - 110) / 4, 90, 145);
        for (int i = 0; i < 4; ++i) {
            const int x = margin + i * (listWidth + gap);
            move(listLabels[i], x, 66, listWidth, 24);
            move(lists[i], x, 92, listWidth, listHeight);
        }
        const int top = 92 + listHeight + 18;
        for (int i = 0; i < 4; ++i) {
            move(textLabels[i], margin, top + i * 34, 90, 26);
            move(texts[i], margin + 96, top + i * 34, column - 96, 26);
        }
        move(enableButton, margin, top + 140, 138, 30);
        move(visibleButton, margin + 148, top + 140, 154, 30);
        move(numericLabel, right, top, column, 26);
        move(slider, right, top + 30, column, 34);
        move(progress, right, top + 74, column, 24);
        move(toggle, right, top + 112, 120, 30);
        move(triState, right + 136, top + 112, column - 136, 30);
        move(execute, right, top + 154, 110, 30);
        move(executions, right + 126, top + 154, column - 126, 30);
        const int longTop = top + 192;
        move(longLabel, margin, longTop, width - margin * 2, 24);
        move(longText, margin, longTop + 26, width - margin * 2, height - longTop - 78);
        move(resetButton, margin, height - 40, 174, 30);
    }
};

struct DynamicPage {
    Controls ui;
    const wchar_t* panelClass{};
    HWND heading{}, inputLabel{}, input{}, inputButton{}, inputStatus{}, choicesLabel{}, neighborLabel{}, choiceHost{}, neighborHost{};
    HWND addChoice{}, removeChoice{}, replaceChoice{}, tableLabel{}, table{}, modelButton{}, tableButton{}, sortButton{};
    HWND treeLabel{}, tree{}, addTree{}, resetButton{}, tableStatus{};
    std::vector<HWND> choices;
    int inputVersion{}, modelVersion{}, treeSequence{}, choiceSequence{};
    bool ascending{};
    int choiceScroll{};
    int pageWidth{}, pageHeight{};

    void Create(HWND parent, CreateControlFn create, MoveControlFn move, const wchar_t* paneClass) {
        ui = {parent, create, move}; panelClass = paneClass;
        heading = ui.Label(L"对象替换、同名分组、混合表格与树节点");
        inputLabel = ui.Label(L"动态输入");
        inputButton = ui.Add(WC_BUTTONW, L"替换输入对象", BS_PUSHBUTTON, ReplaceInput);
        inputStatus = ui.Label(L"");
        choicesLabel = ui.Label(L"动态选项组");
        neighborLabel = ui.Label(L"相邻选项组");
        choiceHost = create(WS_EX_CONTROLPARENT, paneClass, L"动态选项组", WS_CLIPCHILDREN | WS_VSCROLL, parent, 0);
        neighborHost = create(WS_EX_CONTROLPARENT, paneClass, L"相邻选项组", WS_CLIPCHILDREN, parent, 0);
        create(0, WC_BUTTONW, L"动态选项", BS_AUTOCHECKBOX | WS_TABSTOP, neighborHost, 0);
        addChoice = ui.Add(WC_BUTTONW, L"增加同名项", BS_PUSHBUTTON, AddChoice);
        removeChoice = ui.Add(WC_BUTTONW, L"移除首项", BS_PUSHBUTTON, RemoveChoice);
        replaceChoice = ui.Add(WC_BUTTONW, L"替换首项", BS_PUSHBUTTON, ReplaceChoice);
        tableLabel = ui.Label(L"混合数据表格");
        modelButton = ui.Add(WC_BUTTONW, L"重新填充行", BS_PUSHBUTTON, ReplaceModel);
        tableButton = ui.Add(WC_BUTTONW, L"替换表格对象", BS_PUSHBUTTON, ReplaceTable);
        sortButton = ui.Add(WC_BUTTONW, L"切换排序", BS_PUSHBUTTON, SortTable);
        tableStatus = ui.Label(L"");
        treeLabel = ui.Label(L"示例树");
        tree = ui.Add(WC_TREEVIEWW, L"示例树", TVS_HASBUTTONS | TVS_HASLINES | TVS_LINESATROOT,
            SampleTree, WS_EX_CLIENTEDGE);
        SendMessageW(tree, TVM_SETITEMHEIGHT, 24, 0);
        addTree = ui.Add(WC_BUTTONW, L"添加树节点", BS_PUSHBUTTON, AddTreeNode);
        resetButton = ui.Add(WC_BUTTONW, L"重置动态样本", BS_PUSHBUTTON, ResetDynamic);
        Reset();
    }
    void ReplaceInputControl() {
        if (input) DestroyWindow(input);
        input = ui.Add(WC_EDITW, L"相同内容", ES_AUTOHSCROLL, DynamicInput, WS_EX_CLIENTEDGE);
        SetWindowPos(input, inputLabel, 0, 0, 0, 0, SWP_NOMOVE | SWP_NOSIZE | SWP_NOACTIVATE);
        SetWindowTextW(inputStatus, (L"输入对象版本：" + std::to_wstring(++inputVersion)).c_str());
    }
    void CreateTable() {
        if (table) DestroyWindow(table);
        table = ui.Add(WC_LISTVIEWW, L"混合数据表格", LVS_REPORT | LVS_SHOWSELALWAYS, MixedTable, WS_EX_CLIENTEDGE);
        SetWindowPos(table, tableLabel, 0, 0, 0, 0, SWP_NOMOVE | SWP_NOSIZE | SWP_NOACTIVATE);
        ListView_SetExtendedListViewStyle(table, LVS_EX_FULLROWSELECT | LVS_EX_GRIDLINES | LVS_EX_CHECKBOXES | LVS_EX_DOUBLEBUFFER);
        constexpr std::array<const wchar_t*, 3> titles = {L"ID", L"名称", L"启用"};
        for (int i = 0; i < 3; ++i) {
            LVCOLUMNW column{}; column.mask = LVCF_TEXT | LVCF_WIDTH | LVCF_SUBITEM;
            column.pszText = const_cast<wchar_t*>(titles[i]); column.iSubItem = i;
            column.cx = i == 1 ? 150 : 72; ListView_InsertColumn(table, i, &column);
        }
        FillTable();
    }
    void FillTable() {
        ListView_DeleteAllItems(table);
        constexpr std::array<int, 3> ids = {3, 1, 2};
        for (int i = 0; i < 3; ++i) {
            std::wstring text = std::to_wstring(ids[i]);
            LVITEMW item{}; item.mask = LVIF_TEXT | LVIF_PARAM; item.iItem = i;
            item.pszText = const_cast<wchar_t*>(text.c_str()); item.lParam = ids[i];
            ListView_InsertItem(table, &item);
            ListView_SetItemText(table, i, 1, const_cast<wchar_t*>(i < 2 ? L"同名" : L"样本"));
            ListView_SetItemText(table, i, 2, const_cast<wchar_t*>(i == 1 ? L"否" : L"是"));
            ListView_SetCheckState(table, i, i != 1);
        }
        ascending = false;
        SetWindowTextW(tableStatus, (L"表格内容版本：" + std::to_wstring(++modelVersion)).c_str());
    }
    void ItemChanged(const NMLISTVIEW& change) const {
        if (change.iItem < 0 || !(change.uChanged & LVIF_STATE) ||
                !((change.uOldState ^ change.uNewState) & LVIS_STATEIMAGEMASK)) return;
        ListView_SetItemText(table, change.iItem, 2,
            const_cast<wchar_t*>(ListView_GetCheckState(table, change.iItem) ? L"是" : L"否"));
    }
    HTREEITEM InsertTree(const wchar_t* text, HTREEITEM parent) {
        TVINSERTSTRUCTW insert{}; insert.hParent = parent; insert.hInsertAfter = TVI_LAST;
        insert.item.mask = TVIF_TEXT; insert.item.pszText = const_cast<wchar_t*>(text);
        return TreeView_InsertItem(tree, &insert);
    }
    void AddOption(int at = -1, bool checked = false) {
        HWND option = ui.create(0, WC_BUTTONW, L"动态选项", BS_AUTOCHECKBOX | WS_TABSTOP,
            choiceHost, DynamicChoiceFirst + choiceSequence++);
        SendMessageW(option, BM_SETCHECK, checked ? BST_CHECKED : BST_UNCHECKED, 0);
        if (at < 0) choices.push_back(option); else choices.insert(choices.begin() + at, option);
    }
    void Reset() {
        inputVersion = 0; modelVersion = 0; treeSequence = 0; choiceScroll = 0;
        ReplaceInputControl(); CreateTable();
        for (HWND option : choices) DestroyWindow(option);
        choices.clear();
        for (int i = 0; i < 3; ++i) AddOption();
        SendMessageW(GetWindow(neighborHost, GW_CHILD), BM_SETCHECK, BST_UNCHECKED, 0);
        TreeView_DeleteAllItems(tree);
        HTREEITEM root = InsertTree(L"示例组织", TVI_ROOT);
        HTREEITEM development = InsertTree(L"研发部", root);
        InsertTree(L"北京办公室", development); InsertTree(L"上海办公室", development);
        InsertTree(L"支持部", root); TreeView_Expand(tree, root, TVE_EXPAND); TreeView_Expand(tree, development, TVE_EXPAND);
    }
    static int CALLBACK CompareRows(LPARAM left, LPARAM right, LPARAM data) {
        const auto* self = reinterpret_cast<const DynamicPage*>(data);
        return (left < right ? -1 : left > right ? 1 : 0) * (self->ascending ? 1 : -1);
    }
    void LayoutChoices() {
        RECT bounds{}; GetClientRect(choiceHost, &bounds);
        const int contentHeight = ((static_cast<int>(choices.size()) + 1) / 2) * 28;
        choiceScroll = std::clamp(choiceScroll, 0, std::max(0, contentHeight - static_cast<int>(bounds.bottom)));
        SCROLLINFO scroll{}; scroll.cbSize = sizeof(scroll); scroll.fMask = SIF_RANGE | SIF_PAGE | SIF_POS | SIF_DISABLENOSCROLL;
        scroll.nMax = std::max(0, contentHeight - 1); scroll.nPage = bounds.bottom; scroll.nPos = choiceScroll;
        SetScrollInfo(choiceHost, SB_VERT, &scroll, TRUE);
        const int column = bounds.right / 2;
        for (int i = 0; i < static_cast<int>(choices.size()); ++i) {
            ui.move(choices[i], (i % 2) * column, (i / 2) * 28 - choiceScroll, column, 26);
        }
    }
    void ScrollChoices(int command, int position) {
        if (command == SB_LINEUP) choiceScroll -= 28;
        else if (command == SB_LINEDOWN) choiceScroll += 28;
        else if (command == SB_PAGEUP) choiceScroll -= 56;
        else if (command == SB_PAGEDOWN) choiceScroll += 56;
        else if (command == SB_THUMBTRACK || command == SB_THUMBPOSITION) choiceScroll = position;
        else if (command == SB_TOP) choiceScroll = 0;
        else if (command == SB_BOTTOM) choiceScroll = static_cast<int>(choices.size()) * 28;
        LayoutChoices();
    }
    bool Command(int id, int notification) {
        if (notification != BN_CLICKED) return false;
        if (id == ReplaceInput) ReplaceInputControl();
        else if (id == AddChoice) AddOption();
        else if (id == RemoveChoice && !choices.empty()) { DestroyWindow(choices.front()); choices.erase(choices.begin()); }
        else if (id == ReplaceChoice && !choices.empty()) {
            const bool checked = SendMessageW(choices.front(), BM_GETCHECK, 0, 0) == BST_CHECKED;
            DestroyWindow(choices.front()); choices.erase(choices.begin()); AddOption(0, checked);
        }
        else if (id == ReplaceModel) FillTable();
        else if (id == ReplaceTable) CreateTable();
        else if (id == SortTable) { ascending = !ascending; ListView_SortItems(table, CompareRows, reinterpret_cast<LPARAM>(this)); }
        else if (id == AddTreeNode) {
            InsertTree((L"新增成员 " + std::to_wstring(++treeSequence)).c_str(), TreeView_GetRoot(tree));
            TreeView_Expand(tree, TreeView_GetRoot(tree), TVE_EXPAND);
        }
        else if (id == ResetDynamic) Reset();
        else return false;
        Layout(pageWidth, pageHeight);
        return true;
    }
    void Layout(int width, int height) {
        pageWidth = width; pageHeight = height;
        const auto move = ui.move;
        constexpr int margin = 20, gap = 20;
        const int column = (width - margin * 2 - gap) / 2;
        const int right = margin + column + gap;
        move(heading, margin, 10, width - margin * 2, 28);
        move(inputLabel, margin, 52, column, 24); move(input, margin, 82, column, 28);
        move(inputButton, margin, 122, 150, 30); move(inputStatus, margin, 162, column, 26);
        move(choicesLabel, right, 52, column * 2 / 3, 24);
        move(neighborLabel, right + column * 2 / 3, 52, column / 3, 24);
        move(choiceHost, right, 82, column * 2 / 3, 76);
        move(neighborHost, right + column * 2 / 3, 82, column / 3, 76);
        LayoutChoices();
        HWND neighbor = GetWindow(neighborHost, GW_CHILD);
        move(neighbor, 0, 0, column / 3, 26);
        move(addChoice, right, 168, 110, 30); move(removeChoice, right + 120, 168, 100, 30);
        move(replaceChoice, right + 230, 168, 100, 30);
        const int top = 222, gridHeight = std::max(100, height - top - 158);
        move(tableLabel, margin, top, column, 26); move(table, margin, top + 32, column, gridHeight);
        move(modelButton, margin, top + gridHeight + 76, 110, 30);
        move(tableButton, margin + 120, top + gridHeight + 76, 126, 30);
        move(sortButton, margin + 256, top + gridHeight + 76, 100, 30);
        move(tableStatus, margin, top + gridHeight + 40, column, 26);
        move(treeLabel, right, top, column, 26); move(tree, right, top + 32, column, gridHeight);
        move(addTree, right, top + gridHeight + 76, 140, 30);
        move(resetButton, margin, height - 40, 174, 30);
    }
};

} // namespace win32_samples
