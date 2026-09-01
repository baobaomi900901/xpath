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

## 一键构建 + 运行

```powershell
cd D:\code\xpath\ShootingRange\java
.\start.ps1
```

启动后使用方向键移动焦点，按 `Enter` 或空格勾选多个 JDK；在“已完成选择”上按 `Enter` 后，脚本会依次构建并同时启动所选版本。

非交互命令：

```powershell
# 构建全部版本
.\build.ps1 -Versions 8,11,17,21,25

# 同时运行 JDK 8 和 25
.\run.ps1 -Versions 8,25

# 跳过构建直接运行
.\run.ps1 -Versions 8,25 -SkipBuild
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
    model/Employee.java
    util/DataGenerator.java
    util/ExcelUtil.java
```
