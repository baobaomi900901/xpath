# Excel 插件靶场 — 设计文档

日期: 2026-09-17
状态: 已与用户确认(设计已批准,待实施)

## 1. 背景与目标

xpath 仓库目前有 WEB / WIN32 / JAVA / QT / DELPHI 等靶场,缺少 **Office 桌面插件** 这一类
宿主环境。本设计新增一个 Excel 桌面版可安装的 Office 加载项靶场,用于验证自动化在
"Excel Ribbon + WebView2 任务窗格" 这一形态下的定位与交互能力。

目标场景(用户原话拆解):

1. 在 Excel 中安装后,Excel 菜单(Ribbon)出现插件名 **Excel 靶场插件**。
2. 点击该插件的按钮,任务窗格打开,里面有一个 **点击登录** 按钮。
3. 点击后出现一个 **登录框**,可输入名称与密码。
4. 输入 `admin` / `1` 点击登录后:登录框消失,面板显示 **已登录**。
5. 原 "点击登录" 位置变为 **admin**,其右侧带一个小箭头。
6. 点击小箭头弹出菜单,含菜单项 **退出登录**。

## 2. 范围

**范围内**

- Office.js 任务窗格加载项(Add-in Commands 1.1 + VersionOverrides),仅面向 Excel 桌面版(Windows)。
- Ribbon 选项卡 / 组 / 按钮声明。
- 任务窗格内的登录弹窗、登录态、用户菜单、退出登录的完整交互。
- 本地 HTTPS 托管、localhost 证书、sideload 安装与卸载脚本。
- 供自动化使用的稳定元素契约(id / data-testid / aria)。

**范围外(非目标,YAGNI)**

- 真实后端鉴权、账号体系、网络请求;凭据在页面内硬编码校验(`admin` / `1`)。
- Excel 数据的读写(不调用 Excel JS API 操作工作簿)。
- Office on the Web、Mac Excel、Outlook/Word 版本。
- Office 商店发布、生产签名、CI 打包。
- 登录态跨会话持久化(见 §6)。

## 3. 组件与职责

```
OFFICE/excel-addin/           插件本体(静态资源,直接被 HTTPS 服务托管)
  manifest.xml                唯一的安装描述:Ribbon + 任务窗格入口
  src/taskpane.html           任务窗格页面骨架(元素契约的载体)
  src/taskpane.css            样式,含弹窗遮罩与下拉菜单
  src/taskpane.js             状态机:未登录 / 弹窗 / 已登录
  src/commands.html           命令页占位(Office 运行时必需)
  src/commands.js             Office.onReady 占位
  assets/icon-16.png          按钮图标(16/32/80)
  assets/icon-32.png
  assets/icon-80.png
tools/start_excel_addin.py    一站式启动:证书 → HTTPS 服务 → sideload → 可选拉起 Excel
tools/stop_excel_addin.py     卸载:sideload 移除 → 停服务 → 可选卸证书
```

各单元边界:

- `manifest.xml` 是**唯一的** Excel 侧契约。改 Ribbon 文案只需改这里,但必须重启 Excel 才生效。
- `src/*` 是纯静态资源,改完只需在任务窗格内刷新(右键 → 重新加载),不影响安装。
- `start_excel_addin.py` 不解析、不生成 manifest,只做"复制到 Wef 目录 + 起服务 + 校验"。
- `stop_excel_addin.py` 与 start 对称,确保可反复安装/卸载。

## 4. 部署与安装

### 4.1 托管

- 协议/地址: `https://localhost:7300`(WEB 靶场占用 7199,此处避让)。
- 服务实现: Python 标准库 `http.server` + `ssl.SSLContext`,只读托管 `OFFICE/excel-addin/`,
  并强制 `Cache-Control: no-store`(避免 WebView2 缓存旧页面干扰测试)。
- Office 桌面版要求加载项页面为 HTTPS,因此必须走证书流程。

### 4.2 localhost 证书(一次性,免管理员)

1. `New-SelfSignedCertificate -DnsName localhost -CertStoreLocation Cert:\CurrentUser\My`
2. 导出 PFX(带固定口令)到 `OFFICE/excel-addin/.certs/`(该目录加入 `.gitignore`)。
3. 将公钥导入 `Cert:\CurrentUser\Root` 建立信任(不需要管理员,PowerShell 导入不弹 UI 警告)。
4. 服务读取 PFX 启动 HTTPS。

脚本幂等:已存在且未过期的证书直接复用;`--renew-cert` 强制重建。

### 4.3 sideload(安装到 Excel)

- 将 `manifest.xml` 复制为 `%LOCALAPPDATA%\Microsoft\Office\16.0\Wef\<name>.xml`。
- 目录不存在则创建;已存在同名文件则覆盖。
- 写入后需**完全退出并重启 Excel**,Ribbon 才会出现新选项卡。
- 卸载即删除该文件,同样需重启 Excel 生效。

### 4.4 脚本 CLI

```
python tools/start_excel_addin.py [--port 7300] [--no-launch] [--renew-cert] [--skip-sideload]
python tools/stop_excel_addin.py  [--keep-cert] [--no-sideload]
```

- `start` 默认:确保证书 → 起 HTTPS 服务(前台,可 Ctrl+C) → sideload → 尝试拉起 Excel(已运行则提示手动重启)。
- `--no-launch` 只起服务和安装,不开 Excel(便于先做浏览器侧验证)。
- 输出必须包含:服务 URL、sideload 目标路径、下一步操作提示。

## 5. Ribbon 契约

| 项 | 值 |
|---|---|
| 选项卡 (Tab) | `Excel 靶场插件` (id `XPathRangeTab`) |
| 组 (Group) | `登录靶场` (id `XPathRangeGroup`) |
| 按钮 | `打开面板` (id `OpenTaskpaneButton`) |
| 按钮动作 | `ShowTaskpane`,打开 `src/taskpane.html` |
| 图标 | `assets/icon-16.png` / `32` / `80` |

## 6. 任务窗格交互契约

### 6.1 状态机

```
未登录 --点击"[点击登录]"--> 弹窗打开 --提交(admin/1)--> 已登录
   ^                              |                          |
   |                              | 提交(其他) -> 弹窗内报错,停留
   |                              | 取消/关闭 -> 未登录
   +----------点击"退出登录"-------------------------------+
```

- 登录态**不持久化**(不使用 localStorage / sessionStorage):每次打开任务窗格都是"未登录",
  保证自动化起点确定。
- 弹窗为**面板内自绘**:全屏遮罩 + 居中卡片,不使用 `displayDialogAsync`。
- 校验规则硬编码:`名称 === "admin" && 密码 === "1"` 为成功。
- 失败提示文案固定:`账号或密码错误`。
- 成功后:弹窗从 DOM 中移除(而非仅隐藏),状态区文案变为 `已登录`。

### 6.2 元素契约(自动化定位依赖,不得随意改动)

| id | data-testid | 角色/行为 | 文案 | 出现状态 |
|---|---|---|---|---|
| `login-trigger` | `login-trigger` | 按钮,打开登录弹窗 | `点击登录` | 未登录 |
| `login-dialog` | `login-dialog` | 登录弹窗容器 | — | 弹窗打开 |
| `username-input` | `username-input` | 文本输入 | — | 弹窗打开 |
| `password-input` | `password-input` | `type=password` 输入 | — | 弹窗打开 |
| `login-submit` | `login-submit` | 按钮,提交 | `登录` | 弹窗打开 |
| `login-cancel` | `login-cancel` | 按钮,关闭弹窗 | `取消` | 弹窗打开 |
| `login-error` | `login-error` | 错误文案节点 | `账号或密码错误` | 校验失败 |
| `login-status` | `login-status` | 状态文案节点 | `已登录` | 已登录 |
| `user-menu-trigger` | `user-menu-trigger` | 按钮,`admin` + 右侧箭头 `▾`,展开菜单 | `admin` | 已登录 |
| `user-menu` | `user-menu` | 下拉菜单容器 | — | 菜单展开 |
| `logout-item` | `logout-item` | 菜单项,退出登录 | `退出登录` | 菜单展开 |

约定:

- 所有可交互元素用 `<button>`(不用 `<div>` 绑事件),保证键盘/无障碍与自动化可点。
- 关键元素带 `aria-label` / `aria-expanded`(`user-menu-trigger`)。
- 输入框带 `<label for>` 关联。
- 不使用随机类名、不依赖顺序定位。

## 7. 错误处理

| 情况 | 行为 |
|---|---|
| 端口被占用 | 报错并提示 `--port` 换端口,退出码非 0 |
| 证书创建/导入失败 | 打印原始错误 + 提示改用 `--renew-cert`;不静默继续 |
| Wef 目录不可写 | 打印目标路径与权限提示,退出码非 0(服务仍保持运行,便于浏览器侧验证) |
| Excel 正在运行 | 不强制杀进程,提示"请完全退出 Excel 后重新打开" |
| 未安装 Excel | sideload 前检测,缺失则只起服务并给出说明 |
| 页面在浏览器中直接打开(非 Office 宿主) | `Office.onReady` 超时降级,交互照常可用(便于无 Excel 的自动化验证) |

## 8. 验证方案

1. **静态校验**:`manifest.xml` 可被 XML 解析;VersionOverrides 必需节点齐全;图标文件存在。
2. **服务探活**:`curl -k https://localhost:7300/src/taskpane.html` 返回 200 且内容含 `login-trigger`。
3. **浏览器端全流程**(不依赖 Excel):真实浏览器打开页面,依次 点击登录 → 输入 admin/1 → 登录 →
   断言 `login-dialog` 消失、`login-status` 文本为 `已登录`、`user-menu-trigger` 文本为 `admin` →
   点击箭头 → 断言 `user-menu` 可见且含 `退出登录` → 点击 → 断言回到 `login-trigger`。附截图。
4. **Excel 端**:sideload 后重启 Excel,用 UI Automation 枚举 Ribbon 选项卡名,确认存在
   `Excel 靶场插件`;截图/枚举结果作为证据。
5. **卸载验证**:`stop_excel_addin.py` 后 Wef 下 manifest 消失。

## 9. 风险与对策

| 风险 | 对策 |
|---|---|
| Excel 版本不支持 AddInCommands 1.1 | 先用脚本读取 Excel 版本;不支持则明确报错而非静默失败 |
| WebView2 缓存旧页面 | 服务端 `no-store` + 脚本提示"右键重新加载" |
| 自签证书被 WebView2 拒绝 | 证书导入 `CurrentUser\Root` 后用浏览器验证信任链,再 sideload |
| 沙箱阻止写入工作区外的 Wef 目录/证书库 | 一次性申请授权;失败则输出可手动执行的等价命令 |
| 默认口令被误认为真实凭据 | 明文硬编码、无任何外发请求,spec 与 README 中标注"仅靶场演示" |

## 10. 交付物

- `OFFICE/excel-addin/**` 插件本体
- `tools/start_excel_addin.py`、`tools/stop_excel_addin.py`
- `OFFICE/excel-addin/README.md` 安装/卸载/故障排查说明
