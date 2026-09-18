# xpath

面向 **UI 自动化 / RPA / 无障碍(UI tree)测试** 的靶场集合。每个靶场都是一个可独立运行的程序或页面,
分别覆盖不同的宿主环境与技术栈(浏览器、原生 Win32、Qt、Java Swing、Delphi VCL、Excel 加载项),
用于检验自动化在元素定位、坐标与几何、拖拽、菜单、对话框、iframe / Shadow DOM、UIA 压力等场景下的表现。

---

## 靶场一览

| 目录 | 形态 | 技术栈 | 一键启动 |
|---|---|---|---|
| [`WEB/`](WEB) | 浏览器页面,19 条路由 | React 19 + antd 5 + Vite 6 | `cd WEB; pnpm dev` |
| [`WIN32/`](WIN32) | 原生桌面程序 3 个 + UIA 压力程序 + 检测工具 | C++ / Win32 / CMake | `python tools\start_win32.py` |
| [`OFFICE/`](OFFICE/excel-addin) | Excel 加载项(Ribbon + WebView2 任务窗格) | Office.js + 静态 HTML/CSS/JS + Python 标准库 HTTPS | `python tools\start_excel_addin.py` |
| [`JAVA/`](JAVA) | Swing 桌面程序,多 JDK 版本并行 | Java 8/11/17/21/25 + Maven | `python tools\start_java.py` |
| [`QT/`](QT) | Qt Quick 桌面程序 | Qt 5.15.2 + MinGW 8.1 | `.\QT\run.ps1` |
| [`DELPHI/`](DELPHI) | VCL 桌面工程(需 Delphi 编译) | Delphi 2010 (VCL) | 用 Delphi 打开 `Win32VclShootingRange.dpr` |

跨靶场的启动器都在 [`tools/`](tools) 下;`WIN32` / `JAVA` / `QT` 另外各自带 `build.ps1` / `run.ps1`。

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
├─ QT/                     Qt Quick 靶场
│  ├─ src/ qml/ resources/
│  ├─ build/               构建产物
│  └─ run.ps1 / build.ps1
├─ DELPHI/                 Delphi VCL 靶场工程
├─ tools/                  跨靶场启动器(Python)
│  ├─ start_win32.py
│  ├─ start_java.py
│  ├─ start_excel_addin.py / stop_excel_addin.py
│  └─ test_start_java.py
├─ .github/workflows/      GitHub Pages 部署
└─ .private/               本地实验目录,已 gitignore
```

## 环境准备

| 靶场 | 依赖 |
|---|---|
| 通用启动器 | Python 3.8+(仅标准库,无需 pip 安装) |
| WEB | Node.js 22+、pnpm 10.25 |
| WIN32 | Visual Studio 2019+(含"使用 C++ 的桌面开发"工作负载)、CMake 3.20+ |
| OFFICE | Windows + Excel 桌面版(2016+ / Microsoft 365);**不需要**管理员权限、OpenSSL、PowerShell 7 |
| JAVA | Amazon Corretto JDK 8/11/17/21/25,放在 `JAVA/.tools/jdks/corretto/<版本>`;Maven 由启动器自动下载 |
| QT | Qt 5.15.2 + MinGW 8.1(本机装在 `D:\Qt`) |
| DELPHI | Delphi 2010(仅编译需要) |

## 各靶场启动方式

### WEB — 浏览器靶场

```powershell
cd WEB
pnpm install
pnpm dev              # http://localhost:7199, 自动打开浏览器
```

- 构建 / 预览:`pnpm build`(输出到 `WEB/dist`)、`pnpm preview`
- 主要路由:`/`、`/form-controls`、`/table-test`、`/table-div-test`、`/anchor-test`、
  `/geometry-test`、`/element-html-test`、`/iframe-shadow-form`、`/iframe-nested-test`、
  `/shadow-nested-test`、`/download-dialog-test`、`/upload-dialog-test`、`/web-dialog-test`、
  `/keys-click-test`、`/drag-to-test`、`/cookie-test`——完整清单见 `WEB/src/App.tsx`
- **SDK Cookie 观测模式**:设置 `UIPILOT_SDK_WEB_*` 系列环境变量后,`pnpm dev` 会切换为 HTTPS +
  固定端口 + `/api/sdk-web/*` 接口 + 下载响应头;该模式只能在本地跑,线上 Pages 不支持

### WIN32 — 原生 Win32 靶场

```powershell
python .\tools\start_win32.py                                  # 交互式多选菜单
python .\tools\start_win32.py --backends uia msaa canvas       # 指定版本直接启动
python .\tools\start_win32.py --backends uia --skip-build      # 跳过构建,用现有 EXE
python .\tools\start_win32.py --backends uia --no-launch       # 只构建验证,不起窗口
python .\tools\start_win32.py --configuration Debug
```

可用版本:`uia`、`msaa`、`canvas`、`pressure500`、`pressure1000`、`pressure2000`。

也可以直接用 PowerShell:

```powershell
cd WIN32
.\build.ps1
.\run.ps1 -Backend uia -SkipBuild
```

产物在 `WIN32/build/Release/`:

- `win32-shooting-range-uia.exe` — 标准 Win32 控件,完整 UIA 树
- `win32-shooting-range-msaa.exe` — 单个自绘 HWND,只暴露 MSAA `IAccessible` 树
- `win32-shooting-range-canvas.exe` — 同样自绘但不暴露任何内部无障碍节点
- `win32-uia-pressure.exe` — UIA 深度压力靶场,启动参数为嵌套层数(500 / 1000 / 2000)
- `uia-no-msaa-probe.exe` — 关闭 MSAA Proxy 的 UIA 只读检测工具

各版本差异、Tab 功能与拖拽字段说明见 [WIN32/README.md](WIN32/README.md)。

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

### QT — Qt Quick 靶场

```powershell
cd QT
.\run.ps1              # 构建 + 运行
.\run.ps1 -SkipBuild   # 跳过构建直接运行
.\build.ps1            # 只构建
```

用于验证 `Accessible.ignored` 的元素(头像、昵称)是否出现在 UI tree 中。详见 [QT/README.md](QT/README.md)。

### DELPHI — VCL 工程

当前环境没有 Delphi 编译器,工程未实际编译。在装有 Delphi 2010 的机器上:
用 Delphi 打开 `DELPHI/Win32VclShootingRange.dpr` → 目标平台选 Win32、关闭 Runtime Packages → Build Project。
目标 UIA 树结构与功能见 [DELPHI/README.md](DELPHI/README.md)。

## 启动器通用约定

`tools/start_win32.py` 与 `tools/start_java.py` 的交互菜单行为一致:

- 方向键上下移动焦点
- `Enter` 或空格勾选 / 取消勾选
- 在 `[ 已完成选择 ]` 上按 `Enter` 后统一构建并同时启动所选版本
- `Esc` 取消

## WEB 在线部署(GitHub Pages)

首次启用:在仓库 Settings → Pages → Build and deployment → Source 中选择 GitHub Actions。
将改动推送到 main 后,Deploy WEB to GitHub Pages 工作流会自动构建 WEB 并发布 WEB/dist。
每次推送到 main 都会触发,不限制修改目录;也可在 Actions 中手动 Run workflow。

首次部署成功后的地址:https://baobaomi900901.github.io/xpath/
线上子页面使用 Hash 路由,例如 /xpath/#/form-controls,可直接打开和刷新。
本地 pnpm dev 保留原有路由。

GitHub Pages 仅托管静态页面,不能运行 SDK Cookie 观测所需的 /api/sdk-web/* 接口,
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
