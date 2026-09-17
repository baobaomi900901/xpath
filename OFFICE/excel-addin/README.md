# Excel 靶场插件

一个可安装进 **Excel 桌面版** 的 Office 加载项靶场:Excel 菜单里出现 `Excel 靶场插件` 选项卡,
点开任务窗格后完成 `点击登录 → admin/1 → 已登录 → admin ▾ → 退出登录` 的完整交互链,
用于验证自动化在 **Ribbon + WebView2 任务窗格** 形态下的定位与点击能力。

> 凭据 `admin` / `1` 是硬编码在页面里的靶场演示值,页面**不发起任何网络请求**,不采集也不外发任何数据。

## 环境要求

| 项 | 要求 |
|---|---|
| 操作系统 | Windows |
| Excel | 桌面版,支持 Add-in Commands 1.1(Office 2016 及以上 / Microsoft 365) |
| Python | 3.8+(仅用标准库) |
| 证书转换 | `openssl`(随 Git for Windows 安装)或 PowerShell 7(`pwsh`)二选一 |
| 验收脚本 | Node.js 18+(需全局 `WebSocket`,Node 22+ 自带)+ 本机 Chrome 或 Edge |

## 安装

```powershell
python tools/start_excel_addin.py
```

脚本会依次:创建并信任 `localhost` 自签证书 → 把 manifest 复制进 Excel 的 sideload 目录
(`%LOCALAPPDATA%\Microsoft\Office\16.0\Wef\`)→ 启动 HTTPS 服务 `https://localhost:7300` → 尝试拉起 Excel。

**然后完全退出并重新打开 Excel**(Ribbon 只在启动时读取加载项列表),顶部即出现 `Excel 靶场插件` 选项卡。

| 参数 | 作用 |
|---|---|
| `--port 7300` | 换端口(manifest 里的端口会被同步改写) |
| `--no-launch` | 只起服务,不自动开 Excel |
| `--skip-sideload` | 只起服务,不写 Excel 的 sideload 目录 |
| `--prepare-only` | 只做证书与 sideload,不启动服务 |
| `--renew-cert` | 强制重建 localhost 证书 |

## 使用流程

1. Excel 顶部点击 `Excel 靶场插件` 选项卡。
2. 点击组 `登录靶场` 里的 `打开面板` 按钮,右侧出现任务窗格。
3. 面板里点击 `点击登录`。
4. 弹出登录框:名称输入 `admin`,密码输入 `1`,点击 `登录`。
5. 登录框消失,面板右上显示 `已登录`;原 `点击登录` 按钮变成 `admin`,右侧带小箭头 `▾`。
6. 点击 `admin ▾` 展开菜单,点击 `退出登录` 回到未登录状态。

输错密码会在登录框内提示 `账号或密码错误`,弹窗保持打开;点 `取消` 或按 `Esc` 可关闭登录框。

## 卸载

```powershell
python tools\stop_excel_addin.py              # 移除 sideload + 删除 localhost 证书
python tools\stop_excel_addin.py --keep-cert  # 只移除 sideload, 保留证书
```

卸载后同样需要**完全退出并重新打开 Excel**,选项卡才会消失。

## 元素契约(自动化定位用)

关键元素同时带 `id` 与 `data-testid`,取值一致;建议优先用 `data-testid`。
文本内容固定,不使用随机类名,所有可交互元素都是 `<button>`。

| data-testid | 元素 | 文案 | 可见状态 |
|---|---|---|---|
| `login-trigger` | button | 点击登录 | 未登录 |
| `login-dialog` | div(遮罩 + 居中卡片) | — | 登录框打开 |
| `login-form` | form | — | 登录框打开 |
| `username-input` | input[type=text] | — | 登录框打开 |
| `password-input` | input[type=password] | — | 登录框打开 |
| `login-submit` | button[type=submit] | 登录 | 登录框打开 |
| `login-cancel` | button | 取消 | 登录框打开 |
| `login-error` | p[role=alert] | 账号或密码错误 | 校验失败 |
| `login-status` | span | 已登录 | 已登录 |
| `user-menu-trigger` | button(内含 `▾`) | admin | 已登录 |
| `user-menu-name` | span | admin | 已登录 |
| `user-menu` | div[role=menu] | — | 菜单展开 |
| `logout-item` | button | 退出登录 | 菜单展开 |

页面还暴露 `window.__xpathRange.getState()`,返回 `{loggedIn, dialogOpen, menuOpen, error}`,
便于脚本断言内部状态。

## 无 Excel 时的验收

不依赖 Excel 也能验证整套交互(HTTPS 服务 + 真实浏览器):

```powershell
python tools\start_excel_addin.py --no-launch --skip-sideload   # 终端 1, 保持运行
node OFFICE\excel-addin\verify\verify-flow.mjs                  # 终端 2
```

脚本用 CDP 驱动本机 Chrome/Edge 真实点击,覆盖失败密码、取消、登录、展开菜单、退出登录,
并把截图写到 `verify/screenshot-login-dialog.png`、`verify/screenshot-logged-in.png`、
`verify/screenshot-logged-out.png`。

## 故障排查

| 现象 | 处理 |
|---|---|
| Excel 里没有 `Excel 靶场插件` 选项卡 | 确认服务在运行、`%LOCALAPPDATA%\Microsoft\Office\16.0\Wef\xpath-excel-addin.manifest.xml` 存在,并**完全重启** Excel |
| 任务窗格空白或显示旧内容 | 面板内右键 → 重新加载;服务已强制 `no-store`,旧内容一般是没重启面板 |
| Excel 提示加载项来源不受信任 | 重跑 `python tools/start_excel_addin.py --renew-cert`,它会重建证书并写入 `CurrentUser\Root` |
| 端口 7300 被占用 | `python tools/start_excel_addin.py --port 7301`(manifest 端口会同步改写) |
| 提示需要 openssl 或 pwsh | 装 Git for Windows(自带 openssl)或 PowerShell 7 |
| 无法写入 Wef 目录 | 手动把 `OFFICE\excel-addin\manifest.xml` 复制到 `%LOCALAPPDATA%\Microsoft\Office\16.0\Wef\`(文件名需以 `.xml` 结尾) |
| 改了面板页面不生效 | 面板内右键 → 重新加载即可,不用重装 |
| 改了 Ribbon 文案/按钮 | 改 `manifest.xml` 后需重启 Excel |

## 目录结构

```
OFFICE/excel-addin/
  manifest.xml                Ribbon 选项卡 / 组 / 按钮 + 任务窗格入口(安装契约)
  src/taskpane.html|css|js    任务窗格与登录交互(改这里只需重新加载面板)
  src/commands.html|js        Ribbon 命令页占位(Office 运行时要求)
  assets/icon-16|32|80.png    按钮图标, 由 assets/generate_icons.py 生成
  verify/verify-flow.mjs      零依赖端到端验收脚本
  verify/screenshot-*.png     验收截图
tools/start_excel_addin.py    证书 + HTTPS 服务 + sideload
tools/stop_excel_addin.py     卸载
```
