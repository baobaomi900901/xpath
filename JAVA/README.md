# Java 靶场

Java Swing 桌面靶场，用于 UI 自动化测试练习。

## 环境要求

- Amazon Corretto JDK 8、11、17、21、25，安装在 `.tools/jdks/corretto/<版本>`
- 无需预装 Maven（`build.ps1` 会自动下载）

## 功能

### Tab 1：表单控件

- 文本输入框、密码框、邮箱、数字（Spinner）
- 下拉单选、多选（Checkbox 组）
- 单选框（性别）、多选框（兴趣爱好）
- 文本域、协议勾选
- **保存**：弹出模态提示「提交成功」
- **重置**：清空所有表单项

### Tab 2：表格数据

- 1000 条模拟员工数据，7 列
- 每页 20 条，带首页/上一页/下一页/末页及页码按钮
- **导入 Excel**：从 `.xlsx` 文件加载数据
- **导出 Excel**：将全部数据导出为 `.xlsx`

### Tab 3：自绘控件

- 单个 `JPanel` 画布，使用 `Graphics2D` 绘制全部内容，没有嵌入标准输入框、单选框、多选框或图表控件
- 两个输入框：支持键盘输入、中文输入法提交、左右方向键、Home/End、Backspace/Delete；每框最多 80 个 UTF-16 代码单元，不提供文本选择和剪贴板快捷键
- 单选组、多选组：鼠标点击切换；Tab / Shift+Tab 移动逻辑焦点，空格或 Enter 选择，越过首尾后离开画布
- 柱状图：固定五组数据，点击柱形后在文字面板显示对应月份与数值
- 文字面板：画布文字、表单状态、图表状态；自绘“重置样本”按钮恢复初始值
- 缩放窗口时画布等比例缩放，点击坐标同步换算

用于验证元素探测器对非标准控件的识别能力：画布名为 `custom-controls-canvas`，内部没有子组件，也没有为绘制元素提供独立的无障碍节点。通过组件树或 Java Access Bridge 探测时通常只能看到整体画布；OCR / 图像识别是否能识别其中内容取决于探测器。可与“表单控件”页签对照测试。

运行画布结构、交互及多 JDK 回归检查（无需显示窗口）：

```powershell
.\JAVA\tests\custom-controls-tests.ps1
```

测试同时生成渲染预览 `JAVA/target/custom-controls-preview.png`。

### Tab 4：选择与状态

- 标准 `JList` 单选、多选和空列表；非空列表含北京、上海、广州和两个独立的同名项
- 多选列表初始选中北京、上海，支持 Ctrl / Shift；原有表单的复选框组保持原样
- 可编辑、只读、禁用、可切换显示状态的文本框
- 滑块与联动进度条、开关按钮和执行计数，便于检查动作是否执行了一次
- 含 360 行中文、换行、Unicode 表情的只读长文本
- “重置选择与状态”恢复初始值、选中项与控件状态

### Tab 5：动态样本

- 替换输入对象：名称与内容相同，但重新创建 `JTextField`
- 同名复选框组：增加、移除首项、替换首项（保留勾选）；相邻分组独立存在，动态组可滚动
- 三列混合类型表格：整数 ID、同名文本、可编辑布尔单元格；可排序、替换整个表格模型
- 标准树：展开组织层级、添加成员；“重置动态样本”恢复对象、分组、表格和树

两个新页签采用两列分区，随窗口调整宽度，内容过高时在页面内滚动；不改变原有表单、员工表格和自绘页布局。原有“关于”页签移到最后。

运行新页面的无窗口控件、无障碍选择与布局测试（Python 3 标准库，无额外依赖）：

```powershell
python .\JAVA\tests\control-samples-tests.py
# 可限定版本
python .\JAVA\tests\control-samples-tests.py --versions 8 25
```

### Tab 6：重叠命中复现

用于复现 [rust_uia PR #31](https://github.com/ha0018/rust_uia/pull/31) 中可见背景容器压过前景按钮的问题。

- 前景标准按钮名为 `Front Button`，背景依次为 `Back Wrapper`、`Back Content` 两层 panel。
- 按钮位于最前方，背景 panel 的层级更深，双方覆盖同一坐标且均可见。
- 场景父容器保留完整无障碍子节点，故意让 `AccessibleComponent.getAccessibleAt` 返回空，供点命中缺失时的补充遍历使用；普通 Swing 鼠标命中不受影响。
- 点击前景按钮会更新底部计数，可验证实际鼠标命中的确是按钮。
- “打开独立复现窗口”提供同一场景的独立窗口，关闭它不会退出靶场。

复现步骤：

1. 启动靶场，选择“重叠命中复现”页；也可打开独立窗口。
2. 将自动化指认点放在 `Front Button` 中心，优先测试 Auto 模式，再用 JAB 对照。
3. 预期目标为 `push button / Front Button`；若捕获到 `panel / Back Content`，即出现误选。

回归对照：PR `136054f` 在原生点命中失败时，JAB 的全局深度优先会误选背景；Auto 可能直接接受 Agent 的背景容器。原生点命中成功的快路径可能正常，应结合捕获诊断确认实际路径。

验证 JAB 补充遍历时，可新开独立窗口，在鼠标尚未移入场景前，通过坐标捕获按钮中心，检查诊断是否为 `strategy: refined_tree`、`directTargetFound: false`。鼠标悬停后可能进入 `direct` 快路径并正常返回按钮。

在 Corretto 8u504 上实测，PR `136054f` 的 Auto 模式在新标签页及独立窗口均误选 `Back Content`，JAB 在冷态独立窗口的补充遍历中也误选背景；main `dc304a7` 在这些对照用例中均返回 `Front Button`。

运行场景结构、鼠标命中与无障碍行为检查（覆盖五个 JDK，无需显示窗口）：

```powershell
.\JAVA\tests\overlap-hit-tests.ps1
```

测试生成 `JAVA/target/overlap-hit-preview-<版本>.png` 渲染预览。

### Tab 7：单元格命中复现

用于复现 [rust_uia PR #31](https://github.com/ha0018/rust_uia/pull/31) 对合法虚拟表格单元格要求 `showing`，导致捕获退回整表的问题。

- 标准 `JTable`，表名 `Employees`，表头名 `Employee columns`，两行三列：`ID`、`Enabled`、`Name`。
- 文本单元格均为 `same`，中间列为布尔复选框，初始值分别为勾选和未勾选。
- 使用真实 JTable 虚拟无障碍单元格，保持默认渲染器和状态；JAB 返回的有效单元格状态可能只有 `visible`、没有 `showing`。
- “重置示例数据”恢复文本与勾选值；“打开独立复现窗口”提供同一场景的独立入口。

复现步骤：

1. 使用 JDK 8 启动靶场，进入“单元格命中复现”页，并打开新的独立窗口。
2. 在鼠标尚未移入表格前，用 JAB 按坐标捕获首个文本单元格中心，检查是否进入 `strategy: refined_tree`、`directTargetFound: false`。
3. 预期为 `label / same`，矩形仅覆盖该单元格；若返回 `table / Employees` 并框选整表，即复现误选。也可对中间列验证目标是否为 `check box`。

对照版本为 main `dc304a7` 与 PR `848350e`。原生点命中成功的 `direct` 路径可能正常；本场景验证 JAB 补充遍历对虚拟单元格的处理。

在 Corretto 8u504 上实测，嵌入标签页与独立窗口均可复现：main 正确捕获全部六个单元格，PR 将首个 `same` 单元格误选为 `Employees` 整表。此处观察的是 JAB 返回的状态，可能与 Java 程序直接读取 `AccessibleStateSet` 的结果不同。

运行单元格结构、渲染器角色、几何和数据重置检查：

```powershell
.\JAVA\tests\virtual-table-hit-tests.ps1
```

测试覆盖 JDK 8、11、17、21、25，并生成 `JAVA/target/virtual-table-hit-preview-<版本>.png`。

## 一键构建 + 运行

```powershell
cd D:\code\xpath
uv run .\tools\start_java.py
```

Python 启动器使用根目录 `.tools/java-launcher` 中的 uv 环境，不依赖 PowerShell 脚本。启动后使用方向键移动焦点，按 `Enter` 或空格勾选多个 JDK；在“已完成选择”上按 `Enter` 后，脚本会依次构建并同时启动所选版本。

非交互命令：

```powershell
# 构建并验证全部版本，不启动窗口
uv run .\tools\start_java.py --versions 8 11 17 21 25 --no-launch

# 跳过构建，同时运行 JDK 8 和 25
uv run .\tools\start_java.py --versions 8 25 --skip-build
```

各版本产物位于 `target/jdk-<版本>/shooting-range-<版本>.jar`。

> **关于构建 warning**：JDK 25 可能报告 Maven 自身依赖的 `System::load`、`Unsafe` 兼容性提示。脚本在构建成功时隐藏 Maven 输出，构建失败时会完整显示。

## 项目结构

```
java/
  pom.xml
  start.ps1              # 交互式多选入口
  build.ps1 / run.ps1    # 多版本构建与并行启动
  tests/multi-jdk-tests.ps1
  src/main/java/com/xpath/shootingrange/
    Main.java              # 入口
    ShootingRangeApp.java  # 主窗口 + Tabs
    ui/FormPanel.java      # 表单 Tab
    ui/TablePanel.java     # 表格 Tab
    ui/CustomControlsPanel.java # 自绘控件 Tab（单画布）
    ui/ControlSamplesPanel.java # 选择、状态、数值与长文本 Tab
    ui/DynamicSamplesPanel.java # 动态对象、分组、混合表格与树 Tab
    ui/SamplePanelLayout.java   # 两个新页面的公共布局
    ui/OverlapHitPanel.java # 重叠命中复现 Tab + 独立窗口
    ui/VirtualTableHitPanel.java # 虚拟表格单元格命中复现 Tab + 独立窗口
    model/Employee.java
    util/DataGenerator.java
    util/ExcelUtil.java
```
