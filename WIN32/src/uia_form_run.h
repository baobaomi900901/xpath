#pragma once

#include <algorithm>
#include <array>
#include <numeric>
#include <random>
#include <stdexcept>
#include <string>
#include <unordered_map>
#include <vector>

namespace win32_form {

// One configuration per process: visual order, HWND sibling order, and IDs stay in sync.
struct FormRun {
    std::array<int, 10> order{0, 1, 2, 3, 4, 5, 6, 7, 8, 9};
    std::array<int, 10> rowY{42, 84, 126, 168, 210, 252, 294, 336, 378, 470};
    std::wstring panelClassName{L"XPathWin32Panel"};

    static int ItemHeight(int field) {
        return field == 8 ? 76 : 30;
    }

    static FormRun Random(std::mt19937_64& engine) {
        FormRun run;
        std::shuffle(run.order.begin(), run.order.end(), engine);
        int y = 42;
        for (int field : run.order) {
            run.rowY[field] = y;
            y += ItemHeight(field) + 12;
        }
        run.panelClassName += L"_" + std::to_wstring(engine());

        // Keep IDs away from menu commands and within WM_COMMAND's 16-bit identifier.
        run.availableIds_.resize(59001);
        std::iota(run.availableIds_.begin(), run.availableIds_.end(), 1000);
        std::shuffle(run.availableIds_.begin(), run.availableIds_.end(), engine);
        return run;
    }

    int ControlId(int logicalId) {
        const auto existing = logicalIds_.find(logicalId);
        if (logicalId != 0 && existing != logicalIds_.end()) {
            return existing->second;
        }
        if (availableIds_.empty()) {
            throw std::runtime_error("No unused Win32 control IDs remain");
        }
        const int id = availableIds_.back();
        availableIds_.pop_back();
        runtimeIds_.emplace(id, logicalId);
        if (logicalId != 0) {
            logicalIds_.emplace(logicalId, id);
        }
        return id;
    }

    int LogicalId(int runtimeId) const {
        const auto found = runtimeIds_.find(runtimeId);
        return found == runtimeIds_.end() ? 0 : found->second;
    }

private:
    std::vector<int> availableIds_;
    std::unordered_map<int, int> runtimeIds_;
    std::unordered_map<int, int> logicalIds_;
};

} // namespace win32_form
