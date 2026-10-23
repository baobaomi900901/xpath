# Qt 多版本靶场实施计划

**Goal:** 交付 Qt 5.15.2 / 6.8.3 的 Widgets 和 Quick 靶场及统一启动入口。

**Architecture:** QT/src 共享员工分页与拖拽模型，Widgets 和 QML 分别实现 UI。QT/versions.json 固定 SDK；tools/start_qt.py 构建部署到 QT/dist/<version>。

**Tech Stack:** C++17、Qt Widgets / Quick Controls 2、CMake、QtTest、Python 标准库。

## 步骤

- [x] 先创建 tools/test_start_qt.py 和 QT/tests/range_test.cpp，验证版本隔离、分页边界、拖拽边界、控件重置和运行时加载。
- [x] 实现 QT/src/range_model.*：EmployeeModel、DragState，两个 UI 使用同一数据和 JSON 格式。
- [x] 实现 QT/src/widgets_window.*、widgets_main.cpp：十字段、表格分页、动态菜单、真实按钮拖拽、三种表单结构。
- [x] 实现 QT/qml/Range.qml 与 quick_main.cpp：三页和菜单，Accessible 信息、可销毁/恢复的拖拽目标。
- [x] 扩展 QT/CMakeLists.txt，同时保留 acc-hidden-profile；为两个 SDK 运行 CTest。
- [x] 实现 versions.json、start_qt.py 和 PowerShell 包装，使用准确 qmake 版本校验、独立 dist、部署检查，注册启动中心。Qt 5 因旧部署器误判插件，改为复制准确 SDK 的运行依赖。
- [x] 运行 `python -m unittest tools.test_start_qt tools.test_range_launcher_core`、两版本构建及 QtTest；检查截图、部署目录和实际进程。
- [x] 更新 QT/README.md 和根 README 的 Qt 入口，记录真实验证结果。

## 验证记录（2026-10-23）

- Python 启动器和注册中心测试：31 项通过。
- Qt 5.15.2、6.8.3：真实 SDK 构建及 CTest 通过；移除 SDK PATH 后，发行目录 QtTest、Widgets / Quick 三页和原名片示例启动检查通过。
- 四种组合的截图已检查；产物及截图位于忽略的 dist、verify/artifacts 目录。
- 独立 Windows UIA 客户端：四种组合均通过关键名称、ValuePattern 输入、InvokePattern 重置；发现并修复 Qt 5 QML 按钮无障碍调用未触发业务动作的问题，已添加回归验证。
- 代码复核未发现确认的严重或重要缺陷；针对版本差异补充了 Qt 6 原生样式兼容和实际 UIA 验证。

## 约束

只在当前共享工作区执行授权修改，不提交其他正在进行的更改。SDK 下载到 QT/.tools，构建目录与发行目录忽略。不同 Qt DLL 不混用。安装失败时明确报告，不以改标题模拟版本。
