# CEF 多版本浏览器嵌入靶场

Windows x64 原生窗口，左侧是 Win32 ListBox 菜单，右侧嵌入真正的 CEF 浏览器。共享一套 C++ 宿主源码，分别针对 CEF 109 / 125 / 128 / 133 / 154 编译；每个版本拥有独立 EXE、运行库和进程缓存。

## 启动

在仓库根目录执行：

```powershell
cd D:\code\xpath
python .\tools\start_cef.py
```

与 Java 启动器一样，不传版本参数时进入多选菜单，列出 109 / 125 / 128 / 133 / 154：

- 上下方向键移动焦点。
- `Enter` 或空格勾选 / 取消勾选，已选择的版本显示绿色勾选。
- 移动到“已完成选择”后按 `Enter`，统一构建并启动所选版本。
- `Esc` 取消；未选择任何版本时提示继续选择。

使用现有产物也可交互选择：`python .\tools\start_cef.py --skip-build`。
非交互环境需传 `--version` 或 `--versions`。直接指定版本可跳过菜单：

```powershell
python .\tools\start_cef.py --version 109
python .\tools\start_cef.py --version 125
python .\tools\start_cef.py --version 128
python .\tools\start_cef.py --version 133
python .\tools\start_cef.py --version 154
```

一条命令同时启动五个版本：

```powershell
python .\tools\start_cef.py --versions 109 125 128 133 154
```

首次运行自动下载对应的官方 SDK、校验、解压和编译；后续复用 SDK 和增量构建。当前机器已准备好五个版本的产物，可以跳过编译直接启动：

```powershell
python .\tools\start_cef.py --versions 109 125 128 133 154 --skip-build
```

其他参数：

| 参数 | 行为 |
|---|---|
| `--version 109` | 单版本；与 `--versions` 互斥 |
| `--versions 109 154` | 多版本；重复版本合并，按主版本顺序启动 |
| `--skip-build` | 验证并启动现有产物，不下载或编译 |
| `--no-launch` | 只构建/验证，不打开窗口；可与 `--skip-build` 组合 |
| `--force-build` | 清理后重新编译；与 `--skip-build` 互斥 |
| `--base-url http://localhost:7199/` | 切换为本地 WEB 路由 |
| `--remote-debugging-port 9222` | 显式开启 CDP 调试；仅允许单版本，端口范围 1024–65535 |

多版本模式先准备全部产物，再启动各窗口。标题显示 CEF 主版本和完整 Chromium 版本。

## 页面与控件

| 左侧菜单 | 默认页面 |
|---|---|
| 点击测试 | [keys-click-test](https://baobaomi900901.github.io/xpath/#/keys-click-test) |
| 表单测试 | [form-controls](https://baobaomi900901.github.io/xpath/#/form-controls) |
| iframe表单 | [iframe-shadow-form](https://baobaomi900901.github.io/xpath/#/iframe-shadow-form) |

默认打开点击测试。菜单支持鼠标选择和上下方向键切换；地址栏只读；刷新保留当前路由；窗口缩放同步调整浏览器尺寸。宿主显式启用 CEF 无障碍。为保持单个嵌入浏览器，取消创建新浏览器弹窗；现有页面内部的 iframe / Shadow DOM 正常工作。

原生控件 ID：菜单 `1001`、地址栏 `1002`、刷新按钮 `1003`、状态栏 `1004`。浏览器是右侧真实 child HWND，没有将网页截图或 Canvas 替代为界面。

页面直接复用 `WEB/` 的已有实现。开发本地页面时，先在一个终端启动 WEB：

```powershell
cd D:\code\xpath\WEB
pnpm dev
```

再在另一终端启动靶场：

```powershell
cd D:\code\xpath
python .\tools\start_cef.py --versions 109 125 128 133 154 --skip-build --base-url http://localhost:7199/
```

本地地址使用普通路由，线上地址使用 `#/` 路由。`--base-url` 接收无凭据、无查询参数的 HTTP(S) 根地址。

## 固定版本

| CEF 主版本 | CEF 完整版本 | Chromium |
|---|---|---|
| 109 | `109.1.18+gf1c41e4` | `109.0.5414.120` |
| 125 | `125.0.22+gc410c95` | `125.0.6422.142` |
| 128 | `128.4.12+g1d7a1f9` | `128.0.6613.138` |
| 133 | `133.4.8+g99a2ab1` | `133.0.6943.142` |
| 154 | `154.0.28+g564dd6c` | `154.0.8037.58` |

归档选自 [CEF 官方构建分发](https://cef-builds.spotifycdn.com/) 的 Windows x64 minimal SDK，精确文件名、大小、SHA-1 和所需运行文件保存在 [versions.json](versions.json)。校验 SDK 头文件和构建版本标记，避免混用其他版本的运行库。

109 使用 Alloy bootstrap；125 使用 Chrome bootstrap 与 Alloy style；128 及之后使用 Chrome bootstrap 与 Alloy style 的原生窗口嵌入接口。新旧 API 差异集中在宿主编译条件中。

## 构建依赖与产物

- Windows x64。五版本整套验收在 Windows 11 上完成。
- Python 3.8+；启动器仅使用标准库。
- Visual Studio 2022 / 2026，安装“使用 C++ 的桌面开发”工作负载和 Windows SDK。
- CMake 3.21+；Visual Studio 2026 使用支持该生成器的 CMake。启动器也可发现 Visual Studio 自带的 CMake。
- 首次下载需要访问 `cef-builds.spotifycdn.com`。五个压缩 SDK 合计约 880 MB，解压和构建还需额外磁盘空间。

构建全部版本：

```powershell
python .\tools\start_cef.py --versions 109 125 128 133 154 --no-launch
```

| 路径 | 内容 |
|---|---|
| `.cache/downloads/` | 已校验的 SDK 压缩包 |
| `.cache/sdk/<版本>/` | 解压的 SDK |
| `build/<版本>/` | 各版本独立 CMake 构建目录 |
| `dist/<版本>/cef-shooting-range-<版本>.exe` | 可运行宿主及同目录 CEF 运行资源 |
| `.cache/profiles/<版本>/<进程ID>-<标识>/` | 每次启动独立的浏览器数据、缓存和 `cef.log` |

以上产物和缓存已加入 `.gitignore`。分发时需要完整的 `dist/<版本>/` 目录；EXE 依赖同目录 DLL、PAK、snapshot 和 locales 文件。编译使用 SDK 自带的 C++ wrapper，运行资源保持版本一致。

## 验收

启动器测试：

```powershell
python -m unittest tools.test_start_cef -v
```

实际五版本程序验收使用 Node.js 22+ 的内置 WebSocket，无需额外 npm 包。先启动本地 WEB，再运行：

```powershell
node .\CEF\verify\verify-flow.mjs
node .\CEF\verify\verify-flow.mjs 109 154
```

默认连接 `http://localhost:7199/`。验收检查实际 Chromium 版本、原生菜单与路由、可信点击、表单输入、iframe 内 Shadow DOM 表单、尺寸同步、刷新、渲染器无障碍树、弹窗阻止和正常退出。CDP 无障碍检查证明渲染器 AX 可用；原生 UIA 的完整表现可继续用项目现有的 UIA 工具比较。

截图和结果写入 `verify/artifacts/`。验收程序只控制自己创建的靶场进程，结束时关闭它们。

2026-09-28 验证结果：29 项 CEF 启动器测试通过；五个版本在本地 WEB 和内置线上默认地址下各通过 45 项实际验收，共 90 项。统一命令同时创建五个版本窗口的检查也通过。结果分别保存为 `results.json` 和 `results-hosted.json`。

直接验证 EXE 内置的线上默认地址：

```powershell
$env:XPATH_CEF_DEFAULT = '1'
node .\CEF\verify\verify-flow.mjs
Remove-Item Env:XPATH_CEF_DEFAULT
```

也可以用 `XPATH_CEF_BASE` 指定其他 WEB 部署地址。需要手动接入 CDP 时：

```powershell
python .\tools\start_cef.py --version 154 --skip-build --remote-debugging-port 9222
```

## 排查

启动器会提前报告不支持的版本、冲突参数、缺失运行文件和 SDK 身份不一致。编译失败查看控制台的 CMake/MSBuild 输出；运行失败查看当前进程缓存中的 `cef.log`。如果构建缓存属于其他路径或 SDK，按提示移走对应 `build/<版本>/` 后重新构建。

默认加载线上页面需要能够访问 GitHub Pages；开发或离线局域网测试可改用本地 WEB。不同版本及重复启动使用独立缓存，避免 profile 锁冲突。
