// Verify startup randomization without creating any HWND or running wWinMain.
#include "../src/main.cpp"

#include <iostream>
#include <set>
#include <stdexcept>

namespace {
void Require(bool condition, const char* message) {
    if (!condition) {
        throw std::runtime_error(message);
    }
}

void VerifyLayout(const win32_form::FormRun& run) {
    std::set<int> fields;
    int lastBottom = 30;
    for (int field : run.order) {
        Require(field >= 0 && field < 10 && fields.insert(field).second,
                "The randomized layout must include each field exactly once");
        Require(run.rowY[field] >= lastBottom + 12, "Fields must not overlap when the remark box changes position");
        lastBottom = run.rowY[field] + win32_form::FormRun::ItemHeight(field);
    }
    Require(fields.size() == 10 && lastBottom < 515, "All fields must fit above the form action buttons");
}

void VerifyConfigurations() {
    VerifyLayout(g_formRun);
    Require(g_formRun.panelClassName != L"XPathWin32Panel", "Random panes must have a generated class name");
    std::set<std::array<int, 10>> orders;
    std::set<std::wstring> classNames;
    std::set<int> firstIds;
    for (int seed = 0; seed < 128; ++seed) {
        std::mt19937_64 engine(seed);
        auto run = win32_form::FormRun::Random(engine);
        VerifyLayout(run);
        orders.insert(run.order);
        classNames.insert(run.panelClassName);
        firstIds.insert(run.ControlId(NameEdit));
        const auto originalOrder = run.order;
        const auto originalRows = run.rowY;
        const int id = run.ControlId(PasswordEdit);
        Require(run.ControlId(PasswordEdit) == id && run.LogicalId(id) == PasswordEdit,
                "Repeated lookups must keep each control's identity and command mapping");
        Require(run.order == originalOrder && run.rowY == originalRows,
                "ID allocation must not reshuffle a running form");
    }
    Require(orders.size() > 100 && classNames.size() == 128 && firstIds.size() > 100,
            "Different startup seeds must vary field order, pane class names, and IDs");
    const win32_form::FormRun standard;
    Require(standard.order == std::array<int, 10>{0, 1, 2, 3, 4, 5, 6, 7, 8, 9}
            && standard.rowY == std::array<int, 10>{42, 84, 126, 168, 210, 252, 294, 336, 378, 470}
            && standard.panelClassName == L"XPathWin32Panel", "The existing UIA versions must keep their standard layout");
}
}

int main() {
    try {
        std::set<int> ids;
        for (int index = 0; index < 40; ++index) {
            const int id = RuntimeControlId(0);
            Require(id > 0 && id <= 65535, "Anonymous labels and panes must also receive random AutomationIds");
            Require(ids.insert(id).second, "Anonymous elements must have distinct AutomationIds");
            Require(LogicalControlId(id) == 0, "Anonymous IDs must not be decoded as commands");
        }
        for (int logical : {NameEdit, PasswordEdit, EmailEdit, AgeEdit, AgeSpin, CityCombo,
                            CityMultiFirst, GenderMale, HobbyFirst, RemarkEdit, AgreeCheck,
                            SaveButton, ResetButton, PopupMenuButton, EmployeeList, DragArena}) {
            const int id = RuntimeControlId(logical);
            Require(id > 0 && id <= 65535, "IDs must fit the Win32 WM_COMMAND identifier");
            Require(ids.insert(id).second, "Interactive controls must not collide with labels or panes");
            Require(LogicalControlId(id) == logical, "Random IDs must preserve logical command routing");
            Require(RuntimeControlId(logical) == id, "An element's ID must stay stable during a run");
        }
        VerifyConfigurations();
        std::cout << "Random form checks passed without launching an application.\n";
        return 0;
    } catch (const std::exception& error) {
        std::cerr << error.what() << '\n';
        return 1;
    }
}
