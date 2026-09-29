# CEF 多版本浏览器嵌入靶场

## 用户需求

创建 CEF 109 / 125 / 128 / 133 / 154 五个 Windows 靶场，通过统一命令的版本参数启动。左侧菜单为“点击测试”“表单测试”“iframe表单”，右侧嵌入对应网页。默认地址为 `https://baobaomi900901.github.io/xpath/#/` 下的 `keys-click-test`、`form-controls`、`iframe-shadow-form`，页面源码来自现有 WEB 目录。

## 实现选择

使用 C++17 / Win32 / CEF C++ API，共享一套宿主源码，针对每个官方 Windows x64 SDK 独立编译和打包。相较于 CefSharp 或 JCEF，不引入 .NET / JVM 和绑定版本限制；相较于五份宿主代码，公共源码保证菜单和页面行为一致。

CEF 109 保留 Alloy bootstrap；125 起使用 Chrome bootstrap 和 Alloy style，128 起兼容已移除旧 bootstrap 的 API。所有版本使用有窗口的原生父窗口嵌入，显式启用无障碍。版本差异由编译时条件处理，不在一个进程中装载多个 libcef。

## 文件边界

- `CEF/versions.json`：固定五个官方稳定 SDK 的完整版本、归档名、大小和 SHA-1；来自官方构建索引。
- `CEF/src/`：原生宿主与 CEF 生命周期，左侧原生 ListBox，右侧 CEF child HWND；地址栏只读、刷新按钮、加载状态、版本标题、DPI 和尺寸变化处理。
- `CEF/CMakeLists.txt`：针对指定 SDK 构建 `cef-shooting-range-<major>.exe`，复制 Release 与 Resources。
- `tools/start_cef.py`：参数解析、校验和下载、安全解压、增量构建、启动与错误报告。仅 Python 标准库。
- `CEF/verify/`：真实五版本进程、原生菜单、页面/CDP 与 iframe Shadow DOM 验收。

## 命令契约

`python tools/start_cef.py --version 109` 启动单版本；`--versions 109 125 128 133 154` 启动多版本。两种参数互斥，无版本参数时进入与 Java 启动器一致的交互式多选菜单：上下移动，Enter/空格勾选，在“已完成选择”上按 Enter 确认，Esc 取消；初始无勾选，空选择不可确认。非交互环境必须明确指定版本。首次自动准备 SDK 和构建；后续复用产物。`--skip-build` 只运行已有产物；`--no-launch` 只准备/验证构建。交互选择多个版本时，也须在准备 SDK 前拒绝共享调试端口。

`--base-url http://localhost:7199/` 切换为本地 WEB 页面，无须复制或修改页面。`--remote-debugging-port` 用于显式开启 CDP 验收，只允许单版本。每次进程使用独立缓存目录，避免多版本或重复启动锁冲突。多版本启动先准备完全部程序再启动。

## 错误与验证

不支持的版本、冲突参数、无效 URL 和端口在下载/启动前报错；重复版本值合并，按版本顺序启动。下载校验大小和 SHA-1，校验失败不解压；解压拒绝越界和链接。构建失败给出完整命令错误；缺少 SDK、运行库或编译环境时明确失败，不替换成其他内核版本。

先写启动器行为测试和真实程序验收，再实现。五个版本都编译并实际启动；验证版本号、三项菜单与路由切换、表单输入、iframe 内 Shadow 表单、窗口缩放、正常关闭。源码和说明提交范围仅新增 CEF、CEF 启动器及根 README 的相关条目，保留现有 WEBVIEW2 工作。
