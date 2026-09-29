# Electron 四版本靶场实施计划

**目标：** 构建并验收 Electron 22、29、38、44，复用 CEF 的页面入口、布局与启动命令约定。

**架构：** 官方 Windows x64 Electron 运行时 + 共享 `resources/app` 宿主源码；Python 标准库下载、校验、打包和启动；Node 内置 CDP 验收。旧版本 BrowserView，新版本 WebContentsView。

**技术：** Python 3.8+、CommonJS Electron 主进程/隔离 preload、HTML/CSS/JS 宿主、Node.js 22 验收、Windows PowerShell。

## 全局约束

- 主版本必须为 22、29、38、44，固定各版本官方稳定补丁号及 SHA256。
- 复用 CEF 的三个菜单、线上默认地址和本地 `--base-url`；初始 1280×900、最小 960×640。
- 22、29 使用 BrowserView；38、44 使用 WebContentsView。
- 所有选中版本先准备完成，再启动；每次启动独立缓存。
- 不修改已有 CEF、WEBVIEW2 的实现，不撤销用户已有改动。
- 运行时、下载、构建和验收产物均忽略，不提交大型二进制。

## Task 1：启动器与版本清单

- [x] 先编写 `tools/test_start_electron.py`，执行并确认因缺少实现而失败。
- [x] 建立 `ELECTRON/versions.json`，从官方 release 元数据核实四个精确版本和 SHA256。
- [x] 实现 `tools/start_electron.py`：CEF 多选界面、参数校验、安全下载/解压、完整产物校验、共享源码复制、批量启动。
- [x] 测试有效/无效参数、URL、归档校验、路径逃逸、缺失产物和全量准备再启动。

## Task 2：共享宿主

- [x] 先编写 `ELECTRON/tests/config.test.cjs` 并确认失败，再实现 URL、参数和边界计算。
- [x] 实现 `src/main.cjs`、`preload.cjs`、`shell.html/css/js`、`package.json`。
- [x] 校验 IPC 来源；宿主状态事件同步菜单、地址、加载/错误提示；关闭时释放网页视图。
- [x] 添加忽略规则与模块 README。

## Task 3：实际构建与验收

- [x] 编写 `verify/verify-flow.mjs` 和窗口控制助手，先确认未构建产物失败。
- [x] 执行四版本 `--no-launch` 构建；运行启动器与配置测试。
- [x] 对四个实际程序执行本地完整交互验收；默认线上页面四版本冒烟验证。
- [x] 检查截图与 Windows 无障碍节点，记录实际结果。

## Task 4：集成与评审

- [x] 更新根 README 的目录、依赖和启动命令。
- [x] 采用 subagent-driven-development 独立实现启动器；按 requesting-code-review 进行独立代码评审并处理重要问题。
- [x] 再运行受影响检查，报告精确版本、启动命令与验收结果。
