"""Validated catalog editing, kept separate from the launch dashboard."""
from __future__ import annotations

import json
from pathlib import Path
import tkinter as tk
from tkinter import ttk

from .config import save_catalog, validate_catalog


class CatalogEditor(tk.Toplevel):
    def __init__(self, parent, path: Path, on_saved):
        super().__init__(parent)
        self.path, self.on_saved = path, on_saved
        self.title("维护靶场与选项")
        width = min(1000, max(700, self.winfo_screenwidth() - 80))
        height = min(720, max(500, self.winfo_screenheight() - 90))
        self.geometry(f"{width}x{height}")
        self.minsize(min(760, width), min(500, height))
        self.transient(parent)
        self.columnconfigure(0, weight=1)
        self.rowconfigure(2, weight=1)
        ttk.Label(self, text="维护靶场与选项", style="Heading.TLabel").grid(row=0, column=0, sticky="w", padx=20, pady=(16, 8))
        ttk.Label(self, text="编辑后先校验再保存。保存会备份原配置为 .json.bak；完整字段说明见 tools/RANGE_LAUNCHER.md。",
                  wraplength=920).grid(row=1, column=0, sticky="w", padx=20, pady=(0, 12))
        frame = ttk.Frame(self)
        frame.grid(row=2, column=0, sticky="nsew", padx=20)
        frame.columnconfigure(0, weight=1)
        frame.rowconfigure(0, weight=1)
        self.text = tk.Text(frame, wrap="none", font=("Consolas", 10), undo=True,
                            background="#ffffff", foreground="#162233", insertbackground="#245dcc")
        scroll = ttk.Scrollbar(frame, orient="vertical", command=self.text.yview)
        horizontal = ttk.Scrollbar(frame, orient="horizontal", command=self.text.xview)
        self.text.configure(yscrollcommand=scroll.set, xscrollcommand=horizontal.set)
        self.text.grid(row=0, column=0, sticky="nsew")
        scroll.grid(row=0, column=1, sticky="ns")
        horizontal.grid(row=1, column=0, sticky="ew")
        notice = str(path)
        try:
            raw = path.read_bytes()
            try:
                initial = raw.decode("utf-8-sig")
            except UnicodeError:
                if raw.startswith((b"\xff\xfe\x00\x00", b"\x00\x00\xfe\xff")):
                    encoding = "utf-32"
                elif raw.startswith((b"\xff\xfe", b"\xfe\xff")):
                    encoding = "utf-16"
                else:
                    encoding = "gb18030"
                try:
                    initial = raw.decode(encoding)
                    notice = f"原文件不是 UTF-8，已按 {encoding} 打开；请检查文字。保存时转换为 UTF-8 并备份原始文件。"
                except UnicodeError:
                    initial = raw.decode("utf-8", errors="replace")
                    notice = "文件含无法解码的字节，已用替换字符显示；请修正后保存为 UTF-8，原始文件会备份。"
        except OSError as error:
            initial = '{"schema_version": 1, "ranges": []}\n'
            notice = f"原配置无法读取：{error}；可以编辑模板后尝试保存。"
        self.text.insert("1.0", initial)
        self.status = tk.StringVar(value=notice)
        ttk.Label(self, textvariable=self.status, wraplength=920).grid(row=3, column=0, sticky="w", padx=20, pady=10)
        buttons = ttk.Frame(self)
        buttons.grid(row=4, column=0, sticky="ew", padx=20, pady=(0, 18))
        ttk.Button(buttons, text="添加靶场模板", command=self.add_template).pack(side="left")
        ttk.Button(buttons, text="校验配置", command=self.validate).pack(side="left", padx=8)
        ttk.Button(buttons, text="保存并重新加载", style="Primary.TButton", command=self.save).pack(side="right")
        ttk.Button(buttons, text="关闭", command=self.destroy).pack(side="right", padx=8)

    def data(self):
        result = json.loads(self.text.get("1.0", "end-1c"))
        validate_catalog(result)
        return result

    def validate(self):
        try:
            data = self.data()
        except (ValueError, TypeError) as error:
            self.status.set(f"配置未通过校验：{error}")
            return False
        self.status.set(f"校验通过：{len(data['ranges'])} 个靶场。")
        return True

    def save(self):
        try:
            data = self.data()
            save_catalog(self.path, data)
        except (ValueError, TypeError, OSError) as error:
            self.status.set(f"保存失败，原配置保留：{error}")
            return
        self.on_saved()
        self.status.set(f"已保存并重新加载；原配置备份：{self.path.name}.bak")

    def add_template(self):
        try:
            data = self.data()
        except (ValueError, TypeError) as error:
            self.status.set(f"请先修正当前配置：{error}")
            return
        existing = {item["id"] for item in data["ranges"]}
        index = 1
        while f"custom-{index}" in existing:
            index += 1
        data["ranges"].append({
            "id": f"custom-{index}", "label": "新靶场", "category": "自定义",
            "description": "将 command 中的脚本路径替换为实际启动脚本。",
            "command": ["{python}", "{root}/tools/start_custom.py"], "cwd": ".",
            "profiles": [{"id": "run", "label": "启动", "args": []}], "default_profile": "run",
            "options": [],
        })
        self.text.delete("1.0", "end")
        self.text.insert("1.0", json.dumps(data, ensure_ascii=False, indent=2) + "\n")
        self.text.see("end")
        self.status.set("已添加模板；请填写实际名称、路径和选项后保存。")
