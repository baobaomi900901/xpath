# Electron 浏览器嵌入靶场

用户要求参考现有 CEF 内容和启动命令，构建 Electron 22、29、38、44 四个程序，用于元素探测器的兼容性验证。

## 范围与界面

四个版本共享页面和宿主代码，固定官方 Electron Windows x64 运行时。左侧是 Electron 宿主 DOM 菜单“点击测试 / 表单测试 / iframe表单”，右侧是独立的浏览器视图。菜单、只读地址、刷新和状态区沿用 CEF 布局；初始窗口 1280×900，最小 960×640。菜单支持鼠标与上下键，刷新保留当前页面，浏览器区域随窗口调整。

默认根地址为 `https://baobaomi900901.github.io/xpath/#/`；`--base-url` 可连接本地 WEB。三个路由分别为 `keys-click-test`、`form-controls`、`iframe-shadow-form`。显式开启 Chromium 无障碍支持以供元素探测器读取。远程页面禁用 Node 集成，启用上下文隔离和沙箱，阻止额外弹窗。

22、29 使用 BrowserView；38、44 使用 WebContentsView。Electron 宿主控件与 CEF 的 Win32 原生控件不同，此差异应在 README 中说明。精确 Electron、Chromium、Node 版本在标题、状态和清单中可见。

## 分发与启动

采用官方预编译运行时配合 `resources/app` 分发，无需额外 npm 依赖或编译 Electron 源码。相比每版本安装 npm 依赖，此方案让归档来源、SHA256 和完整版本固定、可复用；相比源码编译，它不引入无关编译工具。

产物为 `ELECTRON/dist/<主版本>/electron-shooting-range-<主版本>.exe`，必须连同整个目录使用。缓存位于 `ELECTRON/.cache/`；每次启动使用独立用户数据目录。下载必须校验固定 SHA256，解压拒绝目录逃逸，产物缺失时明确报错。

Python 标准库启动器沿用 CEF 的交互多选、`--version` / `--versions`、`--skip-build`、`--force-build`、`--no-launch`、`--base-url` 和单版本 `--remote-debugging-port`。所有选中版本先准备完成，再启动。调试端口仅绑定 loopback。

## 验收

启动器与纯配置逻辑采用先失败后实现的测试。四个实际进程通过 CDP 验证完整版本、菜单点击和键盘切换、真实输入事件、表单、iframe + Shadow DOM、刷新、窗口缩放、无障碍树、弹窗阻止和正常退出。默认线上地址另作四版本冒烟验证；截图用于检查宿主与网页渲染。已有 CEF、WebView2 与其他用户改动保留。
