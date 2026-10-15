// Verify each standalone pressure EXE's selected depth without creating a window.
#include "../src/uia_pressure_main.cpp"

#include <iostream>

int main() {
    const wchar_t* arguments[] = {nullptr, L"", L"500", L"1000", L"2000", L"invalid"};
    for (const wchar_t* argument : arguments) {
        if (ParseDepth(const_cast<wchar_t*>(argument)) != WIN32_UIA_PRESSURE_FIXED_DEPTH) {
            std::cerr << "Standalone pressure EXE must always use its compiled depth: "
                      << WIN32_UIA_PRESSURE_FIXED_DEPTH << '\n';
            return 1;
        }
    }
    std::cout << "Standalone pressure depth checks passed without launching an application.\n";
    return 0;
}
