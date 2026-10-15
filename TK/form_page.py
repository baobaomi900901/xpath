"""The Win32 range's ten-field form, rendered with actual Tk widgets."""

import tkinter as tk
from tkinter import messagebox, ttk

from .models import CITIES, GENDERS, HOBBIES


class FormPage(ttk.Frame):
    def __init__(self, parent, menu_status):
        super().__init__(parent, name="form", padding=18)
        self.menu_status = menu_status
        self.popup = None
        self.columnconfigure(0, weight=1)
        self.rowconfigure(9, weight=1)

        heading = ttk.Frame(self, name="heading")
        heading.grid(row=0, column=0, sticky="ew", pady=(0, 12))
        heading.columnconfigure(0, weight=1)
        ttk.Label(heading, text="用户信息表单", style="Heading.TLabel").grid(row=0, column=0, sticky="w")
        self.popup_button = ttk.Button(heading, name="popup", text="展开 Tk 菜单 ▼", command=self.show_popup)
        self.popup_button.grid(row=0, column=1)

        self.fields = {
            key: tk.StringVar(self, value=value)
            for key, value in (("name", ""), ("password", ""), ("email", ""),
                               ("age", "25"), ("city", "北京"), ("gender", "男"))
        }
        self.fields["agree"] = tk.BooleanVar(self, value=False)
        self.cities = {city: tk.BooleanVar(self, value=False) for city in CITIES}
        self.hobbies = {hobby: tk.BooleanVar(self, value=False) for hobby in HOBBIES}

        self.name_entry = ttk.Entry(self.item(1, "name", "姓名"), name="input", textvariable=self.fields["name"])
        self.name_entry.grid(row=0, column=1, sticky="ew")
        self.password_entry = ttk.Entry(self.item(2, "password", "密码"), name="input",
                                        textvariable=self.fields["password"], show="*")
        self.password_entry.grid(row=0, column=1, sticky="ew")
        self.email_entry = ttk.Entry(self.item(3, "email", "邮箱"), name="input", textvariable=self.fields["email"])
        self.email_entry.grid(row=0, column=1, sticky="ew")
        self.age_spin = ttk.Spinbox(self.item(4, "age", "年龄"), name="input", from_=18, to=80,
                                    textvariable=self.fields["age"], width=10)
        self.age_spin.grid(row=0, column=1, sticky="w")
        self.city_combo = ttk.Combobox(self.item(5, "city", "城市（单选）"), name="input",
                                       values=CITIES, state="readonly", textvariable=self.fields["city"])
        self.city_combo.grid(row=0, column=1, sticky="ew")

        self.city_checks = self.check_group(6, "cities", "城市（多选）", self.cities)
        gender_item = self.item(7, "gender", "性别（单选）")
        choices = ttk.Frame(gender_item, name="options")
        choices.grid(row=0, column=1, sticky="w")
        for index, gender in enumerate(GENDERS):
            ttk.Radiobutton(choices, name="option{}".format(index), text=gender,
                            value=gender, variable=self.fields["gender"]).grid(row=0, column=index, padx=(0, 20))
        self.hobby_checks = self.check_group(8, "hobbies", "兴趣爱好（多选）", self.hobbies)

        remark_item = self.item(9, "remark", "备注")
        remark_item.rowconfigure(0, weight=1)
        self.remark = tk.Text(remark_item, name="input", height=4, width=30, wrap="word", undo=True,
                              font="TkDefaultFont", borderwidth=1, relief="solid")
        self.remark.grid(row=0, column=1, sticky="nsew")
        scroll = ttk.Scrollbar(remark_item, name="scroll", command=self.remark.yview)
        scroll.grid(row=0, column=2, sticky="ns")
        self.remark.configure(yscrollcommand=scroll.set)
        # A multiline input still participates in the form's keyboard traversal.
        self.remark.bind("<Tab>", lambda event: self.focus_next(event, False))
        self.remark.bind("<Shift-Tab>", lambda event: self.focus_next(event, True))
        ttk.Checkbutton(self.item(10, "agreement", "协议"), name="input", text="同意用户协议",
                        variable=self.fields["agree"]).grid(row=0, column=1, sticky="w")

        actions = ttk.Frame(self, name="actions")
        actions.grid(row=11, column=0, sticky="w", pady=(14, 12))
        self.save_button = ttk.Button(actions, name="save", text="保存", command=self.save)
        self.save_button.grid(row=0, column=0, padx=(152, 12))
        self.reset_button = ttk.Button(actions, name="reset", text="重置", command=self.reset)
        self.reset_button.grid(row=0, column=1)
        ttk.Label(self, name="menu_status", textvariable=menu_status).grid(row=12, column=0, sticky="w")

    def item(self, row, name, label):
        frame = ttk.Frame(self, name=name, padding=(0, 5))
        frame.grid(row=row, column=0, sticky="nsew")
        frame.columnconfigure(1, weight=1)
        ttk.Label(frame, name="label", text=label, width=20).grid(row=0, column=0, sticky="nw", pady=4)
        return frame

    def check_group(self, row, name, label, variables):
        frame = self.item(row, name, label)
        choices = ttk.Frame(frame, name="options")
        choices.grid(row=0, column=1, sticky="w")
        checks = []
        for index, (text, variable) in enumerate(variables.items()):
            check = ttk.Checkbutton(choices, name="option{}".format(index), text=text, variable=variable)
            check.grid(row=0, column=index, padx=(0, 20))
            checks.append(check)
        return checks

    @staticmethod
    def focus_next(event, backwards):
        widget = event.widget.tk_focusPrev() if backwards else event.widget.tk_focusNext()
        widget.focus_set()
        return "break"

    def save(self):
        messagebox.showinfo("提示", "提交成功", parent=self.winfo_toplevel())

    def reset(self):
        defaults = {"name": "", "password": "", "email": "", "age": "25",
                    "city": "北京", "gender": "男", "agree": False}
        for key, value in defaults.items():
            self.fields[key].set(value)
        for variable in (*self.cities.values(), *self.hobbies.values()):
            variable.set(False)
        self.remark.delete("1.0", "end")

    def close_popup(self, event=None):
        popup, self.popup = self.popup, None
        if popup is not None:
            popup.unpost()
            if popup.grab_current() == popup:
                popup.grab_release()
            popup.destroy()

    def choose_action(self, label):
        self.menu_status.set("最近选择: 操作菜单 > " + label)

    def show_popup(self):
        self.close_popup()
        popup = tk.Menu(self, name="action_menu", tearoff=False)
        self.popup = popup
        for label in ("打开", "复制", "重命名", "删除"):
            popup.add_command(label=label, command=lambda label=label: self.choose_action(label))
        popup.add_separator()
        popup.add_command(label="属性", command=lambda: self.choose_action("属性"))
        # On Windows tk_popup runs the native menu's nested message loop.
        # Destroy only after it returns (selection, Escape or outside click).
        try:
            popup.tk_popup(self.popup_button.winfo_rootx(),
                           self.popup_button.winfo_rooty() + self.popup_button.winfo_height())
        finally:
            self.close_popup()
