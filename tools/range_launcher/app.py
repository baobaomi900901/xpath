"""Tk dashboard: select ranges, configure commands and read per-task logs."""
from __future__ import annotations

import json
import os
from pathlib import Path
import re
import subprocess
import tkinter as tk
from tkinter import ttk

from .config import build_command, clear_values, default_values, load_catalog, restore_values
from .editor import CatalogEditor
from .runner import Runner


class ScrollPanel(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent, style="Panel.TFrame")
        self.canvas = tk.Canvas(self, background="#ffffff", highlightthickness=0)
        bar = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.body = ttk.Frame(self.canvas, style="Panel.TFrame")
        self.window = self.canvas.create_window((0, 0), window=self.body, anchor="nw")
        self.canvas.configure(yscrollcommand=bar.set)
        self.canvas.pack(side="left", fill="both", expand=True)
        bar.pack(side="right", fill="y")
        self.body.bind("<Configure>", lambda _: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas.bind("<Configure>", lambda event: self.canvas.itemconfigure(self.window, width=event.width))

    def bind_wheel(self):
        def scroll(event):
            if event.delta:
                self.canvas.yview_scroll(-1 if event.delta > 0 else 1, "units")
            return "break"
        def attach(widget):
            if not isinstance(widget, (ttk.Entry, ttk.Combobox, ttk.Spinbox)):
                widget.bind("<MouseWheel>", scroll, add="+")
            for child in widget.winfo_children():
                attach(child)
        attach(self.body)
        self.canvas.bind("<MouseWheel>", scroll)


class Launcher:
    def __init__(self, root, repo_root: Path, config_path: Path, state_path: Path | None = None):
        self.root, self.repo_root, self.config_path = root, repo_root, config_path
        self.state_path = state_path
        self.log_dir = repo_root / ".private" / "range-launcher" / "logs"
        self.runner = Runner(self.log_dir)
        self.closed = False
        self.items, self.checked, self.settings, self.status_vars = {}, {}, {}, {}
        self.list_cards = {}
        self.current_id, self.option_vars = None, {}
        self.queue, self.pending = [], set()
        self.queue_scheduled = False
        self.queue_id = None
        self.editor = None
        self.persisted = self._load_state()
        root.title("靶场启动中心")
        width = min(1180, max(720, root.winfo_screenwidth() - 80))
        height = min(800, max(540, root.winfo_screenheight() - 90))
        root.geometry(f"{width}x{height}")
        root.minsize(min(940, width), min(660, height))
        root.configure(background="#f4f6fa")
        self._styles()
        self._build_shell()
        self.reload_catalog()
        self.poll_id = root.after(200, self._poll)
        root.protocol("WM_DELETE_WINDOW", self.close)

    def _styles(self):
        style = ttk.Style(self.root)
        if "clam" in style.theme_names():
            style.theme_use("clam")
        style.configure(".", font=("Microsoft YaHei UI", 10), background="#f4f6fa", foreground="#162233")
        style.configure("TButton", padding=(12, 7))
        style.configure("Primary.TButton", background="#245dcc", foreground="white", font=("Microsoft YaHei UI", 10, "bold"))
        style.map("Primary.TButton", background=[("active", "#1c4ca8"), ("disabled", "#d5dce8")])
        style.configure("Title.TLabel", font=("Microsoft YaHei UI", 21, "bold"))
        style.configure("Heading.TLabel", font=("Microsoft YaHei UI", 13, "bold"))
        style.configure("Muted.TLabel", foreground="#627084")
        style.configure("Panel.TFrame", background="#ffffff")
        style.configure("Card.TFrame", background="#ffffff", relief="solid", borderwidth=1)
        style.configure("Focus.TFrame", background="#edf3ff", relief="solid", borderwidth=1)
        style.configure("Card.TLabel", background="#ffffff")
        style.configure("CardMuted.TLabel", background="#ffffff", foreground="#627084", font=("Microsoft YaHei UI", 9))
        style.configure("Card.TCheckbutton", background="#ffffff", font=("Microsoft YaHei UI", 11, "bold"))
        style.configure("Panel.TLabel", background="#ffffff")
        style.configure("Panel.TCheckbutton", background="#ffffff")

    def _build_shell(self):
        header = ttk.Frame(self.root, padding=(24, 20, 24, 12))
        header.pack(fill="x")
        ttk.Label(header, text="靶场启动中心", style="Title.TLabel").pack(side="left")
        actions = ttk.Frame(header)
        actions.pack(side="right")
        ttk.Button(actions, text="维护靶场与选项", command=self.edit_catalog).pack(side="left", padx=4)
        ttk.Button(actions, text="重新加载配置", command=self.reload_catalog).pack(side="left", padx=4)
        ttk.Label(self.root, text="勾选靶场 → 设置版本与启动方式 → 启动所选", style="Muted.TLabel").pack(anchor="w", padx=26, pady=(0, 16))
        content = ttk.Panedwindow(self.root, orient="horizontal")
        content.pack(fill="both", expand=True, padx=24)
        left = ttk.Frame(content, style="Panel.TFrame", padding=12, width=360)
        right = ttk.Frame(content, style="Panel.TFrame", padding=14)
        content.add(left, weight=2)
        content.add(right, weight=4)
        search_row = ttk.Frame(left, style="Panel.TFrame")
        search_row.pack(fill="x", pady=(0, 8))
        self.search = tk.StringVar()
        ttk.Entry(search_row, textvariable=self.search).pack(side="left", fill="x", expand=True)
        self.category = tk.StringVar(value="全部分类")
        self.categories = ttk.Combobox(search_row, textvariable=self.category, values=["全部分类"], state="readonly", width=10)
        self.categories.pack(side="right", padx=(8, 0))
        self.categories.bind("<<ComboboxSelected>>", lambda _: self._render_list())
        self.search.trace_add("write", lambda *_: self._render_list())
        selection = ttk.Frame(left, style="Panel.TFrame")
        selection.pack(fill="x", pady=(0, 10))
        ttk.Button(selection, text="全选可见", command=self.select_visible).pack(side="left")
        ttk.Button(selection, text="清空选项", command=self.clear_selection).pack(side="left", padx=6)
        self.list_panel = ScrollPanel(left)
        self.list_panel.pack(fill="both", expand=True)
        self.detail_title = tk.StringVar(value="选择一个靶场")
        self.detail_description = tk.StringVar(value="在左侧勾选靶场，也可点击名称查看选项。")
        ttk.Label(right, textvariable=self.detail_title, style="Heading.TLabel").pack(anchor="w", pady=(0, 8))
        description = ttk.Label(right, textvariable=self.detail_description, style="Panel.TLabel", wraplength=620, justify="left")
        description.pack(anchor="w", fill="x", pady=(0, 14))
        right.bind("<Configure>", lambda event: description.configure(wraplength=max(260, event.width - 30)))
        self.notebook = ttk.Notebook(right)
        self.notebook.pack(fill="both", expand=True)
        self.options_tab = ttk.Frame(self.notebook, style="Panel.TFrame", padding=12)
        self.logs_tab = ttk.Frame(self.notebook, style="Panel.TFrame", padding=10)
        self.notebook.add(self.options_tab, text=" 启动选项 ")
        self.notebook.add(self.logs_tab, text=" 运行日志 ")
        profile_row = ttk.Frame(self.options_tab, style="Panel.TFrame")
        profile_row.pack(fill="x", pady=(0, 12))
        ttk.Label(profile_row, text="启动方式", style="Panel.TLabel").pack(side="left", padx=(0, 14))
        self.profile = tk.StringVar()
        self.profile_box = ttk.Combobox(profile_row, textvariable=self.profile, state="readonly", width=34)
        self.profile_box.pack(side="left", fill="x", expand=True)
        ttk.Button(profile_row, text="恢复默认", command=self.reset_current).pack(side="right", padx=(8, 0))
        self.profile_box.bind("<<ComboboxSelected>>", self._profile_changed)
        self.options_panel = ScrollPanel(self.options_tab)
        self.options_panel.pack(fill="both", expand=True)
        ttk.Label(self.options_tab, text="启动命令预览", style="Panel.TLabel").pack(anchor="w", pady=(12, 6))
        self.preview = tk.Text(self.options_tab, height=5, wrap="word", font=("Consolas", 9),
                               background="#f4f6fa", foreground="#43516a", relief="flat", padx=10, pady=8, state="disabled")
        self.preview.pack(fill="x")
        log_actions = ttk.Frame(self.logs_tab, style="Panel.TFrame")
        log_actions.pack(fill="x", pady=(0, 8))
        ttk.Button(log_actions, text="清空显示", command=self.clear_log).pack(side="left")
        ttk.Button(log_actions, text="打开日志目录", command=self.open_logs).pack(side="left", padx=6)
        log_frame = ttk.Frame(self.logs_tab)
        log_frame.pack(fill="both", expand=True)
        self.log = tk.Text(log_frame, wrap="word", state="disabled", font=("Consolas", 10),
                           background="#152033", foreground="#e1e8f6", relief="flat", padx=12, pady=10)
        log_bar = ttk.Scrollbar(log_frame, command=self.log.yview)
        self.log.configure(yscrollcommand=log_bar.set)
        self.log.pack(side="left", fill="both", expand=True)
        log_bar.pack(side="right", fill="y")
        self.log.tag_configure("error", foreground="#ffb1a6")
        footer = ttk.Frame(self.root, padding=(24, 14, 24, 18))
        footer.pack(fill="x")
        self.hint = tk.StringVar(value="关闭启动中心不会关闭已启动的靶场；日志保留在本地。")
        ttk.Label(footer, textvariable=self.hint, style="Muted.TLabel", wraplength=740).pack(side="left", fill="x", expand=True)
        self.start_button = ttk.Button(footer, text="启动所选（0）", style="Primary.TButton", command=self.start_selected, state="disabled")
        self.start_button.pack(side="right", padx=(16, 0))

    def _load_state(self):
        if self.state_path:
            try:
                data = json.loads(self.state_path.read_text(encoding="utf-8"))
                return data if isinstance(data, dict) else {}
            except (OSError, ValueError):
                pass
        return {}

    def _store_form(self):
        if self.current_id not in self.settings:
            return
        item = self.items[self.current_id]
        setting = self.settings[self.current_id]
        profiles = {profile["label"]: profile["id"] for profile in item["profiles"]}
        setting["profile"] = profiles.get(self.profile.get(), setting["profile"])
        for option_id, (kind, variable, mapping) in self.option_vars.items():
            if kind == "multi":
                setting["values"][option_id] = [key for key, var in variable.items() if var.get()]
            elif kind == "choice":
                setting["values"][option_id] = mapping.get(variable.get(), "")
            else:
                setting["values"][option_id] = variable.get()

    def reload_catalog(self):
        self._store_form()
        try:
            catalog = load_catalog(self.config_path)
        except (OSError, ValueError) as error:
            self.hint.set(f"配置加载失败，当前清单保留。可点“维护靶场与选项”修正：{error}")
            self._append_log(f"配置错误：{error}\n", error=True)
            return False
        old_checked = {key for key, var in self.checked.items() if var.get()}
        if not self.items:
            old_checked = set(self.persisted.get("selected", []))
        previous = self.settings or self.persisted.get("settings", {})
        previous = previous if isinstance(previous, dict) else {}
        self.items = {item["id"]: item for item in catalog["ranges"]}
        self.settings, self.checked = {}, {}
        for item_id, item in self.items.items():
            old = previous.get(item_id, {})
            old = old if isinstance(old, dict) else {}
            profiles = {profile["id"] for profile in item["profiles"]}
            profile = old.get("profile", item["default_profile"])
            values = restore_values(item, old.get("values"))
            self.settings[item_id] = {"profile": profile if profile in profiles else item["default_profile"], "values": values}
            self.checked[item_id] = tk.BooleanVar(value=item_id in old_checked)
            self.status_vars.setdefault(item_id, tk.StringVar(value="待启动"))
        self.categories.configure(values=["全部分类"] + sorted({item["category"] for item in self.items.values()}))
        if self.category.get() not in self.categories["values"]:
            self.category.set("全部分类")
        self.current_id = self.current_id if self.current_id in self.items else next(iter(self.items), None)
        self.option_vars = {}
        self._render_list()
        if self.current_id:
            self._show_item(self.current_id, save_current=False)
        else:
            self.profile_box.configure(values=[])
            self.profile.set("")
            for child in self.options_panel.body.winfo_children():
                child.destroy()
            self.detail_title.set("还没有靶场")
            self.detail_description.set("点击“维护靶场与选项”添加启动配置。")
            self._set_preview("")
        self.hint.set(f"已加载 {len(self.items)} 个靶场；选项与启动命令可在配置中维护。")
        return True

    def _filtered_items(self):
        query = self.search.get().strip().casefold()
        return [item for item in self.items.values()
                if (self.category.get() == "全部分类" or item["category"] == self.category.get())
                and (not query or query in " ".join((item["id"], item["label"], item.get("description", ""))).casefold())]

    def _render_list(self):
        for child in self.list_panel.body.winfo_children():
            child.destroy()
        self.list_cards.clear()
        visible = self._filtered_items()
        for item in visible:
            item_id = item["id"]
            card = ttk.Frame(self.list_panel.body, style="Focus.TFrame" if item_id == self.current_id else "Card.TFrame", padding=10)
            self.list_cards[item_id] = card
            card.pack(fill="x", padx=(0, 6), pady=(0, 8))
            ttk.Checkbutton(card, text=item["label"], variable=self.checked[item_id], style="Card.TCheckbutton",
                            command=lambda key=item_id: self._selection_changed(key)).pack(anchor="w", fill="x")
            description = ttk.Label(card, text=item.get("description", ""), style="CardMuted.TLabel", wraplength=285, justify="left")
            description.pack(anchor="w", fill="x", pady=(5, 6))
            description.bind("<Button-1>", lambda _, key=item_id: self._show_item(key))
            status = ttk.Frame(card, style="Panel.TFrame")
            status.pack(fill="x")
            ttk.Label(status, text=item["category"], style="CardMuted.TLabel").pack(side="left")
            ttk.Label(status, textvariable=self.status_vars[item_id], style="CardMuted.TLabel").pack(side="right")
        if not visible:
            ttk.Label(self.list_panel.body, text="没有匹配的靶场", style="Panel.TLabel", padding=16).pack()
        self.list_panel.bind_wheel()
        self._selection_count()

    def _selection_count(self):
        count = sum(variable.get() for variable in self.checked.values())
        self.start_button.configure(text=f"启动所选（{count}）", state="normal" if count else "disabled")

    def _selection_changed(self, item_id):
        self._show_item(item_id)
        self._selection_count()

    def select_visible(self):
        for item in self._filtered_items():
            self.checked[item["id"]].set(True)
        self._selection_count()

    def clear_selection(self):
        self._store_form()
        for variable in self.checked.values():
            variable.set(False)
        for item_id, item in self.items.items():
            self.settings[item_id]["values"] = clear_values(item, self.settings[item_id]["values"])
        if self.current_id:
            # Do not copy the old on-screen values back over the cleared data.
            self._show_item(self.current_id, save_current=False)
        self._selection_count()
        self._save_state()
        self.hint.set("已清空全部靶场、版本和附加开关的勾选；启动方式、构建配置、地址、端口及工具路径已保留。")

    def _show_item(self, item_id, save_current=True):
        if save_current:
            self._store_form()
        previous_id = self.current_id
        self.current_id = item_id
        item, setting = self.items[item_id], self.settings[item_id]
        self.detail_title.set(item["label"])
        self.detail_description.set(item.get("description", ""))
        self.profile_box.configure(values=[profile["label"] for profile in item["profiles"]])
        self.profile.set(next(profile["label"] for profile in item["profiles"] if profile["id"] == setting["profile"]))
        for child in self.options_panel.body.winfo_children():
            child.destroy()
        self.option_vars = {}
        for option in item.get("options", []):
            if "profiles" in option and setting["profile"] not in option["profiles"]:
                continue
            self._option_widget(option, setting["values"].get(option["id"]))
        if not self.option_vars:
            ttk.Label(self.options_panel.body, text="此启动方式无需额外选项。", style="Panel.TLabel").pack(anchor="w", pady=10)
        self.options_panel.bind_wheel()
        # Selection only changes card styles; rebuilding the list loses its
        # widgets, keyboard focus and scroll position on every click.
        for key in {previous_id, item_id}:
            card = self.list_cards.get(key)
            if card is not None:
                card.configure(style="Focus.TFrame" if key == item_id else "Card.TFrame")
        self._update_preview()

    def _option_widget(self, option, value):
        frame = ttk.Frame(self.options_panel.body, style="Panel.TFrame", padding=(0, 0, 10, 14))
        frame.pack(fill="x")
        kind, option_id = option["type"], option["id"]
        choices = option.get("choices", [])
        ttk.Label(frame, text=option["label"] + (" *" if option.get("required") else ""), style="Panel.TLabel").pack(anchor="w", pady=(0, 6))
        mapping = {}
        if kind == "multi":
            variables = {}
            values = value if isinstance(value, list) else []
            grid = ttk.Frame(frame, style="Panel.TFrame")
            grid.pack(fill="x")
            for index, choice in enumerate(choices):
                variable = tk.BooleanVar(value=choice["value"] in values)
                variables[choice["value"]] = variable
                ttk.Checkbutton(grid, text=choice["label"], variable=variable, style="Panel.TCheckbutton",
                                command=self._update_preview).grid(row=index // 2, column=index % 2, sticky="w", padx=(0, 14), pady=3)
            self.option_vars[option_id] = (kind, variables, mapping)
            return
        if kind == "choice":
            mapping = {choice["label"]: choice["value"] for choice in choices}
            label = next((choice["label"] for choice in choices if choice["value"] == value), "")
            variable = tk.StringVar(value=label)
            widget = ttk.Combobox(frame, textvariable=variable, values=list(mapping), state="readonly")
        elif kind == "bool":
            variable = tk.BooleanVar(value=value is True)
            widget = ttk.Checkbutton(frame, text="启用", variable=variable, style="Panel.TCheckbutton")
        else:
            variable = tk.StringVar(value="" if value is None else str(value))
            if kind == "integer":
                widget = ttk.Spinbox(frame, textvariable=variable, from_=option.get("min", -2147483648), to=option.get("max", 2147483647))
            else:
                widget = ttk.Entry(frame, textvariable=variable)
        widget.pack(fill="x")
        self.option_vars[option_id] = (kind, variable, mapping)
        variable.trace_add("write", lambda *_: self._update_preview())

    def _profile_changed(self, _event=None):
        self._store_form()
        if self.current_id:
            self._show_item(self.current_id, save_current=False)

    def reset_current(self):
        if not self.current_id:
            return
        item = self.items[self.current_id]
        self.settings[self.current_id] = {"profile": item["default_profile"], "values": default_values(item)}
        self._show_item(self.current_id, save_current=False)
        self.hint.set(f"已恢复 {item['label']} 的配置默认选项；勾选状态保留。")

    def _set_preview(self, text):
        self.preview.configure(state="normal")
        self.preview.delete("1.0", "end")
        self.preview.insert("1.0", text)
        self.preview.configure(state="disabled")

    def _update_preview(self):
        if not self.current_id:
            return
        self._store_form()
        setting = self.settings[self.current_id]
        try:
            command, cwd = build_command(self.items[self.current_id], setting["profile"], setting["values"], self.repo_root)
            self._set_preview(f"工作目录：{cwd}\n{subprocess.list2cmdline(command)}")
        except (ValueError, OSError, TypeError) as error:
            self._set_preview(f"参数需要修正：{error}")

    def start_selected(self):
        self._store_form()
        for item_id, variable in self.checked.items():
            if not variable.get():
                continue
            existing = self.runner.jobs.get(item_id)
            if item_id in self.pending or (existing and existing.state == "running"):
                self._append_log(f"[{self.items[item_id]['label']}] 启动任务仍在运行，已跳过重复请求。\n")
                continue
            item, setting = self.items[item_id], self.settings[item_id]
            try:
                command, cwd = build_command(item, setting["profile"], setting["values"], self.repo_root)
            except (ValueError, OSError, TypeError) as error:
                self.status_vars[item_id].set("参数错误")
                self._append_log(f"[{item['label']}] {error}\n", error=True)
                continue
            self.queue.append((item_id, item["label"], command, cwd))
            self.pending.add(item_id)
            self.status_vars[item_id].set("等待启动")
        self.notebook.select(self.logs_tab)
        self._save_state()
        if self.queue and not self.queue_scheduled:
            self.queue_scheduled = True
            self.queue_id = self.root.after(0, self._next_job)

    def _next_job(self):
        self.queue_id = None
        if self.closed or not self.queue:
            self.queue_scheduled = False
            return
        item_id, label, command, cwd = self.queue.pop(0)
        self.pending.discard(item_id)
        self._append_log(f"\n[{label}] {subprocess.list2cmdline(command)}\n")
        try:
            job = self.runner.start(item_id, label, command, cwd)
            if item_id in self.status_vars:
                self.status_vars[item_id].set("执行中")
            self._append_log(f"[{label}] 日志：{job.log_path}\n")
        except (OSError, ValueError) as error:
            if item_id in self.status_vars:
                self.status_vars[item_id].set("启动失败")
            self._append_log(f"[{label}] 启动失败：{error}\n", error=True)
        if self.queue:
            self.queue_id = self.root.after(100, self._next_job)
        else:
            self.queue_scheduled = False

    def _poll(self):
        if self.closed:
            return
        for event in self.runner.poll():
            item_id = event["id"]
            label = self.runner.jobs[item_id].label
            if event["kind"] == "output":
                self._append_log(f"[{label}] {event['text']}")
            elif event["kind"] == "status":
                failed = event["state"] == "failed"
                text = f"失败（退出码 {event['returncode']}）" if failed else "启动命令完成"
                if item_id in self.status_vars:
                    self.status_vars[item_id].set(text)
                self._append_log(f"\n[{label}] {text}\n", error=failed)
        active = sum(job.state == "running" for job in self.runner.jobs.values())
        if active or self.pending:
            self.hint.set(f"执行中 {active} 项，等待 {len(self.pending)} 项。关闭启动中心不会结束已启动的程序。")
        elif self.runner.jobs:
            failed = sum(job.state == "failed" for job in self.runner.jobs.values())
            self.hint.set(f"启动任务已完成，失败 {failed} 项。状态反映启动命令；已打开的靶场独立运行。")
        self.poll_id = self.root.after(200, self._poll)

    def _append_log(self, text, error=False):
        text = re.sub(r"\x1b\[[0-?]*[ -/]*[@-~]", "", text).replace("\r\n", "\n").replace("\r", "\n")
        self.log.configure(state="normal")
        self.log.insert("end", text, "error" if error else ())
        line_count = int(self.log.index("end-1c").split(".")[0])
        if line_count > 4000:
            self.log.delete("1.0", f"{line_count - 4000}.0")
        self.log.see("end")
        self.log.configure(state="disabled")

    def clear_log(self):
        self.log.configure(state="normal")
        self.log.delete("1.0", "end")
        self.log.configure(state="disabled")

    def open_logs(self):
        self.log_dir.mkdir(parents=True, exist_ok=True)
        if os.name == "nt":
            os.startfile(str(self.log_dir))
        else:
            self.hint.set(str(self.log_dir))

    def edit_catalog(self):
        if self.editor and self.editor.winfo_exists():
            self.editor.lift()
        else:
            self.editor = CatalogEditor(self.root, self.config_path, self.reload_catalog)

    def _save_state(self):
        if not self.state_path:
            return
        self._store_form()
        data = {"selected": [key for key, var in self.checked.items() if var.get()], "settings": self.settings}
        try:
            self.state_path.parent.mkdir(parents=True, exist_ok=True)
            temporary = self.state_path.with_suffix(".tmp")
            temporary.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
            temporary.replace(self.state_path)
        except OSError as error:
            self.hint.set(f"界面选项未保存：{error}")

    def check_ui(self):
        if not self.items:
            raise ValueError("界面自检需要至少一个有效靶场配置")
        profiles = 0
        for item_id, item in self.items.items():
            for profile in item["profiles"]:
                self.settings[item_id]["profile"] = profile["id"]
                self._show_item(item_id, save_current=False)
                self.root.update_idletasks()
                setting = self.settings[item_id]
                build_command(item, profile["id"], setting["values"], self.repo_root)
                profiles += 1
        if self.runner.jobs or self.pending:
            raise RuntimeError("界面自检不应启动任何子进程")
        return {"passed": True, "ranges": len(self.items), "profiles_checked": profiles,
                "range_checkboxes": len(self.checked), "launched_processes": 0}

    def close(self):
        self._save_state()
        self.closed = True
        self.root.after_cancel(self.poll_id)
        if self.queue_id is not None:
            self.root.after_cancel(self.queue_id)
        self.root.destroy()
