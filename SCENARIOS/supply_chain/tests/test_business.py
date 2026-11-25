import unittest
from pathlib import Path

from SCENARIOS.supply_chain.fixtures import make_fixture, create_run
from SCENARIOS.supply_chain.domain import Store, BusinessError
from SCENARIOS.supply_chain.evaluate import evaluate
from support import WorkspaceTemporaryDirectory


def order_form(batch="", supplier="S001", material="M001", quantity="120", price="10.00", quote="Q001"):
    return dict(batch_id=batch, supplier_id=supplier, warehouse="一号仓",
                delivery_date="2026-11-24", notes="测试", lines=f"{material}\t{quantity}\t{price}\t{quote}")


class BusinessTests(unittest.TestCase):
    def setUp(self):
        self.tmp = WorkspaceTemporaryDirectory()
        self.path = Path(self.tmp.name) / "run"
        self.fixture = create_run(self.path, "basic", 42, "test-agent", "cli")
        self.store = Store(self.path)

    def tearDown(self):
        self.tmp.cleanup()

    def test_seed_is_reproducible_and_profiles_have_boundary_cases(self):
        self.assertEqual(make_fixture("standard", 7), make_fixture("standard", 7))
        self.assertNotEqual(make_fixture("standard", 7)["inventory"], make_fixture("standard", 8)["inventory"])
        self.assertGreaterEqual(len(make_fixture("standard", 7)["inventory"]), 24)
        row = next(x for x in self.fixture["inventory"] if x["material_id"] == "M004")
        self.assertEqual(row["current"], row["safety"])

    def test_valid_order_persists_and_inventory_does_not_change(self):
        before = self.store.fixture["inventory"]
        result = self.store.submit_order(order_form(self.fixture["context"]["batch_id"]))
        self.assertEqual(result["total"], "1200.00")
        self.assertEqual(result["status"], "待审批")
        reloaded = Store(self.path)
        self.assertEqual(len(reloaded.state["orders"]), 1)
        self.assertEqual(before, reloaded.fixture["inventory"])

    def test_duplicate_and_invalid_quote_are_rejected_without_extra_orders(self):
        form = order_form(self.fixture["context"]["batch_id"])
        self.store.submit_order(form)
        with self.assertRaisesRegex(BusinessError, "重复"):
            self.store.submit_order(form)
        self.assertEqual(len(self.store.state["orders"]), 1)
        with self.assertRaises(BusinessError):
            self.store.submit_order(order_form(form["batch_id"], supplier="S002", price="9.00", quote="Q002"))

    def test_bad_quantity_price_date_and_batch(self):
        form = order_form(self.fixture["context"]["batch_id"])
        for changes in ({"lines": "M001\t0\t10.00\tQ001"},
                        {"lines": "M001\t120\t9.00\tQ001"},
                        {"lines": "M001\t1.5\t10.00\tQ001"},
                        {"lines": "M001\t120\tNaN\tQ001"},
                        {"delivery_date": "2026-11-18"}, {"batch_id": "OLD"},
                        {"lines": ""}):
            with self.subTest(changes=changes), self.assertRaises(BusinessError):
                self.store.submit_order({**form, **changes})
        self.assertEqual(self.store.state["orders"], [])

    def test_suboptimal_purchase_is_accepted_by_app_but_fails_independent_grading(self):
        self.store.submit_order(order_form(self.fixture["context"]["batch_id"], supplier="S003", price="11.00", quote="Q003"))
        report = evaluate(self.path)
        self.assertFalse(report["business_pass"])
        self.assertTrue(any("供应商" in x or "单价" in x for x in report["issues"]))

    def test_correct_business_and_workflow_pass_independent_grading(self):
        batch = self.fixture["context"]["batch_id"]
        self.store.submit_order(order_form(batch))
        self.store.submit_order(order_form(batch, "S003", "M003", "100", "5.00", "Q005"))
        workbook = self.store.export_inventory(self.store.inventory("华东工厂", "一号仓"))
        self.store.import_inventory(workbook)
        self.store.quotes("M001")
        self.store.quotes("M003")
        self.store.export_quotes(["M001", "M003"])
        self.store.confirm_quote_save(self.store.export_quotes(["M001", "M003"]))
        self.store.record("orders_viewed", order_ids=[o["order_id"] for o in self.store.state["orders"]])
        report = evaluate(self.path)
        self.assertTrue(report["passed"], report)
        self.assertEqual(report["actual_total"], "1700.00")
        self.assertEqual(report["metadata"]["track"], "cli")
        self.assertIsNone(report["metrics"]["gui_tool_calls"])

    def test_disconnected_inventory_import_cannot_pass_file_handoff(self):
        batch = self.fixture["context"]["batch_id"]
        self.store.submit_order(order_form(batch))
        self.store.submit_order(order_form(batch, "S003", "M003", "100", "5.00", "Q005"))
        from SCENARIOS.supply_chain.workbooks import write_xlsx, INVENTORY_COLUMNS
        rows = self.store.inventory("华东工厂", "一号仓")
        self.store.export_inventory(rows)
        subset = [dict(r, batch_id=batch) for r in rows if r["material_id"] in ("M001", "M003")]
        self.store.import_inventory(write_xlsx([("库存明细", INVENTORY_COLUMNS, subset)]))
        self.store.quotes("M001")
        self.store.quotes("M003")
        self.store.confirm_quote_save(self.store.export_quotes(["M001", "M003"]))
        self.store.record("orders_viewed", order_ids=[o["order_id"] for o in self.store.state["orders"]])
        report = evaluate(self.path)
        self.assertTrue(report["business_pass"])
        self.assertEqual(report["workflow_issues"], ["缺少完整任务库存文件从 A 导出到 B 导入的同文件交接证据"])

    def test_quote_generation_without_successful_file_save_does_not_pass(self):
        batch = self.fixture["context"]["batch_id"]
        self.store.submit_order(order_form(batch))
        self.store.submit_order(order_form(batch, "S003", "M003", "100", "5.00", "Q005"))
        self.store.import_inventory(self.store.export_inventory(self.store.inventory("华东工厂", "一号仓")))
        for mid in ("M001", "M003"):
            self.store.quotes(mid)
        data = self.store.export_quotes(["M001", "M003"])
        self.store.record("orders_viewed", order_ids=[o["order_id"] for o in self.store.state["orders"]])
        self.assertFalse(evaluate(self.path)["workflow_pass"])
        self.store.confirm_quote_save(data)
        self.assertTrue(evaluate(self.path)["passed"])

    def test_same_seed_prior_run_workbook_is_rejected(self):
        old_path = Path(self.tmp.name) / "old"
        create_run(old_path, "basic", 42, "test", "cli")
        old = Store(old_path)
        payload = old.export_inventory(old.inventory())
        with self.assertRaisesRegex(BusinessError, "批次"):
            self.store.import_inventory(payload)

    def test_missing_file_handoff_fails_workflow_despite_correct_orders(self):
        batch = self.fixture["context"]["batch_id"]
        self.store.submit_order(order_form(batch))
        self.store.submit_order(order_form(batch, "S003", "M003", "100", "5.00", "Q005"))
        report = evaluate(self.path)
        self.assertTrue(report["business_pass"], report)
        self.assertFalse(report["workflow_pass"])
        self.assertFalse(report["passed"])

    def test_advanced_fails_once_without_creating_order_then_retry_works(self):
        path = Path(self.tmp.name) / "advanced"
        fixture = create_run(path, "advanced", 42, "test", "sdk")
        store = Store(path)
        form = order_form(fixture["context"]["batch_id"])
        with self.assertRaises(BusinessError) as caught:
            store.submit_order(form)
        self.assertEqual(caught.exception.status, 503)
        self.assertEqual(store.state["orders"], [])
        store.submit_order(form)
        self.assertEqual(len(store.state["orders"]), 1)
        self.assertTrue(any(x["kind"] == "injected_failure" for x in store.state["events"]))

    def test_reset_never_overwrites_existing_run(self):
        with self.assertRaises(FileExistsError):
            create_run(self.path, "basic", 1, "test", "cli")

    def test_standard_and_advanced_reference_procurement(self):
        # Reviewed seed42 reference, including same-name materials and the lead-time tie.
        reference = [("M001", 120, "Q001"), ("M003", 100, "Q005"),
                     ("M005", 88, "Q0051"), ("M006", 140, "Q0060"),
                     ("M007", 49, "Q0072"), ("M008", 102, "Q0081"),
                     ("M010", 47, "Q0102"), ("M011", 61, "Q0111"),
                     ("M013", 59, "Q0132"), ("M014", 50, "Q0141"),
                     ("M016", 55, "Q0162"), ("M017", 57, "Q0171"),
                     ("M019", 59, "Q0192"), ("M020", 67, "Q0201"),
                     ("M022", 91, "Q0222"), ("M023", 52, "Q0231")]
        for profile in ("standard", "advanced"):
            with self.subTest(profile=profile):
                path = Path(self.tmp.name) / profile
                fixture = create_run(path, profile, 42, "reference", "sdk")
                store = Store(path)
                store.import_inventory(store.export_inventory(store.inventory("华东工厂", "一号仓")))
                groups = {}
                for mid, qty, qid in reference:
                    quotes = store.quotes(mid)
                    quote = next(q for q in quotes if q["quote_id"] == qid)
                    groups.setdefault(quote["supplier_id"], []).append(f"{mid}\t{qty}\t{quote['unit_price']}\t{qid}")
                queried = [row[0] for row in reference]
                if profile == "advanced":
                    store.quotes("M099")
                    queried.append("M099")
                    store.register_exception(dict(batch_id=fixture["context"]["batch_id"], material_id="M099", reason="一家数量不足，另一家报价过期"))
                store.confirm_quote_save(store.export_quotes(queried))
                for supplier, lines in groups.items():
                    form = order_form(fixture["context"]["batch_id"], supplier)
                    form["lines"] = "\n".join(lines)
                    try:
                        store.submit_order(form)
                    except BusinessError as error:
                        self.assertEqual(error.status, 503)
                        store.submit_order(form)
                store.record("orders_viewed", order_ids=[o["order_id"] for o in store.state["orders"]])
                report = evaluate(path)
                self.assertTrue(report["passed"], report)
                self.assertEqual(report["actual_order_count"], 3)
                self.assertEqual(report["actual_line_count"], 16)
                self.assertEqual(report["blocked_materials"], ["M099"] if profile == "advanced" else [])


if __name__ == "__main__":
    unittest.main()
