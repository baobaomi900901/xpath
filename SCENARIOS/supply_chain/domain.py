"""Persistence and normal business validation. Optimal procurement lives only in evaluation."""
import hashlib
import json
import re
import threading
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path

from .workbooks import INVENTORY_COLUMNS, QUOTE_COLUMNS, read_xlsx, write_xlsx


class BusinessError(ValueError):
    def __init__(self, message, status=400):
        super().__init__(message)
        self.status = status


def price(value):
    try:
        result = Decimal(str(value))
        if not result.is_finite() or result <= 0 or result > 100000000 or result != result.quantize(Decimal("0.01")):
            raise ValueError()
        return result
    except (InvalidOperation, ValueError):
        raise BusinessError("单价必须为大于零、至多两位小数的有效金额") from None


class Store:
    def __init__(self, path):
        self.path = Path(path)
        self.fixture = json.loads((self.path / "fixture.json").read_text(encoding="utf-8"))
        self.state = json.loads((self.path / "state.json").read_text(encoding="utf-8"))
        self.lock = threading.RLock()

    def save(self):
        temporary = self.path / "state.json.tmp"
        temporary.write_text(json.dumps(self.state, ensure_ascii=False, indent=2), encoding="utf-8")
        temporary.replace(self.path / "state.json")

    def record(self, kind, **details):
        with self.lock:
            self.state["events"].append(dict(kind=kind, at=datetime.now(timezone.utc).isoformat(), **details))
            self.save()

    def inventory(self, plant="", warehouse="", search=""):
        needle = search.strip().casefold()
        return [dict(row) for row in self.fixture["inventory"]
                if (not plant or row["plant"] == plant) and (not warehouse or row["warehouse"] == warehouse)
                and (not needle or needle in row["material_id"].casefold() or needle in row["name"].casefold())]

    def export_inventory(self, rows):
        batch = self.fixture["context"]["batch_id"]
        data = write_xlsx([("库存明细", INVENTORY_COLUMNS, [dict(row, batch_id=batch) for row in rows])])
        self.record("inventory_export", material_ids=[r["material_id"] for r in rows], rows=len(rows), sha256=hashlib.sha256(data).hexdigest())
        return data

    def import_inventory(self, data):
        try:
            sheets = read_xlsx(data)
            rows = sheets.get("库存明细", [])
            if not rows or rows[0] != INVENTORY_COLUMNS:
                raise ValueError("库存表头不完整或列顺序不正确，请使用系统 A 导出的文件")
            if len(rows) < 2:
                raise ValueError("库存文件没有数据")
            imported, seen = [], set()
            for number, values in enumerate(rows[1:], 2):
                if len(values) != len(INVENTORY_COLUMNS):
                    raise ValueError(f"第 {number} 行列数不正确")
                row = dict(zip(INVENTORY_COLUMNS, values))
                if row["batch_id"] != self.fixture["context"]["batch_id"]:
                    raise ValueError(f"第 {number} 行不属于当前批次")
                key = tuple(row[x] for x in ("material_id", "plant", "warehouse"))
                if key in seen:
                    raise ValueError(f"第 {number} 行重复")
                seen.add(key)
                expected = next((x for x in self.fixture["inventory"] if tuple(x[k] for k in ("material_id", "plant", "warehouse")) == key), None)
                if expected is None:
                    raise ValueError(f"第 {number} 行物料或仓库无效")
                for column in INVENTORY_COLUMNS[1:]:
                    actual = row[column]
                    original = expected[column]
                    if isinstance(original, bool):
                        equal = actual.lower() == str(original).lower()
                    elif isinstance(original, int):
                        equal = Decimal(actual) == original
                    else:
                        equal = actual == original
                    if not equal:
                        raise ValueError(f"第 {number} 行 {column} 与当前库存不一致")
                imported.append(dict(expected, batch_id=row["batch_id"]))
        except (ValueError, InvalidOperation) as error:
            self.record("inventory_import_rejected", reason=str(error))
            raise BusinessError(str(error)) from None
        self.record("inventory_import", material_ids=[r["material_id"] for r in imported], rows=len(imported), sha256=hashlib.sha256(data).hexdigest())
        return imported

    def quotes(self, material_id=""):
        rows = [dict(q) for q in self.fixture["quotes"] if not material_id or q["material_id"] == material_id]
        self.record("quote_query", material_ids=[material_id] if material_id else sorted({q["material_id"] for q in rows}))
        return rows

    def export_quotes(self, material_ids):
        if not material_ids:
            raise BusinessError("请先查询至少一种物料再导出报价")
        known = {r["material_id"] for r in self.fixture["inventory"]}
        if not set(material_ids) <= known:
            raise BusinessError("导出包含未知物料")
        rows = [q for q in self.fixture["quotes"] if q["material_id"] in material_ids]
        context = self.fixture["context"]
        info = [dict(key=key, value=context[key]) for key in ("batch_id", "today", "deadline", "plant", "warehouse")]
        data = write_xlsx([("报价明细", QUOTE_COLUMNS, rows), ("批次信息", ["key", "value"], info)])
        self.record("quote_export", material_ids=sorted(set(material_ids)), rows=len(rows), sha256=hashlib.sha256(data).hexdigest())
        return data

    def submit_order(self, form):
        with self.lock:
            try:
                return self._submit_order(form)
            except BusinessError as error:
                self.record("order_rejected", reason=str(error), status=error.status)
                raise

    def confirm_quote_save(self, data):
        digest = hashlib.sha256(data).hexdigest()
        with self.lock:
            exported = next((e for e in reversed(self.state["events"]) if e["kind"] == "quote_export" and e.get("sha256") == digest), None)
            if exported is None:
                raise BusinessError("保存确认不匹配本批次已生成的报价文件，请重新导出")
            self.record("quote_file_saved", sha256=digest, material_ids=exported["material_ids"])

    def _submit_order(self, form):
        context = self.fixture["context"]
        if form.get("batch_id") != context["batch_id"]:
            raise BusinessError("任务批次不正确，请刷新当前批次")
        if form.get("warehouse") != context["warehouse"]:
            raise BusinessError("收货仓库必须为本任务的一号仓")
        supplier = next((s for s in self.fixture["suppliers"] if s["supplier_id"] == form.get("supplier_id") and s["active"]), None)
        if supplier is None:
            raise BusinessError("供应商不存在或已停用")
        try:
            delivery = date.fromisoformat(form.get("delivery_date", ""))
        except ValueError:
            raise BusinessError("交货日期格式应为 YYYY-MM-DD") from None
        today, deadline = date.fromisoformat(context["today"]), date.fromisoformat(context["deadline"])
        if not today <= delivery <= deadline:
            raise BusinessError("交货日期不在本任务允许范围内")
        raw_lines = form.get("lines", "").splitlines()
        if not raw_lines or len(raw_lines) > 100:
            raise BusinessError("采购明细不能为空，最多 100 行")
        result, seen, total = [], set(), Decimal(0)
        for number, raw in enumerate(raw_lines, 1):
            fields = raw.split("\t")
            if len(fields) != 4:
                raise BusinessError(f"第 {number} 行应填写物料、数量、单价和报价编号")
            mid, quantity_text, price_text, qid = [x.strip() for x in fields]
            if not re.fullmatch(r"[1-9][0-9]{0,6}", quantity_text):
                raise BusinessError(f"第 {number} 行数量必须为正整数，最多七位")
            quantity, unit_price = int(quantity_text), price(price_text)
            if mid in seen:
                raise BusinessError("同一采购单内物料重复")
            seen.add(mid)
            if any(any(line["material_id"] == mid for line in order["lines"]) for order in self.state["orders"]):
                raise BusinessError(f"物料 {mid} 在本批次已存在采购单，禁止重复采购，请回查订单")
            material = next((r for r in self.fixture["inventory"] if r["material_id"] == mid and r["enabled"] and r["plant"] == context["plant"] and r["warehouse"] == context["warehouse"]), None)
            quote = next((q for q in self.fixture["quotes"] if q["quote_id"] == qid and q["material_id"] == mid and q["supplier_id"] == supplier["supplier_id"]), None)
            if material is None or quote is None:
                raise BusinessError(f"第 {number} 行物料或供应商报价不匹配")
            if unit_price != Decimal(quote["unit_price"]):
                raise BusinessError(f"第 {number} 行单价与报价不一致，请重新核对")
            if not quote["active"] or date.fromisoformat(quote["valid_until"]) < today:
                raise BusinessError(f"第 {number} 行报价已失效或供应商停用")
            if quote["currency"] != "CNY" or quote["unit"] != material["unit"]:
                raise BusinessError(f"第 {number} 行币种或计量单位不一致")
            if not quote["moq"] <= quantity <= quote["available"]:
                raise BusinessError(f"第 {number} 行不满足起订量或可供数量")
            if today + timedelta(days=quote["lead_days"]) > delivery:
                raise BusinessError(f"第 {number} 行无法在所填交货日期供货")
            amount = unit_price * quantity
            total += amount
            result.append(dict(material_id=mid, name=material["name"], unit=material["unit"], quantity=quantity,
                               unit_price=f"{unit_price:.2f}", quote_id=qid, amount=f"{amount:.2f}"))
        if context["profile"] == "advanced" and not self.state["failure_consumed"]:
            self.state["failure_consumed"] = True
            self.record("injected_failure", reason="采购服务暂时不可用，本次未创建订单")
            raise BusinessError("采购服务暂时不可用，本次未创建订单。请保留明细并重试。", 503)
        order = dict(order_id=f"PO-{context['batch_id']}-{len(self.state['orders']) + 1:03}",
                     batch_id=context["batch_id"], supplier_id=supplier["supplier_id"], supplier_name=supplier["name"],
                     warehouse=form["warehouse"], delivery_date=delivery.isoformat(), notes=form.get("notes", "")[:2000],
                     total=f"{total:.2f}", status="待审批", lines=result)
        self.state["orders"].append(order)
        self.record("order_submitted", order_id=order["order_id"], material_ids=sorted(seen), total=order["total"])
        return dict(order)

    def register_exception(self, form):
        with self.lock:
            context = self.fixture["context"]
            mid = form.get("material_id", "").strip()
            reason = form.get("reason", "").strip()
            allowed = {r["material_id"] for r in self.inventory(context["plant"], context["warehouse"]) if r["enabled"]}
            if form.get("batch_id") != context["batch_id"] or mid not in allowed or not reason or len(reason) > 2000:
                raise BusinessError("请填写当前批次的有效物料及异常原因（1 至 2000 字）")
            entry = dict(batch_id=context["batch_id"], material_id=mid, reason=reason)
            self.state["exceptions"] = [x for x in self.state["exceptions"] if x["material_id"] != mid] + [entry]
            self.record("exception_registered", material_id=mid)
            return entry
