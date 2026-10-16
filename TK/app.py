"""Root window, native Tk menus and notebook lifecycle."""

import tkinter as tk
from tkinter import font, ttk

from .drag_page import DragPage
from .form_page import FormPage
from .table_page import TablePage
from .advanced_page import WidgetPage, MenuTextPage


class ShootingRange:
    def __init__(self, hidden=False):
        self.root = tk.Tk()
        if hidden:
            self.root.withdraw()
        self.root.title("Tk 靶场 - tkinter/ttk")
        self.root.geometry("1180x860")
        self.root.minsize(960, 760)
        default_font = font.nametofont("TkDefaultFont", root=self.root)
        default_font.configure(size=10)
        style = ttk.Style(self.root)
        style.configure("Heading.TLabel", font=(default_font.actual("family"), 13, "bold"))
        style.configure("Treeview", rowheight=28)
        self.menu_status = tk.StringVar(self.root, value="菜单测试: 尚未选择菜单项")
        menubar = tk.Menu(self.root, name="menubar", tearoff=False)
        self.file_menu = tk.Menu(menubar, name="file", tearoff=False)
        self.edit_menu = tk.Menu(menubar, name="edit", tearoff=False)
        for label, underline in (("新建(N)", 3), ("打开(O)", 3), ("保存(S)", 3)):
            self.file_menu.add_command(label=label, underline=underline,
                                       command=lambda label=label: self.set_menu_status("文件", label[:2]))
        for label in ("撤销(U)", None, "剪切(T)", "复制(C)", "粘贴(P)", None, "全选(A)"):
            if label is None:
                self.edit_menu.add_separator()
            else:
                self.edit_menu.add_command(label=label, underline=3,
                                           command=lambda label=label: self.set_menu_status("编辑", label[:2]))
        menubar.add_cascade(label="文件(F)", underline=3, menu=self.file_menu)
        menubar.add_cascade(label="编辑(E)", underline=3, menu=self.edit_menu)
        self.root.configure(menu=menubar)
        self.notebook = ttk.Notebook(self.root, name="tabs")
        self.notebook.pack(fill="both", expand=True, padx=12, pady=12)
        self.form = FormPage(self.notebook, self.menu_status)
        self.table = TablePage(self.notebook)
        self.drag = DragPage(self.notebook)
        self.widgets = WidgetPage(self.notebook)
        self.semantics = MenuTextPage(self.notebook)
        for page, title in ((self.form, "表单控件"), (self.table, "表格数据"), (self.drag, "拖拽测试"),
                            (self.widgets, "控件与图元"), (self.semantics, "菜单与文本")):
            self.notebook.add(page, text=title, padding=(14, 6))
        self.notebook.enable_traversal()
        self.notebook.bind("<<NotebookTabChanged>>", self.tab_changed)
        self.root.protocol("WM_DELETE_WINDOW", self.close)

    def set_menu_status(self, group, label):
        self.menu_status.set("最近选择: {} > {}".format(group, label))

    def tab_changed(self, event):
        self.form.close_popup()
        self.drag.end()

    def close(self):
        self.form.close_popup()
        self.drag.end()
        self.root.destroy()


def main(argv=None):
    import argparse

    parser = argparse.ArgumentParser(description="Tk 框架 UI 自动化靶场")
    parser.add_argument("--check", action="store_true", help="在隐藏窗口中初始化全部测试页后退出")
    args = parser.parse_args(argv)
    app = ShootingRange(hidden=args.check)
    if args.check:
        try:
            app.root.update_idletasks()
            print("Tk 环境检查通过: Tcl/Tk {}，表单 / 表格 / 拖拽 / 控件与图元 / 菜单与文本页已初始化。".format(
                app.root.tk.call("info", "patchlevel")))
        finally:
            app.close()
    else:
        app.root.mainloop()
    return 0
