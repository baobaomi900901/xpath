# Delphi VCL UIA 靶场

这是一个面向 Delphi 2010 的无 DFM VCL 示例工程，用于模拟真实 Delphi/VCL 程序的 UIA 树形结构。

## 目标结构

```text
TMainForm
└─ MDIClient
   └─ TLayoutForm
      └─ TLayoutPanel
         └─ TPageControl
            └─ TTabSheet
               └─ TfrmETFDate
                  └─ TRzPanel（本工程用兼容 TPanel 模拟）
                     └─ THs08ComboBox
```

## 功能

- MDI 主窗体和 `TPageControl/TTabSheet`
- 用户信息表单、VCL `THs08ComboBox` 单选下拉框
- 原生“文件/编辑”顶部菜单
- 表单页动态 `TPopupMenu` 操作菜单
- 输入框右键菜单（撤销、剪切、复制、粘贴、全选）
- 表格页 `TListView`
- 拖拽测试、复制状态、销毁/重建 `drag-target`

`THs08ComboBox`、`TRzPanel` 是兼容类。没有安装 Raize Components 时，工程仍可使用标准 VCL 控件编译；它们的真实第三方 Provider 行为不等同于生产程序。

## 一键构建与启动

在仓库根目录执行，Python 仅使用标准库：

```powershell
python .\tools\start_delphi.py                       # Release 构建并打开窗口
python .\tools\start_delphi.py --no-launch           # 只构建并检查产物
python .\tools\start_delphi.py --skip-build          # 直接运行已有 EXE
python .\tools\start_delphi.py --configuration Debug # Debug 构建并启动
python .\tools\start_delphi.py --help
```

也可以直接使用 PowerShell，无需 Python：

```powershell
.\DELPHI\build.ps1
.\DELPHI\run.ps1
.\DELPHI\run.ps1 -SkipBuild
.\DELPHI\build.ps1 -Configuration Debug
```

构建脚本优先从注册表查找 Delphi 2010，其次使用 PATH 中的 `dcc32.exe`。
也可通过环境变量 `DELPHI_DCC32`、PowerShell 参数 `-CompilerPath` 或启动器参数指定编译器：

```powershell
python .\tools\start_delphi.py --no-launch --compiler-path 'C:\Program Files (x86)\Embarcadero\RAD Studio\7.0\bin\dcc32.exe'
```

脚本支持 Delphi 2010 的旧版 VCL 库路径和新版 Delphi 的 `lib/win32/release`、单元命名空间。
编译依赖已安装且可用的 Delphi Win32 编译器及 VCL；脚本不下载或安装 Delphi。
脚本显式按 UTF-8 读取源码；源码也保留 UTF-8 BOM，方便在 Delphi IDE 中打开中文。
若 EXE 正在运行，请先关闭对应窗口再重新构建。

产物：

- Release：`DELPHI/build/Release/Win32VclShootingRange.exe`
- Debug：`DELPHI/build/Debug/Win32VclShootingRange.exe`
- DCU：各配置输出目录的 `dcu/` 子目录

命令行构建静态链接 VCL，不使用 Runtime Packages。运行已有 EXE 无需安装 Delphi。
允许提交 `build/Release/Win32VclShootingRange.exe`，方便直接运行；其余构建产物和 IDE 临时文件仍忽略。更新发布程序时，重新构建 Release 并提交对应 EXE。

## Delphi IDE 编译

1. 用 Delphi 打开 `Win32VclShootingRange.dpr`。
2. 目标平台选 Win32，关闭 Runtime Packages。
3. Build Project，然后运行；IDE 输出目录由本地工程配置决定。

## GUI / UIA 验收

启动后检查三个页面：

1. **表单控件**：输入姓名、密码、邮箱、年龄和备注；选择城市、复选框、单选框；点击保存、重置并观察状态。
2. **菜单**：顶部“文件 / 编辑”、表单“展开菜单”、输入框右键菜单均应弹出；选择后更新菜单状态文本。顶部菜单和自定义右键菜单用于菜单定位、点击及状态回显，当前不会打开文件或执行剪贴板编辑命令。
3. **表格数据**：7 列、100 行员工样例数据，可选择行、滚动并读取单元格。
4. **拖拽测试**：拖动 `drag-target`，位置及移动次数更新，目标保持在区域内；“隐藏”会销毁目标，“重置位置”会重新创建；“复制当前结果”将坐标和移动次数 JSON 写入剪贴板。

用 Inspect 或自己的 UIA / RPA 工具检查标准 VCL 控件和 MDI 层级。控件创建后赋予 Win32 control ID，供系统无障碍代理识别；实际 UIA 树和支持的 Pattern 由 Windows / VCL 代理决定，本工程没有自定义 UIA Provider。

| 控件 | Win32 control ID |
|---|---:|
| MDI 子窗体 | 65280 |
| `TLayoutPanel` | 1508682 |
| `TPageControl` | 2688164 |
| 表单页 `TTabSheet` | 14092350 |
| `TfrmETFDate` | 3278048 |
| `TRzPanel` | 23332742 |
| 姓名 / 密码 / 邮箱 / 年龄 / 备注 | 1001 / 1002 / 1003 / 1004 / 1005 |
| `THs08ComboBox` 城市单选 | 2555932 |
| 展开菜单 | 1010 |
| drag-target / 重置位置 / 复制当前结果 / 隐藏 | 2001 / 2002 / 2003 / 2004 |

2026-10-15 本机验证：Delphi 2010 的 Release / Debug、Delphi 10.3 的 Debug 编译通过；
Windows 桌面实际检查了主窗口、MDI / 表单 UIA ID、输入与重置、顶部菜单和动态菜单、表格页，以及拖拽、销毁和重建目标。
在当前 125% 显示缩放下检查了页面布局。`TLabel` 状态文本在当前系统 UIA 树中未暴露独立节点，需通过画面读取。
