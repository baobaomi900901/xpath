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
                     └─ TPanel「城市（单选）」
                        ├─ TStaticText「城市（单选）」
                        └─ THs08ComboBox
```

## 功能

- MDI 主窗体和 `TPageControl/TTabSheet`
- 参照 Win32 标准 UIA 版，每个表单 item 都有具名 `TPanel` 父容器，包含该字段的标签和控件
- 用户信息表单、VCL `THs08ComboBox` 单选下拉框、年龄微调（18–80，默认 25）
- 保存弹出“提交成功！”模态提示；重置恢复全部输入、单选和复选框默认值
- 原生“文件/编辑”顶部菜单
- 表单页动态 `TPopupMenu` 操作菜单
- 输入框右键菜单（撤销、剪切、复制、粘贴、全选）
- 表格页 `TListView`：1000 条数据，每页 100 条，共 10 页，显示 5 个动态页码，支持首页 / 上一页 / 页码 / 下一页 / 末页
- 拖拽测试、复制状态、销毁/重建 `drag-target`
- 原生 `TStringGrid`：100 行、7 列，固定 ID 列，支持编辑、键盘导航、调整列宽和恢复数据
- 原生 `TDBGrid`：1000 条内存数据，支持编辑 / 提交 / 取消、导航、姓名 / 城市 / 邮箱筛选、点击列头升序排序及恢复数据
- 真实 `TVirtualStringTree` 5.5.3：10 个部门、1000 名员工，按需创建子节点，支持展开 / 折叠、勾选、F2 编辑员工姓名及恢复数据
- `TcxGrid` / `TcxTreeList` 通过 `WITH_DEVEXPRESS` 条件编译；支持 Delphi 11 试用运行时包构建。TcxGrid 提供 1000 条数据及数值 ID 排序、编辑、分组、筛选和恢复；TcxTreeList 提供 10 个部门、1000 名员工及展开 / 折叠、编辑和恢复。未指定库时仍显示待接入说明。

`THs08ComboBox`、`TRzPanel` 是兼容类。没有安装 Raize Components 时，工程仍可使用标准 VCL 控件编译；它们的真实第三方 Provider 行为不等同于生产程序。

表单包含姓名、密码、邮箱、年龄、城市（单选）、城市（多选）、性别（单选）、兴趣爱好（多选）、备注、协议共 10 个 item。
城市的 5 个复选框共享“城市（多选）”父容器，兴趣的 4 个复选框共享“兴趣爱好（多选）”父容器，性别的 3 个单选按钮共享“性别（单选）”父容器。
这些容器在 UIA 树中显示为具名 Pane，字段标签使用有 HWND 的 `TStaticText`；按父节点查找相似控件时，两组复选框具有独立边界。
容器隐藏重复绘制的 Caption，仅通过标签显示字段名。表格采用 10 页、每页 100 条和 5 个动态页码。

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

默认命令行构建静态链接 VCL，不使用 Runtime Packages。运行默认 Release EXE 无需安装 Delphi。
`TDBGrid` 的内存数据集通过 `MidasLib` 静态链接，无需另装数据库或分发 `midas.dll`；修改不会写入外部数据库。
Virtual TreeView 的运行时源码和许可证保存在 `vendor/VirtualTreeView/`，版本来源及下载校验值见该目录说明。
允许提交默认版 `build/Release/Win32VclShootingRange.exe` 和评估版 `build/DevExpressTrial/Release/Win32VclShootingRange.exe`；Debug、DCU、BPL 和其余构建产物仍忽略。两个 EXE 使用不同目录，不会互相覆盖。更新对应程序时，重新构建该版本并提交对应 EXE。

## DevExpress 构建方式

默认 Release 保持不依赖 DevExpress。Delphi 11 评估版本输出到独立的 `build/DevExpressTrial/` 目录，实际创建 TcxGrid 和 TcxTreeList，不再显示待接入说明。
评估版本保留官方试用限制与提示。仓库仅放行本工程生成的评估版 Release EXE，DevExpress 试用库及 BPL 依赖不入库。该 EXE 仍用于具备匹配评估环境的本机测试，不是可直接分发运行的独立发布包；仅克隆仓库无法获得所需运行时依赖。

从 [DevExpress 官方试用下载页](https://www.devexpress.com/products/vcl/download-trial.xml)获取 Delphi 11 Alexandria 对应安装包，并按官方流程初始化试用环境。将 `Library/RS28` 目录传给构建脚本：

```powershell
.\DELPHI\build.ps1 -DevExpressTrialLibrary 'C:\Program Files (x86)\DevExpress\VCL\Library\RS28'
.\DELPHI\run.ps1 -DevExpressTrialLibrary 'C:\Program Files (x86)\DevExpress\VCL\Library\RS28' -SkipBuild
python .\tools\start_delphi.py --devexpress-trial-library 'C:\Program Files (x86)\DevExpress\VCL\Library\RS28'
```

也可设置 `DELPHI_DEVEXPRESS_TRIAL_LIBRARY` 环境变量。评估模式默认选择 Delphi 11（注册表 BDS 22.0），检查 RS28 DCP，并通过 Runtime Packages 链接；显式指定的编译器也必须匹配 Delphi 11。
此模式额外需要 Python 3 标准库，用 `package_runtime.py` 收集 EXE 的传递 BPL 依赖，生成 `runtime-manifest.json` 及本机评估说明。目录中保留 EXE 和全部 BPL 才能运行；缺少包时构建直接报错。
独立运行评估 EXE 时，如出现 DevExpress 官方试用提示，请先手动确认，主窗体随后打开。启动脚本报告进程已启动，不代表试用提示已确认。

- 评估 Release：`build/DevExpressTrial/Release/Win32VclShootingRange.exe`
- 评估 Debug：`build/DevExpressTrial/Debug/Win32VclShootingRange.exe`

提交评估版 EXE 时，在仓库根目录执行（无需 `git add -f`）：

```powershell
git add DELPHI/.gitignore DELPHI/README.md DELPHI/build/DevExpressTrial/Release/Win32VclShootingRange.exe
```

此命令不包含第三方运行时包；运行评估版时仍需按照前述构建步骤，从本机已安装的组件库收集匹配依赖。

2026-10-23 本机已安装官方 DevExpress 26.1.5 Delphi 11 评估组件，编译 Release / Debug，收集到 17 个 Win32 运行时包，并验证传递依赖及清单 SHA-256。
通过 Windows 调试器正常启动 Debug EXE 后，已实际检查两个真实控件、TcxGrid 姓名编辑与恢复、ID 数值排序（降序首条 1000，随后 999）、TcxTreeList 的 10 个部门、员工编辑与恢复、全部展开与折叠。
随后由用户确认官方试用提示，Release EXE 已在不附加调试器的情况下独立进入主界面，两个 DevExpress 页面及原生 UIA 节点已检查。确认提示前，组件可能停留在初始化消息循环，主窗体尚不显示；程序没有修改或关闭官方试用检查。

评估构建按 [DevExpress 官方 UIA 说明](https://docs.devexpress.com/VCL/dxUIAClasses.dxUIAutomationEnabled) 显式开启 `dxUIAutomationEnabled`，两个根节点分别命名为 `TcxGrid 员工表`、`TcxTreeList 部门员工树`。
已观察到原生行列、可编辑单元格和树节点。全部展开后，当前自动化工具的树快照偶有读取超时和缺少部分子树节点的现象；这部分仍需结合实际使用的自动化工具验收。

正式授权库静态构建仍使用以下方式：

取得与编译器版本匹配、支持静态链接的 DevExpress VCL 库后，指定各依赖单元所在目录：

```powershell
.\DELPHI\build.ps1 -DevExpressPaths 'D:\DevExpress\Library\Delphi2010', 'D:\DevExpress\Sources'
```

参数是单元搜索目录列表，不会递归搜索安装目录。也可将路径以分号分隔写入 `DELPHI_DEVEXPRESS_PATHS` 环境变量，再使用现有 Python 启动器。
构建脚本检查 `cxGrid.pas/.dcu` 和 `cxTL.pas/.dcu` 后启用 `WITH_DEVEXPRESS`；控件及其传递依赖都必须在指定路径内可见。
该模式要求对应的源码 / DCU；试用版只有 DCP / BPL，须使用上述 `-DevExpressTrialLibrary` 模式，不能用 `-DevExpressPaths` 替代。

## Delphi IDE 编译

1. 用 Delphi 打开 `Win32VclShootingRange.dpr`。
2. 目标平台选 Win32，关闭 Runtime Packages。
3. 将 `vendor/VirtualTreeView` 加入项目的 Unit / Resource 搜索路径。
4. Build Project，然后运行；IDE 输出目录由本地工程配置决定。

## GUI / UIA 验收

启动后检查原有功能与新增复杂控件页面：

1. **表单控件**：检查 10 个具名 Pane，各自包含字段标签和所属控件；年龄 Pane 包含输入框及微调按钮，城市多选和兴趣多选分属不同 Pane。输入与勾选后点击保存，应弹出“提交成功！”；重置后输入清空、年龄为 25、城市单选为北京、性别为男，所有城市 / 兴趣 / 协议复选框取消勾选。
2. **菜单**：顶部“文件 / 编辑”、表单“展开菜单”、输入框右键菜单均应弹出；选择后更新菜单状态文本。顶部菜单和自定义右键菜单用于菜单定位、点击及状态回显，当前不会打开文件或执行剪贴板编辑命令。
3. **表格数据**：7 列、1000 条员工样例数据，每页 100 条，共 10 页。程序启动默认第 1 页，底部显示当前页、总页数和记录范围；可点击首页、上一页、5 个动态页码、下一页、末页切换实际表格数据。第一页的首页 / 上一页禁用，最后一页的下一页 / 末页禁用，当前页的页码按钮禁用。页码初始为 1–5，选中第 3 页后更新为 2–6，第 4 页为 3–7，第 7–10 页固定为 6–10；按钮显示数字与跳转目标同步更新。第 1 页为 ID 1–100，第 10 页为 ID 901–1000，切换其他页签后保留当前表格页码。
4. **拖拽测试**：拖动 `drag-target`，位置及移动次数更新，目标保持在区域内；“隐藏”会销毁目标，“重置位置”会重新创建；“复制当前结果”将坐标和移动次数 JSON 写入剪贴板。
5. **TStringGrid**：第 1–100 行 ID 连续，ID 列固定且不可编辑；编辑姓名后状态栏回显，恢复数据后撤销编辑。
6. **TDBGrid**：初始为 1000 条；输入 `北京` 应筛出 200 条，输入不存在的关键字应为 0 条；清空恢复全部记录。可编辑姓名并通过导航器提交 / 取消；点击 ID 列头按数值排序，末条 ID 为 1000；恢复数据重新生成默认内容。
7. **TVirtualStringTree**：初始显示 10 个部门，展开每个部门得到 100 名员工；第一部门 ID 1–100，最后部门 ID 901–1000。选中姓名列按 F2 编辑，勾选及展开状态在底部回显；恢复数据清空修改与勾选，回到折叠状态。
8. **TcxGrid / TcxTreeList**：默认构建显示待接入说明。带 DevExpress 的构建应显示真实控件：TcxGrid 共 1000 条，ID 排序为数值顺序，编辑后可恢复；TcxTreeList 共 10 个部门、1000 名员工，全部展开 / 折叠和恢复应生效。

用 Inspect 或自己的 UIA / RPA 工具检查标准 VCL 控件和 MDI 层级。控件创建后赋予 Win32 control ID，供系统无障碍代理识别；实际 UIA 树和支持的 Pattern 由 Windows / VCL 代理决定，本工程没有自定义 UIA Provider。
DevExpress 26.1 评估构建使用库自身的 UIA Provider，其 `AutomationId` 由库生成，不能直接等同于下表的 Win32 control ID；建议用上述根节点名称和行列层级定位。

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
| 协议勾选 / 保存 / 重置 / 年龄微调 | 1006 / 1007 / 1008 / 1009 |
| 菜单状态 / 表单标题 | 1011 / 1012 |
| 10 个表单 item 容器（按上述字段顺序） | 4001–4010 |
| 10 个字段标签（与容器顺序一致） | 4101–4110 |
| 城市多选 / 性别单选 / 兴趣多选 | 4201–4205 / 4301–4303 / 4401–4404 |
| drag-target / 重置位置 / 复制当前结果 / 隐藏 | 2001 / 2002 / 2003 / 2004 |
| 员工表格 / 分页栏 / 页码与记录范围 | 3001 / 3002 / 3003 |
| 首页 / 上一页 / 下一页 / 末页 | 3004 / 3005 / 3006 / 3007 |
| 5 个页码槽位（从左到右，显示数字和跳转目标随当前页更新） | 3101–3105 |
| `TStringGrid` / 恢复 / 状态 | 6010 / 6011 / 6003 |
| `TDBGrid` / 筛选输入 / 恢复 / 导航器 / 状态 | 6110 / 6111 / 6112 / 6113 / 6103 |
| `TVirtualStringTree` / 全部展开 / 全部折叠 / 恢复 / 状态 | 6210 / 6211 / 6212 / 6213 / 6203 |
| DevExpress 可选页 / 表格或依赖说明 / 状态 | 6300、6400 / 6310、6410 / 6303、6403 |
| TcxGrid 恢复 / TcxTreeList 全部展开、全部折叠、恢复 | 6311 / 6411、6412、6413 |

2026-10-15 本机验证：Delphi 2010 的 Release / Debug、Delphi 10.3 的 Debug 编译通过；
Windows 桌面实际检查了主窗口、MDI / 表单 UIA ID、输入与重置、顶部菜单和动态菜单、表格页，以及拖拽、销毁和重建目标。
在当前 125% 显示缩放下检查了页面布局。菜单状态使用 `TStaticText`，可通过 UIA 读取；拖拽页的 `TLabel` 状态文本在当前系统 UIA 树中未暴露独立节点，需通过画面读取。
分页已在实际 Release 程序中验证：首页、上一页、页码跳转、下一页、末页均切换正确；
各页记录范围及首尾禁用状态正确，切换页签后保留当前页。
分页信息使用 `TStaticText`，当前系统可通过 UIA 读取页码、总数和记录范围。
5 个动态页码已实测：第三个槽位从“3”更新为“4”后跳转正确，尾部页码限制为 6–10，首页恢复 1–5。
每页 100 条版本已在实际 Release 程序中验证：第一页读取到连续且唯一的 ID 1–100，第二页显示范围 101–200，末页显示范围 901–1000，并确认第 1000 条记录的 7 列字段齐全；总数为 1000，首尾翻页按钮禁用状态正确。
表单分组已通过实际 UIA 树检查：10 个具名 Pane 的直接子节点均精确匹配各自的标签和控件；
城市与兴趣复选框可分别勾选，性别单选、年龄微调以及保存成功模态提示已实测。

2026-10-19 新增复杂控件构建验证：Delphi 2010 的 Release / Debug、Delphi 10.3 的 Debug 均编译通过。
Release 程序启动成功，已检查新增页签、DevExpress 待接入说明、TStringGrid 布局及其原生单元格编辑器。
界面自动化被用户按 Esc 停止，TStringGrid 编辑提交 / 恢复、TDBGrid 筛选 / 编辑以及虚拟树展开 / 勾选的实际交互验收尚未完成。
