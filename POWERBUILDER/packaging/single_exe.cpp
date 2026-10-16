#define WIN32_LEAN_AND_MEAN
#define NOMINMAX
#include <windows.h>
#include <setupapi.h>
#include <shellapi.h>
#include <tlhelp32.h>
#include <strsafe.h>
#include <objbase.h>
#include <algorithm>
#include <string>
#include <vector>

namespace {
struct Failure { std::wstring message; };
[[noreturn]] void Fail(const std::wstring& message) { throw Failure{message}; }

std::string Utf8(const std::wstring& value) {
    if (value.empty()) return {};
    int size = WideCharToMultiByte(CP_UTF8, WC_ERR_INVALID_CHARS, value.data(), static_cast<int>(value.size()), nullptr, 0, nullptr, nullptr);
    if (!size) Fail(L"Cannot encode a Windows path.");
    std::string result(size, '\0');
    WideCharToMultiByte(CP_UTF8, WC_ERR_INVALID_CHARS, value.data(), static_cast<int>(value.size()), result.data(), size, nullptr, nullptr);
    return result;
}

std::string JsonString(const std::wstring& value) {
    std::string result = "\"";
    for (unsigned char c : Utf8(value)) {
        if (c == '\\' || c == '"') { result += '\\'; result += static_cast<char>(c); }
        else if (c < 32) {
            const char* hex = "0123456789abcdef";
            result += "\\u00"; result += hex[c >> 4]; result += hex[c & 15];
        } else result += static_cast<char>(c);
    }
    return result + "\"";
}

std::wstring FullPath(const std::wstring& value) {
    wchar_t buffer[MAX_PATH];
    DWORD count = GetFullPathNameW(value.c_str(), MAX_PATH, buffer, nullptr);
    if (!count || count >= MAX_PATH) Fail(L"The path is too long: " + value);
    return buffer;
}

void WriteBytes(const std::wstring& path, const void* data, DWORD size, bool create_new = false) {
    HANDLE file = CreateFileW(path.c_str(), GENERIC_WRITE, 0, nullptr,
        create_new ? CREATE_NEW : CREATE_ALWAYS, FILE_ATTRIBUTE_NORMAL, nullptr);
    if (file == INVALID_HANDLE_VALUE) Fail(L"Cannot write: " + path);
    DWORD written = 0;
    BOOL success = WriteFile(file, data, size, &written, nullptr);
    CloseHandle(file);
    if (!success || written != size) Fail(L"Incomplete write: " + path);
}

std::string ReadReport(const std::wstring& path) {
    HANDLE file = CreateFileW(path.c_str(), GENERIC_READ, FILE_SHARE_READ, nullptr, OPEN_EXISTING, FILE_ATTRIBUTE_NORMAL, nullptr);
    if (file == INVALID_HANDLE_VALUE) Fail(L"The application did not produce its self-test report.");
    DWORD size = GetFileSize(file, nullptr);
    if (size == INVALID_FILE_SIZE || size > 1024 * 1024) { CloseHandle(file); Fail(L"Invalid self-test report size."); }
    std::string result(size, '\0');
    DWORD read = 0;
    BOOL success = ReadFile(file, result.data(), size, &read, nullptr);
    CloseHandle(file);
    if (!success || read != size) Fail(L"Cannot read the self-test report.");
    if (result.compare(0, 3, "\xef\xbb\xbf") == 0) result.erase(0, 3);
    return result;
}

bool SafeName(const std::wstring& name) {
    return !name.empty() && name != L"." && name != L".." &&
        name.find_first_of(L"\\/:\"<>|?*") == std::wstring::npos &&
        name.back() != L'.' && name.back() != L' ';
}

// The cabinet is flat; no archive entry may escape this newly created folder.
UINT CALLBACK ExtractCallback(PVOID context, UINT notification, UINT_PTR parameter, UINT_PTR) {
    const auto& directory = *static_cast<std::wstring*>(context);
    if (notification == SPFILENOTIFY_FILEINCABINET) {
        auto* info = reinterpret_cast<FILE_IN_CABINET_INFO_W*>(parameter);
        if (!SafeName(info->NameInCabinet)) { SetLastError(ERROR_INVALID_NAME); return FILEOP_ABORT; }
        std::wstring destination = directory + L"\\" + info->NameInCabinet;
        if (FAILED(StringCchCopyW(info->FullTargetName, MAX_PATH, destination.c_str()))) {
            SetLastError(ERROR_FILENAME_EXCED_RANGE); return FILEOP_ABORT;
        }
        return FILEOP_DOIT;
    }
    if (notification == SPFILENOTIFY_FILEEXTRACTED)
        return reinterpret_cast<FILEPATHS_W*>(parameter)->Win32Error;
    if (notification == SPFILENOTIFY_NEEDNEWCABINET) return ERROR_BAD_FORMAT;
    return NO_ERROR;
}

struct TemporaryFolder {
    std::wstring path;
    TemporaryFolder() {
        wchar_t temp[MAX_PATH], guid_text[40];
        DWORD size = GetTempPathW(MAX_PATH, temp);
        if (!size || size >= MAX_PATH) Fail(L"Cannot locate the Windows temporary directory.");
        GUID guid;
        if (FAILED(CoCreateGuid(&guid)) || !StringFromGUID2(guid, guid_text, 40)) Fail(L"Cannot create a unique extraction directory.");
        path = std::wstring(temp) + L"PowerBuilderRange-" + guid_text;
        if (path.size() + 100 >= MAX_PATH) Fail(L"The Windows temporary directory path is too long.");
        if (!CreateDirectoryW(path.c_str(), nullptr)) Fail(L"Cannot create: " + path);
    }
    ~TemporaryFolder() {
        // Only flat files inside the exact GUID folder created above are removed.
        // Do not recurse or follow directories/reparse points.
        for (int attempt = 0; attempt < 5; ++attempt) {
            WIN32_FIND_DATAW entry;
            HANDLE search = FindFirstFileW((path + L"\\*").c_str(), &entry);
            if (search != INVALID_HANDLE_VALUE) {
                do {
                    if (!(entry.dwFileAttributes & FILE_ATTRIBUTE_DIRECTORY)) {
                        std::wstring file = path + L"\\" + entry.cFileName;
                        SetFileAttributesW(file.c_str(), FILE_ATTRIBUTE_NORMAL);
                        DeleteFileW(file.c_str());
                    }
                } while (FindNextFileW(search, &entry));
                FindClose(search);
            }
            if (RemoveDirectoryW(path.c_str())) return;
            Sleep(150);
        }
    }
};

void ExtractPayload(HINSTANCE instance, TemporaryFolder& folder) {
    HRSRC resource = FindResourceW(instance, MAKEINTRESOURCEW(101), RT_RCDATA);
    if (!resource) Fail(L"The embedded application payload is missing.");
    DWORD size = SizeofResource(instance, resource);
    HGLOBAL loaded = LoadResource(instance, resource);
    const void* data = loaded ? LockResource(loaded) : nullptr;
    if (!data || !size) Fail(L"Cannot read the embedded application payload.");
    std::wstring cabinet = folder.path + L"\\payload.cab";
    WriteBytes(cabinet, data, size, true);
    if (!SetupIterateCabinetW(cabinet.c_str(), 0, ExtractCallback, &folder.path))
        Fail(L"Cannot unpack the application (Windows error " + std::to_wstring(GetLastError()) + L").");
    DeleteFileW(cabinet.c_str());
}

std::wstring LoadedRuntime(DWORD process_id, HANDLE process) {
    for (int attempt = 0; attempt < 400; ++attempt) {
        HANDLE snapshot = CreateToolhelp32Snapshot(TH32CS_SNAPMODULE | TH32CS_SNAPMODULE32, process_id);
        if (snapshot != INVALID_HANDLE_VALUE) {
            MODULEENTRY32W entry{};
            entry.dwSize = sizeof(entry);
            if (Module32FirstW(snapshot, &entry)) {
                do {
                    if (_wcsicmp(entry.szModule, L"pbvm.dll") == 0) {
                        std::wstring path = entry.szExePath;
                        CloseHandle(snapshot);
                        return path;
                    }
                } while (Module32NextW(snapshot, &entry));
            }
            CloseHandle(snapshot);
        }
        if (WaitForSingleObject(process, 0) == WAIT_OBJECT_0) break;
        Sleep(25);
    }
    return {};
}
} // namespace

int WINAPI wWinMain(HINSTANCE instance, HINSTANCE, PWSTR, int) {
    bool self_test = false;
    std::wstring report_path;
    try {
        int count = 0;
        LPWSTR* arguments = CommandLineToArgvW(GetCommandLineW(), &count);
        if (!arguments) Fail(L"Cannot read command-line arguments.");
        std::vector<std::wstring> args(arguments, arguments + count);
        LocalFree(arguments);
        for (size_t index = 1; index < args.size(); ++index) {
            if (args[index] == L"--self-test") self_test = true;
            else if (args[index] == L"--report" && index + 1 < args.size()) report_path = FullPath(args[++index]);
            else Fail(L"Usage: PowerBuilderRange.exe [--self-test [--report <file>]]");
        }
        if (!report_path.empty() && !self_test) Fail(L"--report requires --self-test.");
        if (self_test && report_path.empty()) report_path = FullPath(L"powerbuilder-package-self-test.json");

        TemporaryFolder folder;
        ExtractPayload(instance, folder);
        std::wstring executable = folder.path + L"\\PowerBuilderShootingRange.exe";
        std::wstring command = L"\"" + executable + L"\"" + (self_test ? L" --self-test" : L"");
        STARTUPINFOW startup{};
        startup.cb = sizeof(startup);
        startup.dwFlags = STARTF_USESHOWWINDOW;
        startup.wShowWindow = self_test ? SW_HIDE : SW_SHOWNORMAL;
        PROCESS_INFORMATION child{};
        if (!CreateProcessW(executable.c_str(), command.data(), nullptr, nullptr, FALSE, 0, nullptr, folder.path.c_str(), &startup, &child))
            Fail(L"Cannot start PowerBuilder (Windows error " + std::to_wstring(GetLastError()) + L").");
        CloseHandle(child.hThread);
        std::wstring runtime = self_test ? LoadedRuntime(child.dwProcessId, child.hProcess) : L"";
        DWORD waited = WaitForSingleObject(child.hProcess, self_test ? 60000 : INFINITE);
        if (waited != WAIT_OBJECT_0) {
            // Only the self-test child created by this invocation is terminated.
            TerminateProcess(child.hProcess, 1);
            WaitForSingleObject(child.hProcess, 5000);
            CloseHandle(child.hProcess);
            Fail(L"The packaged application self-test timed out.");
        }
        DWORD exit_code = 1;
        GetExitCodeProcess(child.hProcess, &exit_code);
        CloseHandle(child.hProcess);
        if (self_test) {
            std::string application = ReadReport(folder.path + L"\\self-test.json");
            bool verified = _wcsicmp(runtime.c_str(), (folder.path + L"\\pbvm.dll").c_str()) == 0;
            bool passed = exit_code == 0 && verified && application.find("\"passed\":true") != std::string::npos;
            std::string result = "{\"bundled_runtime_verified\":" + std::string(verified ? "true" : "false") +
                ",\"loaded_runtime\":" + JsonString(runtime) + ",\"extraction_directory\":" + JsonString(folder.path) +
                ",\"application\":" + application + "}\n";
            WriteBytes(report_path, result.data(), static_cast<DWORD>(result.size()));
            return passed ? 0 : 1;
        }
        return static_cast<int>(exit_code);
    } catch (const Failure& error) {
        if (self_test && !report_path.empty()) {
            try {
                std::string result = "{\"passed\":false,\"error\":" + JsonString(error.message) + "}\n";
                WriteBytes(report_path, result.data(), static_cast<DWORD>(result.size()));
            } catch (...) {}
        } else MessageBoxW(nullptr, error.message.c_str(), L"PowerBuilder 靶场", MB_OK | MB_ICONERROR);
        return 1;
    }
}
