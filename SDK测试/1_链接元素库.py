# connect_library_min.py
import uipilot

LIBRARY_DIR = r"C:\Users\moby\Desktop\work_tree\锚点"

with uipilot.Client(timeout=5) as client:
    pkg = client.open(LIBRARY_DIR)

    print("连接成功")
    print("元素库:", pkg.library_dir)
    print("Win 元素数量:", pkg.win_count)
    print("Web 元素数量:", pkg.web_count)
    print("Image 元素数量:", pkg.image_count)