# Qt 多版本 RPA 靶场

参考 Win32 靶场的同一套业务场景，以真实 Qt 5.15.2 和 Qt 6.8.3 分别构建 Widgets / Quick 界面。支持四个组合同时运行，窗口标题显示实际运行库版本。

| Qt | Windows 工具链 | 界面 |
|---|---|---|
| 5.15.2 | MinGW 8.1 x64 | Widgets、Quick Controls 2 / QML |
| 6.8.3 | MinGW 13.1 x64 | Widgets、Quick Controls 2 / QML |

## 启动

仓库根目录执行：

```powershell
# 方向键多选 Qt 版本，构建后同时启动 Widgets 和 QML
python tools/start_qt.py
# 已有产物同时启动四个窗口
python tools/start_qt.py --versions 5.15.2 6.8.3 --skip-build
# 只启动 Qt 6.8 Widgets，字段顺序和 objectName 每次启动随机
python tools/start_qt.py --versions 6.8.3 --frontends widgets --form-mode random --skip-build
# 无字段分组的 Widgets
python tools/start_qt.py --versions 5.15.2 --frontends widgets --form-mode flat --skip-build
# 保留的 Accessible.ignored 名片示例
python tools/start_qt.py --versions 5.15.2 --frontends profile --skip-build
```

也可运行 `python tools/start.py`，勾选 **Qt Widgets / QML**，选择版本、界面和表单结构。

PowerShell 包装：`./QT/build.ps1` 只构建，`./QT/run.ps1 -SkipBuild` 运行两个版本；支持 `-Versions 5.15.2`、`-Frontends widgets`、`-FormMode random`、`-SdkRoot D:/Qt`。

## 功能与 Win32 对应

- **十字段表单**：姓名、密码、邮箱、年龄（18–80，默认25）、城市单选、城市多选、性别、兴趣、备注和协议。城市、兴趣选项和 Win32 一致；保存弹出模态“提交成功”，重置恢复初值。
- **表格数据**：与 Win32 相同的1000条员工数据、七列，每页20条，共50页；首页、上一页、五个动态页码、下一页、末页。Widgets 使用真实 QTableView；QML 使用七列 ListView delegate，适合比较原生模型视图与 QML 可访问节点，后者不承诺 UIA Grid/Table Pattern。
- **菜单**：文件/编辑菜单和每次重新创建、关闭即销毁的弹出菜单，包含重置、子菜单和关于对话框。这里是 Qt 菜单，不是 Win32 HMENU 的复刻。
- **拖拽**：120×80 的 `drag-target`，初始居中且限制在区域内；隐藏时销毁目标，重置时恢复。记录当前位置、相对初始/本次位移、九宫格锚点、移动次数、耗时；复制固定顺序 JSON，与 Win32 字段相同。坐标和尺寸是 Qt 逻辑像素，高 DPI 下需由自动化客户端换算；`delay_after` 仍由调用方测量。
- **Widgets 表单结构**：`grouped` 为具名字段容器，`flat` 将标签和控件直接放在表单页，`random` 随机字段顺序和表单后代 objectName。随机配置在本进程内固定，重置不重新洗牌；中文可访问名称保持稳定。Qt 类名没有随机化。
- **原名片示例**：头像、昵称 `Accessible.ignored: true`，正文可访问。

Qt 可访问性由相应版本的平台插件提供，不把 objectName 等同于所有版本的 Windows AutomationId，也不将这四个组合称为“纯 MSAA”或“无内部树”。用 Inspect 或自己的 RPA 客户端验证实际树与 Pattern。Widgets 与 QML 的树结构预期不同。

## 构建依赖

Python 3.9+、CMake 3.16+（Qt 6 建议较新版本）、Ninja，及对应 Qt SDK / MinGW。版本固定在 `versions.json`。启动器依次查找 `QT/.tools`、`QT_SDK_ROOT` 环境变量（未设置则为 `D:/Qt`），也可明确传 `--sdk-root`。

目录应为：

```text
<SDK根>/5.15.2/mingw81_64/
<SDK根>/6.8.3/mingw_64/
<SDK根>/Tools/mingw810_64/bin/
<SDK根>/Tools/mingw1310_64/bin/
```

安装器可按需调用 aqtinstall（启动已有程序不需要它）：

```powershell
python -m pip install aqtinstall
python tools/start_qt.py --versions 5.15.2 6.8.3 --install-sdk --no-launch
```

下载使用安装器的校验，网络或镜像失败会停止并报告。可自行准备 SDK，再通过 `--sdk-root` 使用。每次构建先检查 qmake 的精确版本；两个版本的 CMake 缓存、运行库和产物分别隔离。

Qt 6 使用 windeployqt 部署。Qt 5 的部分 MinGW SDK 保留 PE 调试信息，旧部署器会错误识别发行插件；因此从该 SDK 复制 DLL、插件和 QML 模块，并以移除 SDK PATH 的实际运行测试验证。该策略使 Qt 5 运行目录偏大，但避免依赖本机 SDK。

## 产物与分发

```text
QT/dist/5.15.2/qt-widgets-range.exe
QT/dist/5.15.2/qt-quick-range.exe
QT/dist/6.8.3/qt-widgets-range.exe
QT/dist/6.8.3/qt-quick-range.exe
```

每个版本目录还包含 `acc-hidden-profile.exe`、测试程序、Qt DLL、插件、QML 模块、`qt.conf` 和带 SHA-256 的 `manifest.json`。分发时复制**整个版本目录**，不能只复制 EXE，也不要混用两套 Qt DLL。运行已有发行目录不需要 Qt SDK、编译器或 Python；直接双击 EXE 即可。分发 Qt 时保留并遵循所用 Qt 发行包的许可条件。

## 验收

```powershell
python -m unittest tools.test_start_qt tools.test_range_launcher_core
python tools/start_qt.py --versions 5.15.2 6.8.3 --no-launch
python tools/start_qt.py --versions 5.15.2 6.8.3 --skip-build --self-test
python QT/verify/uia_smoke.py --versions 5.15.2 6.8.3
```

`--no-launch` 检查产物而不启动靶场；构建阶段会执行窗口测试。`--self-test` 在只保留 Windows 系统 PATH 的环境中运行发行目录的 QtTest，并短暂打开两套界面的三个页签和原名片示例，生成截图后关闭。报告和截图位于 `QT/verify/artifacts/`。QtTest 涵盖分页边界、表单重置、可访问名称、随机/平铺结构、重复打开菜单、模态保存、实际鼠标拖拽、剪贴板、目标隐藏/恢复和 QML 加载警告。

`uia_smoke.py` 从独立 PowerShell / Windows UI Automation 客户端查找六个关键名称，通过姓名输入框的 ValuePattern 填值，再通过重置按钮的 InvokePattern 清空。它只访问本次启动的靶场 PID，验收后关闭窗口。QML 按钮显式连接 Accessible Press 动作与点击处理，使 Qt 5 / 6 的该操作一致；它不是通过私有业务接口完成的 UIA 验收。

人工 RPA 验收建议：比较两版本的名称/角色/父子关系；填写和重置十字段；翻到第50页确认ID1000；反复打开动态菜单；拖至边缘、复制JSON、隐藏后重新捕获；在100%/125%/150%缩放下核对坐标。自动化测试未替代你的 RPA 产品自身的兼容性验收。

2026-10-23 本机验证：Python 测试31项通过；两个真实 SDK 的构建、CTest、移除 SDK PATH 的发行目录测试及三个页签截图检查通过；四种组合的外部 UIA 名称识别、姓名输入和重置调用全部通过。对应 XML、PNG、UIA JSON 保存在 `verify/artifacts/`。
