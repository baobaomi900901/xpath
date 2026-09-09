# Win32 靶场

原生 Win32 C++ 桌面靶场，用于比较原生 UIA、纯 MSAA 和无内部无障碍树三种情况。三个程序都包含相同的表单与表格功能。

## 三个版本

### UIA 版

`win32-shooting-range-uia.exe` 使用标准 Win32 控件。Windows 为这些控件提供 UIA Provider，输入框、按钮、复选框和表格等元素可通过 UIA 的名称、AutomationId 和 Pattern 定位。

UIA 版还提供原生“文件/编辑”顶部菜单，以及表单页右上角的“展开原生菜单”按钮。按钮每次点击都会动态创建原生弹出菜单，关闭后销毁，可用于测试菜单项捕获、菜单关闭后的相似捕获启动及重新展开后的选择。MSAA 版使用相同类型的原生系统菜单；Canvas 版保留自绘菜单，以维持无内部无障碍树的边界。

### MSAA 版

`win32-shooting-range-msaa.exe` 使用单个自绘 HWND 表现全部控件，通过 `WM_GETOBJECT(OBJID_CLIENT)` 暴露完整的 `IAccessible` 树：

- 不实现任何原生 UIA Provider
- 内部表单和表格元素只由 MSAA `IAccessible` 提供
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

```powershell
cd D:\code\xpath

# 打开交互式多选菜单，可选择一个或多个版本
python .\tools\start_win32.py

# 非交互构建验证
python .\tools\start_win32.py --backends uia msaa canvas --no-launch
```

交互菜单使用方向键移动焦点，按 `Enter` 或空格勾选版本；在“已完成选择”上按 `Enter` 后统一构建并同时启动所选版本。

也可以直接使用 PowerShell：

```powershell
cd .\WIN32
.\build.ps1
.\run.ps1 -Backend uia -SkipBuild
.\run.ps1 -Backend msaa -SkipBuild
.\run.ps1 -Backend canvas -SkipBuild
```

生成的程序位于：

- `build\Release\win32-shooting-range-uia.exe`
- `build\Release\win32-shooting-range-msaa.exe`
- `build\Release\win32-shooting-range-canvas.exe`
- `build\Release\uia-no-msaa-probe.exe`
