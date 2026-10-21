import json
import tkinter as tk
import unittest
from unittest.mock import patch

from TK.app import ShootingRange


class AppTests(unittest.TestCase):
    def setUp(self):
        self.app = ShootingRange()
        self.root = self.app.root
        self.errors = []
        self.root.report_callback_exception = lambda *error: self.errors.append(error)
        self.root.update()

    def tearDown(self):
        self.root.destroy()
        self.assertEqual([], self.errors, "Tk callback raised an exception")

    def select(self, page):
        self.app.notebook.select(page)
        self.root.update()

    def test_form_reset_restores_every_default(self):
        form = self.app.form
        form.fields["name"].set("测试用户")
        form.fields["password"].set("secret")
        form.fields["email"].set("test@example.com")
        form.fields["age"].set("38")
        form.fields["city"].set("杭州")
        form.fields["gender"].set("女")
        form.cities["深圳"].set(True)
        form.hobbies["音乐"].set(True)
        form.fields["agree"].set(True)
        form.remark.insert("1.0", "多行\n备注")
        form.reset_button.invoke()
        self.assertEqual({"name": "", "password": "", "email": "", "age": "25",
                          "city": "北京", "gender": "男", "agree": False},
                         {key: value.get() for key, value in form.fields.items()})
        self.assertFalse(any(value.get() for value in form.cities.values()))
        self.assertFalse(any(value.get() for value in form.hobbies.values()))
        self.assertEqual("", form.remark.get("1.0", "end-1c"))
        self.assertTrue(form.password_entry.cget("show"))
        self.assertEqual("readonly", str(form.city_combo.cget("state")))

    def test_advanced_controls_keep_duplicate_items_and_nested_nodes(self):
        page = self.app.widgets
        self.select(page)
        self.assertEqual(2, page.listbox.get(0, "end").count("重复项"))
        self.assertEqual(("grandchild",), page.tree.get_children("child"))
        self.assertFalse(self.root.getboolean(page.tree.item("child", "open")))
        self.assertEqual("hidden", str(page.tabs.tab(page.tabs.tabs()[-1], "state")))
        self.assertEqual("hidden", page.canvas.itemcget("hidden", "state"))
        self.assertEqual("readonly", str(page.readonly.cget("state")))
        self.assertEqual("disabled", str(page.disabled.cget("state")))
        self.assertEqual(30, page.scale.get())
        self.assertEqual(60, page.progress.cget("value"))

    def test_independent_menu_callbacks_report_real_results(self):
        page = self.app.semantics
        self.select(page)
        page.context_menu.invoke(0)
        self.assertEqual("已执行右键命令", page.status.get())
        page.context_menu.children["nested"].invoke(0)
        self.assertEqual("已执行二级命令", page.status.get())
        for name, label in (("classic", "经典菜单"), ("themed", "主题菜单")):
            menu = page.children["menus"].children[name].children["menu"]
            menu.invoke(0)
            self.assertEqual("已执行" + label, page.status.get())
            self.assertEqual("disabled", menu.entrycget(1, "state"))

    def test_text_tags_have_click_bindings_ranges_and_hidden_content(self):
        page = self.app.semantics
        self.select(page)
        self.assertEqual(4, len(page.text.tag_ranges("repeated")))
        self.assertTrue(self.root.getboolean(page.text.tag_cget("hidden", "elide")))
        self.assertTrue(page.text.tk.call(str(page.text), "tag", "bind", "first_link", "<Button-1>"))
        self.assertFalse(page.text.tk.call(str(page.text), "tag", "bind", "style", "<Button-1>"))
        self.assertEqual("第一个链接", page.text.get("first_link.first", "first_link.last"))

    def test_save_opens_modal_success_message(self):
        with patch("TK.form_page.messagebox.showinfo") as showinfo:
            self.app.form.save_button.invoke()
        self.assertEqual("提交成功", showinfo.call_args.args[1])
        self.assertEqual(self.root, showinfo.call_args.kwargs["parent"])

    def test_table_paging_displays_real_data_and_disables_boundaries(self):
        table = self.app.table
        self.select(table)
        self.assertEqual(20, len(table.tree.get_children()))
        self.assertEqual("1", str(table.tree.item(table.tree.get_children()[0], "values")[0]))
        self.assertTrue(table.first_button.instate(["disabled"]))
        self.assertTrue(table.previous_button.instate(["disabled"]))
        table.next_button.invoke()
        self.assertEqual(2, table.current_page)
        self.assertEqual("21", str(table.tree.item(table.tree.get_children()[0], "values")[0]))
        table.last_button.invoke()
        self.assertEqual(50, table.current_page)
        self.assertEqual("1000", str(table.tree.item(table.tree.get_children()[-1], "values")[0]))
        self.assertTrue(table.next_button.instate(["disabled"]))
        self.assertTrue(table.last_button.instate(["disabled"]))
        self.assertEqual(["46", "47", "48", "49", "50"],
                         [button.cget("text") for button in table.page_buttons])
        table.page_buttons[0].invoke()
        self.assertEqual(46, table.current_page)
        table.go_to_page(0)
        self.assertEqual(46, table.current_page)
        table.first_button.invoke()
        self.assertEqual(1, table.current_page)

    def test_popup_is_destroyed_after_selection_and_escape(self):
        form = self.app.form
        created = []

        def select_copy(menu, *coordinates):
            # Windows tk_popup blocks in an OS menu loop. Exercise the real
            # menu and callback while substituting only that modal call.
            created.append(menu)
            self.assertTrue(menu.winfo_exists())
            menu.invoke(1)

        for _ in range(2):
            with patch.object(tk.Menu, "tk_popup", autospec=True, side_effect=select_copy):
                form.popup_button.invoke()
            self.root.update()
            self.assertEqual("最近选择: 操作菜单 > 复制", self.app.menu_status.get())
            self.assertFalse(created[-1].winfo_exists())
            self.assertIsNone(form.popup)
        with patch.object(tk.Menu, "tk_popup"):
            form.popup_button.invoke()
        self.root.update()
        self.assertIsNone(form.popup)
        self.app.file_menu.invoke(0)
        self.assertEqual("最近选择: 文件 > 新建", self.app.menu_status.get())

    def test_drag_pointer_events_clipboard_hide_and_reset(self):
        drag = self.app.drag
        self.select(drag)
        target = drag.target
        target.event_generate("<ButtonPress-1>", x=10, y=20)
        self.root.update()
        self.assertTrue(drag.state.dragging)
        target.event_generate("<B1-Motion>", x=10000, y=10000)
        target.event_generate("<ButtonRelease-1>", x=10000, y=10000)
        self.root.update()
        self.assertFalse(drag.state.dragging)
        self.assertEqual(drag.arena.winfo_width() - 120, drag.state.left)
        self.assertEqual(drag.arena.winfo_height() - 80, drag.state.top)
        self.assertGreaterEqual(drag.state.move_count, 1)
        drag.copy_button.invoke()
        payload = json.loads(self.root.clipboard_get())
        self.assertEqual("topLeft", payload["anchor"]["sudokuPart"])
        self.assertEqual(drag.state.left, payload["left"])
        drag.hide_button.invoke()
        self.root.update()
        self.assertFalse(target.winfo_exists())
        self.assertTrue(drag.hide_button.instate(["disabled"]))
        drag.reset_button.invoke()
        self.root.update()
        self.assertTrue(drag.target.winfo_ismapped())
        self.assertEqual((drag.arena.winfo_width() - 120) // 2, drag.state.left)
        self.assertEqual(0, drag.state.move_count)

    def test_resize_keeps_drag_target_inside_the_arena(self):
        drag = self.app.drag
        self.select(drag)
        drag.state.left = 10000
        drag.state.top = 10000
        self.root.geometry("960x760")
        self.root.update()
        self.assertLessEqual(drag.state.left + 120, drag.arena.winfo_width())
        self.assertLessEqual(drag.state.top + 80, drag.arena.winfo_height())
        self.assertEqual(120, drag.target.winfo_width())
        self.assertEqual(80, drag.target.winfo_height())

    def test_release_applies_final_pointer_position_without_motion_event(self):
        drag = self.app.drag
        self.select(drag)
        left, top = drag.state.left, drag.state.top
        drag.target.event_generate("<ButtonPress-1>", x=10, y=20)
        drag.target.event_generate("<ButtonRelease-1>", x=100, y=70)
        self.root.update()
        self.assertEqual((left + 90, top + 50), (drag.state.left, drag.state.top))
        self.assertEqual(1, drag.state.move_count)
        self.assertFalse(drag.state.dragging)

    def test_stable_widget_paths_and_distinct_option_groups(self):
        self.assertEqual(".tabs.form.name.input", str(self.app.form.name_entry))
        self.assertEqual(".tabs.table.employees", str(self.app.table.tree))
        self.select(self.app.drag)
        self.assertEqual(".tabs.drag.arena.drag-target", str(self.app.drag.target))
        self.assertNotEqual(self.app.form.city_checks[0].winfo_parent(),
                            self.app.form.hobby_checks[0].winfo_parent())


if __name__ == "__main__":
    unittest.main()
