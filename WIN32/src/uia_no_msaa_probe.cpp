#include <windows.h>
#include <ole2.h>
#include <UIAutomation.h>
#include <wrl/client.h>

#include <fcntl.h>
#include <io.h>
#include <iostream>
#include <string>

using Microsoft::WRL::ComPtr;

namespace {

constexpr wchar_t kDefaultWindowTitle[] = L"Win32 靶场 - MSAA Only";

void PrintUsage() {
    std::wcout
        << L"用法:\n"
        << L"  uia-no-msaa-probe.exe\n"
        << L"  uia-no-msaa-probe.exe --title \"窗口标题\"\n"
        << L"  uia-no-msaa-probe.exe --hwnd 0x123456\n";
}

bool ParseWindow(int argc, wchar_t* argv[], HWND* window) {
    if (!window) {
        return false;
    }

    if (argc == 1) {
        *window = FindWindowW(nullptr, kDefaultWindowTitle);
        return *window != nullptr;
    }

    if (argc == 3 && std::wstring(argv[1]) == L"--title") {
        *window = FindWindowW(nullptr, argv[2]);
        return *window != nullptr;
    }

    if (argc == 3 && std::wstring(argv[1]) == L"--hwnd") {
        wchar_t* end = nullptr;
        const unsigned long long value = std::wcstoull(argv[2], &end, 0);
        if (!end || *end != L'\0') {
            return false;
        }
        *window = reinterpret_cast<HWND>(static_cast<ULONG_PTR>(value));
        return IsWindow(*window) != FALSE;
    }

    return false;
}

std::wstring ReadBstr(BSTR value) {
    const std::wstring result = value ? std::wstring(value, SysStringLen(value)) : L"";
    SysFreeString(value);
    return result;
}

HRESULT RemoveMsaaProxy(IUIAutomation* automation) {
    ComPtr<IUIAutomationProxyFactoryMapping> mapping;
    HRESULT result = automation->get_ProxyFactoryMapping(&mapping);
    if (FAILED(result)) {
        return result;
    }

    UINT count = 0;
    result = mapping->get_Count(&count);
    if (FAILED(result)) {
        return result;
    }
    if (count == 0) {
        return E_UNEXPECTED;
    }

    // Microsoft documents the MSAA-to-UIA proxy as the final default entry.
    // Removing it changes only this IUIAutomation client's proxy table.
    return mapping->RemoveEntry(count - 1);
}

void PrintElement(IUIAutomationElement* element, const wchar_t* prefix) {
    BSTR name = nullptr;
    BSTR className = nullptr;
    BSTR frameworkId = nullptr;
    BSTR providerDescription = nullptr;
    CONTROLTYPEID controlType = 0;

    element->get_CurrentName(&name);
    element->get_CurrentClassName(&className);
    element->get_CurrentFrameworkId(&frameworkId);
    element->get_CurrentProviderDescription(&providerDescription);
    element->get_CurrentControlType(&controlType);

    std::wcout
        << prefix << L"Name: " << ReadBstr(name) << L"\n"
        << prefix << L"ClassName: " << ReadBstr(className) << L"\n"
        << prefix << L"FrameworkId: " << ReadBstr(frameworkId) << L"\n"
        << prefix << L"ControlTypeId: " << controlType << L"\n"
        << prefix << L"ProviderDescription: " << ReadBstr(providerDescription) << L"\n";
}

HRESULT AnalyzeDescendants(
    HWND window,
    IUIAutomationElementArray* descendants,
    int descendantCount,
    int* legacyCount,
    int* clientAreaCount,
    int* clientAreaLegacyCount
) {
    if (!window || !descendants || !legacyCount || !clientAreaCount || !clientAreaLegacyCount) {
        return E_INVALIDARG;
    }

    RECT clientBounds{};
    if (!GetClientRect(window, &clientBounds)) {
        return HRESULT_FROM_WIN32(GetLastError());
    }
    POINT clientOrigin{clientBounds.left, clientBounds.top};
    if (!ClientToScreen(window, &clientOrigin)) {
        return HRESULT_FROM_WIN32(GetLastError());
    }
    OffsetRect(&clientBounds, clientOrigin.x, clientOrigin.y);

    *legacyCount = 0;
    *clientAreaCount = 0;
    *clientAreaLegacyCount = 0;
    for (int index = 0; index < descendantCount; ++index) {
        ComPtr<IUIAutomationElement> element;
        HRESULT result = descendants->GetElement(index, &element);
        if (FAILED(result)) {
            return result;
        }

        VARIANT value{};
        result = element->GetCurrentPropertyValue(
            UIA_IsLegacyIAccessiblePatternAvailablePropertyId,
            &value
        );
        if (FAILED(result)) {
            VariantClear(&value);
            return result;
        }
        const bool isLegacy = value.vt == VT_BOOL && value.boolVal == VARIANT_TRUE;
        if (isLegacy) {
            ++(*legacyCount);
        }
        VariantClear(&value);

        RECT elementBounds{};
        result = element->get_CurrentBoundingRectangle(&elementBounds);
        if (FAILED(result)) {
            return result;
        }
        RECT intersection{};
        if (IntersectRect(&intersection, &clientBounds, &elementBounds)) {
            ++(*clientAreaCount);
            if (isLegacy) {
                ++(*clientAreaLegacyCount);
            }
        }
    }
    return S_OK;
}

}  // namespace

int wmain(int argc, wchar_t* argv[]) {
    _setmode(_fileno(stdout), _O_U8TEXT);
    _setmode(_fileno(stderr), _O_U8TEXT);

    HWND window = nullptr;
    if (!ParseWindow(argc, argv, &window)) {
        std::wcerr << L"未找到目标窗口，或参数无效。\n";
        PrintUsage();
        return 2;
    }

    const HRESULT initializeResult = CoInitializeEx(nullptr, COINIT_MULTITHREADED);
    if (FAILED(initializeResult)) {
        std::wcerr << L"CoInitializeEx 失败: 0x" << std::hex << initializeResult << L"\n";
        return 1;
    }

    int exitCode = 1;
    {
        ComPtr<IUIAutomation> automation;
        HRESULT result = CoCreateInstance(
            CLSID_CUIAutomation,
            nullptr,
            CLSCTX_INPROC_SERVER,
            IID_PPV_ARGS(&automation)
        );
        if (FAILED(result)) {
            std::wcerr << L"创建 UI Automation 客户端失败: 0x" << std::hex << result << L"\n";
        } else if (FAILED(result = RemoveMsaaProxy(automation.Get()))) {
            std::wcerr << L"关闭 MSAA Proxy 失败: 0x" << std::hex << result << L"\n";
        } else {
            ComPtr<IUIAutomationElement> root;
            result = automation->ElementFromHandle(window, &root);
            if (FAILED(result)) {
                std::wcerr << L"读取目标窗口失败: 0x" << std::hex << result << L"\n";
            } else {
                ComPtr<IUIAutomationCondition> trueCondition;
                ComPtr<IUIAutomationElementArray> descendants;
                result = automation->CreateTrueCondition(&trueCondition);
                if (SUCCEEDED(result)) {
                    result = root->FindAll(TreeScope_Descendants, trueCondition.Get(), &descendants);
                }

                int descendantCount = -1;
                if (SUCCEEDED(result)) {
                    result = descendants->get_Length(&descendantCount);
                }

                int legacyDescendantCount = -1;
                int clientAreaDescendantCount = -1;
                int clientAreaLegacyDescendantCount = -1;
                if (SUCCEEDED(result)) {
                    result = AnalyzeDescendants(
                        window,
                        descendants.Get(),
                        descendantCount,
                        &legacyDescendantCount,
                        &clientAreaDescendantCount,
                        &clientAreaLegacyDescendantCount
                    );
                }

                if (FAILED(result)) {
                    std::wcerr << L"枚举 UIA 子元素失败: 0x" << std::hex << result << L"\n";
                } else {
                    std::wcout << L"MSAA Proxy: disabled for this process only\n";
                    PrintElement(root.Get(), L"Root.");
                    std::wcout
                        << L"UIA descendant count (including non-client window chrome): "
                        << descendantCount << L"\n"
                        << L"LegacyIAccessible descendant count: "
                        << legacyDescendantCount << L"\n"
                        << L"Client-area UIA descendant count: "
                        << clientAreaDescendantCount << L"\n"
                        << L"Client-area LegacyIAccessible descendant count: "
                        << clientAreaLegacyDescendantCount << L"\n";
                    exitCode = 0;
                }
            }
        }
    }

    CoUninitialize();
    return exitCode;
}
