# 禁止启动 CDP 与打包实施计划

**Goal:** 三类靶场忽略调试启动参数，正常打开窗口，交付重新构建的完整运行包。

**Architecture:** 每个宿主在 Chromium 初始化前控制调试入口；Python 启动器不转发调试配置。独立任务修改各自文件，统一的实际进程验收检查所有产物。

**Tech Stack:** Windows x64、C++17、CEF、Electron CJS、WebView2、Python 标准库。

## Global Constraints

- CEF 109、125、128、133、154；Electron 22、29、38、44；WebView2 Release。
- 添加 CDP 参数不阻止正常启动，不创建 CDP 端口或 pipe。
- 不引入调试后门，不修改系统环境变量或注册表配置。
- 保留现有 WEB 工作区改动；不提交或推送代码。

## Task 1: CEF

- [x] 修改 tools/test_start_cef.py：调试参数被忽略，启动命令不含调试选项；运行以确认旧实现失败。
- [x] 修改 CEF/src/main.cpp：设置 command_line_args_disabled=true，删除调试端口解析与赋值。
- [x] 修改 tools/start_cef.py：旧参数隐藏并忽略，移除转发及单版本限制。
- [x] 运行 python -m unittest tools.test_start_cef tools.test_cef_processes。
- [x] 更新 CEF/README.md；构建全部五个版本。

## Task 2: Electron

- [x] 更新 ELECTRON/tests/config.test.cjs、tools/test_start_electron.py：调试参数不进入配置或启动命令；确认旧实现失败。
- [x] 主进程 require electron 后同步 removeSwitch 三种 remote-debugging 开关，配置仅保留 baseUrl。
- [x] 启动器隐藏并忽略旧参数，移除转发及单版本限制。
- [x] 运行配置与启动器测试；更新 ELECTRON/README.md；打包全部四个版本。

## Task 3: WebView2 与实际程序验收

- [x] 添加 tools/verify_no_cdp.py，使用独立进程、临时 profile、可用端口验证窗口和监听；在旧产物上确认检测到开放的 CDP。
- [x] WebView2 在环境创建前固定浏览器附加参数，移除调试器环境注入，屏蔽嵌套命令行入口。
- [x] 更新启动器兼容行为、WEBVIEW2/README.md、三套 verify-flow.mjs 入口和根 README。
- [x] 构建 WebView2；对全部十个产物执行无 CDP 验收。

## Task 4: 交付

- [x] 检查最终差异并修复审查发现。
- [x] 将 CEF/Electron 的完整 dist 版本目录及 WebView2 Release EXE 分别打 ZIP。
- [x] 写入 SHA256 清单与验收结果，检查归档必需文件齐全。
- [x] 报告产物路径、测试证据和覆盖范围。

## 验收结果

102 项 Python 回归测试、6 项 Electron 配置测试通过；62 项实际窗口与无 CDP 验收通过。9 项补充 CRT pipe 验收通过，4 个未修改的 Electron 运行时阳性对照均响应。CEF 的补充管道结果不含匹配的阳性对照。

10 个完整 ZIP 已生成并通过 CRC 检查，SHA256 与验收记录位于 `artifacts/no-cdp-2026-10-23/`。本次不包含页面内部交互与 UIA 深度回归。
