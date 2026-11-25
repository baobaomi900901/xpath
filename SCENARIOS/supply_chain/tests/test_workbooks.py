import io
import unittest
import zipfile
from pathlib import Path

from SCENARIOS.supply_chain.fixtures import create_run
from SCENARIOS.supply_chain.domain import Store, BusinessError
from SCENARIOS.supply_chain.workbooks import write_xlsx, read_xlsx, INVENTORY_COLUMNS
from support import WorkspaceTemporaryDirectory


class WorkbookTests(unittest.TestCase):
    def test_real_ooxml_preserves_codes_unicode_numbers_and_xml_characters(self):
        rows = [{"code": "00123", "name": "轴承 & <组件>", "qty": 12}]
        data = write_xlsx([("库存明细", ["code", "name", "qty"], rows)])
        with zipfile.ZipFile(io.BytesIO(data)) as z:
            self.assertIn("[Content_Types].xml", z.namelist())
            self.assertIn("xl/worksheets/sheet1.xml", z.namelist())
        self.assertEqual(read_xlsx(data)["库存明细"][1], ["00123", "轴承 & <组件>", "12"])

    def test_inventory_roundtrip_and_forged_import_rejected(self):
        with WorkspaceTemporaryDirectory() as temp:
            create_run(Path(temp) / "run", "basic", 42, "test", "cli")
            store = Store(Path(temp) / "run")
            rows = store.inventory(plant="华东工厂", warehouse="一号仓")
            payload = store.export_inventory(rows)
            imported = store.import_inventory(payload)
            self.assertEqual(len(imported), 4)
            forged = [{**row, "batch_id": store.fixture["context"]["batch_id"]} for row in rows]
            forged[0]["current"] = 999
            with self.assertRaisesRegex(BusinessError, "库存|不一致"):
                store.import_inventory(write_xlsx([("库存明细", INVENTORY_COLUMNS, forged)]))

    def test_non_xlsx_and_missing_header_rejected(self):
        for payload in (b"not excel", write_xlsx([("库存明细", ["name"], [{"name": "x"}])])):
            with WorkspaceTemporaryDirectory() as temp:
                create_run(Path(temp) / "run", "basic", 42, "test", "cli")
                with self.assertRaises(BusinessError):
                    Store(Path(temp) / "run").import_inventory(payload)


if __name__ == "__main__":
    unittest.main()
