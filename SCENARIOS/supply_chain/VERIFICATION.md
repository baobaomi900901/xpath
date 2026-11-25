# 开发验收记录

日期：2026-11-17。Windows，本机已安装的 MSVC / CMake / JDK8 / Node / Python，以及 UIAutoma CLI / Runtime 0.1.1。

## 自动检查

- Python unittest：24项通过，含真实XLSX、HTTP全流程、独立验收正反例、跨轮次旧文件拒绝、库存交接哈希、报价保存确认、重复单防止、标准/增强档seed42参考采购和503重试。
- Web Node测试：4项通过（分页、数值排序、完整查询导出、重置）。JS语法检查通过。
- Win32 Release编译通过，CTest 1/1通过（UTF-8 TSV、金额排序、真实二进制保存及保存失败）。
- Java8 source/target编译通过，PurchaseModelTest与PurchaseHttpTest通过（行身份、异步代次、金额、表单编码、真实503→201传输）。
- 启动、任务生成、空白轮次不通过验收、停止、历史结果保留均已执行。
- 业务服务与界面独立代码审查完成，重要问题修复后复核无剩余重要问题。

## 基础档真实 GUI 全流程

使用你的 UIAutoma GUI CLI 操作，界面阶段没有直接调用业务HTTP接口或写入内部订单状态：

1. Chrome通过已连接的UIAutoma浏览器通道打开A，读取库存，点击导出下载真实XLSX（2027字节）。
2. B 原生打开对话框选择该文件，显示4条库存；分别查询M001/M003；原生另存为对话框保存报价XLSX，界面提示已保存。
3. C Swing输入供应商，编辑采购明细，确认金额1200.00，提交并看到订单号与待审批提示。
4. C 将下一单改为另一供应商及物料，确认金额500.00，提交；在订单列表点击刷新，读到两张订单、金额及待审批状态。
5. 组织者运行离线 `evaluate`，结果：**passed=true，business_pass=true，workflow_pass=true，2张采购单，总金额1700.00**。

对应历史运行目录：`runtime/runs/2b0df9a568d1481bb6b0ce2205ce49d2/`，保留 `evaluation.json` / `evaluation.md`、原始状态与任务。GUI下载文件和截图在忽略的runtime目录中。此轮用于开发验收，未统计Agent推理/Token/费用，也不构成模型排名。

实测的Swing JTable单元格通过JAB呈现为renderer label，直接对label调用input会报element_readonly。正常GUI操作可以先进入单元格编辑，再通过键盘/剪贴板输入，移焦提交编辑；该方式已完成两单。参测Agent需要自行选择适合工具能力的操作方式。

初始沙箱内启动曾出现Windows GUI初始化错误0xc0000142，前台激活失败。通过正常桌面进程启动后，前台激活、控件树与完整流程均通过。请从Windows普通桌面终端启动靶场再进行Agent评测。

标准与增强档完整数据和业务结果已有自动化回归；未逐项运行其完整GUI流程。SDK赛道未额外跑一轮GUI验收。生产资产不依赖UIAutoma，其他GUI CLI/SDK也可按相同业务任务参测。

## 可选障碍模式增量验收

新增启动参数 `--obstacles`，默认关闭。本轮回归：Python27项、Web7项、CTest1项、Java Model/HTTP/Lazy三组全部通过。Lazy组包含真实1200ms Swing定时器、重复激活/页面复用/关闭取消，以及任务信息早于/晚于表单创建的测试。固定seed的库存/报价/供应商在开关两侧保持相同。

已在普通桌面以 `advanced --seed 42 --obstacles` 启动，通过UIAutoma CLI实测：

- Win32初始树只有入口/状态/菜单，没有业务Edit/List；点击进入后观察到加载提示及禁用入口，随后出现实际业务控件，表格名称正确。
- Java首次选择异常登记与采购页均观察到仅有加载占位，之后才出现表单。采购页从未创建时成功登记M099异常；随后采购页读取到正确批次及一号仓。供应商录入S003，切走再切回仍为S003，无重复加载。
- Web两次刷新业务元素UUID不同；业务元素ID均带随机前缀，ARIA标题与datalist关联无断链。查询M099得到1条、重置得到28条、每页8条，GUI点击下载真实XLSX（3268字节）。浏览器扩展后续注入的外部元素不作为业务元素验收。
- 配置保存在 `runtime/runs/6d4724c12beb455886f0c54b1010d59e/` 的context与metadata，历史运行不会覆盖。

本增量验证覆盖障碍本身、页面状态及文件下载，未在障碍模式重新完成全部采购单。原基础业务完整GUI验收记录见上文。

## Win32 按需 UIA / MSAA 增量验收

2026-11-17，对供应链 B 客户端实现独立的默认静默、按请求构建 Provider 层。与 `--obstacles` 的业务控件延迟创建相互独立，详细操作与平台边界见 [Win32 无障碍说明](win32/ACCESSIBILITY.md)。

- Release 应用、Provider 库、原生测试及进程外探针均编译通过。最终 CTest **2/2通过**（supplier-model / supplier-accessibility），Python **27项通过**；本轮未修改 Web / Java 源码。
- 原生测试验证非目标对象ID不激活、32位对象ID的符号/零扩展、根对象复用、24线程工厂身份一致、弱缓存释放、数据代次失效、空闲回收及旧COM引用安全。1000行列表仅请求根时1个节点，查找第900行后2个，访问单元格后3个；没有预建1000行。还验证原生按钮/输入框、表头动作与命中、单元格边界及MSAA选择/焦点语义。
- 普通桌面进程外探针实测：新启动目标的 active / live / total / roots / 应用事件 / 原生委托计数均为0；UIA根请求后只有1个根节点。释放引用后等待35秒，active和live均回到0、退休次数增加；再次请求创建新根。MSAA OBJID_CLIENT根及子项、UIA RawViewWalker首个子项均跨进程成功。探针结果示例保存在忽略的 `runtime/a11y-final-msaa.txt` 和 `runtime/a11y-final-uia.txt`。
- 实际 UIAutoma CLI 遍历发现过 HWND 片段重复拼接，已修复并加入回归：UIA交给系统host拼接子HWND，MSAA单独保留子窗口枚举。修复后初始完整树为23个后代，truncated=false / budget_exhausted=false，未重复；导入后库存表的表头、4行和各单元格可读，报价表的3行、12列表头/单元格及offscreen状态可读。
- 本轮GUI通过A导出2026字节库存XLSX，原生打开对话框导入B，库存显示4行；通过Value输入M001并查询，显示3条报价与1个已查询物料。最终报价XLSX为2621字节，包含Q003/Q001/Q002三条M001报价，SHA-256与服务的quote_file_saved事件相符，界面显示已保存。另存为阶段用户也有操作，且工具返回过automation_input_failed / stale_node，因此此段保存结果**不记为无人工介入的Agent成功**；未据此重算评测得分。
- 本轮运行目录：`runtime/runs/1052a562dd48494e80aa60382c324139/`。没有重新执行Java采购或完整业务判分；本次验证集中于Win32改造及A→B文件交接。

本模块没有主动发出UIA / MSAA树事件；Windows自带HWND、标题栏、标准控件代理及其事件仍由系统管理。Inspect读取树本身会激活Provider，不能用Inspect已经遍历后的状态证明“启动时未创建”。30秒无访问租期是回收策略，不是精确的客户端断开通知；持有但长期未访问的旧引用会失效，需要重新定位。没有进行完整性能/内存基准，不宣称已证明启动性能显著提升。代码审查发现的问题已修复并复核，实际外部树遍历也已重验。
