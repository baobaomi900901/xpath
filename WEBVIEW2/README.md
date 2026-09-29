# WebView2 浏览器套壳靶场

Windows x64 桌面程序，左侧为标准 Win32 菜单，右侧为真实 Microsoft Edge WebView2 页面，供 UI 自动化 / RPA / UIA 及浏览器元素定位测试使用。

## 页面

| 原生菜单项 | 页面地址 |
|---|---|
| 点击测试（默认） | https://baobaomi900901.github.io/xpath/#/keys-click-test |
| 表单测试 | https://baobaomi900901.github.io/xpath/#/form-controls |
| iframe表单 | https://baobaomi900901.github.io/xpath/#/iframe-shadow-form |

选中菜单后在同一个 WebView2 控件中导航。网页使用现有线上页面，iframe 和 Shadow DOM 保持网页本身的结构；不需要启动本地 WEB 服务。

左侧菜单支持鼠标、上下方向键选择。顶部地址框只读，可选中复制；“刷新”重新加载当前页面。底部显示初始化、加载和错误状态。页面内部导航到上述三个地址时，左侧菜单同步选中对应项目。

## 环境要求

- Windows 10 / 11 x64。
- 构建：Visual Studio 2019+ 的“使用 C++ 的桌面开发”工作负载和 Windows SDK。CMake 最低版本按 VS 区分：VS2019 为 3.20+、VS2022 为 3.21+、VS2026 为 4.2+。脚本会检查 PATH 中的 CMake 是否支持对应生成器，不满足时尝试 Visual Studio 自带版本。
- 运行：[Microsoft Edge WebView2 Runtime](https://developer.microsoft.com/microsoft-edge/webview2/)。只有 Edge 浏览器并不代表已安装 Runtime。
- Python 3.8+：仅使用 `tools/start_webview2.py` 时需要。
- Node.js 22+：仅运行验收脚本时需要。
- 网络能够访问三个 GitHub Pages 页面；首次构建还需要访问 `api.nuget.org`。

SDK 固定为 `Microsoft.Web.WebView2 1.0.4191.47`，首次构建由 `build.ps1` 下载官方 NuGet 包、校验 SHA256 并解压到 `.tools/`，后续复用缓存。Loader 静态链接到 EXE。

## 构建与启动

在仓库根目录执行：

```powershell
python .\tools\start_webview2.py                     # 构建并启动
python .\tools\start_webview2.py --no-launch         # 只构建并检查产物
python .\tools\start_webview2.py --configuration Debug
```

启动器每次默认先执行构建，再启动程序；源码未变化时使用增量构建。

或者只使用 PowerShell：

```powershell
.\WEBVIEW2\run.ps1         # 构建并启动
.\WEBVIEW2\build.ps1       # 只构建
```

若本机执行策略禁止脚本，可单次运行：

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\WEBVIEW2\run.ps1
```

Release 产物：`WEBVIEW2/build/Release/webview2-shooting-range.exe`。已装好 Runtime 的电脑可直接运行该 EXE；如果提示缺少 Visual C++ Runtime，安装 Microsoft Visual C++ 2015–2022 x64 Redistributable。

浏览器用户数据默认保存在 `%LOCALAPPDATA%\XPath\WebView2Range`。关闭再启动会保留网站的 Cookie、localStorage 等数据；切换页面时按照网站本身的逻辑更新状态。不要将用户数据目录提交到仓库。

## 自动化定位

主窗口标题：`WebView2 浏览器靶场`，窗口类名：`XPathWebView2Range`。

| 宿主控件 | Win32 控件 ID | 类型 |
|---|---|---|
| 左侧测试菜单 | 1001 | 标准 LISTBOX，项目名称对应上述三项 |
| 当前地址 | 1002 | 只读 EDIT |
| 刷新 | 1003 | BUTTON |
| 加载状态 | 1004 | STATIC |

WebView2 子树由运行时提供无障碍信息，页面的 DOM、iframe 和 Shadow DOM 由原有 WEB 页面定义。可以使用 Inspect 或自己的自动化工具观察原生菜单与浏览器内容在同一个桌面窗口下的结构。

## 验收

构建后运行：

```powershell
node .\WEBVIEW2\verify\verify-flow.mjs
```

验收会启动一个独立测试实例，通过 Win32 消息操作实际菜单和刷新按钮，通过本机 CDP 检查实际 WebView2 页面：

1. 默认点击测试页面及三个菜单文案。
2. 点击页面按钮并确认交互日志。
3. 方向键切换菜单并在普通表单输入。
4. 菜单选择 iframe 页面并在 iframe → Open Shadow DOM 表单输入。
5. 调整窗口大小、最小化及恢复。
6. 原生刷新按钮重载当前页面。
7. 模拟断网时显示加载失败，恢复网络后刷新恢复页面。
8. 原生关闭窗口，宿主进程正常退出。

验收无需安装 npm 包；使用 Node.js 自带 WebSocket。结果和页面截图保存在 `verify/artifacts/`，该目录已 gitignore。测试实例使用独立用户数据目录，调试端口只在验收启动时设置；正常启动不会主动开启远程调试。

## 故障排查

- **初始化失败**：按窗口中的提示检查 Runtime 和用户数据目录权限，处理后点“刷新”重新初始化。
- **页面加载失败**：确认网络或代理能访问 GitHub Pages，恢复后点“刷新”。错误状态中包含 WebView2 的 `WebErrorStatus`。
- **SDK 下载失败**：检查 `api.nuget.org` 的访问与代理配置，重新运行构建脚本；无需重新安装 Visual Studio。
- **浏览器进程退出**：底部提示后点“刷新”重新创建 WebView2。
- **验收连接失败**：运行环境需允许启动 WebView2 子进程及访问本机调试端口，限制网络的沙箱可能阻止这些操作。

源码基于微软的 [Win32 WebView2 接入方式](https://learn.microsoft.com/en-us/microsoft-edge/webview2/get-started/win32)，运行时分发方式见 [官方文档](https://learn.microsoft.com/en-us/microsoft-edge/webview2/concepts/distribution)。
