# 靶场启动中心

在仓库根目录执行：

```powershell
uv run .\tools\start.py
```

默认在独立进程中打开界面，检查约 1 秒后归还终端；关闭终端后界面继续运行。启动中心自身的输出保存在 `.private/range-launcher/logs/launcher-*.log`，命令会打印本次日志路径。

需要在终端查看调试输出、等窗口关闭后再返回时，执行：

```powershell
uv run .\tools\start.py --foreground
```

启动中心使用 Python 3.8+ 标准库，不需要安装第三方 Python 包。图形界面需要当前 Python 含有 Tcl/Tk；Windows Python 安装程序中的组件名通常为 `tcl/tk and IDLE`。各靶场原有的编译工具、运行时和 Excel 等宿主要求仍然适用，详见各靶场 README。

## 使用流程

1. 用搜索和分类找到靶场，勾选需要启动的条目。
2. 选中某个条目，在选项区设置启动方式、版本和其他参数。勾选表示加入本次批量启动，选中条目用于查看或修改它的选项。
3. 查看命令预览，确认版本与启动方式后，点击启动所选靶场。
4. 在任务和日志区域查看脚本输出、退出码和日志文件。日志保存在 `.private/range-launcher/logs/`，可点击“打开日志目录”查看。可以继续操作界面或启动其他条目；同一靶场的启动任务仍在运行时不能重复启动。

启动方式右侧的“恢复默认”会恢复当前靶场在配置文件中的默认选项，保留勾选状态。修改清单默认值后，已有个人选项会保留；点击此按钮即可应用新的默认值。

左侧“清空选项”会取消全部靶场、版本和附加开关的勾选，包括被搜索或分类隐藏的条目，以及其他启动方式下暂未显示的开关。各靶场当前的启动方式、构建配置、WEB 路由根地址、端口及工具路径保留；已选择的 Debug、自定义地址、端口和路径也会保留。此前被旧版清空的基础配置，会在重新加载设置或点击清空时补回默认值：构建配置为 Release，Excel 端口为 7300，WEB 地址为默认线上地址；未指定的工具路径仍为空，沿用自动查找。清空结果会保存到个人设置，启动前需重新选择必选版本。

配置中的默认选项不表示自动执行。打开启动中心或修改配置不会启动靶场，需由用户勾选并点击启动。启动中心不使用 OCR，也不操作靶场内部控件；窗口内功能由用户人工测试。

任务状态反映启动脚本的生命周期。大部分脚本创建应用窗口后会退出，因此“成功”表示脚本返回 0，不能据此判断靶场窗口仍然存活或功能测试通过。Tk 前台方式会等窗口关闭，Excel 服务则会持续运行。关闭启动中心不会终止已经启动的应用或服务。

## 默认清单与选项

`tools/ranges.json` 包含九个现有启动脚本：

| 靶场 | 默认方式 | 主要选项 | 点击“清空选项”后 |
| --- | --- | --- | --- |
| Win32 | `--skip-build`，运行已有 EXE | 必选一个或多个 backend，默认 `uia`；Release / Debug | 清空 backend 勾选；保留构建配置，默认 Release |
| Tk / ttk | 启动独立窗口 | 独立窗口、前台运行、隐藏窗口检查 | 保留当前启动方式 |
| Java Swing | `--skip-build`，运行已有 JAR | 必选 JDK 8 / 11 / 17 / 21 / 25，默认 17；构建时可强制重建 | 清空 JDK 勾选并关闭强制构建 |
| CEF | `--skip-build`，运行已有产物 | 必选 109 / 125 / 128 / 133 / 154，默认 133；WEB 地址；构建时可干净重建 | 清空版本勾选并关闭强制构建；保留 WEB 地址 |
| Electron | `--skip-build`，运行已有产物 | 必选 22 / 29 / 38 / 44，默认 38；WEB 地址；构建时可重新打包 | 清空版本勾选并关闭强制打包；保留 WEB 地址 |
| Delphi VCL | `--skip-build`，运行已有 EXE | Release / Debug；构建时可指定 `dcc32.exe` | 保留构建配置和编译器路径；默认 Release、路径自动查找 |
| PowerBuilder | `--mode exe`，运行单文件包 | 开发方式显式传 `--mode dev`，可设置 Utilities、Runtime、跳过构建；可仅检查产物 | 保留模式及 Utilities / Runtime 路径；取消跳过构建、仅检查的勾选 |
| WebView2 | 构建并启动 | Release / Debug；也可构建验证而不启动 | 保留构建配置，默认 Release |
| Excel 加载项 | 服务并打开工作簿 | HTTPS 端口默认 7300；手动打开工作簿；重建证书；跳过注册及工作簿生成 | 保留端口和启动方式；关闭重建证书、跳过注册的开关 |

Win32、Java、CEF 和 Electron 始终通过 `--backends` 或 `--versions` 显式传入非空版本列表，避免进入终端交互菜单。已有产物缺失时，切换到构建方式。Release / Debug 同时决定 Win32 和 Delphi 查找已有产物的目录。

PowerBuilder 的开发字段只在 `dev` 方式生效。留空时沿用原脚本的环境变量、注册表或默认路径查找规则；Utilities 与 Runtime 需要匹配原脚本要求的 25.0.0.3683。单文件包方式不传开发参数。

CEF 和 Electron 支持通过 `--base-url` 切换 WEB 路由根地址，例如本地 `http://localhost:7199/` 或线上 `https://baobaomi900901.github.io/xpath/#/`。程序会在根地址后拼接 `keys-click-test`、`form-controls`、`iframe-shadow-form` 等固定路由，目标部署需提供这些页面；该字段用于指定靶场 WEB 的部署位置。

WebView2 原脚本不支持 `--skip-build`，两种方式都会执行构建。CEF 原脚本在构建或启动前会清理本仓库所选版本的旧进程；“检查已有产物”传 `--skip-build --no-launch`，沿用原脚本的纯检查行为。

Excel 的两种方式都持续提供 HTTPS 服务。手动打开方式传 `--no-launch`，默认仍准备证书、注册加载项并生成工作簿；只有勾选“跳过加载项注册与工作簿生成”才同时省去后两步，此时也不会自动打开工作簿。该服务运行中时，相同 Excel 条目不能再次启动。关闭启动中心后服务会继续运行；如需手动管理服务，可在终端使用原脚本，按 `Ctrl+C` 退出。

## 编辑配置与恢复备份

点击“维护靶场与选项”打开内置配置编辑器，修改后点击“校验配置”，再“保存并重新加载”。“添加靶场模板”可作为起点；保存前需改为实际存在的脚本和参数。校验失败时先按提示修正 JSON 或字段，保持当前可用配置。

成功保存会先备份原配置到 `tools/ranges.json.bak`，再原子替换 `tools/ranges.json`。备份为最近一次保存前的版本，多次保存会更新备份。恢复时关闭配置编辑器，将备份内容复制回 `tools/ranges.json`，再在启动中心重新加载；也可在仓库根目录执行：

```powershell
Copy-Item -LiteralPath .\tools\ranges.json.bak -Destination .\tools\ranges.json
uv run .\tools\start.py --check
```

也可使用文本编辑器修改 JSON。清单必须是 UTF-8 JSON，不能带注释或末尾逗号。手动编辑不会触发内置保存备份，应先自行复制一份。界面保存的个人选择位于仓库 `.private` 中，与这里维护的默认清单分开。

如果外部编辑器把文件保存成 UTF-16 或 GBK，启动中心会报告编码错误，维护编辑器可尝试解码并显示转换说明。检查文字后保存可转为 UTF-8，备份仍保留转换前的原始字节。

## 清单结构

顶层为 `{"schema_version": 1, "ranges": [...]}`。每个靶场必须包含以下字段：

| 字段 | 含义 |
| --- | --- |
| `id` | 清单内唯一且稳定的标识；用于关联界面选择和任务 |
| `label`、`category`、`description` | 显示名称、分类和说明 |
| `command` | 非空字符串数组；每个数组元素是一个独立命令参数 |
| `cwd` | 工作目录；相对路径以仓库根目录解析，通常为 `"."` |
| `profiles` | 至少一个启动方式，每项含唯一 `id`、显示 `label`、字符串数组 `args` |
| `default_profile` | `profiles` 中某个方式的 `id` |
| `options` | 选项数组，没有额外选项时使用 `[]` |

命令可使用 `{python}`（当前 Python）、`{root}`（仓库根目录）和 `{powershell}`（可用的 PowerShell）。默认清单仅需前两个。不要给占位符额外套引号，带空格的路径也应保持一个数组元素。执行顺序为 `command`、当前方式的 `args`、适用选项的参数，启动时使用参数数组。

每个 option 都含 `id`、`label`、`type`、`flag`、`default`，还可使用 `required`、`profiles`、`min`、`max`、`choices` 和 `clearable`。选项的 `profiles` 是适用方式的 ID 列表；省略则适用于所有方式。切换到其他方式后，该选项不生成参数。

省略 `clearable` 时，`bool` 和 `multi` 默认可清空，`choice`、`text`、`integer` 默认保留；也可显式设置 `true` 或 `false`。默认清单对构建配置、WEB 地址、工具路径和端口均显式设置了 `clearable: false`。加载设置或清空时，受保护字段的空文本或 `null` 会补回配置默认值，过期的单选值也会恢复默认选项。合法的自定义基础配置会保留；版本多选清空后会保持为空，直到用户重新勾选。

| `type` | `default` 示例 | 生成参数及约束 |
| --- | --- | --- |
| `choice` | `"Release"` | `--configuration Release`；`choices` 是 `{value,label}` 对象数组，默认值必须是其中一个 `value` |
| `multi` | `["uia"]` | `--backends uia msaa`；每个值分别传参，必须属于 `choices`；`required: true` 时不能全不选 |
| `text` | `""` | 非空时生成 `--compiler-path` 和整段文本两个参数；可选空文本不传参数，`required: true` 时须填写 |
| `bool` | `false` | 为 `true` 时只生成 `--no-launch` 这样的开关，为 `false` 时不传该开关 |
| `integer` | `7300` | `--port 7300`；可用 `min`、`max` 限定整数范围 |

`flag` 必须是底层脚本真实支持的参数。`bool` 适合 `store_true` 类型的开关；需要固定参数组合时，应把组合放在 profile 的 `args` 中。启动中心只验证清单结构与选项值，脚本自身还会检查产物、网址、工具版本或参数组合等业务条件。

## 添加一个靶场

下面是一项完整模板。先创建相应的 `tools/start_my_range.py`，确保它接受示例中的参数；再把对象加入 `ranges` 数组并校验。模板不会添加到默认九项中，也不会自动执行。

```json
{
  "id": "my-range",
  "label": "我的靶场",
  "category": "自定义",
  "description": "说明运行要求和默认行为。",
  "command": ["{python}", "{root}/tools/start_my_range.py"],
  "cwd": ".",
  "profiles": [
    {"id": "run", "label": "运行已有产物", "args": ["--skip-build"]},
    {"id": "build", "label": "构建并启动", "args": []}
  ],
  "default_profile": "run",
  "options": [
    {
      "id": "configuration", "label": "构建配置", "type": "choice", "flag": "--configuration", "default": "Release",
      "choices": [{"value": "Release", "label": "Release"}, {"value": "Debug", "label": "Debug"}]
    },
    {
      "id": "versions", "label": "版本", "type": "multi", "flag": "--versions", "default": ["stable"], "required": true,
      "choices": [{"value": "stable", "label": "稳定版"}, {"value": "preview", "label": "预览版"}]
    },
    {"id": "data_dir", "label": "数据目录", "type": "text", "flag": "--data-dir", "default": ""},
    {"id": "force_build", "label": "强制构建", "type": "bool", "flag": "--force-build", "default": false, "profiles": ["build"]},
    {"id": "port", "label": "端口", "type": "integer", "flag": "--port", "default": 8000, "min": 1, "max": 65535}
  ]
}
```

先对照脚本的 `argparse` 定义或 `--help` 核实每个参数及允许值，再在启动中心查看生成命令。多版本脚本需显式传版本，互斥参数应通过启动方式或 `profiles` 限制避免同时出现。不能仅凭 JSON 通过校验认定目标程序已经可用。

维护时可先运行无 GUI 配置检查；隐藏界面构造检查需要 Tcl/Tk：

```powershell
uv run .\tools\start.py --check
uv run .\tools\start.py --self-test
```

`--check` 检查清单，`--self-test` 检查启动中心隐藏窗口的构造；二者均不启动真实靶场。它们不能替代用户勾选启动及窗口内的人工验收。
