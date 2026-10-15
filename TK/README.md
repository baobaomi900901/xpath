# Tk 框架靶场

参考 `WIN32/` 标准版的 tkinter/ttk 桌面靶场，主要面向 Windows UI 自动化、元素探测与坐标操作测试。
仅使用 Python 标准库，不需要编译、pip 安装或下载运行时。

## 启动

需要 **Python 3.8+，且安装了 Tcl/Tk**。Windows Python 安装器中须包含 `tcl/tk and IDLE` 组件。
在仓库根目录运行：

```powershell
python .\tools\start_tk.py                 # 检查环境后启动窗口，返回 PID
python .\tools\start_tk.py --no-launch     # 初始化并销毁隐藏窗口，验证三个测试页
python .\tools\start_tk.py --foreground    # 前台运行，关闭窗口后返回，便于查看错误
python .\tools\start_tk.py --help
```

也可直接运行 `python -m TK`。从其他目录启动时，使用启动器的绝对路径：

```powershell
python D:\code\xpath\tools\start_tk.py
```

启动器复用当前 Python 解释器，不创建虚拟环境。`--no-launch` 仍需可用的桌面环境和 Tcl/Tk；缺少依赖或窗口初始化失败时返回非零退出码。

## 测试内容

窗口标题为“Tk 靶场 - tkinter/ttk”，默认 1180×860，最小 960×760。
支持调整大小、Tab 控件焦点切换及 `Ctrl+Tab` / `Ctrl+Shift+Tab` 切换页面。

### 表单控件

- 姓名、掩码密码、邮箱输入框，18–80 的年龄微调框（初始 25）。
- 城市下拉单选和五项城市多选：北京、上海、广州、深圳、杭州。
- 性别单选：男、女、其他；兴趣多选：阅读、运动、音乐、旅行。
- 多行备注和“同意用户协议”。备注框支持换行，Tab 切到下一个控件。
- 保存弹出“提交成功”模态提示；重置恢复空输入、年龄 25、城市北京、性别男和全部未勾选。
- 顶部“文件 / 编辑”菜单，表单右上角的动态操作菜单。菜单项仅更新“最近选择”状态。
  操作菜单每次展开时创建，选择、Esc 或点击外部关闭后销毁，支持反复捕获/展开测试。

### 表格数据

使用 ttk.Treeview 展示 1000 条确定性员工数据，生成规则与 Win32 相同。
七列为 ID、姓名、部门、城市、状态、邮箱、入职日期，每页 20 条，共 50 页。
支持首页、上一页、五个相邻页码、下一页、末页及横纵滚动条。边界及当前页按钮禁用。

### 拖拽测试

`drag-target` 为实际 Tk Button，大小 120×80，初始居中于拖拽区域内。
支持边界限制、重置位置、隐藏目标、复制当前结果。
隐藏会销毁目标控件；重置会重新创建目标并居中。

记录位置、相对初始位移、本次位移、按下时的局部坐标、九宫格区域、有效移动次数与耗时。
九宫格名称为 `topLeft` / `topCenter` / `topRight`、`middleLeft` / `middleCenter` / `middleRight`、
`bottomLeft` / `bottomCenter` / `bottomRight`。
移动次数只在目标位置变化时增加，耗时用单调时钟统计。
切换页面、隐藏、重置或按 Esc 会结束当前拖拽并释放抓取。

“复制当前结果”将 JSON 写入剪贴板，字段顺序与 Win32 相同：

```json
{"left":240,"top":160,"initialLeft":240,"initialTop":160,"deltaLeft":0,"deltaTop":0,"startLeft":240,"startTop":160,"sessionDeltaLeft":0,"sessionDeltaTop":0,"anchor":{"x":60,"y":40,"sudokuPart":"middleCenter"},"moveCount":0,"durationMs":0,"dragging":false}
```

`left/top` 相对拖拽区域，采用 Tk 坐标单位；与其他坐标工具对比时注意本机 DPI 缩放。
`delay_after` 是自动化调用方的等待时间，靶场无法直接观测。

## 元素定位

采用 Tk/ttk 自身控件和菜单，不添加 UIA/MSAA Provider。
Windows UIA/MSAA 可见节点与 Pattern 由本机 Python/Tk 和探测器决定，应以实际捕获结果为准。
以下是程序内稳定的 **Tk widget path**，不等同于 Windows AutomationId：

| 控件 | Tk path |
|---|---|
| 主窗口 / Tab | `.` / `.tabs` |
| 姓名 / 密码 / 邮箱 | `.tabs.form.name.input` / `.tabs.form.password.input` / `.tabs.form.email.input` |
| 年龄 / 城市单选 | `.tabs.form.age.input` / `.tabs.form.city.input` |
| 城市多选组 / 兴趣多选组 | `.tabs.form.cities.options` / `.tabs.form.hobbies.options` |
| 性别选项 / 备注 / 协议 | `.tabs.form.gender.options` / `.tabs.form.remark.input` / `.tabs.form.agreement.input` |
| 保存 / 重置 | `.tabs.form.actions.save` / `.tabs.form.actions.reset` |
| 操作菜单按钮 / 动态菜单 | `.tabs.form.heading.popup` / `.tabs.form.action_menu` |
| 员工表格 / 翻页栏 | `.tabs.table.employees` / `.tabs.table.pagination` |
| 拖拽区域 / 目标 | `.tabs.drag.arena` / `.tabs.drag.arena.drag-target` |

组内控件依次命名为 `option0`、`option1` 等。表格行 ID 为 `employee-1` 到 `employee-1000`，仅当前页行存在。

## 验证

在仓库根目录执行（UI 测试需要桌面环境，会短暂创建窗口）：

```powershell
python -m unittest discover -s TK/tests -v
python -m unittest tools.test_start_tk -v
python tools/start_tk.py --no-launch
```

覆盖表单默认值/重置/保存、分页边界、动态菜单创建销毁、真实 Tk 拖拽事件、隐藏恢复、缩放和剪贴板 JSON。
Windows 原生菜单消息循环与模态提示的阻塞调用在单元测试中替换；实际菜单交互需另行进行桌面验收。
