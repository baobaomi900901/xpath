# xpath

面向 **UI 自动化 / RPA / 无障碍(UI tree)测试** 的靶场集合。每个靶场都是一个可独立运行的程序或页面,
分别覆盖不同的宿主环境与技术栈(浏览器、CEF / WebView2 / Electron 嵌入、原生 Win32、Tk、Qt、Java Swing、Delphi VCL、Excel 加载项),
用于检验自动化在元素定位、坐标与几何、拖拽、菜单、对话框、iframe / Shadow DOM、UIA 压力等场景下的表现。

---

## 靶场一览

可通过统一桌面界面勾选多个靶场、设置版本和启动方式，再点击启动：

```powershell
uv run .\tools\start.py
```

默认在独立进程中打开界面，约 1 秒后归还终端，关闭终端后界面继续运行。需要在终端查看调试输出时，使用 `uv run .\tools\start.py --foreground`。

启动中心使用 Python 标准库 Tk，支持搜索、分类、运行日志和配置维护。点击“维护靶场与选项”可补充靶场和参数，也可直接编辑 [tools/ranges.json](tools/ranges.json)；操作与扩展说明见 [启动中心指南](tools/RANGE_LAUNCHER.md)。

| 目录                            | 形态                                             | 技术栈                                             | 一键启动                            |
| ------------------------------- | ------------------------------------------------ | -------------------------------------------------- | ----------------------------------- |
| [`WEB/`](WEB)                   | 浏览器页面,21 个测试入口                          | React 19 + antd 5 + Vite 6                         | `cd WEB; pnpm dev`                  |
| [`WIN32/`](WIN32)               | 原生桌面程序 5 个 + UIA 压力程序 + 检测工具      | C++ / Win32 / CMake                                | `python tools\start_win32.py`       |
| [`TK/`](TK)                     | Tk 桌面程序，表单 / 表格 / 拖拽 / 菜单           | Python / tkinter / ttk                             | `python tools\start_tk.py`          |
| [`WEBVIEW2/`](WEBVIEW2)         | 浏览器套壳桌面程序,原生菜单 + 3 个线上测试页面   | C++ / Win32 / WebView2 SDK 1.0.4191.47 / CMake     | `python tools\start_webview2.py`    |
| [`CEF/`](CEF)                   | 109 / 125 / 128 / 133 / 154 五版本浏览器嵌入靶场 | C++ / Win32 / CEF / CMake                          | `python tools\start_cef.py`         |
| [`ELECTRON/`](ELECTRON)         | 22 / 29 / 38 / 44 四版本浏览器嵌入靶场           | Electron / BrowserView / WebContentsView           | `python tools\start_electron.py`    |
| [`OFFICE/`](OFFICE/excel-addin) | Excel 加载项(Ribbon + WebView2 任务窗格)         | Office.js + 静态 HTML/CSS/JS + Python 标准库 HTTPS | `python tools\start_excel_addin.py` |
| [`JAVA/`](JAVA)                 | Swing 桌面程序,多 JDK 版本并行                   | Java 8/11/17/21/25 + Maven                         | `python tools\start_java.py`        |
| [`QT/`](QT)                     | Qt 5.15 / 6.8 双版本 Widgets + QML 靶场           | C++ / Qt / CMake / MinGW x64                      | `python tools\start_qt.py`          |
| [`DELPHI/`](DELPHI)             | VCL 桌面程序，表单 / 菜单 / 表格 / 拖拽          | Delphi 2010 (VCL / Win32)                          | `python tools\start_delphi.py`      |
| [`POWERBUILDER/`](POWERBUILDER) | PB 原生表单 / DataWindow / 菜单 / 拖拽          | PowerBuilder 2025 GA Utilities + Runtime            | `python tools\start_powerbuilder.py` |

跨靶场的启动器都在 [`tools/`](tools) 下;`WIN32` / `WEBVIEW2` / `JAVA` / `QT` / `DELPHI` 另外各自带 `build.ps1` / `run.ps1`。

## 目录结构

```
xpath/
├─ WEB/                    浏览器靶场(Vite + React)
│  ├─ src/pages/           各测试页面
│  ├─ public/              iframe、下载样例等静态资源
│  ├─ scripts/
│  └─ vite.config.ts       普通靶场模式 + SDK Cookie 靶场模式
├─ WIN32/                  原生 Win32 靶场
│  ├─ src/                 各版本源码
│  ├─ build/               CMake 构建产物(Release/*.exe)
│  ├─ dist/
│  ├─ build.ps1 / run.ps1
│  └─ CMakeLists.txt
├─ TK/                     Tk 框架桌面靶场（Python 标准库）
│  ├─ app.py / *_page.py   主窗口、表单、表格、拖拽、图元与文本菜单页
│  ├─ models.py            员工数据与拖拽状态
│  └─ tests/               模型与真实 Tk 控件测试
├─ OFFICE/excel-addin/     Excel 加载项靶场
│  ├─ manifest.xml         Ribbon 选项卡 / 组 / 按钮 + 任务窗格入口
│  ├─ src/                 任务窗格页面与登录交互
│  ├─ assets/              图标及其生成脚本
│  ├─ verify/              零依赖 CDP 端到端验收脚本与截图
│  └─ dist/                生成的靶场工作簿(已 gitignore)
├─ JAVA/                   Java Swing 靶场
│  ├─ src/main/java/…
│  ├─ .tools/              本地 JDK 与 Maven(已 gitignore)
│  ├─ tests/
│  └─ pom.xml
├─ QT/                     Qt 5.15 / 6.8 Widgets + QML 靶场
│  ├─ src/ qml/ resources/
│  ├─ build/               构建产物
│  └─ run.ps1 / build.ps1
├─ DELPHI/                 Delphi VCL 靶场工程、build.ps1 / run.ps1
├─ POWERBUILDER/           PowerBuilder 原生控件和 DataWindow 靶场
│  ├─ src/                 PowerScript 导出对象（UTF-8）
│  ├─ build/Release/       EXE、PBD、Runtime XML 和验证日志（已忽略）
│  └─ dist/                含运行时的单文件 EXE（已忽略）
├─ WEBVIEW2/               WebView2 浏览器套壳靶场
│  ├─ src/                 原生菜单与 WebView2 宿主
│  ├─ verify/              实际程序的禁用 CDP 验收
│  └─ build.ps1 / run.ps1
├─ CEF/                    CEF 五版本浏览器嵌入靶场
│  ├─ src/                 共享的原生菜单与 CEF 宿主
│  ├─ versions.json        固定官方 SDK 版本与校验信息
│  ├─ verify/              禁用 CDP 实际进程验收
│  └─ CMakeLists.txt       独立编译到 dist/<版本>/
├─ ELECTRON/               Electron 四版本浏览器嵌入靶场
│  ├─ src/                 共享宿主 DOM 菜单与独立网页视图
│  ├─ versions.json        固定官方运行时版本与 SHA256
│  ├─ verify/              禁用 CDP 实际进程验收
│  └─ dist/<版本>/         四个完整运行目录(已 gitignore)
├─ tools/                  跨靶场启动器(Python)
│  ├─ start.py             可视化启动中心（Tk / 标准库）
│  ├─ ranges.json          可维护的靶场、启动方式及参数
│  ├─ range_launcher/     界面、配置校验及进程日志模块
│  ├─ start_win32.py
│  ├─ start_tk.py / test_start_tk.py
│  ├─ start_java.py / start_delphi.py
│  ├─ start_powerbuilder.py / test_start_powerbuilder.py
│  ├─ start_webview2.py
│  ├─ start_cef.py / test_start_cef.py
│  ├─ start_electron.py / test_start_electron.py
│  ├─ start_excel_addin.py / stop_excel_addin.py
│  └─ test_start_java.py
├─ .github/workflows/      GitHub Pages 部署
└─ .private/               本地实验目录,已 gitignore
```

## 环境准备

| 靶场       | 依赖                                                                                                                                                                   |
| ---------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 通用启动器 | Python 3.8+(仅标准库,无需 pip 安装)                                                                                                                                    |
| WEB        | Node.js 22+、pnpm 10.25                                                                                                                                                |
| WIN32      | Visual Studio 2019+(含"使用 C++ 的桌面开发"工作负载)、CMake 3.20+                                                                                                      |
| TK         | Python 3.8+，含 Tcl/Tk（Windows 安装组件 `tcl/tk and IDLE`）；无需编译或 pip 安装                                                                                      |
| WEBVIEW2   | Windows 10/11 x64 + WebView2 Runtime;启动器默认构建,需 Python 3.8+、PowerShell、Visual Studio 2019/2022/2026 C++ + Windows SDK、匹配 VS 的 CMake;SDK 自动下载,详见下文 |
| CEF        | Windows 10/11 x64、Python 3.8+;默认构建需 Visual Studio 2022/2026 C++ + Windows SDK、匹配 VS 的 CMake,CEF SDK 自动下载;`--skip-build` 需对应版本完整运行目录           |
| ELECTRON   | Windows 10/11 x64、Python 3.8+(仅标准库);官方运行时自动下载并校验 SHA256,无需 Node.js / npm / C++ 编译工具;禁用 CDP 验收使用 Python                                        |
| OFFICE     | Windows + Excel 桌面版(2016+ / Microsoft 365);**不需要**管理员权限、OpenSSL、PowerShell 7                                                                              |
| JAVA       | Amazon Corretto JDK 8/11/17/21/25,放在 `JAVA/.tools/jdks/corretto/<版本>`;Maven 由启动器自动下载                                                                       |
| QT         | Qt 5.15.2 / MinGW 8.1、Qt 6.8.3 / MinGW 13.1、CMake、Ninja；已有发行目录可直接运行                                                                                                                                |
| DELPHI     | Delphi 2010(仅编译需要)                                                                                                                                                |
| POWERBUILDER | Windows 10/11 + PowerBuilder Utilities / Runtime 2025 GA 25.0.0.3683；编译工具无需 IDE 许可证                                                                              |

## 各靶场启动方式

### WEB — 浏览器靶场

```powershell
cd WEB
pnpm install
pnpm dev              # http://localhost:7199, 自动打开浏览器
```

- 构建 / 预览:`pnpm build`(输出到 `WEB/dist`)、`pnpm preview`
- 主要路由:`/`、`/login-test`、`/registration-test`、`/form-controls`、`/table-test`、`/table-div-test`、`/anchor-test`、
  `/geometry-test`、`/element-html-test`、`/iframe-shadow-form`、`/iframe-nested-test`、
  `/shadow-nested-test`、`/download-dialog-test`、`/upload-dialog-test`、`/web-dialog-test`、
  `/keys-click-test`、`/drag-to-test`、`/cookie-test`、`/canvas-test`——完整清单见 `WEB/src/App.tsx`
- **SDK Cookie 观测模式**:设置 `UIPILOT_SDK_WEB_*` 系列环境变量后,`pnpm dev` 会切换为 HTTPS +
  固定端口 + `/api/sdk-web/*` 接口 + 下载响应头;该模式只能在本地跑,线上 Pages 不支持

登录测试（`/login-test`）支持切换“账号登录”和“手机验证码登录”：账号 `admin` / 密码 `1`，手机号 `13922832244` / 验证码 `1990`，均严格匹配。账号登录须账号和密码都有值才启用登录按钮，清空任意一项就重新禁用。手机登录须先点击验证码输入框右侧的“发送验证码”，手机号校验通过后才启用验证码输入框和登录按钮；修改手机号会清空验证码并重新禁用。校验失败时，模态弹窗分别提示“账号错误”“密码错误”“手机号错误”或“验证码错误”，先校验账号或手机号。登录成功后可退出重试，切换方式和退出均清空输入并恢复初始状态。该页面为本地模拟，不发送短信或保存登录状态。

登录成功后进入“网银转账”，包含转账账号、金额、客户名称、收款银行、分行支行名称、联行号、转账用途，底部依次为“重置”“转账”按钮。每次登录或点击“重置”都会更换控件及容器的随机 `id` / `class` / `name`、字段的真实 DOM 顺序和 1–5 层包裹；每次重建保证顺序及深度变化，中文标签及可访问关联保持有效。重置保留输入，正常输入不触发随机化，页面不显示轮次，适合验证旧定位失效后的元素特征修复。转账时先校验，随后弹窗核对信息，提交后显示模拟回执，可继续转账或退出；不会发送支付请求。

浏览器验收：先启动 WEB 服务，再在 `WEB` 目录运行 `node tests/login-test.mjs`（需可用的 `playwright` 模块和 Chrome；可用 `LOGIN_PLAYWRIGHT_MODULE` 指定已有模块路径）。`LOGIN_TEST_BASE_URL` 默认 `http://127.0.0.1:7199/`，验证 Pages 预览时设为其 `/xpath/#/` 根地址。

转账及随机结构验收：同一环境下运行 `node tests/bank-transfer-test.mjs`，覆盖四轮连续重建、数据保留、金额/账号校验、确认及回执、两种登录入口和窄屏布局；可用 `LOGIN_TEST_SCREENSHOT_DIR` 指定截图目录。

业务流水号使用“规范金额 + 96 位随机因子 + 共享密钥”的 HMAC-SHA256 签名，签名取前 96 位，以 Base64URL 编码为 `TR_<16字符随机因子>_<16字符签名>`，总长 36 字符，不再循环使用固定的 10 条数据。配置文件 [fixtures/bank-transfer-auth.json](fixtures/bank-transfer-auth.json) 提供两端相同的密钥。二次确认弹窗和成功回执使用同一编号，取消后重新发起生成新编号；登记按填写金额重新验签，拒绝乱填、篡改或金额不匹配的编号。旧长编号需重新生成，协议和 CS 实现约定见 [fixtures/README.md](fixtures/README.md)。这是密钥随前端分发的靶场模拟方案，不提供严格全局去重或真实安全鉴权。

“登记”（`/registration-test`）使用真实 iframe（`#registration-frame`，内部路由 `/registration-form-content`）承载业务流水号及上述七项转账信息。表单、登记/重置按钮和结果弹窗都在 iframe 内。使用相同密钥验证流水号签名与填写金额是否匹配，同时校验必填项、账号和金额，联行号和用途可空。成功弹窗显示登记摘要，失败保留输入；无需额外服务或写入请求，可用于本地与静态 Pages。浏览器验收：在 `WEB` 目录运行 `node tests/registration-test.mjs`；算法验收运行 `node tests/transfer-reference-test.mjs`，浏览器环境变量沿用上述说明。

### WIN32 — 原生 Win32 靶场

```powershell
python .\tools\start_win32.py                                  # 交互式多选菜单
python .\tools\start_win32.py --backends uia uia-no-pane uia-random msaa canvas # 指定版本直接启动
python .\tools\start_win32.py --backends uia --skip-build      # 跳过构建,用现有 EXE
python .\tools\start_win32.py --backends uia --no-launch       # 只构建验证,不起窗口
python .\tools\start_win32.py --configuration Debug
```

可用版本:`uia`、`uia-no-pane`、`uia-random`、`msaa`、`canvas`、`pressure500`、`pressure1000`、`pressure2000`。

所有版本也可打包成独立的 Windows x64 EXE，无需 Python 或额外的 VC++ 运行库：

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\WIN32\package.ps1
```

独立 EXE 和合集 ZIP 位于 `WIN32/dist/`，完整文件清单见 [WIN32/README.md](WIN32/README.md)。

也可以直接用 PowerShell:

```powershell
cd WIN32
.\build.ps1
.\run.ps1 -Backend uia -SkipBuild
```

产物在 `WIN32/build/Release/`:

- `win32-shooting-range-uia.exe` — 标准 Win32 控件,完整 UIA 树
- `win32-shooting-range-uia-no-pane.exe` — 标准 Win32 控件,表单字段无独立 Pane
- `win32-shooting-range-uia-random.exe` — 标准 Win32 控件,每次启动随机排列字段、控件 ID 和 Pane 类名
- `win32-shooting-range-msaa.exe` — 单个自绘 HWND,只暴露 MSAA `IAccessible` 树
- `win32-shooting-range-canvas.exe` — 同样自绘但不暴露任何内部无障碍节点
- `win32-uia-pressure.exe` — UIA 深度压力靶场,启动参数为嵌套层数(500 / 1000 / 2000)
- `uia-no-msaa-probe.exe` — 关闭 MSAA Proxy 的 UIA 只读检测工具

各版本差异、Tab 功能与拖拽字段说明见 [WIN32/README.md](WIN32/README.md)。

### TK — Tk 框架靶场

参考 Win32 标准版，使用 tkinter/ttk 实现十字段表单、1000 条员工数据分页、120×80 目标拖拽、顶部菜单和动态弹出菜单。

```powershell
python .\tools\start_tk.py                # 检查环境并启动
python .\tools\start_tk.py --no-launch    # 用隐藏窗口检查环境及全部页面
python .\tools\start_tk.py --foreground   # 前台运行，便于查看错误
```

仅需带 Tcl/Tk 的 Python 3.8+，无需构建。启动器复用当前解释器；也可在仓库根目录执行 `python -m TK`。
控件使用 Tk/ttk 自身的实现，可访问性以本机 Python/Tk 的实际表现为准。
功能、Tk 控件路径及验证命令见 [TK/README.md](TK/README.md)。

### WEBVIEW2 — 浏览器套壳靶场

左侧为原生菜单“点击测试 / 表单测试 / iframe表单”,右侧在 WebView2 中直接加载对应的线上 GitHub Pages 页面。
默认打开点击测试,支持刷新、键盘切换、窗口缩放及 iframe / Shadow DOM 表单。

#### WebView2 版本

| 项目           | 版本与来源                                                                                                                                |
| -------------- | ----------------------------------------------------------------------------------------------------------------------------------------- |
| 编译 SDK       | `Microsoft.Web.WebView2 1.0.4191.47`,固定在 [WEBVIEW2/sdk-version.txt](WEBVIEW2/sdk-version.txt);构建脚本下载官方 NuGet 包并校验 SHA256。 |
| 浏览器 Runtime | 使用本机安装的 Evergreen WebView2 Runtime,宿主没有固定浏览器内核版本。2026-09-29 本机读取到的 Runtime 为 `151.0.4129.93`。                |

SDK 版本与 Runtime 版本分别表示编译接口和实际浏览器运行时。Evergreen Runtime 会自动更新,其他机器或后续运行的版本可能不同;具体机制见 [微软运行时分发说明](https://learn.microsoft.com/en-us/microsoft-edge/webview2/concepts/distribution#the-evergreen-runtime-distribution-mode)。
CEF 则按下文的五套固定 SDK 分别编译,运行时随各自的产物目录一起分发。

#### 启动与构建依赖

| 使用方式           | 依赖                                                                                                                                                                                                    |
| ------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 使用 Python 启动器 | Windows 10/11 x64、Python 3.8+、PowerShell、已安装的 [WebView2 Runtime](https://developer.microsoft.com/microsoft-edge/webview2/),以及下列编译工具。Python 仅使用标准库,无需 `pip install`。            |
| 编译工具           | Visual Studio 2019 / 2022 / 2026 的“使用 C++ 的桌面开发”工作负载、MSVC x64 编译工具、Windows SDK。CMake 按 VS 版本分别要求 3.20+ / 3.21+ / 4.2+;脚本检查 PATH CMake 的兼容性,不满足时尝试 VS 自带版本。 |
| 直接运行已有 EXE   | Windows 10/11 x64、WebView2 Runtime,以及对应 MSVC 的 Visual C++ x64 运行库;无需 Python、Visual Studio 或 CMake。                                                                                        |
| 网络               | 加载默认页面需访问 GitHub Pages;首次构建下载 SDK 还需访问 `api.nuget.org`。                                                                                                                             |
| 自动化验收         | 运行 `python .\tools\verify_no_cdp.py --kind webview2`;日常启动无需 Node.js 或 pnpm。                                                                                                           |

运行前需确保已安装 WebView2 Runtime;缺失时从上面的官方入口下载 Evergreen 安装程序,本程序不会自动安装。
默认加载线上页面,无需启动本地 WEB 开发服务。

#### 启动命令

在仓库根目录执行。**启动器每次默认先构建再启动,不提供 `--skip-build` 参数**;源码未变化时执行增量构建。

```powershell
cd D:\code\xpath
python .\tools\start_webview2.py                     # 构建并启动
python .\tools\start_webview2.py --no-launch         # 只构建并检查产物,不打开窗口
python .\tools\start_webview2.py --configuration Debug  # Debug 构建并启动
python .\tools\start_webview2.py --help              # 查看全部参数
```

也可直接使用 PowerShell,此方式无需 Python:

```powershell
.\WEBVIEW2\run.ps1                              # Release 构建并启动
.\WEBVIEW2\build.ps1                            # 仅构建
.\WEBVIEW2\run.ps1 -Configuration Debug         # Debug 构建并启动
```

如果本机执行策略禁止脚本,可单次使用:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\WEBVIEW2\run.ps1
```

已完成构建且只想直接打开现有程序时:

```powershell
.\WEBVIEW2\build\Release\webview2-shooting-range.exe
```

Release 产物为 `WEBVIEW2/build/Release/webview2-shooting-range.exe`,Debug 产物位于 `WEBVIEW2/build/Debug/`。
SDK 缓存位于 `WEBVIEW2/.tools/`,浏览器用户数据默认位于 `%LOCALAPPDATA%\XPath\WebView2Range`,跨次启动保留网站数据。
自动化控件 ID、验收和故障排查见 [WEBVIEW2/README.md](WEBVIEW2/README.md)。

### CEF — 五版本浏览器嵌入靶场

左侧是原生菜单“点击测试 / 表单测试 / iframe表单”,右侧在对应版本的 CEF 中嵌入现有 WEB 页面。
默认打开点击测试,支持刷新、键盘切换、窗口缩放和 iframe / Shadow DOM 表单。默认页面如下:

| 菜单       | 页面                                                                              |
| ---------- | --------------------------------------------------------------------------------- |
| 点击测试   | [keys-click-test](https://baobaomi900901.github.io/xpath/#/keys-click-test)       |
| 表单测试   | [form-controls](https://baobaomi900901.github.io/xpath/#/form-controls)           |
| iframe表单 | [iframe-shadow-form](https://baobaomi900901.github.io/xpath/#/iframe-shadow-form) |

#### 为什么选择这五个版本

按本项目指定的 **109 / 125 / 128 / 133 / 154** 建立固定兼容性测试矩阵,覆盖传统嵌入方式、启动架构迁移、API 版本化和较新内核。
五个程序复用同一套宿主源码和 WEB 页面,便于对比不同内核下的元素定位、点击、表单、iframe / Shadow DOM 和无障碍表现。

| 主版本 | 固定 CEF 版本       | Chromium         | 作为测试节点的原因                                                                                                                                                                                                           |
| ------ | ------------------- | ---------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 109    | `109.1.18+gf1c41e4` | `109.0.5414.120` | 传统 Alloy 启动方式的旧版本基线;官方 109 分支支持 Win7+ 部署,110 起转为 Win10+,适合覆盖旧内核兼容场景。[官方分支说明](https://chromiumembedded.github.io/cef/branches_and_building.html#legacy-release-branches-unsupported) |
| 125    | `125.0.22+gc410c95` | `125.0.6422.142` | Alloy 开始拆分为 bootstrap(启动组件)与 style(浏览器样式),可以用 Chrome bootstrap 创建 Alloy style 嵌入窗口,是启动架构迁移的起点。[官方架构说明](https://chromiumembedded.github.io/cef/architecture.html#cef3)               |
| 128    | `128.4.12+g1d7a1f9` | `128.0.6613.138` | 移除 Alloy bootstrap,嵌入窗口使用 Chrome bootstrap + Alloy style,覆盖升级后的启动、窗口和交互兼容性。[官方架构说明](https://chromiumembedded.github.io/cef/architecture.html#cef3)                                           |
| 133    | `133.4.8+g99a2ab1`  | `133.0.6943.142` | 引入 CEF API 版本化,覆盖新 API / ABI 机制下的宿主适配;本项目仍针对每套 SDK 独立编译。[官方 API 版本说明](https://chromiumembedded.github.io/cef/api_versioning.html#supported-versions)                                      |
| 154    | `154.0.28+g564dd6c` | `154.0.8037.58`  | 作为本项目 2026-09-28 固定的较新内核对照点,用于与旧版本比较相同页面的自动化行为;后续运行复用此精确版本。                                                                                                                     |

SDK 来自 [CEF 官方二进制分发](https://cef-builds.spotifycdn.com/),精确版本、归档大小、SHA-1 和运行文件清单固定在 [CEF/versions.json](CEF/versions.json)。
各版本分别编译和启动独立进程,使用各自的运行库与缓存。

#### 启动与构建依赖

| 使用方式                     | 依赖                                                                                                                                                                                                                        |
| ---------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 运行已有产物(`--skip-build`) | Windows 10/11 x64、Python 3.8+、完整的 `CEF/dist/<版本>/` 目录;无需编译工具或下载 SDK。启动器仅使用 Python 标准库,无需 `pip install`。                                                                                      |
| 首次运行或重新构建           | 上述系统与 Python 环境,另需 Visual Studio 2022 / 2026 的“使用 C++ 的桌面开发”工作负载、MSVC x64 编译工具、Windows SDK。VS2022 需 CMake 3.21+,VS2026 需 CMake 4.2+;启动器优先使用 PATH 中的 CMake,找不到时使用 VS 自带版本。 |
| 加载默认线上页面             | 能访问 GitHub Pages;首次准备 SDK 还需能访问 `cef-builds.spotifycdn.com`。                                                                                                                                                   |
| 加载本地 WEB 页面            | 另需 Node.js 22+、pnpm 10.25,并保持 WEB 开发服务运行。                                                                                                                                                                      |

CEF 运行库随靶场目录一起分发,无需安装 Chrome 或 WebView2 Runtime。分发时保留整个 `dist/<版本>/` 目录,包括 DLL、PAK、snapshot、`locales/` 和 `version.json`。
CEF 启动器支持 `--skip-build` 直接运行完整产物目录;WebView2 启动器始终默认构建,直接运行已有 WebView2 产物请使用上文的 EXE 命令。
五个 SDK 压缩包合计约 880 MB,解压和构建还需额外磁盘空间。当前五版本已在 Windows 11 验收;109 行中的旧 Windows 说明是上游分支的历史支持范围,本项目宿主的其他系统环境需另行验证。

#### 启动命令

在仓库根目录执行。首次运行会自动下载并校验所选版本 SDK、解压、编译,随后启动;后续复用 SDK 并进行增量构建。

```powershell
cd D:\code\xpath
python .\tools\start_cef.py                                    # 交互多选,构建后启动
python .\tools\start_cef.py --skip-build                       # 交互多选,使用已有产物
python .\tools\start_cef.py --version 109                      # 指定一个版本
python .\tools\start_cef.py --versions 109 125 128 133 154      # 一次启动五个版本
python .\tools\start_cef.py --versions 109 154 --skip-build     # 直接启动两个已有版本
python .\tools\start_cef.py --versions 109 125 128 133 154 --no-launch  # 只构建/验证
python .\tools\start_cef.py --version 154 --force-build         # 清理后重新编译并启动
python .\tools\start_cef.py --help                             # 查看全部参数
```

不传版本时进入与 Java 启动器一致的交互式多选菜单:上下键移动,`Enter` / 空格勾选,在“已完成选择”上按 `Enter` 启动,`Esc` 取消。
`--version` 与 `--versions` 互斥,传入任一参数即跳过菜单;非交互环境须明确指定版本。
`--skip-build` 与 `--force-build` 互斥;`--no-launch` 可与 `--skip-build` 组合,只检查已有产物。
多版本模式先准备所有选中版本的产物,再启动各个窗口。

构建或启动前会自动终止当前仓库 `CEF/dist/<版本>/` 中所选版本的旧进程,包括同一 EXE 的渲染器、GPU 等 CEF 子进程,并等待退出,避免 EXE / DLL 被占用。所选版本已打开的窗口会关闭;未选中的版本和其他目录的同名程序不受影响。终止失败或等待超时会报错并停止后续构建/启动。只有 `--skip-build --no-launch` 的纯产物检查不清理进程。

开发本地页面时,先在一个终端启动 WEB:

```powershell
cd D:\code\xpath\WEB
pnpm install
pnpm dev                         # http://localhost:7199/
```

再在另一个终端启动 CEF,连接同一套 WEB 源码:

```powershell
cd D:\code\xpath
python .\tools\start_cef.py --versions 109 125 128 133 154 --skip-build --base-url http://localhost:7199/
```

`--base-url` 使用以 `/` 或 `#/` 结尾的 HTTP(S) 根地址。默认线上根地址为 `https://baobaomi900901.github.io/xpath/#/`,本地使用普通路由。
CEF 已禁止通过启动参数开启 CDP；直接给 EXE 添加调试参数也会被忽略，窗口正常启动。启动器兼容并忽略旧调试选项。

可执行程序在 `CEF/dist/<版本>/cef-shooting-range-<版本>.exe`,SDK 和下载缓存位于 `CEF/.cache/`,构建目录为 `CEF/build/<版本>/`。
每次启动使用独立的 `CEF/.cache/profiles/<版本>/<进程ID>-<标识>/` 数据目录,其中包含 `cef.log`,可用于运行问题排查。
当前禁用 CDP 的验收运行 `python .\tools\verify_no_cdp.py --kind cef`。旧 CDP 页面交互结果属于历史版本。详细步骤见 [CEF/README.md](CEF/README.md)。

### ELECTRON — 四版本浏览器嵌入靶场

参考 CEF 的三个页面入口、窗口布局和启动器约定。左侧菜单为 Electron 宿主 DOM，右侧为独立网页视图；22 / 29 使用 BrowserView，38 / 44 使用 WebContentsView。
固定 Electron **22.3.27 / 29.4.6 / 38.8.6 / 44.4.5**，对应 Chromium **108 / 122 / 140 / 152**，显式开启无障碍支持以供元素探测器比较。

```powershell
python .\tools\start_electron.py                              # 交互多选，构建并启动
python .\tools\start_electron.py --versions 22 29 38 44 --skip-build  # 启动四个已有程序
python .\tools\start_electron.py --versions 22 29 38 44 --no-launch   # 仅构建和验证
python .\tools\start_electron.py --version 22 --skip-build
python .\tools\start_electron.py --versions 22 44 --skip-build --base-url http://localhost:7199/
```

默认加载线上 GitHub Pages，无需启动本地 WEB。首次构建自动下载并校验官方运行时，随后复制共享应用源码；不依赖 npm、Visual Studio 或 CMake。
产物为 `ELECTRON/dist/<版本>/electron-shooting-range-<版本>.exe`，分发时保留整个运行目录。
每次启动使用独立缓存；参数、精确版本、控件标识和验收命令见 [ELECTRON/README.md](ELECTRON/README.md)。
四版本均忽略 CDP 启动参数，正常打开窗口且不开放 CDP 端口或 pipe。当前验收运行 `python .\tools\verify_no_cdp.py --kind electron`；旧 CDP 页面交互结果属于历史版本。

### OFFICE — Excel 加载项靶场

```powershell
python .\tools\start_excel_addin.py     # 装证书 → 起 HTTPS 服务 → 生成并打开靶场工作簿
python .\tools\stop_excel_addin.py      # 卸载
```

要点:

- 加载项是**文档级绑定**的,必须打开生成的 `OFFICE\excel-addin\dist\Excel 靶场插件.xlsx`,
  顶部才会出现 `Excel 靶场插件` 选项卡;"新建空白工作簿"里没有
- HTTPS 服务要**保持常驻**(脚本前台运行,`Ctrl+C` 结束)
- 换一台电脑的完整步骤、验收清单与故障排查见 [OFFICE/excel-addin/README.md](OFFICE/excel-addin/README.md)

### JAVA — Swing 多版本靶场

```powershell
python .\tools\start_java.py                                       # 交互式多选菜单
python .\tools\start_java.py --versions 8 11 17 21 25 --no-launch  # 只构建验证,不起窗口
python .\tools\start_java.py --versions 8 25 --skip-build          # 跳过构建,直接运行
python .\tools\start_java.py --versions 17 --force-build           # 强制重新构建
```

产物在 `JAVA/target/jdk-<版本>/shooting-range-<版本>.jar`。
功能与构建注意事项见 [JAVA/README.md](JAVA/README.md)。

### QT — 多版本 Widgets / QML 靶场

```powershell
python tools/start_qt.py --versions 5.15.2 6.8.3 --skip-build
python tools/start_qt.py --versions 6.8.3 --frontends widgets --form-mode random --skip-build
python tools/start_qt.py --versions 5.15.2 6.8.3 --no-launch
python tools/start_qt.py --versions 5.15.2 6.8.3 --skip-build --self-test
```

两个真实 Qt SDK 分别构建 Widgets 和 Quick/QML，共四个组合。对齐 Win32 的十字段表单、1000条员工数据/20条分页、菜单和带JSON结果的拖拽；Widgets 另有分组、平铺和随机表单。保留原名片隐藏节点示例（`--frontends profile`），已接入统一启动中心。

完整运行目录位于 `QT/dist/<版本>/`，可复制整个目录后直接运行EXE；安装、构建和验收说明见 [QT/README.md](QT/README.md)。

### DELPHI — VCL 桌面靶场

```powershell
python .\tools\start_delphi.py                       # 构建并启动
python .\tools\start_delphi.py --no-launch           # 仅构建
python .\tools\start_delphi.py --skip-build          # 启动已有程序
python .\tools\start_delphi.py --configuration Debug
```

默认优先使用已安装的 Delphi 2010，也可指定 `--compiler-path` 或环境变量 `DELPHI_DCC32`。
PowerShell 入口为 `.\DELPHI\build.ps1` / `.\DELPHI\run.ps1`。
Release 产物为 `DELPHI/build/Release/Win32VclShootingRange.exe`，运行已有 EXE 无需 Delphi。
包含 MDI 层级、每个表单 item 的独立具名 Pane、原生菜单、10 页表格（共 1000 条，每页 100 条，5 个动态页码）和拖拽测试，构建参数与验收方式见 [DELPHI/README.md](DELPHI/README.md)。
新增原生 `TStringGrid`、`TDBGrid` 和真实 `TVirtualStringTree` 复杂控件测试页；`TcxGrid` / `TcxTreeList` 的可选构建需要匹配的 DevExpress VCL 库，默认 EXE 的这两个页签显示待接入说明。

### POWERBUILDER — PowerBuilder 桌面靶场

```powershell
python .\tools\start_powerbuilder.py                         # 方向键菜单：启动 EXE / 开发模式
python .\tools\start_powerbuilder.py --mode exe              # 直接启动单文件 EXE
python .\tools\start_powerbuilder.py --mode dev              # 从源码编译并启动
python .\tools\start_powerbuilder.py --skip-build            # 运行已有程序
python .\tools\start_powerbuilder.py --no-launch             # 仅构建检查
python .\tools\start_powerbuilder.py --skip-build --self-test # PB 内部自检后关闭
python .\tools\package_powerbuilder.py                      # 打包为含运行时的单个 EXE
```

三个页签包含十字段表单、七列原生 DataWindow（1000 条、每页 20 条、50 页）和拖拽测试，另有原生菜单。默认从注册表发现已安装的 Utilities 和匹配 Runtime，支持 `--tools-path` / `--runtime-path`；不需要数据库。
产物为 `POWERBUILDER/build/Release/PowerBuilderShootingRange.exe`，运行时保留同目录的 PBD、XML 和 pb.ini。安装要求、可访问性设置及人工测试步骤见 [POWERBUILDER/README.md](POWERBUILDER/README.md)。
单文件版为 `POWERBUILDER/dist/PowerBuilder靶场.exe`，可复制到其他 Windows 10 / 11 电脑双击运行，无需另装 Python、PowerBuilder 或 VC++ Runtime。

## 浏览器靶场禁止 CDP 的发行包

CEF、Electron、WebView2 均已禁用通过启动参数开启 CDP，直接启动 EXE 也生效。添加调试参数仍正常打开窗口。

本次 Windows x64 ZIP 位于 `artifacts/no-cdp-2026-10-23/`：CEF 109/125/128/133/154、Electron 22/29/38/44、WebView2 Release。完整解压后运行目录内 EXE；WebView2 依赖已安装的 WebView2 Runtime。目录附带 `manifest.json`、`SHA256SUMS.txt` 和验收记录。

重新打包前先构建并运行三套 `verify/verify-flow.mjs`，再分别运行 `tools/verify_cdp_pipe.mjs` 的 CEF、Electron 及 Electron 阳性对照并将结果保存到对应 `verify/artifacts/`；最后运行 `python tools/package_browser_ranges.py`。各靶场 README 说明了验收范围与依赖。

## 启动器通用约定

`tools/start_win32.py`、`tools/start_java.py`、`tools/start_cef.py` 与 `tools/start_electron.py` 的交互菜单行为一致:

- 方向键上下移动焦点
- `Enter` 或空格勾选 / 取消勾选
- 在 `[ 已完成选择 ]` 上按 `Enter` 后统一构建并同时启动所选版本
- `Esc` 取消

PowerBuilder 启动器复用 Win32 的按键读取、颜色和终端配置，按同样方式操作；其“启动 EXE / 开发模式”为单选。

## WEB 在线部署(GitHub Pages)

首次启用:在仓库 Settings → Pages → Build and deployment → Source 中选择 GitHub Actions。
将改动推送到 main 后,Deploy WEB to GitHub Pages 工作流会自动构建 WEB 并发布 WEB/dist。
每次推送到 main 都会触发,不限制修改目录;也可在 Actions 中手动 Run workflow。

首次部署成功后的地址:https://baobaomi900901.github.io/xpath/
线上子页面使用 Hash 路由,例如 /xpath/#/form-controls,可直接打开和刷新。
本地 pnpm dev 保留原有路由。

GitHub Pages 仅托管静态页面,不能运行 SDK Cookie 观测所需的 /api/sdk-web/\* 接口,
也不能提供本地 HTTP/HTTPS 测试域名及 Vite 插件的下载响应头。
Cookie 服务端测试请继续使用本地靶场;fetch + Blob 下载仍可在线使用。

本地验证 Pages 构建(PowerShell):

```powershell
cd WEB
pnpm install --frozen-lockfile
$env:VITE_GITHUB_PAGES = 'true'
pnpm run build --base /xpath/
Remove-Item Env:VITE_GITHUB_PAGES
```

## 约定

- 每个靶场目录下都有自己的 `README.md`,记录该靶场的功能、验收方式与注意事项
- 跨靶场的启动器统一放在 `tools/`(Python,仅标准库)
- `.private/` 是本地实验目录,已在 `.gitignore` 中排除
- 新增靶场时:目录放在仓库根、启动器放进 `tools/`,并在本文件"靶场一览"里补一行
