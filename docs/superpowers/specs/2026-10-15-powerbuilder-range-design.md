# PowerBuilder 靶场设计

## 目标与环境

参考 `WIN32/src/main.cpp`，使用真正的 PowerBuilder 窗口、控件和 DataWindow 制作 Windows 10/11 桌面靶场。源码放在 `POWERBUILDER/`，启动入口为 `tools/start_powerbuilder.py`。不使用 OCR；用户自行进行桌面人工测试。

环境采用 PowerBuilder 2025 GA 25.0.0.3683 的 Utilities 和同版本 Runtime。该 GA 的官方系统要求包含 Windows 10；不采用已停止支持 Windows 10 的 2025 R2。使用 x86 Pcode 应用，覆盖 Windows 10/11 的 x86/x64 运行环境。当前机器实际运行结果与 Windows 10 的兼容目标分别记录，不把本机 Windows 11 上运行当成 Windows 10 实测。

## 实现方案

采用原生 PowerBuilder 表单加原生 DataWindow 表格：表单控件保持常见 PB 程序的类型和行为，表格保留 PB 特有的 DataWindow 结构，方便元素自动化工具实测。

备选方案是把表单也放进 DataWindow。它更集中，但会减少普通 SingleLineEdit、DropDownListBox、CheckBox 和 RadioButton 的测试覆盖，因此不作为本次默认方案。

## 页面与行为

1. **表单控件**：姓名、密码、邮箱、年龄、城市单选、城市多选、性别单选、兴趣多选、备注、协议共十项。城市为北京、上海、广州、深圳、杭州；性别为男、女、其他；兴趣为阅读、运动、音乐、旅行。初始年龄 25、城市单选北京、性别男，其他输入为空、其他勾选关闭。密码框使用 Password 属性，多行备注使用 MultiLineEdit。保存弹出“提交成功”，重置恢复初始状态。
2. **表格数据**：原生 DataWindow，1000 条内存生成的员工记录，每页 20 条，共 50 页。列为 ID、姓名、部门、城市、状态、邮箱、入职日期。数据公式与 Win32 版本保持一致：各分类按 ID 取模轮换，姓名为“用户<ID>”，邮箱为 `user<ID>@example.com`，入职日期使用 2024 年及 ID 取模生成月日。支持首页、上一页、动态页码、下一页和末页，正确禁用首尾页按钮；切换页签保留当前页。无需数据库、DSN 或网络。
3. **拖拽测试**：使用 PB 控件 `drag-target`，目标初始居中，显示位置和移动结果，可在限定区域拖动、重置、隐藏/恢复并复制 JSON 结果。屏幕像素和 PB 布局单位转换使用 PB 提供的转换函数。
4. **菜单**：顶部文件/编辑菜单，以及表单动态弹出菜单；操作回显状态。输入控件保留框架原生编辑交互。

## 可访问性

随程序提供 `pb.ini`，在 `[Application]` 中设置 `Accessibility=1`，同时启用框架自身的 UIA 和 MSAA 支持。为控件、页面、DataWindow 和列设置清晰的 AccessibleName/AccessibleDescription，部署或检查匹配的 `pbacc.dll` 和 `PBAccessibility.dll`。不实现伪造的 Win32/PB 类名或额外自定义 UIA Provider。实际可探测节点及 Pattern 以 CLI 实测或用户人工检查为准。

## 构建与启动

源码使用 PB 导出对象格式，构建在独立 `build/Release` 目录中进行，避免把 PBL、PBD、日志和 Runtime DLL 混入源码。通过 Utilities 的官方命令行工具从源码生成 EXE，检查编译返回码和产物；失败时输出日志位置。

启动器仅使用 Python 标准库，支持默认构建启动、`--no-launch` 仅构建检查、`--skip-build` 运行已有产物，以及明确指定工具与 Runtime 路径。默认根据本机已安装版本发现 Utilities/Runtime，缺失或版本不匹配时明确报错，不下载安装未知副本。已在运行的 EXE 需要用户关闭后才能覆盖，不自动结束用户进程。

预期启动命令：`python .\tools\start_powerbuilder.py`。

## 验证与交付

使用真实 PowerBuilder 编译工具验证语法、EXE/PBD 和运行时配置。验证启动器的路径发现、失败处理和跳过构建行为。对表格首末页、页码边界和数据生成规则进行有意义的程序验证。用户负责完整人工桌面测试；如进行额外桌面探测，仅使用 CLI，不使用 OCR。

README 说明依赖版本、安装位置、启动命令、字段初始值、表格规则和人工检查步骤。仅当安装、真实编译及对应验证完成后，才将其记录为已完成。

## 官方依据

- [PowerBuilder 2025 GA Readme / Windows 10 支持](https://www.appeon.com/system/files/product-readme/PowerBuilder%202025%20GA%203683%20Readme.htm)
- [Utilities 命令行构建及无需 IDE 许可证](https://docs.appeon.com/pb2025/pbug/Tutorial_Building_your_PowerClient_project_with_commands.html)
- [PBAutoBuild 的 PBC 部署参数](https://docs.appeon.com/pb2025/pbug/pbc_d_and_related_parameters.html)
- [PB 可访问性配置和部署要求](https://docs.appeon.com/pb2025/application_techniques/Creating.html)
- [从导出对象重建 PBL 的 OrcaScript 方式](https://docs.appeon.com/pb2025/troubleshooting_guide/tr_057.html)
