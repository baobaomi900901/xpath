"""A real Tk button as the movable target, with matching Win32 telemetry."""

import tkinter as tk
from tkinter import ttk

from .models import DragState, TARGET_HEIGHT, TARGET_WIDTH, anchor_region


class DragPage(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent, name="drag", padding=18)
        self.state = DragState()
        self.target = None
        self.initialized = False
        self.columnconfigure(0, weight=1)
        self.rowconfigure(7, weight=1)
        ttk.Label(self, text="拖拽测试", style="Heading.TLabel").grid(row=0, column=0, sticky="w")
        ttk.Label(self, text="拖动 drag-target；目标限制在区域内。复制当前结果可获得与 Win32 一致的 JSON 字段。").grid(
            row=1, column=0, sticky="w", pady=(8, 14))
        self.position = tk.StringVar(self)
        self.anchor = tk.StringVar(self)
        self.result = tk.StringVar(self)
        self.status = tk.StringVar(self, value="状态: 空闲")
        for row, (name, variable) in enumerate((("position", self.position), ("anchor", self.anchor),
                                                ("result", self.result), ("status", self.status)), start=2):
            ttk.Label(self, name=name, textvariable=variable).grid(row=row, column=0, sticky="w", pady=4)
        actions = ttk.Frame(self, name="actions")
        actions.grid(row=6, column=0, sticky="w", pady=(10, 14))
        self.reset_button = ttk.Button(actions, name="reset", text="重置位置", command=self.reset)
        self.copy_button = ttk.Button(actions, name="copy", text="复制当前结果", command=self.copy)
        self.hide_button = ttk.Button(actions, name="hide", text="隐藏 drag-target", command=self.hide)
        for index, button in enumerate((self.reset_button, self.copy_button, self.hide_button)):
            button.grid(row=0, column=index, padx=(0, 12))
        self.arena = tk.Frame(self, name="arena", background="#edf2f7", width=600, height=360,
                              highlightthickness=0, borderwidth=0)
        self.arena.grid(row=7, column=0, sticky="nsew")
        self.arena.bind("<Configure>", self.resize)
        self.bind("<Unmap>", self.end)
        self.create_target()
        self.update_labels()

    def create_target(self):
        if self.target is not None:
            return
        self.target = tk.Button(self.arena, name="drag-target", text="drag-target", cursor="fleur",
                                 background="#c9e3ff", activebackground="#aed5ff", relief="raised")
        self.target.bind("<ButtonPress-1>", self.begin)
        self.target.bind("<B1-Motion>", self.move)
        self.target.bind("<ButtonRelease-1>", self.release)
        self.target.bind("<Escape>", self.end)

    def place_target(self):
        if self.target is not None:
            self.target.place(x=self.state.left, y=self.state.top, width=TARGET_WIDTH, height=TARGET_HEIGHT)

    def resize(self, event):
        if not self.initialized:
            self.state.reset(event.width, event.height)
            self.initialized = True
        else:
            self.state.clamp(event.width, event.height)
        self.place_target()
        self.update_labels()

    def begin(self, event):
        self.state.begin(event.x, event.y)
        self.target.focus_set()
        self.target.grab_set()
        self.status.set("状态: 拖拽中")
        self.update_labels()
        return "break"

    def move(self, event):
        self.state.move(event.x_root - self.arena.winfo_rootx(), event.y_root - self.arena.winfo_rooty(),
                        self.arena.winfo_width(), self.arena.winfo_height())
        self.place_target()
        self.update_labels()
        return "break"

    def end(self, event=None):
        if self.state.dragging:
            self.state.end()
            if self.target is not None and self.target.grab_current() == self.target:
                self.target.grab_release()
            self.status.set("状态: 空闲")
            self.update_labels()
        return "break"

    def release(self, event):
        self.move(event)
        return self.end()

    def reset(self):
        self.end()
        self.create_target()
        self.state.reset(self.arena.winfo_width(), self.arena.winfo_height())
        self.initialized = self.arena.winfo_width() > 1
        self.place_target()
        self.hide_button.state(["!disabled"])
        self.status.set("状态: 空闲")
        self.update_labels()

    def hide(self):
        self.end()
        if self.target is not None:
            self.target.destroy()
            self.target = None
        self.hide_button.state(["disabled"])
        self.status.set("状态: 元素已隐藏")

    def copy(self):
        try:
            self.clipboard_clear()
            self.clipboard_append(self.state.to_json())
            self.status.set("状态: 已复制当前结果")
        except tk.TclError:
            self.status.set("状态: 复制失败（剪贴板可能正被占用）")

    def update_labels(self):
        state = self.state
        self.position.set("当前位置: left={}, top={}    相对初始: Δleft={}, Δtop={}".format(
            state.left, state.top, state.left - state.initial_left, state.top - state.initial_top))
        self.anchor.set("按下锚点: x={}, y={}, sudoku_part={}".format(
            state.anchor_x, state.anchor_y, anchor_region(state.anchor_x, state.anchor_y)))
        self.result.set("本次拖拽: Δleft={}, Δtop={}, move={}, duration={}ms".format(
            state.left - state.start_left, state.top - state.start_top, state.move_count, state.duration_ms))
