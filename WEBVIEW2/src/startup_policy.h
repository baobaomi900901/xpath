#pragma once

#include <windows.h>
#include <shellapi.h>
#include <string>

namespace startup_policy {
// A non-empty process-local override prevents the loader from falling back to
// AdditionalBrowserArguments in the registry. Chromium rejects -1 as a debug
// port; 0 must not be used here because it requests an ephemeral listening port.
inline bool DisableRemoteDebugging() {
    if (!SetEnvironmentVariableW(L"WEBVIEW2_ADDITIONAL_BROWSER_ARGUMENTS",
                                 L"--remote-debugging-port=-1")) return false;
    for (const wchar_t* name : {L"WEBVIEW2_WAIT_FOR_SCRIPT_DEBUGGER",
                                L"WEBVIEW2_PIPE_FOR_SCRIPT_DEBUGGER"}) {
        if (!SetEnvironmentVariableW(name, nullptr) && GetLastError() != ERROR_ENVVAR_NOT_FOUND)
            return false;
    }
    return true;
}

// WebView2 can read --edge-webview-switches directly from the host command line,
// after environment options have been applied. This host has no command-line
// options of its own. Re-enter with a clean OS command line before loading the
// runtime instead of modifying the process command-line buffer in place.
// The original process waits so callers can still wait for normal app exit.
inline bool RunWithoutArguments(int showCommand, int& exitCode) {
    int count = 0;
    LPWSTR* arguments = CommandLineToArgvW(GetCommandLineW(), &count);
    if (!arguments) { exitCode = 1; return true; }
    LocalFree(arguments);
    if (count <= 1) return false;
    std::wstring executable(32768, L'\0');
    const DWORD length = GetModuleFileNameW(nullptr, executable.data(),
                                           static_cast<DWORD>(executable.size()));
    if (!length || length >= executable.size()) { exitCode = 1; return true; }
    executable.resize(length);
    std::wstring command = L"\"" + executable + L"\"";
    STARTUPINFOW startup{sizeof(startup)};
    startup.dwFlags = STARTF_USESHOWWINDOW;
    startup.wShowWindow = static_cast<WORD>(showCommand);
    PROCESS_INFORMATION process{};
    if (!CreateProcessW(executable.c_str(), command.data(), nullptr, nullptr, FALSE,
                        0, nullptr, nullptr, &startup, &process)) {
        exitCode = 1;
        return true;
    }
    CloseHandle(process.hThread);
    DWORD result = 1;
    if (WaitForSingleObject(process.hProcess, INFINITE) == WAIT_OBJECT_0)
        GetExitCodeProcess(process.hProcess, &result);
    CloseHandle(process.hProcess);
    exitCode = static_cast<int>(result);
    return true;
}
}  // namespace startup_policy
