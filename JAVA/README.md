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
    model/Employee.java
    util/DataGenerator.java
    util/ExcelUtil.java
```
