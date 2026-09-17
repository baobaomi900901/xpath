# Excel 靶场插件

一个可安装进 **Excel 桌面版** 的 Office 加载项靶场:加载项选项卡里点 `打开面板`,任务窗格里完成
`点击登录 → admin/1 → 已登录 → admin ▾ → 退出登录` 的完整交互链,用于验证自动化在
**Ribbon + WebView2 任务窗格** 形态下的定位与点击能力。

> 凭据 `admin` / `1` 是硬编码在页面里的靶场演示值。页面**不发起任何网络请求**,不采集也不外发任何数据。

---

## 1. 前置条件

| 项 | 要求 | 说明 |
|---|---|---|
| 操作系统 | Windows 10 / 11 | 证书与注册表机制都是 Windows 专有 |
| Excel | 桌面版,支持 Add-in Commands 1.1(Office 2016 及以上 / Microsoft 365) | 需要能访问 `%LOCALAPPDATA%\Microsoft\Office\16.0\Wef` |
| Python | 3.8 及以上 | **只用标准库**,不需要 pip 安装任何包 |
| 管理员权限 | **不需要** | 证书写入当前用户的证书存储,注册表写入 `HKCU` |
| openssl / PowerShell 7 | **不需要** | 证书转换只用系统自带的 Windows PowerShell 5.1 + .NET |
| Node.js | 仅"无 Excel 验收"和"注册状态自查"时需要 | 验收脚本需要 Node 22+(自带全局 `WebSocket`) |

> 也就是说:一台干净的 Windows + Excel + Python 就能跑,不用装 Git、不用装 OpenSSL、不用装 PowerShell 7。

---

## 2. 在一台新电脑上的完整步骤

### 步骤 0:拿到代码

把 `xpath` 仓库放到目标机器,例如 `D:\code\xpath`。至少要包含:

```
OFFICE/excel-addin/manifest.xml
OFFICE/excel-addin/src/…
tools/start_excel_addin.py
```

### 步骤 1:一次性安装 + 启动服务

在仓库根目录打开终端:

```powershell
cd D:\code\xpath
python tools\start_excel_addin.py
```

脚本按顺序自动完成:

1. 创建 `localhost` 自签证书(传统 CSP 提供程序,私钥可导出),并加入当前用户的受信任根存储;
2. 导出 PEM(仅用 Windows PowerShell 5.1 + Python 编码,零外部依赖);
3. 把加载项注册进 Excel 的**开发者加载项目录**:
   `HKCU\SOFTWARE\Microsoft\Office\16.0\WEF\Developer\<插件Id>` = manifest 绝对路径;
4. 生成**靶场工作簿** `OFFICE\excel-addin\dist\Excel 靶场插件.xlsx`(内嵌 webextension 引用);
5. 用默认程序打开这个工作簿;
6. **前台常驻** HTTPS 服务 `https://localhost:7300`。

> **这个终端窗口必须一直开着。** 关掉窗口 = 服务停止 = 任务窗格打不开。
> 只想准备不驻留用 `--prepare-only`;不想自动开工作簿用 `--no-launch`。

### 步骤 2:确认打开的是靶场工作簿

Excel 标题栏应为 `Excel 靶场插件.xlsx`。没自动打开就手动打开:

```
D:\code\xpath\OFFICE\excel-addin\dist\Excel 靶场插件.xlsx
```

> ⚠️ **"新建空白工作簿"里没有这个选项卡。** Office 的旁加载加载项在这里是**文档级绑定**的:
> 注册表只说明"上哪儿找 manifest",真正让 Ribbon 出现的是工作簿内部的
> `xl/webextensions/webextension.xml`(`store="developer" storeType="Registry"`)。
> 这是 Office 官方开发/旁加载流程的固有行为,不是配置出错。

### 步骤 3:使用插件

| # | 操作 | 预期 |
|---|---|---|
| 1 | 点顶部选项卡最右侧、`帮助` 之后的 `Excel 靶场插件` | 显示组 `登录靶场` 和按钮 `打开面板` |
| 2 | 点 `打开面板` | 右侧出现任务窗格,里面有 `点击登录` |
| 3 | 点 `点击登录` | 弹出登录框:名称 / 密码 / 取消 / 登录 |
| 4 | 名称填 `admin`,密码填 `1`,点 `登录` | 登录框消失;右上显示 `已登录`;按钮变成 `admin` + 右侧小箭头 `▾` |
| 5 | 点 `admin ▾` | 展开菜单,含菜单项 `退出登录` |
| 6 | 点 `退出登录` | 回到未登录状态,重新显示 `点击登录` |

输错密码会在登录框内提示 `账号或密码错误` 且弹窗保持打开;点 `取消` 或按 `Esc` 可关闭登录框。

### 步骤 4:不需要重启 Excel

加载项是随工作簿打开的,Excel 已经在运行也没关系。若 Ribbon 没出现,见第 5、8 节。

---

## 3. 每次开机 / 重启电脑后

**只有一步**:重新运行

```powershell
cd D:\code\xpath
python tools\start_excel_addin.py
```

其余机器状态(证书、Root 信任、注册表项、`Wef` 里的 manifest、靶场工作簿)都会持久保留,
脚本启动时自动复用或按需重建。

## 4. 什么持久、什么每次要做

| 项 | 位置 | 重启电脑后 | 说明 |
|---|---|---|---|
| localhost 证书 + Root 信任 | `Cert:\CurrentUser\My` / `Root` | ✅ 保留 | 到期前一直复用 |
| 插件注册项 | `HKCU\SOFTWARE\Microsoft\Office\16.0\WEF\Developer` | ✅ 保留 | 键名是 manifest 里的 `<Id>` |
| manifest 副本 | `%LOCALAPPDATA%\Microsoft\Office\16.0\Wef\xpath-excel-addin.manifest.xml` | ✅ 保留 | 换端口时会被改写 |
| 靶场工作簿 | `OFFICE\excel-addin\dist\Excel 靶场插件.xlsx` | ✅ 保留 | 每次启动都会重新生成 |
| **HTTPS 服务** | `https://localhost:7300` | ❌ **丢失** | 必须每次手动启动并保持终端开着 |

## 5. 怎么确认装好了

按顺序三条,任一条不过就照第 8 节排查:

```powershell
# ① 服务在跑,而且证书受信任(不要加 -k)
curl.exe -s -o NUL -w "%{http_code}`n" https://localhost:7300/src/taskpane.html
# 期望:200

# ② 加载项已注册到开发者目录(需要 Node)
npx office-addin-dev-settings registered
# 期望:7f3a9c21-4b8e-4d6a-9f10-2c5e8b7a4d31  …\Wef\xpath-excel-addin.manifest.xml

# ③ 打开靶场工作簿,看选项卡
```

不改动鼠标键盘、纯浏览器侧的完整交互验收(需要 Node 22+ 与本机 Chrome 或 Edge):

```powershell
# 终端 1
python tools\start_excel_addin.py --no-launch      # 只起服务
# 终端 2
node OFFICE\excel-addin\verify\verify-flow.mjs
```

脚本会真实点击走完失败密码、取消、登录、展开菜单、退出登录,断言 56 项并输出截图到
`OFFICE/excel-addin/verify/screenshot-*.png`。

## 6. 卸载

```powershell
python tools\stop_excel_addin.py               # 移除注册项 + manifest + 靶场工作簿 + localhost 证书
python tools\stop_excel_addin.py --keep-cert   # 保留证书, 只卸载加载项
python tools\stop_excel_addin.py --no-sideload # 只清证书, 不动加载项
```

## 7. 参数速查

| 参数 | 作用 |
|---|---|
| `--port 7300` | 换 HTTPS 端口(manifest 里的端口会被同步改写) |
| `--no-launch` | 只起服务,不自动打开靶场工作簿 |
| `--skip-sideload` | 只起服务,不注册加载项、不生成工作簿 |
| `--prepare-only` | 只做证书 / 注册 / 工作簿,不启动服务 |
| `--renew-cert` | 强制重建 localhost 证书 |

## 8. 故障排查

| 现象 | 处理 |
|---|---|
| Excel 里没有 `Excel 靶场插件` 选项卡 | ① 确认打开的是 `dist\Excel 靶场插件.xlsx`,不是空白工作簿;② 确认服务在跑(第 5 节 ①);③ 确认注册项存在(第 5 节 ②);④ 重启 Excel 后重新打开靶场工作簿 |
| 上面都对但选项卡仍不出现 | 开运行日志再试一次,然后搜插件 Id:<br>`npx office-addin-dev-settings runtime-log --enable D:\code\xpath\.private\addin-runtime-log.txt`<br>重开 Excel → 读日志里的 `SolutionId`。日志为空说明加载没报错 |
| `Wef` 缓存不一致(曾手动删过单个 manifest) | **完全退出 Excel** 后清空 `%LOCALAPPDATA%\Microsoft\Office\16.0\Wef\` 的**全部内容**(官方要求整体清,不要只删单个文件),再跑 `python tools\start_excel_addin.py --prepare-only`,然后重开 Excel |
| 任务窗格空白 / 显示旧内容 | 面板内右键 → 重新加载;服务已强制 `Cache-Control: no-store` |
| Excel 提示加载项来源不受信任 | `python tools\start_excel_addin.py --prepare-only --renew-cert`,它会重建证书并写入 `CurrentUser\Root` |
| 端口 7300 被占用 | `python tools\start_excel_addin.py --port 7301`(manifest 端口会同步改写) |
| 提示"证书私钥不是 CSP 密钥" | 证书是旧版本脚本建的:`python tools\start_excel_addin.py --prepare-only --renew-cert` |
| 卸载后证书仍在 Root 里 | `--keep-cert` 会保留;或手动 `certutil -user -delstore Root localhost` |
| 改了面板页面不生效 | 面板内右键 → 重新加载,不用重装 |
| 改了 Ribbon 文案 / 按钮 | 改 `manifest.xml` → 重跑 `--prepare-only` → 重开靶场工作簿 |

## 9. 自动化定位契约

关键元素同时带 `id` 与 `data-testid`,取值一致;建议优先用 `data-testid`。
文案固定,不使用随机类名,所有可交互元素都是 `<button>`。

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

## 10. 目录结构

```
OFFICE/excel-addin/
  manifest.xml                  Ribbon 选项卡 / 组 / 按钮 + 任务窗格入口(安装契约)
  src/taskpane.html|css|js      任务窗格与登录交互(改这里只需重新加载面板)
  src/commands.html|js          Ribbon 命令页占位(Office 运行时要求)
  assets/icon-16|32|80.png      按钮图标, 由 assets/generate_icons.py 生成
  verify/verify-flow.mjs        零依赖 CDP 端到端验收脚本
  verify/screenshot-*.png       验收截图
  dist/Excel 靶场插件.xlsx      安装时生成的靶场工作簿(已 gitignore)
  .certs/                       localhost 证书材料(已 gitignore)
tools/start_excel_addin.py      证书 + HTTPS 服务 + 注册 + 生成并打开靶场工作簿
tools/stop_excel_addin.py       卸载
```

## 11. 原理备忘(为什么长这样)

- **为什么必须有靶场工作簿**:桌面版 Excel 的旁加载加载项是文档级绑定的。注册表
  `WEF\Developer\<Id>` 只说明"上哪儿找 manifest",工作簿里的
  `<we:reference id="<Id>" store="developer" storeType="Registry" />` 才说明"这个文档要加载哪个加载项"。
  两者缺一不可。官方 `office-addin-dev-settings sideload` 同样是生成一个临时工作簿再打开它。
- **为什么不依赖 openssl / PowerShell 7**:证书用传统 CSP 提供程序创建,使
  `RSACryptoServiceProvider.ExportParameters` 在 .NET Framework 下可用(CNG 密钥不支持导出参数),
  再由 Python 编码成 PKCS#1 PEM(CPython 的 `ssl` 不支持直接读 PKCS#12)。
- **为什么用 `certutil` 而不是 `Import-Certificate` / `Remove-Item`**:非交互会话下对 Root 存储的
  增删会因 "UI is not allowed" 失败,`certutil -user -addstore / -delstore` 可以静默完成。
- **已知限制**:① 不是全局安装,选项卡只在靶场工作簿里出现;② 服务必须常驻;
  ③ 端口默认固定 7300。若要全局安装,需要"受信任目录 + 网络共享",创建共享需要管理员权限。
