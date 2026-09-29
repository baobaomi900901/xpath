# Electron 四版本浏览器嵌入靶场

参考 CEF 靶场，复用同一套 WEB 页面：左侧“点击测试 / 表单测试 / iframe表单”，右侧为独立网页视图。默认打开线上点击测试，无需启动本地 WEB。

| 主版本 | 固定 Electron | Chromium | Node | 右侧嵌入方式 |
|---|---|---|---|---|
| 22 | 22.3.27 | 108.0.5359.215 | 16.17.1 | BrowserView |
| 29 | 29.4.6 | 122.0.6261.156 | 20.9.0 | BrowserView |
| 38 | 38.8.6 | 140.0.7339.249 | 22.22.0 | WebContentsView |
| 44 | 44.4.5 | 152.0.7977.130 | 24.21.0 | WebContentsView |

精确版本与官方归档 SHA256 固定在 [versions.json](versions.json)。版本取自 [Electron 官方发布记录](https://releases.electronjs.org/)，采用官方 [预编译运行时分发方式](https://www.electronjs.org/docs/latest/tutorial/application-distribution#with-prebuilt-binaries)，无需安装 Node.js、npm、Visual Studio 或 CMake 来构建和启动。

与 CEF 的 Win32 原生菜单不同，本靶场的菜单、地址、刷新和状态是 Electron 宿主 DOM；右侧 BrowserView / WebContentsView 拥有独立 webContents，不是宿主 HTML 中的 iframe。iframe + Shadow DOM 场景仍来自现有 WEB 页面。源码通过同一接口兼容两种视图，便于比较不同内核和嵌入方式的元素探测结果。

程序显式调用 [`app.setAccessibilitySupportEnabled(true)`](https://www.electronjs.org/docs/latest/api/app#appsetaccessibilitysupportenabledenabled)，开启 Chromium 无障碍树；保留各版本 Windows 无障碍 provider 的默认行为。标题和左侧信息显示实际 Electron、Chromium、Node 和视图类型，防止把 SDK、宿主版本和浏览器内核混为一谈。

## 启动与构建

Windows 10/11 x64，启动器需 Python 3.8+，仅使用标准库。首次构建需访问 GitHub 官方 release；默认页面需访问 GitHub Pages。构建结果可直接运行，无需 Python；分发必须保留整个 `dist/<主版本>/` 目录。

在仓库根目录执行：

```powershell
python .\tools\start_electron.py                        # 交互多选，构建后启动
python .\tools\start_electron.py --skip-build           # 多选已有产物
python .\tools\start_electron.py --version 22           # 构建并启动一个版本
python .\tools\start_electron.py --versions 22 29 38 44  # 构建并启动四个版本
python .\tools\start_electron.py --versions 22 29 38 44 --skip-build
python .\tools\start_electron.py --versions 22 29 38 44 --no-launch
python .\tools\start_electron.py --version 44 --force-build
python .\tools\start_electron.py --help
```

交互操作与 CEF 相同：上下键移动，空格 / Enter 勾选，在“已完成选择”上按 Enter 启动，Esc 取消。非交互终端必须指定版本。`--version` / `--versions` 互斥，`--skip-build` / `--force-build` 互斥；`--no-launch --skip-build` 只验证现有运行目录。批量模式先准备所有选中版本，再启动窗口。

首次下载后校验 SHA256 并安全解压，再将共享 `src/` 复制到 `resources/app/`；后续构建复用已校验归档、更新应用源码。`--force-build` 从已校验缓存重新打包。每个运行目录的 `version.json` 和应用 `runtime.json` 固定版本；主进程还会核对实际运行时。

直接运行已有 EXE：

```powershell
.\ELECTRON\dist\22\electron-shooting-range-22.exe
.\ELECTRON\dist\29\electron-shooting-range-29.exe
.\ELECTRON\dist\38\electron-shooting-range-38.exe
.\ELECTRON\dist\44\electron-shooting-range-44.exe
```

## 页面与控件

| 菜单 | 默认线上地址 |
|---|---|
| 点击测试 | `https://baobaomi900901.github.io/xpath/#/keys-click-test` |
| 表单测试 | `https://baobaomi900901.github.io/xpath/#/form-controls` |
| iframe表单 | `https://baobaomi900901.github.io/xpath/#/iframe-shadow-form` |

| 宿主 DOM ID | CEF 对照编号 `data-control-id` | 功能 |
|---|---|---|
| `menu`、`menu-0` / `menu-1` / `menu-2` | 1001 | 三项页面菜单，支持点击及上下键 / Home / End |
| `address` | 1002 | 可选择复制的只读地址 |
| `refresh` | 1003 | 忽略缓存刷新当前页面 |
| `status` | 1004 | 加载、就绪、失败状态 |

这些编号是 DOM 属性，不是 Win32 HWND 控件 ID。窗口默认 1280×900，最小 960×640；内容区域按 DIP 布局，与 CEF 的左侧 220、顶部 52、右侧 12、底部 34 间距一致。

远程页面关闭 Node 集成、开启上下文隔离与沙箱；只在本地宿主暴露限定 IPC。额外弹窗被阻止，加载失败会在状态栏显示，刷新或切换菜单可重试。

## 本地开发与调试

先保持 WEB 服务运行：

```powershell
cd .\WEB
pnpm install
pnpm dev
```

然后从仓库根目录启动：

```powershell
python .\tools\start_electron.py --versions 22 29 38 44 --skip-build --base-url http://localhost:7199/
python .\tools\start_electron.py --version 44 --skip-build --remote-debugging-port 9222
```

`--base-url` 使用以 `/` 或 `#/` 结尾的 HTTP(S) 根地址，不含查询参数或账号。调试端口仅允许单版本，范围 1024–65535，仅绑定 `127.0.0.1`。CDP 有两个 page target：本地 `shell.html` 和右侧远程页面；iframe 按 Chromium 的 frame / DOM 树继续向内探测。

每次启动创建独立 `ELECTRON/.cache/profiles/<主版本>/<PID>-<随机标识>/`，多版本、多实例之间不共享 Cookie 和缓存。独立复制运行目录时，缓存改存 EXE 所在目录的 `.cache/`。下载和运行目录均已 gitignore；手动清理旧 profile 前应关闭对应程序。

## 验收

启动器测试与配置测试：

```powershell
python -m unittest discover -s tools -p test_start_electron.py
node .\ELECTRON\tests\config.test.cjs
```

实际程序验收需 Node.js 22+、Windows PowerShell，以及已经构建的四个运行目录。保持本地 WEB 服务运行后：

```powershell
node .\ELECTRON\verify\verify-flow.mjs
node .\ELECTRON\verify\verify-flow.mjs 22 44
$env:XPATH_ELECTRON_DEFAULT = '1'
node .\ELECTRON\verify\verify-flow.mjs
Remove-Item Env:XPATH_ELECTRON_DEFAULT
```

本地模式验证实际完整版本、菜单鼠标 / 键盘、可信点击、表单输入、iframe + Shadow DOM、窗口缩放、刷新、CDP 无障碍树、Windows UIA / MSAA 节点、弹窗阻止、错误状态和恢复、正常退出；线上模式验证默认地址与相同交互（不执行网络失败注入和原生无障碍采样）。

原生采样先读取 UIA；若 UIA 没有暴露网页内部元素，再直接读取旧版本的 MSAA 树，断言宿主菜单和网页独有“单击触发”按钮均存在。结果记录本机实际使用的原生接口，保留版本默认行为，不强制把旧内核切换为新 provider。截图、结果和无障碍采样保存在 `verify/artifacts/`，忽略不提交。

2026-09-29 本机四版本验收完成：33 项启动器测试、5 项配置测试、本地 48 项和默认线上 40 项实际程序检查通过。本机原生采样中，22 / 29 / 38 的宿主菜单和网页按钮通过 MSAA 读取，44 通过 UIA 读取；这是本次系统环境的观测结果。验收脚本按版本顺序启动、检查并关闭各个窗口。
