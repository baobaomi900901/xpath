# Win32 靶场

原生 Win32 C++ 桌面靶场，用于比较原生 UIA、纯 MSAA 和无内部无障碍树三种情况。五个程序都包含相同的表单与表格功能，其中 UIA 提供表单项有 Pane、无 Pane 和随机表单三个版本。

## 五个版本

### UIA 版

`win32-shooting-range-uia.exe` 使用标准 Win32 控件。Windows 为这些控件提供 UIA Provider，输入框、按钮、复选框和表格等元素可通过 UIA 的名称、AutomationId 和 Pattern 定位。

UIA 版还提供原生“文件/编辑”顶部菜单，以及表单页右上角的“展开原生菜单”按钮。按钮每次点击都会动态创建原生弹出菜单，关闭后销毁，可用于测试菜单项捕获、菜单关闭后的相似捕获启动及重新展开后的选择。MSAA 版使用相同类型的原生系统菜单；Canvas 版保留自绘菜单，以维持无内部无障碍树的边界。

### UIA 表单 item 无 Pane 版

`win32-shooting-range-uia-no-pane.exe` 与 UIA 版共用标准 Win32 控件源码，但不创建每个字段的 Pane。标签和控件直接位于“表单控件页”中，可用于对比城市和兴趣爱好复选框共享父容器时的相似元素查找。窗口标题为“Win32 靶场 - UIA (表单item 无 Pane)”。

### UIA 随机表单版

`win32-shooting-range-uia-random.exe` 基于 UIA 版，窗口标题为“Win32 靶场 - UIA (随机表单)”。每次启动随机排列十个表单字段，界面布局和 Pane 的节点顺序采用同一份启动配置。备注框始终保留多行高度，字段之间不会重叠。

所有通过程序创建的控件、标签和 Pane 都使用各自随机且唯一的 Win32 ID（原生 UIA 的 AutomationId 来源），自定义 Pane 的 ClassName 也在每次启动时随机变化。字段名称、选项含义、标准控件类型和原有功能保持一致，城市多选和兴趣多选仍位于各自的 Pane。随机配置在本次进程内固定，调整窗口大小、切换 Tab 和重置表单不会重新洗牌。

可以在交互菜单中选择“UIA 版（标准 Win32 控件_随机表单）”，或执行 `python .\tools\start_win32.py uia-random`。每次重新启动可用 Inspect 对比字段顺序、AutomationId、Pane ClassName 和位置的变化。

### MSAA 版

`win32-shooting-range-msaa.exe` 使用单个自绘 HWND 表现全部控件，通过 `WM_GETOBJECT(OBJID_CLIENT)` 暴露完整的 `IAccessible` 树：

- 不实现任何原生 UIA Provider
- 内部表单和表格元素只由 MSAA `IAccessible` 提供
- 十个表单字段各有具名的 `ROLE_SYSTEM_PANE` 父节点，包含各自的标签与控件
- Inspect 的 UIA 模式仍会通过 MSAA → UIA Proxy 显示内部树
- 桥接节点可通过 `IsLegacyIAccessiblePatternAvailable=true` 和 `LegacyIAccessible.*` 属性识别
- 提供 MSAA Name、Value、Role、State、Location、Focus 和 DefaultAction
- 表单输入、选择、保存/重置和表格分页可通过 MSAA 操作
- 使用原生 `HMENU` 提供“文件/编辑”顶部菜单，表单页“展开原生菜单”按钮通过 `TrackPopupMenuEx` 创建动态菜单；系统自动提供 MSAA 菜单节点

### 自绘版

`win32-shooting-range-canvas.exe` 与 MSAA 版共用自绘表单、表格和键盘/鼠标交互代码，但不暴露内部无障碍元素：

- 不实现内部 UIA Provider
- 不实现或返回内部 `IAccessible`/MSAA 树
- UIA 和 MSAA 客户端只能获得系统为顶层 HWND 提供的窗口外壳，看不到内部表单和表格
- 内部元素只能通过图像、坐标或程序私有接口操作
- 代码内部使用与 MSAA 版相同的表单 Pane 分组，但不向 Inspect 暴露这些节点
- 显示与 MSAA 版相同的自绘顶部菜单和动态弹出菜单，但不暴露对应的内部可访问节点

## 关闭 MSAA Proxy 的 UIA 检测工具

`uia-no-msaa-probe.exe` 是一个只读控制台工具。它从自己的 UIA 客户端 Proxy Factory Mapping 中移除最后的 MSAA Proxy，然后输出目标窗口根元素、全部 UIA 后代数量和客户区后代数量。该修改只影响工具自身，不影响 Inspect。

Windows 仍可能为标题栏、最小化、最大化和关闭按钮提供非客户区节点。判断内部表单/表格树是否可见时，以 `Client-area UIA descendant count` 和 `Client-area LegacyIAccessible descendant count` 为准；对 MSAA 版和自绘版，关闭 Proxy 后两者均为 `0`。

先启动目标窗口，再执行：

```powershell
# 默认检测“Win32 靶场 - MSAA Only”
.\WIN32\build\Release\uia-no-msaa-probe.exe

# 检测其他版本
.\WIN32\build\Release\uia-no-msaa-probe.exe --title "Win32 靶场 - Canvas Only"
```

## 功能

### Tab 1：表单控件

- 姓名、密码、邮箱输入框和年龄微调框
- 城市下拉单选（点击展开选项，选中、点击外部或按 `Esc` 后收起）、城市复选框组
- 性别单选框、兴趣爱好复选框组
- 多行备注、协议勾选
- **保存**：弹出模态提示“提交成功”
- **重置**：恢复表单初始值

UIA 版与 MSAA 版的每个表单字段都有独立的具名 Pane 父容器，包含该字段的标签及所属控件。例如，“城市（多选）”Pane 包含五个城市复选框，“兴趣爱好（多选）”Pane 包含四个兴趣复选框；按父容器查找相似元素时，两组选项可分别定位。自绘版只在内部模型中使用相同分组，UIA 表单 item 无 Pane 版则保留平铺结构。

### Tab 2：表格数据

- 1000 条模拟员工数据，共 7 列
- 每页 20 条
- 首页、上一页、页码、下一页、末页按钮

### Tab 3：拖拽测试

- `drag-target` 是 120×80 的可拖拽目标，初始位于拖拽区域中心
- 目标会被限制在拖拽区域内，“重置位置”可恢复到中心
- “隐藏 drag-target”会将目标从当前版本的内部元素树和可视界面中移除，“重置位置”会恢复目标并回到中心
- “复制当前结果”将当前拖拽状态以固定字段顺序的 JSON 写入 Unicode 剪贴板，状态文字显示复制成功或失败
- 显示当前 `left/top`、相对初始位移和本次拖拽的 `Δleft/Δtop`
- 记录按下锚点的局部坐标和九宫格区域
- 记录 `WM_MOUSEMOVE` 数量和拖拽耗时，可用于对比 `smooth`/`instant`、`simulative` 和 `move_speed`
- `delay_after` 是调用方在拖拽完成后的等待，靶场程序无法直接观测，需由调用方统计 `drag_to` 总耗时
- UIA 版使用名称为 `drag-target` 的原生按钮子窗口
- MSAA 版暴露名称为 `drag-target`、带 `STATE_SYSTEM_MOVEABLE` 的动态 `IAccessible` 节点
- Canvas 版提供相同的可视拖拽功能，但不暴露内部 UIA/MSAA 节点

## 环境要求

- Visual Studio 2019 或更高版本，并安装“使用 C++ 的桌面开发”工作负载
- CMake 3.20 或更高版本

## 构建与运行

### 独立 EXE 打包

在仓库根目录执行：

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\WIN32\package.ps1
```

脚本在 `WIN32/build/package` 中构建 x64 Release，运行不创建窗口的测试，并检查每个 EXE 的 DLL 依赖。C++ 运行库静态链接，分发后的程序无需 Python、Visual Studio 或 VC++ 运行库安装包，只依赖 Windows 系统 DLL。

产物位于 `WIN32/dist`，靶场 EXE 使用 `tools/start_win32.py` 的选项名称。每个 EXE 都可以单独复制到其他 Windows x64 机器运行：

| EXE | 内容 |
|---|---|
| `UIA 版（标准 Win32 控件）.exe` | UIA，有表单 item Pane |
| `UIA 版（标准 Win32 控件_表单item 无 Pane 版本）.exe` | UIA，无表单 item Pane |
| `UIA 版（标准 Win32 控件_随机表单）.exe` | UIA，启动时随机化表单 |
| `MSAA 版（仅 IAccessible）.exe` | MSAA，有表单 item Pane |
| `自绘版（无内部无障碍树）.exe` | 自绘，无内部无障碍树 |
| `UIA 压力靶场（500 层）.exe` | 固定 500 层，双击直接运行 |
| `UIA 压力靶场（1000 层）.exe` | 固定 1000 层，双击直接运行 |
| `UIA 压力靶场（2000 层）.exe` | 固定 2000 层，双击直接运行 |
| `UIA 压力靶场（通用版）.exe` | 通用压力版，可传入 500/1000/2000 参数 |
| `UIA 检测工具（禁用 MSAA Proxy）.exe` | 命令行 UIA 检测工具 |

同时生成 `win32-shooting-ranges-x64.zip`、使用说明 `README.txt` 和记录 SHA-256、文件大小及系统 DLL 依赖的 `manifest.json`。打包不会启动靶场窗口，产物、ZIP 和构建缓存均不纳入 Git。

### UIA 深度压力靶场

`win32-uia-pressure.exe` 只生成标准 Win32 UIA 元素树，不包含测试统计逻辑。通过参数选择嵌套深度：

```powershell
.\WIN32\build\Release\win32-uia-pressure.exe 500
.\WIN32\build\Release\win32-uia-pressure.exe 1000
.\WIN32\build\Release\win32-uia-pressure.exe 2000
```

每层是标准 Win32 `TreeView` 的嵌套 `TreeItem`，名称为 `uia-pressure-level-N`，父子关系形成单链；最后一层使用红色文字和浅红背景标识。

```powershell
cd D:\code\xpath

# 打开交互式多选菜单，可选择一个或多个版本
python .\tools\start_win32.py

# 非交互构建验证
python .\tools\start_win32.py --backends uia uia-no-pane uia-random msaa canvas --no-launch
```

交互菜单使用方向键移动焦点，按 `Enter` 或空格勾选版本；在“已完成选择”上按 `Enter` 后统一构建并同时启动所选版本。

也可以直接使用 PowerShell：

```powershell
cd .\WIN32
.\build.ps1
.\run.ps1 -Backend uia -SkipBuild
.\run.ps1 -Backend uia-no-pane -SkipBuild
.\run.ps1 -Backend uia-random -SkipBuild
.\run.ps1 -Backend msaa -SkipBuild
.\run.ps1 -Backend canvas -SkipBuild
```

生成的程序位于：

- `build\Release\win32-shooting-range-uia.exe`
- `build\Release\win32-shooting-range-uia-no-pane.exe`
- `build\Release\win32-shooting-range-uia-random.exe`
- `build\Release\win32-shooting-range-msaa.exe`
- `build\Release\win32-shooting-range-canvas.exe`
- `build\Release\uia-no-msaa-probe.exe`
