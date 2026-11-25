import json
import threading
import unittest
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

from SCENARIOS.supply_chain.fixtures import create_run
from SCENARIOS.supply_chain.server import make_server
from SCENARIOS.supply_chain.evaluate import evaluate
from support import WorkspaceTemporaryDirectory


class HttpTests(unittest.TestCase):
    def setUp(self):
        self.tmp = WorkspaceTemporaryDirectory()
        self.path = Path(self.tmp.name) / "run"
        create_run(self.path, "basic", 42, "http-test", "cli")
        self.server = make_server(self.path, 0)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.url = f"http://127.0.0.1:{self.server.server_port}"

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join()
        self.tmp.cleanup()

    def get(self, path):
        return urllib.request.urlopen(self.url + path, timeout=5)

    def test_context_tsv_exports_import_and_quote_query(self):
        context = json.loads(self.get("/api/context").read())
        self.assertEqual(context["plant"], "华东工厂")
        self.assertIn("batch_id\t", self.get("/api/context?format=tsv").read().decode())
        rows = json.loads(self.get("/api/inventory").read())["rows"]
        self.assertEqual(len(rows), 4)
        workbook = self.get("/api/export/inventory").read()
        request = urllib.request.Request(self.url + "/api/import/inventory", data=workbook,
                                        headers={"Content-Type": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"})
        with urllib.request.urlopen(request) as response:
            self.assertIn("M001", response.read().decode())
        self.assertIn("Q001", self.get("/api/quotes?material_id=M001&format=tsv").read().decode())
        self.assertTrue(self.get("/api/export/quotes?material_ids=M001,M003").read().startswith(b"PK"))

    def test_obstacle_mode_reaches_web_without_changing_business_rows(self):
        default_html = self.get("/").read().decode()
        self.assertIn('data-obstacles="false"', default_html)
        self.assertIn('/obstacles.js', default_html)
        with self.get("/obstacles.js") as response:
            self.assertEqual(response.status, 200)
        self.server.store.fixture["context"]["obstacles"] = True
        self.assertIn('data-obstacles="true"', self.get("/").read().decode())
        context = json.loads(self.get("/api/context").read())
        self.assertTrue(context["obstacles"])
        self.assertEqual(len(json.loads(self.get("/api/inventory").read())["rows"]), 4)

    def test_validation_and_no_answer_or_operator_files_exposed(self):
        for path in ("/api/answers", "/fixture.json", "/state.json", "/CONTRACT.md", "/web/REPORT.md", "/../fixture.json"):
            with self.subTest(path=path), self.assertRaises(urllib.error.HTTPError) as caught:
                self.get(path)
            self.assertEqual(caught.exception.code, 404)
            caught.exception.close()
        with self.assertRaises(urllib.error.HTTPError) as caught:
            self.get("/api/export/quotes")
        self.assertEqual(caught.exception.code, 400)
        caught.exception.close()

    def test_post_order_is_persistent_and_requery_returns_summary(self):
        context = json.loads(self.get("/api/context").read())
        form = dict(batch_id=context["batch_id"], supplier_id="S001", warehouse="一号仓",
                    delivery_date="2026-11-24", notes="test", lines="M001\t120\t10.00\tQ001")
        request = urllib.request.Request(self.url + "/api/orders", data=urllib.parse.urlencode(form).encode())
        with urllib.request.urlopen(request) as response:
            self.assertEqual(response.status, 201)
            self.assertIn("1200.00", response.read().decode())
        self.assertEqual(len(json.loads(self.get("/api/orders").read())["rows"]), 1)
        self.assertIn("M001", self.get("/api/orders?format=tsv").read().decode())

    def test_complete_real_file_and_order_http_workflow_passes_offline_evaluation(self):
        context = json.loads(self.get("/api/context").read())
        inventory = self.get("/api/export/inventory").read()
        inventory_file = self.path / "库存导出.xlsx"
        inventory_file.write_bytes(inventory)
        request = urllib.request.Request(self.url + "/api/import/inventory", data=inventory_file.read_bytes())
        with urllib.request.urlopen(request) as response:
            self.assertIn("M004", response.read().decode())
        for mid in ("M001", "M003"):
            self.get("/api/quotes?material_id=" + mid + "&format=tsv").close()
        quotes = self.get("/api/export/quotes?material_ids=M001,M003").read()
        quote_file = self.path / "供应商报价.xlsx"
        quote_file.write_bytes(quotes)
        request = urllib.request.Request(self.url + "/api/confirm/quotes", data=quote_file.read_bytes())
        with urllib.request.urlopen(request) as response:
            self.assertIn("已确认", response.read().decode())
        for supplier, mid, quantity, price, quote in [("S001", "M001", 120, "10.00", "Q001"), ("S003", "M003", 100, "5.00", "Q005")]:
            form = dict(batch_id=context["batch_id"], supplier_id=supplier, warehouse=context["warehouse"],
                        delivery_date=context["deadline"], lines=f"{mid}\t{quantity}\t{price}\t{quote}")
            request = urllib.request.Request(self.url + "/api/orders", data=urllib.parse.urlencode(form).encode())
            with urllib.request.urlopen(request) as response:
                self.assertEqual(response.status, 201)
        self.assertFalse(evaluate(self.path)["workflow_pass"], "尚未回查应不通过")
        self.assertIn("待审批", self.get("/api/orders?format=tsv").read().decode())
        report = evaluate(self.path)
        self.assertTrue(report["passed"], report)
        self.assertEqual(report["actual_total"], "1700.00")


if __name__ == "__main__":
    unittest.main()
