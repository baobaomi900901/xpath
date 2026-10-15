"""Deterministic fixtures and drag telemetry shared with the Win32 range."""

import json
import time
from dataclasses import dataclass


CITIES = ("北京", "上海", "广州", "深圳", "杭州")
GENDERS = ("男", "女", "其他")
HOBBIES = ("阅读", "运动", "音乐", "旅行")
PAGE_SIZE = 20
TARGET_WIDTH = 120
TARGET_HEIGHT = 80


def build_employees():
    departments = ("研发部", "产品部", "市场部", "销售部", "人事部")
    statuses = ("在职", "离职", "待入职")
    return [
        (number, "用户{}".format(number), departments[number % 5],
         CITIES[number % 5], statuses[number % 3],
         "user{}@example.com".format(number),
         "2024-{:02d}-{:02d}".format(number % 12 + 1, number % 28 + 1))
        for number in range(1, 1001)
    ]


def anchor_region(x, y):
    column = max(0, min(2, x * 3 // TARGET_WIDTH))
    row = max(0, min(2, y * 3 // TARGET_HEIGHT))
    return (
        "topLeft", "topCenter", "topRight", "middleLeft", "middleCenter",
        "middleRight", "bottomLeft", "bottomCenter", "bottomRight",
    )[row * 3 + column]


@dataclass
class DragState:
    left: int = 0
    top: int = 0
    initial_left: int = 0
    initial_top: int = 0
    start_left: int = 0
    start_top: int = 0
    anchor_x: int = 60
    anchor_y: int = 40
    move_count: int = 0
    duration_ms: int = 0
    dragging: bool = False
    started_at: float = 0.0

    def reset(self, width, height):
        self.left = max(0, width - TARGET_WIDTH) // 2
        self.top = max(0, height - TARGET_HEIGHT) // 2
        self.initial_left = self.start_left = self.left
        self.initial_top = self.start_top = self.top
        self.anchor_x, self.anchor_y = 60, 40
        self.move_count = self.duration_ms = 0
        self.dragging = False
        self.started_at = 0.0

    def clamp(self, width, height):
        self.left = max(0, min(self.left, max(0, width - TARGET_WIDTH)))
        self.top = max(0, min(self.top, max(0, height - TARGET_HEIGHT)))

    def begin(self, x, y, now=None):
        self.start_left, self.start_top = self.left, self.top
        self.anchor_x = max(0, min(x, TARGET_WIDTH - 1))
        self.anchor_y = max(0, min(y, TARGET_HEIGHT - 1))
        self.move_count = self.duration_ms = 0
        self.dragging = True
        self.started_at = time.monotonic() if now is None else now

    def move(self, pointer_x, pointer_y, width, height):
        if not self.dragging:
            return
        old_position = self.left, self.top
        self.left, self.top = pointer_x - self.anchor_x, pointer_y - self.anchor_y
        self.clamp(width, height)
        if old_position != (self.left, self.top):
            self.move_count += 1

    def end(self, now=None):
        if self.dragging:
            ended_at = time.monotonic() if now is None else now
            self.duration_ms = max(0, int((ended_at - self.started_at) * 1000))
            self.dragging = False

    def to_json(self):
        # Keep both field names and insertion order aligned with DragStateJson().
        return json.dumps({
            "left": self.left, "top": self.top,
            "initialLeft": self.initial_left, "initialTop": self.initial_top,
            "deltaLeft": self.left - self.initial_left,
            "deltaTop": self.top - self.initial_top,
            "startLeft": self.start_left, "startTop": self.start_top,
            "sessionDeltaLeft": self.left - self.start_left,
            "sessionDeltaTop": self.top - self.start_top,
            "anchor": {"x": self.anchor_x, "y": self.anchor_y,
                       "sudokuPart": anchor_region(self.anchor_x, self.anchor_y)},
            "moveCount": self.move_count, "durationMs": self.duration_ms,
            "dragging": self.dragging,
        }, ensure_ascii=False, separators=(",", ":"))
