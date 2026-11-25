#pragma once
#include <windows.h>

namespace lazy_a11y {
constexpr UINT DiagnosticsMessage = WM_APP + 0x3A;
constexpr DWORD IdleTimeoutMs = 30000;
constexpr UINT_PTR RetirementTimerId = 0xA113;
// UI thread only. Attachment allocates metadata, never COM providers.
void Attach(HWND hwnd);
void Detach(HWND hwnd);
void Invalidate(HWND hwnd);
void Shutdown();
} // namespace lazy_a11y
