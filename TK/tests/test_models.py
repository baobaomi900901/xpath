import json
import unittest

from TK import models


class EmployeeTests(unittest.TestCase):
    def test_employee_data_matches_win32_rows_and_page_boundaries(self):
        rows = models.build_employees()
        self.assertEqual(1000, len(rows))
        self.assertEqual((1, "用户1", "产品部", "上海", "离职",
                          "user1@example.com", "2024-02-02"), rows[0])
        self.assertEqual(list(range(1, 1001)), [row[0] for row in rows])
        self.assertEqual(21, rows[20][0])
        self.assertEqual(1000, rows[-1][0])
        self.assertEqual(rows, models.build_employees())


class DragTests(unittest.TestCase):
    def test_all_nine_anchor_regions(self):
        self.assertEqual([
            "topLeft", "topCenter", "topRight", "middleLeft", "middleCenter",
            "middleRight", "bottomLeft", "bottomCenter", "bottomRight",
        ], [models.anchor_region(x, y) for y in (0, 40, 79) for x in (0, 60, 119)])
        self.assertEqual("topLeft", models.anchor_region(-30, -20))
        self.assertEqual("bottomRight", models.anchor_region(200, 200))

    def test_drag_clamps_to_arena_and_records_session_and_total_offsets(self):
        drag = models.DragState()
        drag.reset(600, 400)
        self.assertEqual((240, 160), (drag.left, drag.top))
        drag.begin(10, 20, now=1.0)
        drag.move(1010, 1020, 600, 400)
        drag.move(1010, 1020, 600, 400)
        drag.end(now=1.125)
        payload = json.loads(drag.to_json())
        self.assertEqual((480, 320), (payload["left"], payload["top"]))
        self.assertEqual((240, 160), (payload["deltaLeft"], payload["deltaTop"]))
        self.assertEqual(1, payload["moveCount"])
        self.assertEqual(125, payload["durationMs"])
        self.assertFalse(payload["dragging"])
        self.assertEqual({"x": 10, "y": 20, "sudokuPart": "topLeft"}, payload["anchor"])
        drag.begin(60, 40, now=2.0)
        drag.move(-50, -50, 600, 400)
        drag.end(now=2.5)
        payload = json.loads(drag.to_json())
        self.assertEqual(-480, payload["sessionDeltaLeft"])
        self.assertEqual(-240, payload["deltaLeft"])

    def test_json_schema_order_and_reset_match_win32(self):
        drag = models.DragState()
        drag.reset(600, 400)
        self.assertEqual([
            "left", "top", "initialLeft", "initialTop", "deltaLeft", "deltaTop",
            "startLeft", "startTop", "sessionDeltaLeft", "sessionDeltaTop",
            "anchor", "moveCount", "durationMs", "dragging",
        ], list(json.loads(drag.to_json())))
        drag.begin(10, 10, now=1.0)
        drag.move(50, 50, 600, 400)
        drag.reset(80, 60)
        payload = json.loads(drag.to_json())
        self.assertEqual((0, 0), (payload["left"], payload["top"]))
        self.assertEqual(0, payload["moveCount"])
        self.assertFalse(payload["dragging"])
        self.assertEqual("middleCenter", payload["anchor"]["sudokuPart"])


if __name__ == "__main__":
    unittest.main()
