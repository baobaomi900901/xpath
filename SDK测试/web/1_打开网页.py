# import uipilot


# URL = "https://www.baidu.com"
# BROWSER = "chrome"  # 可改为 "edge"


# with uipilot.Client(timeout=5) as client:
#     client.inner.web_navigate(URL, mode=BROWSER, timeout_ms=20_000).raise_for_error()
#     client.inner.web_wait_ready(mode=BROWSER, page_url=URL, timeout_ms=20_000).raise_for_error()

#     page = client.inner.web_get_browser_info(mode=BROWSER, page_url=URL)

# print("打开网页成功")
# print("url:", page.get("url"))
# print("title:", page.get("title"))


from uipilot import web

web_object = web.create('www.baidu.com', 'chrome', load_timeout=20)
print(web_object)