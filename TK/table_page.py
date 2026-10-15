"""Seven-column employee table with Win32-compatible pagination."""

import tkinter as tk
from tkinter import ttk

from .models import PAGE_SIZE, build_employees


class TablePage(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent, name="table", padding=18)
        self.employees = build_employees()
        self.current_page = 1
        self.total_pages = (len(self.employees) + PAGE_SIZE - 1) // PAGE_SIZE
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)
        ttk.Label(self, text="员工数据表（共 1000 条，每页 20 条）", style="Heading.TLabel").grid(
            row=0, column=0, sticky="w", pady=(0, 12))
        columns = ("id", "name", "department", "city", "status", "email", "join_date")
        self.tree = ttk.Treeview(self, name="employees", columns=columns, show="headings", selectmode="browse")
        for key, label, width in zip(columns, ("ID", "姓名", "部门", "城市", "状态", "邮箱", "入职日期"),
                                     (60, 120, 120, 100, 100, 240, 130)):
            self.tree.heading(key, text=label)
            self.tree.column(key, width=width, minwidth=width, stretch=key == "email", anchor="w")
        self.tree.grid(row=1, column=0, sticky="nsew")
        vertical = ttk.Scrollbar(self, name="vertical", command=self.tree.yview)
        vertical.grid(row=1, column=1, sticky="ns")
        horizontal = ttk.Scrollbar(self, name="horizontal", orient="horizontal", command=self.tree.xview)
        horizontal.grid(row=2, column=0, sticky="ew")
        self.tree.configure(yscrollcommand=vertical.set, xscrollcommand=horizontal.set)

        pages = ttk.Frame(self, name="pagination")
        pages.grid(row=3, column=0, sticky="w", pady=14)
        self.first_button = ttk.Button(pages, name="first", text="首页", width=7, command=lambda: self.go_to_page(1))
        self.previous_button = ttk.Button(pages, name="previous", text="上一页", width=7,
                                          command=lambda: self.go_to_page(self.current_page - 1))
        self.page_buttons = [ttk.Button(pages, name="page{}".format(index), width=4) for index in range(5)]
        self.next_button = ttk.Button(pages, name="next", text="下一页", width=7,
                                      command=lambda: self.go_to_page(self.current_page + 1))
        self.last_button = ttk.Button(pages, name="last", text="末页", width=7,
                                      command=lambda: self.go_to_page(self.total_pages))
        for index, button in enumerate((self.first_button, self.previous_button, *self.page_buttons,
                                        self.next_button, self.last_button)):
            button.grid(row=0, column=index, padx=(0, 6))
        self.page_info = tk.StringVar(self)
        ttk.Label(self, name="page_info", textvariable=self.page_info).grid(row=4, column=0, sticky="w")
        self.refresh()

    def go_to_page(self, page):
        if 1 <= page <= self.total_pages:
            self.current_page = page
            self.refresh()

    def refresh(self):
        children = self.tree.get_children()
        if children:
            self.tree.delete(*children)
        first = (self.current_page - 1) * PAGE_SIZE
        rows = self.employees[first:first + PAGE_SIZE]
        for row in rows:
            self.tree.insert("", "end", iid="employee-{}".format(row[0]), values=row)
        start_page = max(1, min(self.current_page - 2, self.total_pages - 4))
        for offset, button in enumerate(self.page_buttons):
            page = start_page + offset
            button.configure(text=str(page), command=lambda page=page: self.go_to_page(page))
            button.state(["disabled"] if page == self.current_page else ["!disabled"])
        for button in (self.first_button, self.previous_button):
            button.state(["disabled"] if self.current_page == 1 else ["!disabled"])
        for button in (self.next_button, self.last_button):
            button.state(["disabled"] if self.current_page == self.total_pages else ["!disabled"])
        self.page_info.set("第 {} / {} 页，当前显示 {} - {} 条".format(
            self.current_page, self.total_pages, first + 1, first + len(rows)))
