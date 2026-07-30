import os
import time
from datetime import datetime

import uiautomation as uia
from PIL import Image
import mss

# Minimal demo:
# - Find the WeChat "消息" list control via UIAutomation.
# - Poll visible children; when content fingerprint changes, capture a screenshot
#   of the message list control's bounding rectangle.
# - Save screenshots into a local .tmp folder.
#
# Notes:
# - This demo is best-effort for "new message detected".
# - It does NOT extract nickname/avatar; it only screenshots the message area.


HERE_DIR = os.path.dirname(os.path.abspath(__file__))
OUT_DIR = os.path.join(HERE_DIR, ".tmp")
os.makedirs(OUT_DIR, exist_ok=True)

POLL_INTERVAL_SEC = 0.6
MAX_CAPTURES = 50

# From your UIA dump:
# - AutomationId = "chat_message_list"
# - ClassName   = "mmui::RecyclerListView"
# - Name        = "消息"
TARGET_AUTOMATION_ID = "chat_message_list"
TARGET_CLASS_NAME = "mmui::RecyclerListView"
TARGET_NAME = "消息"


def find_message_list():
    """
    BFS over UIA control tree to locate the "消息" message list container.

    This avoids relying on non-universal helper APIs like FindFirst/WalkControl.
    """
    root = uia.GetRootControl()
    max_depth = 40
    max_nodes = 50000

    target_aid = TARGET_AUTOMATION_ID
    target_class = TARGET_CLASS_NAME
    target_name = TARGET_NAME

    stack = [(root, 0)]
    visited = 0

    while stack:
        ctrl, depth = stack.pop()
        visited += 1
        if visited > max_nodes:
            break
        if depth > max_depth:
            continue

        try:
            if (
                getattr(ctrl, "AutomationId", None) == target_aid
                and getattr(ctrl, "ClassName", None) == target_class
                and (getattr(ctrl, "Name", None) or "").strip() == target_name
            ):
                return ctrl
        except Exception:
            pass

        if depth == max_depth:
            continue

        try:
            children = ctrl.GetChildren()
        except Exception:
            continue

        # DFS/BFS doesn't matter for the demo; we just traverse.
        for ch in children:
            stack.append((ch, depth + 1))

    return None


def list_fingerprint(msg_list_ctrl):
    """
    Fingerprint visible items (best-effort) by concatenating the last few non-empty child texts.

    Returns:
        fp (str), child_count (int), sample (list[str])
    """
    try:
        children = msg_list_ctrl.GetChildren()
    except Exception:
        return "", 0, []

    items = []
    sample = []
    for ch in children:
        try:
            n = ""
            try:
                n = (getattr(ch, "Name", None) or "").strip()
            except Exception:
                n = ""

            # Fallback: sometimes Name can be empty for some controls.
            if not n:
                try:
                    legacy = getattr(ch, "LegacyIAccessible", None)
                    if legacy is not None:
                        n = (getattr(legacy, "Name", None) or "").strip()
                except Exception:
                    n = ""

            if not n:
                continue

            n = n.replace("\r", " ").replace("\n", " ")
            # Add a coarse position bucket so that scrolling/virtualization
            # changes can still trigger.
            top_bucket = None
            try:
                r = getattr(ch, "BoundingRectangle", None)
                if r is not None:
                    top = int(getattr(r, "Top", getattr(r, "top", 0)))
                    top_bucket = int(top / 10)
            except Exception:
                top_bucket = None

            if top_bucket is None:
                items.append(n[:120])
            else:
                items.append(f"{n[:80]}@{top_bucket}")

            names_for_sample = items[-1]  # same string already sliced
            if len(sample) < 5:
                sample.append(names_for_sample[:80])
        except Exception:
            continue

    tail = items[-8:]
    return "|".join(tail), len(items), sample


def screenshot_rect(rect):
    """
    Screenshot the area described by UIA BoundingRectangle.
    """
    left = int(getattr(rect, "Left", rect.left))
    top = int(getattr(rect, "Top", rect.top))
    right = int(getattr(rect, "Right", rect.right))
    bottom = int(getattr(rect, "Bottom", rect.bottom))

    width = max(1, right - left)
    height = max(1, bottom - top)

    with mss.mss() as sct:
        img = sct.grab({"left": left, "top": top, "width": width, "height": height})

        # mss returns BGRA bytes; convert to RGB for saving.
        im = Image.frombytes("RGB", img.size, img.bgra, "raw", "BGRX")
        return im


def main():
    print("Starting WeChat message screenshot demo.", flush=True)
    print("Ensure a chat window is open and visible.", flush=True)

    # Locate once first to avoid doing a full UI tree BFS every poll.
    msg_list = find_message_list()
    if msg_list is None:
        print("Message list not found yet; will retry...", flush=True)
    else:
        print("Message list found; start polling visible children.", flush=True)

    last_fp = None
    captures = 0

    debug_printed = 0
    while captures < MAX_CAPTURES:
        if msg_list is None:
            time.sleep(1.0)
            msg_list = find_message_list()
            continue

        fp, child_count, sample = list_fingerprint(msg_list)

        if debug_printed < 5:
            sample_ascii = [ascii(x) for x in sample]
            print(
                f"[DEBUG] child_count={child_count} fp_len={len(fp)} sample={sample_ascii}",
                flush=True,
            )
            debug_printed += 1

        if last_fp is None:
            last_fp = fp
        elif fp != last_fp and fp.strip():
            rect = msg_list.BoundingRectangle
            img = screenshot_rect(rect)

            ts = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]
            out_path = os.path.join(OUT_DIR, f"msg_{ts}.png")
            img.save(out_path)

            captures += 1
            print(f"[CAPTURE {captures}/{MAX_CAPTURES}] saved: {out_path}", flush=True)
            last_fp = fp

        time.sleep(POLL_INTERVAL_SEC)

    print("Done.", flush=True)


if __name__ == "__main__":
    main()

