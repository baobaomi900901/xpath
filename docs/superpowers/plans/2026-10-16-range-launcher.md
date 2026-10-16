# 靶场启动中心 Implementation Plan

> **For agentic workers:** Use focused parallel implementation for the independent core and catalog, then integrate the Tk interface and review it.

**Goal:** 用一个 Windows 桌面程序勾选并启动现有 tools 靶场，并通过可编辑、可校验的配置维护后续靶场与选项。

**Architecture:** Tk/ttk 提供靶场清单、动态选项、命令预览、运行日志和配置编辑器。配置负责描述现有脚本的非交互命令；进程模块以参数数组启动，输出写入独立日志，界面定期读取。关闭启动中心不会结束已启动的程序。

**Tech Stack:** Python 3.8+ 标准库、tkinter/ttk、JSON、subprocess。

## Global Constraints

- 不使用 OCR，不模拟靶场内鼠标操作；完整应用交互由用户人工测试。
- 保持现有各靶场启动脚本及命令行参数兼容。
- 无第三方 Python 依赖；入口为 `uv run .\tools\start.py`。
- 本次纳入 tools 中九个靶场启动脚本；路径基于仓库根目录解析，不依赖当前工作目录。
- 不提交、推送或修改其他项目；不结束用户已启动的应用。

## 接口与文件

- `tools/range_launcher/config.py`: `load_catalog(Path)->dict`, `validate_catalog(dict)->None`, `save_catalog(Path,dict)->None`（校验、备份及原子替换）, `default_values(item)->dict`, `build_command(item,profile_id,values,repo_root,python_executable)->(list[str],Path)`。
- JSON 顶层 `schema_version:1, ranges:[]`。每项含 `id,label,category,description,command,cwd,profiles,default_profile,options`；profile 含 `id,label,args`；option 含 `id,label,type,flag,default`，支持 `choice,multi,text,bool,integer`，选择项为 `choices:[{value,label}]`，可选 `required,profiles,min,max`。
- 命令占位符 `{python}`、`{root}`、`{powershell}`；profile 参数在 option 参数之前。未适用于当前 profile 的 option 不生成参数；必填多选不可为空。
- `tools/range_launcher/runner.py`: `Runner(log_dir)`，`.jobs` 字典，`.start(id,label,command,cwd)->Job`，`.poll()->list[dict]`。Job 含 id,label,command,cwd,log_path,state,returncode；state 为 running/succeeded/failed。事件包含 id,kind(output/status),text,state,returncode。
- `tools/ranges.json` 描述九个靶场；`tools/RANGE_LAUNCHER.md` 描述扩展方法。
- `tools/range_launcher/app.py` 提供 Tk 窗口；`tools/start.py` 提供入口及无 GUI 的 `--check` 配置检查、`--self-test` 隐藏界面构造检查。

## Task 1: 配置与进程核心

- [x] 编写并运行失败测试：缺失/重复 ID、非法 profile/默认值、非交互命令生成、中文与空格参数、失败退出、运行中重复启动、日志输出。
- [x] 实现配置校验、命令构建、原子保存和日志进程管理。
- [x] 用实际短生命周期 Python 子进程验证返回码、输出和参数，禁止 shell 拼接。

## Task 2: 靶场清单与维护说明

- [x] 根据实际 argparse 参数覆盖 Win32/Tk/Java/CEF/Electron/Delphi/PowerBuilder/WebView2/Excel。
- [x] 多版本脚本始终生成明确版本参数，避免进入控制台交互菜单。
- [x] 编写 JSON 模板、选项类型及备份恢复说明。

## Task 3: Tk 界面

- [x] 实现搜索、分类、实际勾选控件、版本/启动方式选项、命令预览与批量启动。
- [x] 用 after 读取任务和日志，保持界面响应，保留其他任务的错误信息。
- [x] 实现配置编辑、添加模板、校验保存及重新加载，保存界面选项到 .private。
- [x] 入口处理 Tk 缺失错误，并支持配置检查与隐藏窗口结构自检。

## Task 4: 集成验证与交付

- [x] 运行核心测试、九个条目的参数兼容检查及 Tk 隐藏界面自检。
- [x] 审查异步进程生命周期、配置错误恢复和命令引用，修复确定问题。
- [x] 更新根 README，交付 uv 启动命令与维护配置路径；真实靶场由用户勾选启动并人工测试。

## 验证结果

2026-10-16：用户的 uv Python 3.13 / Tk 8.6 环境中，25 项核心测试与 10 项隐藏界面测试通过；完整隐藏界面自检覆盖 9 个靶场、24 个启动方式，未启动真实靶场。端到端检查从隐藏启动中心调用 PowerBuilder 的 `--mode exe --no-launch` 成功，确认命令、子进程和日志链路。审查发现的非 UTF-8 配置恢复问题已修复，并验证 UTF-16 / GB18030 转换及原字节备份。
