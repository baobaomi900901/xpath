# Win32 靶场

原生 Win32 C++ 桌面靶场，用于比较原生 UIA、纯 MSAA 和无内部无障碍树三种情况。三个程序都包含相同的表单与表格功能。

## 三个版本

### UIA 版

`win32-shooting-range-uia.exe` 使用标准 Win32 控件。Windows 为这些控件提供 UIA Provider，输入框、按钮、复选框和表格等元素可通过 UIA 的名称、AutomationId 和 Pattern 定位。

### MSAA 版

`win32-shooting-range-msaa.exe` 使用单个自绘 HWND 表现全部控件，通过 `WM_GETOBJECT(OBJID_CLIENT)` 暴露完整的 `IAccessible` 树：

- 不实现任何原生 UIA Provider
- 内部表单和表格元素只由 MSAA `IAccessible` 提供
- Inspect 的 UIA 模式仍会通过 MSAA → UIA Proxy 显示内部树
- 桥接节点可通过 `IsLegacyIAccessiblePatternAvailable=true` 和 `LegacyIAccessible.*` 属性识别
- 提供 MSAA Name、Value、Role、State、Location、Focus 和 DefaultAction
- 表单输入、选择、保存/重置和表格分页可通过 MSAA 操作

### 自绘版

`win32-shooting-range-canvas.exe` 与 MSAA 版共用自绘表单、表格和键盘/鼠标交互代码，但不暴露内部无障碍元素：

- 不实现内部 UIA Provider
- 不实现或返回内部 `IAccessible`/MSAA 树
- UIA 和 MSAA 客户端只能获得系统为顶层 HWND 提供的窗口外壳，看不到内部表单和表格
- 内部元素只能通过图像、坐标或程序私有接口操作

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
- 城市下拉单选、城市复选框组
- 性别单选框、兴趣爱好复选框组
- 多行备注、协议勾选
- **保存**：弹出模态提示“提交成功”
- **重置**：恢复表单初始值

### Tab 2：表格数据

- 1000 条模拟员工数据，共 7 列
- 每页 20 条
- 首页、上一页、页码、下一页、末页按钮

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
