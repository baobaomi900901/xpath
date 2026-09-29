# WebView2 浏览器套壳靶场设计

日期：2026-09-28
状态：用户已确认（2026-09-28）

## 目标与界面

新增 Windows 桌面靶场，左侧为原生菜单，右侧为真实 WebView2 浏览器控件，供 UI 自动化、RPA 和无障碍元素定位测试使用。

窗口标题为“WebView2 浏览器靶场”。初始窗口大小约 1280 × 900，允许调整大小；左侧菜单宽度约 220 个逻辑像素，右侧内容随窗口大小变化。菜单采用标准 Win32 控件，支持鼠标和键盘选择，选中项有明显标识。默认选中“点击测试”。

菜单名称和目标地址按以下顺序固定：

| 菜单 | WebView2 加载地址 |
|---|---|
| 点击测试 | https://baobaomi900901.github.io/xpath/#/keys-click-test |
| 表单测试 | https://baobaomi900901.github.io/xpath/#/form-controls |
| iframe表单 | https://baobaomi900901.github.io/xpath/#/iframe-shadow-form |

菜单切换在同一个 WebView2 控件内进行。浏览器控件直接加载上述完整地址，页面内部的 iframe 和 Shadow DOM 保持现有网站行为。

内容区上方显示当前页面地址并提供刷新按钮；底部显示初始化、加载、就绪或错误状态。窗口最小化、恢复、调整大小及 DPI 改变时，浏览器内容区正确跟随布局。

## 技术方案与备选

推荐 C++17 + Win32 + Microsoft WebView2 SDK + CMake。现有 WIN32 靶场使用相同工具链，本机已有 Visual Studio C++ 构建环境。新增独立 WEBVIEW2 目录，避免将不同宿主靶场混入 WIN32。

备选 C# WinForms + WebView2：界面代码更少，但当前机器没有 .NET SDK，需要额外准备构建环境。

备选 WPF + WebView2：适合更复杂的界面样式，同样增加 .NET 工具链依赖；本次三个菜单的需求无需引入。

## 目录与启动

- WEBVIEW2/src/main.cpp：原生窗口、菜单、WebView2 初始化、导航、布局及资源释放。
- WEBVIEW2/CMakeLists.txt：固定版本 WebView2 SDK 依赖和 x64 EXE 构建。
- WEBVIEW2/build.ps1：检测 Visual Studio/CMake、准备 SDK、执行构建。
- WEBVIEW2/run.ps1：每次默认构建并启动。
- WEBVIEW2/README.md：依赖、启动、输出路径、验收步骤及故障排查。
- WEBVIEW2/.gitignore：排除 SDK 缓存和构建产物。
- tools/start_webview2.py：标准库 Python 启动器，每次默认构建，支持 --no-launch 只构建。
- README.md：将新靶场加入总览、目录结构和启动说明。

默认构建产物为 WEBVIEW2/build/Release/webview2-shooting-range.exe。首次构建下载固定版本的官方 NuGet SDK，之后复用本地缓存。WebView2 Loader 使用静态链接，减少分发文件。

运行需要 Microsoft Edge WebView2 Runtime。浏览器用户数据放入当前用户 LocalAppData 下的靶场专用目录，避免依赖 EXE 所在目录的写权限。程序不自动安装运行时或修改系统浏览器设置。

## 初始化与错误处理

在 STA 线程初始化 COM，异步创建 WebView2 环境和控制器。初始化期间允许用户选择菜单，并在控件准备完成后加载最后选中的地址。

运行时缺失、初始化失败或网页加载失败时显示可理解的状态和错误信息。刷新按钮在初始化完成后启用，网络恢复后可以重试。关闭窗口时释放控制器和 COM 资源，避免异步回调继续使用已销毁窗口。

## 验收

1. Release 构建成功，产生可运行的 EXE。
2. 首次启动默认加载点击测试页面。
3. 三个菜单项分别加载用户指定的完整 Hash 路由，页面能够交互。
4. 验证点击页面按钮、表单输入以及 iframe 表单输入。
5. 菜单支持键盘切换，刷新可以重新加载当前页面。
6. 调整窗口大小和最小化/恢复时浏览器布局正常。
7. 网络或初始化错误有明确反馈，关闭窗口正常结束。
8. 启动器默认构建后启动，支持只构建选项。

验证以实际 Windows 构建和运行结果为准；外网不可达时单独记录线上页面交互的验证限制。
