// Own-process tests of the actual native widgets; no external UI automation.
#include "../src/main.cpp"
#include <iostream>
#include <stdexcept>

void Require(bool value, const char* message) {
    if (!value) throw std::runtime_error(message);
}

void Fits(HWND child, HWND parent) {
    RECT rect{}, client{};
    GetWindowRect(child, &rect); MapWindowPoints(nullptr, parent, reinterpret_cast<POINT*>(&rect), 2);
    GetClientRect(parent, &client);
    Require(rect.left >= 0 && rect.top >= 0 && rect.right <= client.right && rect.bottom <= client.bottom,
            "Control must stay inside its page at the minimum window size");
    Require(rect.right > rect.left && rect.bottom > rect.top, "Control must have usable size");
}

int main() {
    HWND window = nullptr;
    try {
        g_app.instance = GetModuleHandleW(nullptr);
        INITCOMMONCONTROLSEX controls{sizeof(controls), ICC_WIN95_CLASSES};
        Require(InitCommonControlsEx(&controls) != FALSE, "Common controls initialization");
        Require(RegisterWindowClasses(g_app.instance), "Register sample classes");
        // Creating the real window also exercises early WM_SIZE during SetMenu.
        window = CreateWindowExW(0, kMainWindowClass, kWindowTitle, WS_OVERLAPPEDWINDOW | WS_CLIPCHILDREN,
                                 0, 0, 900, 680, nullptr, nullptr, g_app.instance, nullptr);
        Require(window != nullptr, "Create full sample window without showing it");
        auto& selection = g_selectionSamples;
        auto& dynamic = g_dynamicSamples;
        Require(!(GetWindowLongPtrW(selection.lists[0], GWL_STYLE) & (LBS_MULTIPLESEL | LBS_EXTENDEDSEL)), "Single list style");
        Require(GetWindowLongPtrW(selection.lists[1], GWL_STYLE) & LBS_MULTIPLESEL, "Ordinary multiple list style");
        Require(GetWindowLongPtrW(selection.lists[3], GWL_STYLE) & LBS_EXTENDEDSEL, "Extended multiple list style");
        Require(SendMessageW(selection.lists[1], LB_GETSELCOUNT, 0, 0) == 2 &&
                SendMessageW(selection.lists[3], LB_GETSELCOUNT, 0, 0) == 2, "Native initial selection really includes two items");
        Require(SendMessageW(selection.lists[2], LB_GETCOUNT, 0, 0) == 0, "Empty list has no placeholder");
        Require(GetWindowLongPtrW(selection.texts[1], GWL_STYLE) & ES_READONLY, "Readonly text style");
        Require(!IsWindowEnabled(selection.texts[2]), "Disabled text state");
        selection.Command(win32_samples::ChangeEnabled, BN_CLICKED);
        Require(IsWindowEnabled(selection.texts[2]) != FALSE, "Enable action");
        selection.Command(win32_samples::ChangeVisible, BN_CLICKED);
        Require(!(GetWindowLongPtrW(selection.texts[3], GWL_STYLE) & WS_VISIBLE), "Hide action");
        SendMessageW(selection.slider, TBM_SETPOS, TRUE, 73); selection.UpdateNumber();
        Require(SendMessageW(selection.progress, PBM_GETPOS, 0, 0) == 73, "Progress follows slider");
        selection.Command(win32_samples::Execute, BN_CLICKED);
        Require(selection.executionCount == 1, "Execution counter"); selection.Reset();
        Require(!IsWindowEnabled(selection.texts[2]) && selection.hiddenVisible && selection.executionCount == 0, "Reset states");
        Require(GetWindowTextLengthW(selection.longText) > 12000, "Long Unicode text sample");
        Require(GetWindow(dynamic.input, GW_HWNDPREV) == dynamic.inputLabel, "Native input label association");
        dynamic.Command(win32_samples::ReplaceInput, BN_CLICKED);
        Require(dynamic.inputVersion == 2 && GetWindow(dynamic.input, GW_HWNDPREV) == dynamic.inputLabel, "Replacement retains label order");
        SendMessageW(dynamic.choices.front(), BM_SETCHECK, BST_CHECKED, 0);
        dynamic.Command(win32_samples::ReplaceChoice, BN_CLICKED);
        Require(SendMessageW(dynamic.choices.front(), BM_GETCHECK, 0, 0) == BST_CHECKED, "Replace retains choice state");
        for (int i = 0; i < 20; ++i) dynamic.Command(win32_samples::AddChoice, BN_CLICKED);
        dynamic.ScrollChoices(SB_BOTTOM, 0);
        Require(dynamic.choices.size() == 23 && dynamic.choiceScroll > 0, "Large choice group can scroll");
        Require(GetWindow(GetWindow(dynamic.neighborHost, GW_CHILD), GW_HWNDNEXT) == nullptr, "Separate adjacent group");
        dynamic.Command(win32_samples::ReplaceTable, BN_CLICKED);
        Require(ListView_GetItemCount(dynamic.table) == 3 && GetWindow(dynamic.table, GW_HWNDPREV) == dynamic.tableLabel, "Replace table and preserve label");
        ListView_SetCheckState(dynamic.table, 0, FALSE);
        wchar_t checkedText[8]{}; ListView_GetItemText(dynamic.table, 0, 2, checkedText, 8);
        Require(std::wstring(checkedText) == L"否", "Checkbox change must update its displayed state column");
        Require((GetWindowLongPtrW(g_app.employeeList, GWL_STYLE) & LVS_SINGLESEL) != 0, "Original table remains single-select");
        dynamic.Command(win32_samples::AddTreeNode, BN_CLICKED);
        Require(TreeView_GetCount(dynamic.tree) == 6, "Append tree member");
        dynamic.Command(win32_samples::ResetDynamic, BN_CLICKED);
        Require(dynamic.choices.size() == 3 && dynamic.choiceScroll == 0 && TreeView_GetCount(dynamic.tree) == 5, "Reset structure");
        for (auto size : {SIZE{900,680}, SIZE{1024,720}, SIZE{1280,800}}) {
            SetWindowPos(window, nullptr, 0, 0, size.cx, size.cy, SWP_NOZORDER | SWP_NOACTIVATE);
            Fits(selection.longText, selection.ui.parent); Fits(selection.resetButton, selection.ui.parent);
            Fits(dynamic.table, dynamic.ui.parent); Fits(dynamic.sortButton, dynamic.ui.parent);
            Fits(dynamic.addTree, dynamic.ui.parent); Fits(dynamic.resetButton, dynamic.ui.parent);
            RECT action{}, footer{}; GetWindowRect(dynamic.sortButton, &action); GetWindowRect(dynamic.resetButton, &footer);
            Require(action.bottom < footer.top, "Dynamic table actions must not overlap footer");
        }
        DestroyWindow(window);
        std::cout << "Native control samples passed.\n";
        return 0;
    } catch (const std::exception& error) {
        if (window) DestroyWindow(window);
        std::cerr << error.what() << '\n'; return 1;
    }
}
