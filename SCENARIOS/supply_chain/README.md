# 库存补货综合 GUI 靶场

用于比较不同 Agent 使用 GUI 自动化 CLI / SDK，跨 **Web → 原生 Win32 → Java Swing** 完成同一业务任务的能力。不是自动完成采购的示例脚本；选物料、计算数量、比较报价、分供应商建单都由参测 Agent 决定。

## 启动

在仓库根目录的 Windows 桌面终端执行：

```powershell
python tools/start_supply_chain.py launch --profile standard --seed 42 --agent agent-a --track cli
```

首次启动自动构建 Win32 EXE、Java class，启动本地服务、B/C 桌面窗口并用默认浏览器打开 A。默认地址为 `http://127.0.0.1:8765`，可通过 `--port` 修改。也可在统一启动中心 `python tools/start.py` 选择「综合场景：库存补货」。

需要 Python 3.10+、CMake 3.16+、MSVC C++ 工具，以及 JDK 8+。无需新增 Python、npm 或 Maven 依赖，不下载构建工具。Java 优先使用 JAVA_HOME、PATH 中的 JDK，再检查本仓库已有的 Corretto。Win32 靶场不支持 Linux/macOS。

```powershell
# 首次单独构建；会先停止当前场景，释放正在运行的 EXE
python tools/start_supply_chain.py build

# 使用现有产物，为另一个 Agent 创建新一轮数据
python tools/start_supply_chain.py launch --skip-build --profile standard --seed 42 --agent agent-b --track sdk

# 查看当前轮次给 Agent 的任务文本
python tools/start_supply_chain.py task

# 验收当前轮次，成功退出0，业务/流程未通过退出1，运行错误退出2
python tools/start_supply_chain.py evaluate

# 停止当前服务和由该服务启动的 B/C，保留结果；浏览器标签页需自行关闭
python tools/start_supply_chain.py stop
```

每次 `launch` 自动停止上一轮，创建全新的运行目录和批次号。相同 profile/seed 的业务数据完全相同，运行标识不同，旧轮次文件不可混用。不同 Agent 应使用相同 profile/seed/工具文档/时间预算，并各自执行多次。

## 可选 GUI 障碍

启动时加 `--obstacles`：

```powershell
python tools/start_supply_chain.py launch --profile standard --seed 42 --agent agent-a --track cli --obstacles
```

也可在启动中心勾选「GUI障碍（惰性加载 / 随机ID）」。不加参数时保留原来的加载方式和网页ID。障碍独立于业务难度，basic / standard / advanced均可组合使用。

- **Win32**：初始仅显示入口及状态。点击「进入报价工作台」后显示加载提示，1200毫秒后才创建业务输入框、表格和操作按钮；这些控件在加载前不存在于窗口/无障碍树中。
- **Java**：页签首次被选中后显示加载提示，1200毫秒后才创建该页业务控件；未访问的页签保留占位，已创建页面的录入内容在切换后保留。初始选中的订单页也走同一加载流程。
- **Web**：每次刷新重新随机生成全部已有元素ID。可见文案、字段名称和业务数据保持一致，标签、候选列表、ARIA引用同步更新。Agent需要依据当前界面定位，固定ID不再跨刷新有效。

桌面加载采用非阻塞UI定时器，重复点击不会创建多份控件。加载延迟固定，便于对比；网页ID刻意每次刷新变化，不由业务seed固定。`metadata.json`及验收报告记录是否启用障碍。比较不同Agent时应统一该开关。

## Win32 按需无障碍 Provider

供应商客户端的应用 Provider 默认按请求创建，与上述业务控件加载开关独立。每个应用 HWND 在首次有效 UIA/MSAA 请求前只保存轻量状态；根、列表行和单元格按访问创建，列表重建后旧代次失效。回收采用 COM 引用安全及空闲租期策略。

Windows 自身仍可能暴露窗口、标题栏等系统代理；Inspect 获取树本身就会激活对应请求。可用独立诊断探针检查请求前创建计数，详见 [Win32 Provider 实现与验证](win32/ACCESSIBILITY.md)。

`reset` 只停止旧轮次并创建一个空白批次、生成任务文件，不启动应用；普通评测直接使用 `launch` 即可。历史运行目录可传给 `evaluate --run-dir <目录>` 和 `task --run-dir <目录>`。

默认后台服务无控制台窗口。`--foreground` 在当前终端运行，Ctrl+C 结束服务与所属桌面应用。`--no-browser` 不自动开浏览器；`--no-apps --no-browser` 仅运行服务，供开发测试使用。受限 Agent 沙箱可能无法初始化 Windows GUI（例如 0xc0000142），请从正常桌面终端启动靶场，再让 Agent 接管；启动器会检测桌面进程立即退出并报告错误。

## 三个系统

| 系统 | 界面与业务 | Agent 需要完成 |
|---|---|---|
| A 库存管理 | 本地 Web；工厂/仓库/关键字、排序、每页8条、导出全查询结果 | 查询目标范围，导出真实 XLSX，自行识别缺料和计算补货数量 |
| B 供应商报价 | C++ Win32 标准控件；原生文件菜单/打开/保存对话框、库存/报价表、单价排序、详情弹窗 | 导入 A 文件，选择缺料物料，查询报价，判断合格最低价，导出已查询物料的全部报价 |
| C 采购管理 | Java Swing；订单回查、供应商/物料选择弹窗、可编辑明细、确认/错误弹窗、异常登记 | 按供应商合并订单，逐行录入，提交审批、失败恢复、回查确认、登记无法采购物料 |

系统无需账号。任务业务日期固定为 **2026-11-17**，交货截止 **2026-11-24**，不依赖电脑当天日期。当前库存按可用库存口径；不另算在途或占用。

触发条件：启用物料、目标工厂/仓库、当前可用库存 **低于** 安全库存。数量＝目标库存－当前可用库存。等于安全库存不采购。

报价必须：供应商与报价启用、未过期、起订量≤采购数量≤可供数量、业务日期+供货天数≤交货日期、CNY含税且单位一致。先比单价，再比供货天数，再按供应商编码升序。每种物料只选一家完整供货的供应商。同供应商合并一张采购单，没有合格供应商的物料登记异常。

系统 C 做正常采购校验，不替 Agent 强制选最优供应商或正确补货数量。合法但决策错误的订单可以被提交，独立验收会判错。同批次同物料重复采购会被阻止。提交后状态「待审批」，不修改库存。

## 档位

| profile | 数据与挑战 |
|---|---|
| basic | 4项物料，包含无需采购、等于安全库存、低价但数量不足；适合工具入门和排查 |
| standard | 24项目标启用物料，加其他工厂/仓库/停用干扰；多页、同名物料、价格平手、失效/停用/交期/起订量/单位/币种干扰报价 |
| advanced | 标准档加无合格供应商物料；首次合法提交注入一次503且不创建订单，要求保留录入、确认状态后恢复 |

正常加载、桌面切换、文件定位、横向表格滚动和多供应商分单是标准场景的一部分。自绘/OCR专测可使用仓库原有靶场，本场景保持标准控件便于定位失败原因。

## 参测输入与组织者资料

启动器输出 `runtime/runs/<运行ID>/task.md`，这是可交给 Agent 的具体任务，包含真实批次、入口、规则和所选赛道，不包含按钮步骤和标准答案。另向 Agent 提供你的 CLI 或 SDK 文档、工具入口、导出文件保存目录及统一时间预算。允许读取正常导出文件和脚本编排；界面观察/定位/操作必须经过指定 GUI 工具。

`CONTRACT.md`、源码、fixture/state、评分报告及运行控制文件属于组织者资料，不能作为参测输入。实际评测建议让 Agent 从独立工作目录执行，只开放工具文档与导出目录，并由外部工具轨迹核查是否绕过 GUI。此仓库是可调试靶场，不提供对恶意同用户进程的安全隔离。

运行目录包含：

- `fixture.json`：固定业务数据；`metadata.json`：Agent、赛道、seed、档位、创建时间。
- `state.json`：真实采购单、异常和持久化业务事件；写入采用临时文件替换。
- `task.md`：参测任务；`service.log` / `app-*.log`：启动日志。
- `evaluation.json` / `evaluation.md`：执行验收命令后生成的机器与人工报告。

`runtime/` 和 `build/` 均不纳入 Git。重置不会删除历史记录。

## 独立验收

离线 evaluator 不调用提交校验或推荐函数，独立计算缺料、最优报价与订单归属，检查：

- 物料有无遗漏/多买/重复，数量、供应商、单价、报价编号、明细/订单金额是否准确。
- 是否按供应商合并，批次/仓库/交货日期/待审批状态是否正确，异常登记是否对应无法采购物料。
- 完整目标库存是否从 A 导出并由 B 导入**同一文件**（SHA-256关联且先导出后导入），防止只凑齐物料编号便通过。
- 缺料是否查询并导出报价；B 必须在文件成功写入、flush关闭后确认保存，生成过文件但本地保存失败不算成功。
- 创建的订单是否在订单列表回查中出现；增强档是否覆盖提交失败恢复。

`business_pass` 和 `workflow_pass` 分开报告，二者均通过才 `passed=true`。金额使用 Decimal，不依赖浮点累计。

内部事件只记录业务应用发生的操作，**不是 GUI 工具调用轨迹**。工具调用量、无效调用、Token、费用、人工介入、工具使用合规须由外部运行器采集，报告中未采集项为 null。内置耗时为创建运行至最后业务事件，包含准备/空闲时间，不用于冒充纯 Agent 推理耗时。

## 开发验证

在仓库根目录执行：

```powershell
python -m unittest discover -s SCENARIOS/supply_chain/tests -v
python tools/start_supply_chain.py build
ctest --test-dir SCENARIOS/supply_chain/build/win32 -C Release --output-on-failure
node SCENARIOS/supply_chain/web/model.test.cjs
node SCENARIOS/supply_chain/web/obstacles.test.cjs
java '-Djava.awt.headless=true' -cp SCENARIOS/supply_chain/build/java PurchaseModelTest
java '-Djava.awt.headless=true' -cp SCENARIOS/supply_chain/build/java PurchaseHttpTest
java '-Djava.awt.headless=true' -cp SCENARIOS/supply_chain/build/java PurchaseLazyTest
```

Python 验证业务与文件格式、HTTP导出/导入/下单/回查、重置隔离及独立判分；Node验证分页/排序/导出范围/重置；原生测试验证TSV、金额及UIA/MSAA按需生命周期；Java验证表格模型、金额、UTF-8传输和503重试。接口测试是组织者验证，不代表参测 Agent 可以绕过界面。

已用UIAutoma GUI CLI跑通基础档的完整桌面流程，得到2张待审批采购单，总金额1700.00，离线验收通过。详细证据与尚未覆盖的GUI变体见 [开发验收记录](VERIFICATION.md)。
