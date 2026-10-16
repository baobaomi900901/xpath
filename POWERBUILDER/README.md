# PowerBuilder 桌面靶场

参考 Win32 靶场，使用 PowerBuilder 原生控件、Tab、Menu 和 DataWindow 实现。三个页面分别用于表单、表格分页和拖拽测试。数据在内存中生成，无需数据库。

## 单文件 EXE

打包产物为 `POWERBUILDER/dist/PowerBuilder靶场.exe`。将这一个文件复制到 Windows 10 / 11 电脑后双击运行即可，无需安装 Python、PowerBuilder 或 VC++ Runtime。

EXE 内含 x86 应用、匹配的 PowerBuilder Runtime 25.0.0.3683、VC++ 运行库及许可文件。启动时解压到当前用户的 `%TEMP%/PowerBuilderRange-{GUID}`，正常关闭应用后清理该目录，无需管理员权限。

向其他人分发时，可使用 `dist/PowerBuilder靶场-便携包.zip`。解压整个目录并保留目录结构，然后在解压目录执行：

```powershell
python .\tools\start_powerbuilder.py
# 或直接启动单文件 EXE：
python .\tools\start_powerbuilder.py --mode exe
```

运行脚本需要 Python 3.8+；在菜单中选择“启动 EXE”不需要安装 PowerBuilder。便携包同时带有 `tools/start_win32.py`，用于启动菜单的按键和颜色。手动复制文件时必须带上它，并将 EXE 保留在 `POWERBUILDER/dist/PowerBuilder靶场.exe`，与 `tools/` 同属一个根目录。便携包包含 PowerScript 源码；开发模式另需下文的匹配编译环境。

在仓库根目录重新打包：

```powershell
python .\tools\package_powerbuilder.py
```

打包机需要下文所列的 Utilities / Runtime，以及 Visual Studio C++ x86 构建工具；压缩使用 Windows 自带的 `makecab.exe`。构建使用独立目录 `build/package/`，完成自检后才发布到 `dist/`。同目录的 `manifest.json` 记录 SHA-256、文件清单和自检结果，运行 EXE 不需要此文件。

打包时会将单个 EXE 复制到含中文和空格的独立目录，将 PATH 限制为 Windows 系统目录，再检查实际加载的 PBVM 来自本次解压目录、3093 项应用自检通过及退出后的目录清理。也可手动运行命令行自检：

```powershell
Start-Process -FilePath '.\POWERBUILDER\dist\PowerBuilder靶场.exe' `
  -ArgumentList '--self-test --report package-self-test.json' -Wait
Get-Content .\package-self-test.json -Encoding UTF8
```

## 启动

在仓库根目录运行启动菜单：

```powershell
cd D:\code\xpath
python .\tools\start_powerbuilder.py
```

菜单参考 Win32 启动器，并共用其按键读取、颜色和终端配置：上下方向键移动，`Enter` 或空格选择 / 取消选择，在 `[ 已完成选择 ]` 上按 `Enter` 启动，`Esc` 取消。两种模式保持单选，选中项以绿色勾选标记显示。

`1. 启动 EXE` 直接运行 `dist/PowerBuilder靶场.exe`，无需编译器或已安装的 Runtime；`2. 开发模式` 从 `src/` 重新编译并启动。非交互终端请使用下面的 `--mode` 参数。

也可以跳过菜单，直接指定模式：

```powershell
python .\tools\start_powerbuilder.py --mode exe  # 启动打包好的单文件 EXE
python .\tools\start_powerbuilder.py --mode dev  # 从源码编译并启动
```

已构建过时，可直接运行现有程序：

```powershell
python .\tools\start_powerbuilder.py --skip-build
```

其他命令：

```powershell
python .\tools\start_powerbuilder.py --no-launch               # 只编译，不打开窗口
python .\tools\start_powerbuilder.py --skip-build --self-test  # PB 自检，完成后关闭自身窗口
python .\tools\start_powerbuilder.py --skip-build --no-launch  # 检查现有产物及 Runtime
python .\tools\start_powerbuilder.py --help
```

原有命令行参数默认使用开发模式，不显示菜单。`--no-launch` 和 `--self-test` 也支持与 `--mode exe` 一起使用；`--skip-build`、`--tools-path`、`--runtime-path` 仅用于开发模式。

编译会覆盖本靶场的生成文件；已有窗口运行时，请先关闭该窗口，再重新构建。启动器不会结束用户进程。完整桌面交互由使用者人工测试，不使用 OCR。

## 环境

- Windows 10 / 11；生成 x86 Pcode 应用，可在相应的 Windows x86/x64 环境运行。
- Python 3.8+，启动器只使用标准库。
- **PowerBuilder Utilities 2025 GA 25.0.0.3683**，包含 `orcascr250.exe`；编译工具无需 IDE 许可证。
- **PowerBuilder Runtime 25.0.0.3683**，须包含可访问性 DLL。Utilities 和 Runtime 版本需匹配。

本次已安装的位置：

```text
C:\Program Files (x86)\Appeon\PowerBuilderUtilities 25.0
C:\Program Files (x86)\Appeon\Common\PowerBuilder\Runtime 25.0.0.3683
```

默认从注册表发现安装目录，也可显式指定：

```powershell
python .\tools\start_powerbuilder.py `
  --tools-path 'C:\Program Files (x86)\Appeon\PowerBuilderUtilities 25.0' `
  --runtime-path 'C:\Program Files (x86)\Appeon\Common\PowerBuilder\Runtime 25.0.0.3683'
```

环境变量为 `POWERBUILDER_TOOLS`、`POWERBUILDER_RUNTIME`。`--skip-build` 不调用编译器，但仍验证运行时；可用 `--skip-build --runtime-path ...` 更新运行时路径。

2025 GA 的[官方系统要求](https://www.appeon.com/system/files/product-readme/PowerBuilder%202025%20GA%203683%20Readme.htm)包含 Windows 10；本工程固定该 GA 版本。官方[命令行构建说明](https://docs.appeon.com/pb2025/pbug/Tutorial_Building_your_PowerClient_project_with_commands.html)说明 Utilities 可独立运行，无需 IDE 许可证。本次安装未安装 IDE、PowerServer 或数据库。

## 表单控件

| 项目 | PB 控件 | 初始值 |
|---|---|---|
| 姓名 | SingleLineEdit `sle_name` | 空 |
| 密码 | SingleLineEdit `sle_password`，Password=true | 空 |
| 邮箱 | SingleLineEdit `sle_email` | 空 |
| 年龄 | EditMask `em_age`，数字微调，范围 0–150 | 25 |
| 城市（单选） | DropDownListBox `ddlb_city` | 北京 |
| 城市（多选） | 五个 CheckBox `cb_city1`–`cb_city5` | 全未选 |
| 性别（单选） | 三个 RadioButton | 男 |
| 兴趣爱好（多选） | 四个 CheckBox `cb_hobby1`–`cb_hobby4` | 全未选 |
| 备注 | MultiLineEdit `mle_remark` | 空 |
| 协议 | CheckBox `cb_agree` | 未勾选 |

城市选项：北京、上海、广州、深圳、杭州。兴趣选项：阅读、运动、音乐、旅行。保存会弹出“提交成功”，重置恢复初始值。

顶部提供“文件 / 编辑”菜单；表单“展开原生菜单”每次创建一个 PB Menu，选择后销毁，并回显操作。弹出菜单的“打开 / 复制 / 更多”用于菜单定位和状态回显。输入框保留框架原生编辑行为。

## 表格数据

`dw_employees` 是真正的 DataWindow，七列为 ID、姓名、部门、城市、状态、邮箱、入职日期。共 1000 条确定性员工记录，每页 20 条，共 50 页。支持首页、上一页、五个动态页码、下一页和末页；首尾页按钮和当前页按钮正确禁用，切换 Tab 保留页码。

数据与 Win32 靶场的公式一致。可人工核对：

| ID | 姓名 | 部门 | 城市 | 状态 | 邮箱 | 入职日期 |
|---|---|---|---|---|---|---|
| 1 | 用户1 | 产品部 | 上海 | 离职 | user1@example.com | 2024-02-02 |
| 1000 | 用户1000 | 研发部 | 北京 | 离职 | user1000@example.com | 2024-05-21 |

第一页显示 ID 1–20，末页显示 ID 981–1000。末页的五个页码为 46–50；其 AccessibleName 与显示文本同步更新。

## 拖拽测试

`drag-target` 为原生 PB CommandButton，尺寸为 120×80 像素。按下后由源按钮捕获鼠标，移动时保持按下锚点并跟随指针；松手位置无需落在目标按钮自身范围内。目标位置始终限制在拖拽区域内，指针移出区域时位置钳制到边界。坐标在 PB 布局单位与像素之间转换，记录当前位置、相对初始位置的位移、本次拖拽位移、按下锚点和投放次数。

“隐藏 drag-target”隐藏目标；“重置位置”恢复显示并居中，清空计数；“复制当前结果”把 JSON 写入剪贴板。`drop_count` 是投放次数，调用方的移动轨迹数量和 `delay_after` 需由调用方统计。

鼠标移动不会累计投放次数，正常松手只计一次。失去鼠标捕获、隐藏或重置会结束当前拖拽，避免残留拖拽状态。实际拖拽交互由使用者人工测试。

## 可访问性

生成目录的 `pb.ini`：

```ini
[Application]
Accessibility=1
```

按[官方配置方式](https://docs.appeon.com/pb2025/application_techniques/Creating.html)启用框架自身的 UIA 和 MSAA。表单控件、页签、表格及列均有 AccessibleName；状态文本与动态页码会同步更新名称。Runtime 检查包括 `pbacc.dll` 和 `PBAccessibility.dll`。

实际可探测节点、单元格结构及 Pattern 以本机 Runtime 和 CLI 实测为准。本次验证没有将程序内部自检等同于外部 UIA 单元格探测。

## 产物与源码

构建产物位于 `POWERBUILDER/build/Release/`：

```text
PowerBuilderShootingRange.exe
pb_range.pbd
PowerBuilderShootingRange.xml
pb.ini
build.log / import.log
self-test.json               # 运行自检后生成
```

运行时保留 EXE、PBD、XML 和 pb.ini，并安装匹配的 Runtime；无需安装 IDE。XML 的 `Application/RuntimePath` 指向 Runtime 安装目录，启动器会校验其 DLL 版本。生成文件不纳入 Git。

`src/` 保存可编辑的 UTF-8 PowerScript 导出对象：应用入口、主窗口、表单、表格、拖拽区域、菜单、布局与自检。构建时将对象复制为带 BOM 的 UTF-16 源码，并用 OrcaScript 离线导入生成 PBL/PBD/EXE，不改写 `src/`。

## 本机验证

2026-10-15：Utilities 和 Runtime 安装日志均为 `ResultCode=0`，实际 OrcaScript 编译成功；启动器 6 项单元测试通过，原生 PB 自检 3085 项通过。自检覆盖全部 50 页的记录数量、ID/姓名/邮箱、代表记录其余列、表单默认值及重置、菜单路由、单选互斥、动态可访问名称、屏幕尺寸上限及客户区边界、拖拽坐标边界与隐藏恢复。

2026-10-16：生成 31,360,000 字节的单文件 EXE；独立中文目录运行时确认 PBVM 来自包内解压目录，3085 项应用自检通过，退出后解压目录已清理。打包校验与启动器共 11 项单元测试在 `python -O` 模式下通过，发布校验不会因优化模式被跳过。本次同时修正原生控件像素对齐引起的拖拽边界偏移。

拖拽修复增加 8 项内部状态回归，涵盖目标原范围外的落点、按下锚点、边界、松手计数、重复结束及取消后的移动；总计 3093 项。检查直接调用内部状态方法，不模拟鼠标拖拽，不能替代人工检查 Windows 消息与真实鼠标交互。

```powershell
python -m unittest tools.test_start_powerbuilder -v
python -O -m unittest POWERBUILDER.verify.test_package_smoke -v
python .\tools\start_powerbuilder.py --no-launch
python .\tools\start_powerbuilder.py --skip-build --self-test
```

自检会创建并关闭自身的测试窗口。鼠标实际拖拽、菜单弹出、密码遮挡、编辑操作与外部 UIA/MSAA 树仍需人工检查。Windows 10 兼容性按所选官方 Runtime 的系统要求设置，本次未在独立 Windows 10 机器上实测。
