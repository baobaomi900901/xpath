import json

import uipilot


LIBRARY_DIR = r"C:\Users\moby\Desktop\work_tree\锚点"
ELEMENT_NAME = "百度一下"


def item_to_dict(kind, item):
    return {
        "type": kind,
        "id": item.id,
        "name": item.name,
        "raw": item.raw,
    }


with uipilot.Client(timeout=5) as client:
    pkg = client.open(LIBRARY_DIR)

    results = []

    for item in pkg.win32.list():
        if item.name == ELEMENT_NAME:
            results.append(item_to_dict("win32", item))

    for item in pkg.web.list():
        if item.name == ELEMENT_NAME:
            results.append(item_to_dict("web", item))

    for item in pkg.image.list():
        if item.name == ELEMENT_NAME:
            results.append(item_to_dict("image", item))

print(json.dumps(results, ensure_ascii=False, indent=2))
