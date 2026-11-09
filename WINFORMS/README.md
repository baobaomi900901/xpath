# WinForms GUI 自动化靶场

一个可独立编译运行的 C# / WinForms 桌面靶场，用同一个主窗体提供两套完全不同的 UI 架构：

| Tab | 架构 | 训练目标 |
|---|---|---|
| **Tab 1 · 标准控件靶场** | 原生 WinForms 控件 | UIAutomation 树、AutomationId、Enabled 状态、模态窗口、表格排序 |
| **Tab 2 · 地狱自绘靶场** | 单个纯 GDI+ `Panel` | 截图、OCR、模板匹配、坐标点击、键盘输入、悬停菜单 |

项目目标框架为 **.NET Framework 4.8.1**，使用经典 `.csproj`，不依赖 NuGet 包。

---

## 1. 构建与运行

前置条件：

- Windows 10 / 11
- .NET Framework 4.8.1 运行时
- Visual Studio 2022 或更高版本的 MSBuild，并安装 .NET 桌面开发 / .NET Framework 4.8.1 targeting pack

### 从统一启动中心启动（推荐）

`tools/ranges.json` 已加入 `winforms` 靶场：

```powershell
uv run .\tools\start.py
```

在启动中心选择 **WinForms 标准 + 自绘**，然后按需选择：

| Profile | 行为 |
|---|---|
| 构建并启动 | Release 构建后打开靶场窗口 |
| 仅运行已有 EXE | 跳过构建；若产物不存在会自动构建 |
| 构建（不启动） | 只构建 Release 产物，适合流水线检查 |

启动中心默认在后台打开界面；需要查看启动日志时使用：

```powershell
uv run .\tools\start.py --foreground
```

校验全部靶场配置和默认命令（不会打开窗口）：

```powershell
uv run .\tools\start.py --check
```

### 直接运行

在仓库根目录执行：

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\WINFORMS\build.ps1 -Configuration Release
.\WINFORMS\bin\Release\GuiAutomationRange.exe
```

也可以直接构建并启动：

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\WINFORMS\run.ps1
```

只构建不启动：

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\WINFORMS\run.ps1 -NoLaunch
```

如果本机只安装了 v4.8 targeting pack，请把 `GuiAutomationRange.csproj` 中的：

```xml
<TargetFrameworkVersion>v4.8.1</TargetFrameworkVersion>
```

改为 `v4.8`。项目没有使用 4.8.1 独有 API。

---

## 2. 目录结构

```text
WINFORMS/
├─ GuiAutomationRange.csproj      经典 .NET Framework WinForms 工程
├─ app.manifest                   asInvoker + System DPI awareness
├─ build.ps1                      MSBuild 自动定位与构建脚本
├─ run.ps1                        构建（可选）并启动
├─ README.md
└─ src/
   ├─ Program.cs                  应用入口与未处理异常提示
   ├─ MainForm.cs                 TabControl 主窗体
   ├─ StandardRangePage.cs        Tab 1：全部原生标准控件
   ├─ ConfirmDeleteDialog.cs      Tab 1：自定义模态确认框
   ├─ CanvasRangePanel.cs         Tab 2：纯 GDI+ 自绘与事件拦截
   └─ TestData.cs                 全部假数据与测试常量
```

---

## 3. Tab 1：标准控件靶场

### 模块 1 · 复杂登录表单

- `TextBox` 账号
- `TextBox` 密码，`PasswordChar = '*'`
- `ComboBox` 环境选择（DropDownList）
- `CheckBox` 记住密码
- `Button` 登录
- 实时登录结果 `Label`

测试账号：

```text
admin / Admin@123
```

环境任选；账号或密码错误、空值都会给出不同状态文字。支持在账号/密码框按 `Enter` 提交。

### 模块 2 · 异步加载区域

点击 **查询数据** 后：

1. `btnQuery.Enabled` 立即变为 `false`
2. `ProgressBar` 从 0 运行到 100
3. 3 秒后按钮恢复，`lblQueryStatus` 文本变为 **查询成功**
4. `lblQueryResult` 显示返回 10 条测试记录

适合测试 `Invoke` 后的 Enabled 状态轮询、进度条 Pattern、固定等待与条件等待。

### 模块 3 · 多级弹窗

1. 点击 **删除记录...**
2. 打开自定义 `ConfirmDeleteDialog`（标准 `Form.ShowDialog`）
3. 点击 **确认删除** 后，再弹出一个标准 `MessageBox` 成功提示
4. 取消第一层则不会出现成功提示

确认框按钮也有稳定的 `AutomationId`，可单独练习嵌套窗口切换。

### 模块 4 · 标准数据表格

- 原生 `DataGridView`
- 10 行、7 列假数据
- 所有列可点击表头升 / 降序
- 表头显示排序箭头
- 10 行数据全部存在；在高 DPI / 大字体环境下若出现标准滚动条，可滚动查看全部行

### Tab 1 关键 AutomationId

| 控件 | AutomationId | 说明 |
|---|---|---|
| 账号 | `txtAccount` | Edit / ValuePattern |
| 密码 | `txtPassword` | Edit，密码遮罩 |
| 环境 | `cmbEnvironment` | ComboBox |
| 记住密码 | `chkRemember` | CheckBox |
| 登录 | `btnLogin` | InvokePattern |
| 清空登录 | `btnClearLogin` | InvokePattern |
| 登录结果 | `lblLoginResult` | Text |
| 查询 | `btnQuery` | 点击后禁用 3 秒 |
| 进度条 | `prgQuery` | ProgressBar |
| 查询状态 | `lblQueryStatus` | 完成时为“查询成功” |
| 删除记录 | `btnDelete` | 打开模态确认框 |
| 确认删除 | `btnConfirmDelete` | 自定义对话框中 |
| 取消删除 | `btnCancelDelete` | 自定义对话框中 |
| 重置删除列表 | `btnResetDelete` | 恢复演示记录 |
| 表格 | `dgvRecords` | DataGridView |
| 运行日志 | `lstEventLog` | ListBox |

登录表单、查询和删除操作都会向运行日志追加时间戳记录。

---

## 4. Tab 2：地狱自绘靶场

### 4.1 无标准控件 / 无辅助功能语义

Tab 2 的页面内只有一个 `CanvasRangePanel`：

- **0 个子控件**
- 不设置任何 `AccessibleName`
- 不设置任何 `AccessibleRole`
- 不创建隐藏的 TextBox / Button / Label / Timer 句柄
- 所有可见内容都在 `OnPaint` 中用 `Graphics` 绘制
- 所有鼠标与键盘交互在 `OnMouseDown` / `OnMouseUp` / `OnMouseMove` / `OnKeyDown` / `OnKeyPress` / `OnMouseWheel` 中手写

用 Inspect.exe、Spy++ 或 UIAutomation 查看时，Tab 2 内部只能看到这个空 Panel。

### 4.2 场景 1 · 自绘登录框

- 自绘边框、标签、输入框和登录按钮
- 点击账号 / 密码 / 验证码输入框后获得焦点
- 支持字符输入、`Backspace` 退格、`Tab` 切换字段、`Enter` 登录
- 光标以 530 ms 间隔闪烁
- 密码以 `*` 遮罩
- 固定验证码 **A8B9**，带随机角度字符、干扰线和椭圆噪声
- 登录成功条件：

```text
账号：admin
密码：Admin@123
验证码：A8B9（大小写不敏感）
```

### 4.3 场景 2 · 自绘数据表格

- 5 行 × 3 列
- 表头：`订单号` / `状态` / `金额`
- 网格线、交替行背景、状态颜色全部由 GDI+ 绘制
- 没有 DataGridView、ListView 或任何可访问子节点
- 数据只能通过 OCR 或截图比对读取
- 翻页后表格数据与日志内容同时刷新

### 4.4 场景 3 · 分页与自定义滚动条

- 完全自绘的 `上一页` / `下一页` 按钮
- 当前页 `PAGE 01 / 03`
- 20 行日志内容，可滚轮滚动
- 自绘滚动条：上下箭头、轨道、滑块
- 支持拖动滑块、点击轨道翻页、点击箭头单行滚动
- 切换分页会刷新表格和日志

### 4.5 场景 4 · 动态悬浮菜单

顶部绘制 **文件 / 编辑 / 帮助** 三个热区：

- 鼠标悬停热区 → 在其下方弹出矩形菜单
- 鼠标离开热区与菜单区域 → 菜单消失
- 菜单项有 Hover 高亮，可点击执行
- 文件：重置会话、随机化坐标、退出程序
- 编辑：复制账号、粘贴账号、清空事件日志
- 帮助：快捷键说明、关于靶场

---

## 5. 防作弊 / 反脆弱机制

### 5.1 坐标随机化 ±30 px

- 每次进程启动时，所有自绘输入框、主按钮、分页按钮、主题按钮、菜单热区都会获得独立的随机偏移
- 水平 / 垂直偏移范围均为 `[-30, +30]` 像素
- 偏移会被限制在卡片边界内，避免控件跑出画布
- 按 `F5` 或点击 **随机布局** 可重新随机化
- 同一进程内窗口缩放不会重新随机化，布局仍使用同一组偏移

### 5.2 视觉防抖 300 ms

所有带文字的自绘按钮（登录、上一页、下一页、切换主题、随机布局）执行流程：

1. `MouseDown` 开始按钮颜色渐变
2. 渐变进度为 `elapsed / 300ms`
3. 只有在按钮内按住 **至少 300 ms** 后释放，才执行点击动作
4. 提前释放会被取消，并显示“视觉防抖拦截：只按住了 xxx ms”
5. 按下后移出按钮再释放也会取消

自动化脚本必须使用 `mouse_down` → `sleep(0.35)` → `mouse_up`，或对应的 `click_and_hold`。

菜单项不使用 300 ms 防抖，点击立即生效。

### 5.3 主题干扰

点击 **切换主题 F2** 或按 `F2`：

- 亮色 / 暗色主题即时切换
- 背景、卡片、边框、文字、按钮、表格、日志颜色全部变化
- 布局坐标不变，但颜色特征完全改变
- 适合测试模板匹配、颜色阈值和截图差异算法

### 5.4 快捷键

| 快捷键 | 功能 |
|---|---|
| `F2` | 切换亮色 / 暗色主题 |
| `F5` | 重新随机化坐标 |
| `Tab` / `Shift+Tab` | 切换自绘输入焦点 |
| `Backspace` | 删除当前输入框末字符 |
| `Enter` | 登录 |
| `Esc` | 清除输入焦点与悬浮菜单 |
| `Ctrl+V` | 粘贴到当前输入框 |
| 鼠标滚轮 | 滚动自绘日志 |

---

## 6. 假数据

- 标准表格：10 条员工记录，7 列
- 自绘表格：3 页 × 5 行 × 3 列订单记录
- 自绘日志：3 页 × 20 行
- 删除演示：4 条待删除记录，可循环重置
- 登录：`admin / Admin@123`，验证码 `A8B9`

所有数据集中在 `src/TestData.cs`，便于自动化脚本对照。

---

## 7. 人工测试清单

### Tab 1

- [ ] 空账号或空密码点击登录 → 出现错误提示
- [ ] `admin / Admin@123` → 登录成功
- [ ] 勾选“记住密码”后登录 → 成功文字包含“已记住本次运行”
- [ ] 点击查询 → 按钮立即禁用，进度条走 3 秒，最后显示“查询成功”
- [ ] 查询过程中再次点击 → 没有并发查询
- [ ] 点击删除 → 确认框 → 取消 → 只关闭第一层
- [ ] 点击删除 → 确认 → 出现删除成功 MessageBox → 下一条记录前移
- [ ] 删除到没有记录 → 删除按钮禁用；重置列表后恢复
- [ ] 连续点击表头 → 升序 / 降序切换，排序箭头正确
- [ ] 10 行数据全部存在；高 DPI 下若出现滚动条可滚动查看

### Tab 2

- [ ] 用 Inspect / Spy++ 查看 Tab 2 → 内部只有空 Panel，没有子控件
- [ ] 点击账号框 → 出现闪烁光标 → 输入字符
- [ ] 输入后按 Backspace → 删除末字符
- [ ] 密码框 → 显示 `*` 遮罩
- [ ] 输入验证码 A8B9（大小写均可）→ 登录成功
- [ ] 输入错误验证码 → 错误提示
- [ ] 快速点击登录（<300 ms）→ 操作被拒绝
- [ ] 按住登录 ≥300 ms 后释放 → 执行登录
- [ ] 点击下一页 → 页码、表格 5 行、日志内容同时变化
- [ ] 拖动自绘滚动条滑块 / 点击轨道 / 滚轮 → 日志滚动
- [ ] 鼠标悬停“文件 / 编辑 / 帮助” → 菜单出现；移出 → 菜单消失
- [ ] 点击菜单项 → 对应动作生效
- [ ] 按 F5 → 输入框和按钮位置改变
- [ ] 按 F2 → 主题切换，截图颜色特征变化
- [ ] 重启程序 → 控件位置与上次不同

---

## 8. 说明

- 临时截图与验证产物可放在 `WINFORMS/artifacts/`，该目录已在本地 `.gitignore` 中忽略。
- `bin/`、`obj/` 为构建产物，不纳入版本控制。
- 本项目面向主动授权的 GUI 自动化研究与靶场测试，不包含绕过任何生产系统安全控制的功能。
