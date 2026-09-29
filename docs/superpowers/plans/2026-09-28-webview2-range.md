# WebView2 浏览器靶场 Implementation Plan

> **For agentic workers:** Use executing-plans to implement this plan task-by-task. Steps use checkbox syntax for tracking.

**Goal:** 提供可独立运行的 Windows WebView2 套壳靶场，左侧三个菜单加载指定线上测试页面。

**Architecture:** C++17 原生 Win32 窗口承载标准列表控件和 WebView2。构建、启动和运行验证各有独立入口。

**Tech Stack:** MSVC、CMake 3.20+、Microsoft.Web.WebView2 1.0.4191.47、PowerShell、Python 3.8+、Node.js 22+（验收工具）。

## Global Constraints

- Windows x64，使用独立 WEBVIEW2 目录和 tools/start_webview2.py。
- 三个菜单及完整 Hash URL 按已确认设计固定。
- 默认点击测试，初始化期间保留最后选择，原生菜单可使用键盘。
- SDK 版本固定并缓存，Loader 静态链接，用户数据存储在 LocalAppData。
- 支持窗口缩放、DPI、刷新、错误提示和安全关闭。

## Task 1: 建立实际程序的回归验收

**Files:** WEBVIEW2/verify/verify-flow.mjs、WEBVIEW2/verify/native-controls.ps1。

- [x] 写验收入口，首先断言构建产物存在；不存在时明确失败。
- [x] 使用专用临时 profile 和 localhost CDP 端口启动程序，通过原生控件切换菜单、调整窗口、刷新和关闭。
- [x] 在真实 WebView2 中验证三个 URL、点击交互、普通表单及 iframe 输入。

Run:

```powershell
node WEBVIEW2/verify/verify-flow.mjs
```

未实现时预期：`Executable missing`；完成后预期：每个场景输出 PASS，关闭后进程退出。

## Task 2: 构建并实现原生宿主

**Files:** WEBVIEW2/src/main.cpp、WEBVIEW2/src/app.manifest、WEBVIEW2/src/app.rc、WEBVIEW2/CMakeLists.txt、WEBVIEW2/build.ps1、WEBVIEW2/.gitignore。

**Interfaces:** Win32 标准控件 ID：菜单 1001、地址 1002、刷新 1003、状态 1004。主窗口类名 `XPathWebView2Range`。WebView2 使用环境变量 `WEBVIEW2_ADDITIONAL_BROWSER_ARGUMENTS` 和 `WEBVIEW2_USER_DATA_FOLDER` 的标准覆盖能力，验收工具仅为自己的子进程设置。

- [x] 准备 SDK 缓存和 CMake x64 构建，链接 WebView2LoaderStatic.lib。
- [x] 实现 Win32 原生列表菜单、只读地址、刷新、状态和响应 DPI 的布局。
- [x] 用 WRL ComPtr 管理 COM，异步回调持有窗口状态的弱引用；关闭时先标记关闭，再释放 controller。
- [x] 处理初始化和导航 HRESULT、加载失败、Hash 路由 source changed、浏览器进程失败。
- [x] 运行 Release 构建，检查编译诊断。

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File WEBVIEW2/build.ps1
```

预期：生成 WEBVIEW2/build/Release/webview2-shooting-range.exe，编译无错误。

## Task 3: 启动入口、文档及交付验证

**Files:** WEBVIEW2/run.ps1、tools/start_webview2.py、WEBVIEW2/README.md、README.md。

- [x] 实现默认构建及 `--configuration`、`--no-launch`，产物缺失和子程序失败返回非零码。
- [x] 编写安装依赖、启动命令、验收命令及运行时/网络问题排查。
- [x] 在根 README 的一览、结构、依赖和启动说明中登记新靶场。
- [x] 运行真实 WebView2 验收，保留结果和窗口截图；审核资源生命周期、导航事件和脚本错误传播。
- [x] 将已完成步骤标记，报告实际构建及运行结果。

```powershell
python tools/start_webview2.py --no-launch
node WEBVIEW2/verify/verify-flow.mjs
git diff --check
```

预期：启动器构建检查返回 0，三个页面和原生交互验收通过，diff 无空白错误。

## 实际验证结果（2026-09-28）

- MSVC Release 构建成功，无编译警告或错误；EXE 已生成。
- 真实 WebView2 验收共 8 个场景全部通过，结果见 `WEBVIEW2/verify/artifacts/results.json`。
- Python 构建/产物检查、Python 启动和 PowerShell 启动均成功，真实窗口默认页面为点击测试。
- 用模拟旧 CMake 抢占 PATH，确认脚本回退到 VS 自带 CMake 并成功构建。
- 所有 PowerShell 脚本语法检查、Python AST 检查及 `git diff --check` 通过。
- 已检查完整宿主窗口截图 `WEBVIEW2/verify/artifacts/window.png` 和 iframe 页面截图。
- 独立只读代码审查发现的慢启动等待及 CMake 兼容性问题已修复并复核。

本机网络沙箱会阻止 WebView2 调试连接，真实程序验收在获准的非沙箱运行环境中完成。

2026-09-29：按用户要求移除 Python `--skip-build` 和 PowerShell `-SkipBuild`，所有启动入口默认执行构建。
