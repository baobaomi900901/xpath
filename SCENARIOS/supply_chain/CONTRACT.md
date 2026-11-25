# 库存补货综合靶场：组件约定

已确认目标：用同一业务任务评估不同 Agent 使用 GUI CLI / SDK 跨 Web、原生 Win32、Java Swing 的能力。业务数据只能通过界面查询与正常导出文件取得；内部 HTTP 接口是应用实现细节，禁止参测 Agent 直接访问。

## 目录与运行方式

独立场景目录 `SCENARIOS/supply_chain/`，不改变原有各类控件靶场。Python 标准库服务绑定 `127.0.0.1`，默认端口 8765，托管 A 网页、业务数据、xlsx 导出、订单存储。B 为原生 Win32 C++，C 为 Java 8 兼容 Swing。两个桌面程序参数均为 `--url http://127.0.0.1:8765`。所有 API 响应 UTF-8；桌面端使用 TSV 避免新增 JSON 库。TSV 首行为下面约定的英文列名，字段不含制表符和换行。

## API

- `GET /api/context`：JSON `{run_id,batch_id,today,deadline,profile,seed,plant,warehouse}`。默认 plant=`华东工厂`，warehouse=`一号仓`。
- `GET /api/context?format=tsv`：一条记录，列 `run_id,batch_id,today,deadline,profile,seed,plant,warehouse`。
- `GET /api/inventory?plant=...&warehouse=...&search=...`：JSON `{rows:[...]}`，行字段 `material_id,name,unit,plant,warehouse,current,safety,target,enabled`；enabled 为 boolean。服务返回全部匹配行，Web 自己分页；查询参数空时不过滤。不提供建议采购数量。
- `GET /api/export/inventory?plant=...&warehouse=...&search=...`：真实 xlsx，工作表 `库存明细`，首行列 `batch_id,material_id,name,unit,plant,warehouse,current,safety,target,enabled`；为查询范围全部行，不只当前页。
- `POST /api/import/inventory`：body 为 xlsx 原始字节，Content-Type `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet`。校验表头、批次、物料编码、完整数据是否与库存一致；成功返回 TSV（列同 inventory 加 batch_id，列顺序同导出）。包含所有导入行，由 Agent 判断需要查询哪些物料。失败 HTTP 400 UTF-8 文本。
- `GET /api/quotes?material_id=...&format=tsv`：列 `quote_id,material_id,supplier_id,supplier_name,unit_price,available,moq,lead_days,valid_until,active,currency,unit`。无 material_id 返回全部报价。active 为 `true` / `false`，价格为两位小数人民币含税价；不标识最佳报价。
- `GET /api/export/quotes?material_ids=M001,M003`：xlsx `报价明细`，列同 quotes，另有 `批次信息` 工作表；传入物料集合导出所有候选报价，不标最佳供应商。未传入物料集合返回 400，避免无意导出全库。
- `GET /api/suppliers?format=tsv`：列 `supplier_id,name,active`。
- `POST /api/confirm/quotes`：B 成功写入、flush并关闭保存文件后，上传同一 xlsx 原始字节，服务按 SHA-256 与此前生成文件匹配并记录保存确认；成功纯文本 `报价文件保存已确认`。此端点仅是应用内遥测，不是参测 Agent 工具。
- `GET /api/materials?format=tsv`：列 `material_id,name,unit`（仅本任务工厂仓库启用物料）。
- `GET /api/orders?format=tsv`：列 `order_id,batch_id,supplier_id,supplier_name,warehouse,delivery_date,total,status,lines`。lines 是人可读中文摘要，表格用于回查；状态为 `待审批`。
- `GET /api/orders`：JSON `{rows:[order...]}`，含真实 lines 数组。
- `POST /api/orders`：`application/x-www-form-urlencoded`，字段 `batch_id,supplier_id,warehouse,delivery_date,notes,lines`。lines 为多行 TSV，无表头，每行 `material_id\tquantity\tunit_price\tquote_id`。成功 HTTP 201 TSV 一行，列 `order_id,total,status`；校验失败 HTTP 400 UTF-8 文本；增强档首次合法提交注入 HTTP 503（重试可成功），不创建订单。
- `POST /api/exceptions`：form 字段 `batch_id,material_id,reason`；记录无合格供应商等未处理事项，成功 HTTP 201 UTF-8 文本。C 提供异常登记界面。同物料重复登记更新记录。
- `GET /health`：JSON `{status:"ok",run_id}`。

所有响应 `Cache-Control: no-store`。错误正文 UTF-8 纯文本。API 不公开标准答案和评分。订单只校验真实采购约束：有效批次、供应商、物料、报价、价格匹配、数量为正整数、起订量、库存、有效日期、交期、目标仓库；不强制最佳供应商或恰好补货数量，这些由独立验收判断。阻止同批次同物料重复采购，不允许空单。单价与金额以整数分/Decimal 处理。提交日期不晚于任务 deadline 且不早于 today + lead_days。

## 业务与数据

触发：enabled 且 current < safety；quantity=target-current。合格报价：active、有效期 >= today、available >= quantity、quantity >= moq、today+lead_days <= deadline、CNY、计量单位一致。选最低价，其次最短交期，其次 supplier_id。同供应商合并订单。无法采购的物料登记异常。提交成功后回查确认，不更新库存。

三档 basic / standard / advanced，固定任务日期 2026-11-17，截止 2026-11-24，不依赖执行机器日期。基础 4 行：M001 current40/safety80/target160；M002 150/100/200；M003 20/60/120；M004 60/60/120。M001 合格最优 S001=10.00，S002=9.00 但供货80，S003=11.00；M003 最优 S003=5.00，S001=6.00。标准档扩展至少 24 行、同名物料、干扰工厂仓库、过期/停用/交期过长/起订量/单位不一致报价、价格平手。增强档增加无合格供应商物料及一次提交失败。seed 只确定数据与排序，所有 Agent 相同 seed 数据相同。

## 界面要求

A：完整中文业务网页，工厂/仓库/关键字筛选、查询/重置、可排序库存表、每页8条分页、导出全部查询结果、加载与错误反馈。无最佳补货提示。可见任务批次和业务日期。使用语义化标签和标准 HTML 控件，适配桌面窗口。文件直接由浏览器下载。

B：真正 Win32 标准控件（非 WebView/Tk）。文件菜单、导入库存文件按钮与原生打开对话框、导入库存列表、物料编码查询、报价表格（支持单价排序）、详情弹窗、导出已查询物料报价（原生保存对话框）、状态栏。导入行仅提供库存原值，不自动选最优。查询到的物料集合跨查询保留，用于导出；导入新文件清空集合。保存 .xlsx 二进制。

C：真正 Swing。订单列表/新建采购单/异常登记；供应商选择对话框、批次与仓库与交货日期、可编辑明细表（material_id,quantity,unit_price,quote_id），增行删行、金额实时计算、提交确认、成功展示订单号、失败保留录入、订单刷新回查。供应商和物料可通过选择弹窗查询，不暴露最优方案。异常登记 material_id + reason。HTTP 不阻塞 EDT，错误可读，重试不清空数据。窗口和关键控件提供有意义的 accessible name。

## 评测

可选 `--obstacles`：默认关闭。创建运行时 context / metadata 记录 boolean `obstacles`，旧运行缺失时按false。serve从持久化context读取，并向B/C传递同名开关。B首次点击工作台入口、C首次激活页签时用非阻塞1200ms定时器真正创建业务控件。A在应用引导时随机化DOM IDs并维护标签/datalist/ARIA关联；应用闭包持有控件引用。障碍不改变库存、报价、供应商或验收业务规则，Web ID不使用业务seed固定。

评测端离线读取持久化状态与 fixture，以独立规则计算预期（不能调用订单提交/推荐函数），报告采购遗漏/多余/数量/供应商/金额/分单/异常登记、导出与导入事件、失败与重试事件。结果 JSON 和 Markdown，未通过退出码1。运行元数据包含 agent、track(cli/sdk)、seed、profile；不伪造 token/成本/GUI工具调用数，这些由外部记录导入或注明未采集。内部事件不证明工具使用合规，合规由外部执行轨迹审计。

重置生成独立 runtime/run 目录，默认忽略 git。每次执行先关闭旧应用服务；新运行不同 run_id，固定 seed 可复现。启动器构建所需 EXE/class，启动服务与三个应用，集成 tools/ranges.json。参测任务文件与评测说明分离，任务文件不包含答案和内部接口。
