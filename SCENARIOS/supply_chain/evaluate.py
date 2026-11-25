"""Operator-only offline oracle. Intentionally does not import the submission domain."""
import json
from collections import Counter, defaultdict
from datetime import date, datetime, timedelta
from decimal import Decimal, InvalidOperation
from pathlib import Path


def evaluate(run_dir):
    path = Path(run_dir)
    fixture = json.loads((path / "fixture.json").read_text(encoding="utf-8"))
    state = json.loads((path / "state.json").read_text(encoding="utf-8"))
    metadata = json.loads((path / "metadata.json").read_text(encoding="utf-8"))
    context = fixture["context"]
    today, deadline = date.fromisoformat(context["today"]), date.fromisoformat(context["deadline"])
    active_suppliers = {s["supplier_id"] for s in fixture["suppliers"] if s["active"]}
    expected, blocked = {}, []
    for row in fixture["inventory"]:
        if not (row["enabled"] and row["plant"] == context["plant"] and row["warehouse"] == context["warehouse"] and row["current"] < row["safety"]):
            continue
        quantity = row["target"] - row["current"]
        candidates = [q for q in fixture["quotes"]
                      if q["material_id"] == row["material_id"] and q["supplier_id"] in active_suppliers and q["active"]
                      and q["currency"] == "CNY" and q["unit"] == row["unit"]
                      and q["moq"] <= quantity <= q["available"] and date.fromisoformat(q["valid_until"]) >= today
                      and today + timedelta(days=q["lead_days"]) <= deadline]
        if not candidates:
            blocked.append(row["material_id"])
            continue
        chosen = min(candidates, key=lambda q: (Decimal(q["unit_price"]), q["lead_days"], q["supplier_id"]))
        expected[row["material_id"]] = dict(quantity=quantity, supplier_id=chosen["supplier_id"],
                                            unit_price=chosen["unit_price"], quote_id=chosen["quote_id"],
                                            lead_days=chosen["lead_days"], name=row["name"], unit=row["unit"])
    issues, workflow_issues, found = [], [], defaultdict(list)
    orders = state["orders"]
    supplier_counts = Counter()
    actual_total = Decimal(0)
    for order in orders:
        supplier_counts[order.get("supplier_id")] += 1
        if order.get("batch_id") != context["batch_id"] or order.get("warehouse") != context["warehouse"] or order.get("status") != "待审批":
            issues.append(f"订单 {order.get('order_id')} 的批次、仓库或状态错误")
        try:
            delivery = date.fromisoformat(order.get("delivery_date", ""))
            valid_date = today <= delivery <= deadline
        except ValueError:
            delivery, valid_date = today, False
        if not valid_date:
            issues.append(f"订单 {order.get('order_id')} 交货日期无效")
        calculated = Decimal(0)
        if not order.get("lines"):
            issues.append(f"订单 {order.get('order_id')} 没有采购明细")
        for line in order.get("lines", []):
            mid = line.get("material_id")
            found[mid].append((order, line))
            try:
                quantity, unit_price = Decimal(str(line.get("quantity"))), Decimal(str(line.get("unit_price")))
                if not quantity.is_finite() or not unit_price.is_finite() or quantity <= 0 or quantity != quantity.to_integral_value() or unit_price <= 0:
                    raise ValueError()
                amount = quantity * unit_price
                calculated += amount
                if Decimal(str(line.get("amount"))) != amount:
                    issues.append(f"物料 {mid} 的明细金额错误")
            except (InvalidOperation, ValueError, TypeError):
                issues.append(f"物料 {mid} 的数量、单价或金额无效")
        try:
            if Decimal(str(order.get("total"))) != calculated:
                issues.append(f"订单 {order.get('order_id')} 总金额错误")
        except InvalidOperation:
            issues.append(f"订单 {order.get('order_id')} 总金额无效")
        actual_total += calculated
        for mid, item in expected.items():
            if any(line.get("material_id") == mid for line in order.get("lines", [])) and delivery < today + timedelta(days=item["lead_days"]):
                issues.append(f"物料 {mid} 的交货日期早于供货周期")
    for mid, item in expected.items():
        entries = found.get(mid, [])
        if len(entries) != 1:
            issues.append(f"物料 {mid} 应采购一次，实际 {len(entries)} 次（遗漏或重复）")
            continue
        order, line = entries[0]
        if line.get("quantity") != item["quantity"]:
            issues.append(f"物料 {mid} 采购数量错误：应为 {item['quantity']}")
        if order.get("supplier_id") != item["supplier_id"]:
            issues.append(f"物料 {mid} 未选择规则要求的最低价供应商")
        if line.get("unit_price") != item["unit_price"]:
            issues.append(f"物料 {mid} 单价错误：应为 {item['unit_price']}")
        if line.get("quote_id") != item["quote_id"]:
            issues.append(f"物料 {mid} 报价编号错误")
        if line.get("name") != item["name"] or line.get("unit") != item["unit"]:
            issues.append(f"物料 {mid} 名称或计量单位错误")
    for mid in set(found) - set(expected):
        issues.append(f"物料 {mid} 不应创建采购单")
    required_suppliers = {v["supplier_id"] for v in expected.values()}
    if set(supplier_counts) != required_suppliers or any(n != 1 for n in supplier_counts.values()):
        issues.append("采购单未按选定供应商各合并一单")
    exception_ids = [entry["material_id"] for entry in state["exceptions"] if entry.get("batch_id") == context["batch_id"] and entry.get("reason", "").strip()]
    if Counter(exception_ids) != Counter(blocked):
        issues.append(f"异常登记不匹配：应登记 {', '.join(sorted(blocked)) or '无'}")
    required_materials = set(expected) | set(blocked)
    events = state["events"]
    for kind, label in [("inventory_export", "库存导出"), ("inventory_import", "库存导入"), ("quote_query", "报价查询"), ("quote_export", "报价导出")]:
        coverage = {mid for event in events if event["kind"] == kind for mid in event.get("material_ids", [])}
        if not required_materials <= coverage:
            workflow_issues.append(f"{label}缺少物料：{', '.join(sorted(required_materials - coverage))}")
    # Link the actual files, rather than accepting disconnected material-ID unions.
    inventory_scope = {r["material_id"] for r in fixture["inventory"] if r["plant"] == context["plant"] and r["warehouse"] == context["warehouse"]}
    inventory_exports, quote_exports, saved_quotes = {}, {}, set()
    linked_inventory = False
    viewed_orders = set()
    for event in events:
        digest = event.get("sha256")
        ids = set(event.get("material_ids", []))
        if event["kind"] == "inventory_export" and digest:
            inventory_exports[digest] = ids
        elif event["kind"] == "inventory_import" and digest in inventory_exports:
            if inventory_scope <= ids and inventory_scope <= inventory_exports[digest]:
                linked_inventory = True
        elif event["kind"] == "quote_export" and digest:
            quote_exports[digest] = ids
        elif event["kind"] == "quote_file_saved" and digest in quote_exports:
            saved_quotes.update(ids & quote_exports[digest])
        elif event["kind"] == "orders_viewed":
            viewed_orders.update(event.get("order_ids", []))
    if not linked_inventory:
        workflow_issues.append("缺少完整任务库存文件从 A 导出到 B 导入的同文件交接证据")
    if not required_materials <= saved_quotes:
        workflow_issues.append("报价文件尚未确认成功保存，或未覆盖全部补货物料")
    if not {o["order_id"] for o in orders} <= viewed_orders:
        workflow_issues.append("采购单创建后尚未通过订单列表回查")
    if context["profile"] == "advanced" and not any(e["kind"] == "injected_failure" for e in events):
        workflow_issues.append("尚未覆盖增强档的提交失败恢复")
    elapsed = None
    if events:
        elapsed = round((datetime.fromisoformat(events[-1]["at"]) - datetime.fromisoformat(metadata["created_at"])).total_seconds(), 3)
    return dict(passed=not issues and not workflow_issues, business_pass=not issues, workflow_pass=not workflow_issues,
                issues=issues + workflow_issues, business_issues=issues, workflow_issues=workflow_issues,
                metadata=metadata, expected_order_count=len(required_suppliers), actual_order_count=len(orders),
                expected_line_count=len(expected), actual_line_count=sum(len(o.get("lines", [])) for o in orders),
                expected_total=f"{sum((Decimal(v['unit_price']) * v['quantity'] for v in expected.values()), Decimal(0)):.2f}",
                actual_total=f"{actual_total:.2f}", blocked_materials=sorted(blocked),
                metrics=dict(elapsed_to_last_business_event_seconds=elapsed, business_event_count=len(events),
                             rejected_submissions=sum(e["kind"] == "order_rejected" for e in events),
                             injected_failures=sum(e["kind"] == "injected_failure" for e in events),
                             gui_tool_calls=None, gui_tool_errors=None, tokens=None, cost=None, human_interventions=None),
                compliance="业务事件只能证明数据流转；CLI/SDK 使用合规、GUI调用、人工介入、Token与成本须结合外部执行轨迹审计。")


def write_report(run_dir, report):
    path = Path(run_dir)
    (path / "evaluation.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    lines = ["# 综合靶场验收", "", f"结果：{'通过' if report['passed'] else '未通过'}", "",
             f"Agent：{report['metadata']['agent']}；赛道：{report['metadata']['track']}；档位：{report['metadata']['profile']}；seed：{report['metadata']['seed']}；GUI障碍：{'开启' if report['metadata'].get('obstacles', False) else '关闭'}", "",
             f"采购单：{report['actual_order_count']} / {report['expected_order_count']}；明细：{report['actual_line_count']} / {report['expected_line_count']}；金额：{report['actual_total']} / {report['expected_total']}", ""]
    lines += ["- " + issue for issue in report["issues"]] or ["业务与文件交接检查全部通过。"]
    lines += ["", report["compliance"], "", "耗时从运行创建至最后业务事件，包含准备和空闲时间；不是纯 Agent 推理耗时。"]
    (path / "evaluation.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
