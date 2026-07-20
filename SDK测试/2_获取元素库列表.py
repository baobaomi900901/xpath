# list_all_elements_json.py
import json
import uipilot

LIBRARY_DIR = r"C:\Users\moby\Desktop\work_tree\锚点"

with uipilot.Client(timeout=5) as client:
    pkg = client.open(LIBRARY_DIR)

    elements = []

    for kind, group in [
        ("win32", pkg.win32.list()),
        ("web", pkg.web.list()),
        ("image", pkg.image.list()),
    ]:
        for item in group:
            elements.append({
                "type": kind,
                "id": item.id,
                "name": item.name,
                "raw": item.raw,
            })

print(json.dumps(elements, ensure_ascii=False, indent=2))