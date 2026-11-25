"""Loopback application backend. Never serve operator files or evaluation answers."""
import json
import mimetypes
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, quote, urlsplit

from .domain import BusinessError, Store
from .workbooks import INVENTORY_COLUMNS, QUOTE_COLUMNS

WEB_ROOT = Path(__file__).resolve().parent / "web"
ASSETS = {"/": "index.html", "/index.html": "index.html", "/style.css": "style.css",
          "/app.js": "app.js", "/model.js": "model.js", "/obstacles.js": "obstacles.js"}
XLSX_TYPE = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"


def tsv(columns, rows):
    def cell(value):
        text = str(value).lower() if isinstance(value, bool) else str(value)
        return text.replace("\t", " ").replace("\r", " ").replace("\n", " ")
    return ("\t".join(columns) + "\n" + "".join("\t".join(cell(row.get(c, "")) for c in columns) + "\n" for row in rows)).encode("utf-8")


def make_server(run_dir, port=8765, control_token=None):
    store = Store(run_dir)

    class Handler(BaseHTTPRequestHandler):
        protocol_version = "HTTP/1.1"

        def log_message(self, format, *args):
            # Persistent business events are the audit source; avoid noisy console logs.
            pass

        def reply(self, body, content_type="text/plain; charset=utf-8", status=200, filename=None):
            if isinstance(body, str):
                body = body.encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            if filename:
                self.send_header("Content-Disposition", "attachment; filename*=UTF-8''" + quote(filename))
            self.end_headers()
            self.wfile.write(body)

        def json(self, value, status=200):
            self.reply(json.dumps(value, ensure_ascii=False), "application/json; charset=utf-8", status)

        def dataset(self, columns, rows, query):
            if query.get("format") == "tsv":
                self.reply(tsv(columns, rows), "text/tab-separated-values; charset=utf-8")
            else:
                self.json(dict(rows=rows))

        def do_GET(self):
            try:
                self.handle_get()
            except BusinessError as error:
                self.reply(str(error), status=error.status)
            except (BrokenPipeError, ConnectionResetError):
                pass

        def handle_get(self):
            parsed = urlsplit(self.path)
            query = {k: v[-1] for k, v in parse_qs(parsed.query).items()}
            route = parsed.path
            if route in ASSETS:
                asset = WEB_ROOT / ASSETS[route]
                if not asset.is_file():
                    return self.reply("界面资源不存在", status=404)
                kind = mimetypes.guess_type(asset.name)[0] or "application/octet-stream"
                body = asset.read_bytes()
                if asset.name == "index.html" and store.fixture["context"].get("obstacles", False):
                    body = body.replace(b'data-obstacles="false"', b'data-obstacles="true"')
                return self.reply(body, kind + "; charset=utf-8")
            if route == "/health":
                return self.json(dict(status="ok", run_id=store.fixture["context"]["run_id"]))
            if route == "/api/context":
                context = store.fixture["context"]
                return self.reply(tsv(list(context), [context]), "text/tab-separated-values; charset=utf-8") if query.get("format") == "tsv" else self.json(context)
            if route in ("/api/inventory", "/api/export/inventory"):
                rows = store.inventory(**{key: query.get(key, "") for key in ("plant", "warehouse", "search")})
                if route.endswith("/inventory") and "/export/" in route:
                    return self.reply(store.export_inventory(rows), XLSX_TYPE, filename=f"库存补货需求_{store.fixture['context']['batch_id']}.xlsx")
                return self.json(dict(rows=rows))
            if route == "/api/quotes":
                return self.dataset(QUOTE_COLUMNS, store.quotes(query.get("material_id", "")), query)
            if route == "/api/export/quotes":
                ids = [x.strip() for x in query.get("material_ids", "").split(",") if x.strip()]
                return self.reply(store.export_quotes(ids), XLSX_TYPE, filename=f"供应商报价_{store.fixture['context']['batch_id']}.xlsx")
            if route == "/api/suppliers":
                return self.dataset(["supplier_id", "name", "active"], store.fixture["suppliers"], query)
            if route == "/api/materials":
                context = store.fixture["context"]
                return self.dataset(["material_id", "name", "unit"], [r for r in store.inventory(context["plant"], context["warehouse"]) if r["enabled"]], query)
            if route == "/api/orders":
                with store.lock:
                    orders = [dict(o) for o in store.state["orders"]]
                    store.record("orders_viewed", order_ids=[o["order_id"] for o in orders])
                if query.get("format") != "tsv":
                    return self.json(dict(rows=orders))
                rows = [dict(o, lines="；".join(f"{line['material_id']} {line['name']} ×{line['quantity']} @{line['unit_price']} 报价:{line['quote_id']}" for line in o["lines"])) for o in orders]
                return self.dataset(["order_id", "batch_id", "supplier_id", "supplier_name", "warehouse", "delivery_date", "total", "status", "lines"], rows, query)
            return self.reply("未找到", status=404)

        def do_POST(self):
            try:
                size = int(self.headers.get("Content-Length", "0"))
                if size <= 0 or size > 8 * 1024 * 1024:
                    self.close_connection = True
                    return self.reply("请求体为空或超过 8MB", status=400)
                self.connection.settimeout(15)
                body = self.rfile.read(size)
                if len(body) != size:
                    return self.reply("请求体不完整", status=400)
                route = urlsplit(self.path).path
                if route == "/api/import/inventory":
                    return self.reply(tsv(INVENTORY_COLUMNS, store.import_inventory(body)), "text/tab-separated-values; charset=utf-8")
                if route == "/api/confirm/quotes":
                    store.confirm_quote_save(body)
                    return self.reply("报价文件保存已确认")
                form = {k: v[-1] for k, v in parse_qs(body.decode("utf-8"), keep_blank_values=True).items()}
                if route == "/api/orders":
                    order = store.submit_order(form)
                    return self.reply(tsv(["order_id", "total", "status"], [order]), "text/tab-separated-values; charset=utf-8", 201)
                if route == "/api/exceptions":
                    store.register_exception(form)
                    return self.reply("异常已登记", status=201)
                if route == "/__control/stop" and control_token and form.get("token") == control_token:
                    self.reply("正在关闭")
                    threading.Thread(target=self.server.shutdown, daemon=True).start()
                    return
                return self.reply("未找到", status=404)
            except BusinessError as error:
                self.reply(str(error), status=error.status)
            except (ValueError, UnicodeDecodeError):
                self.reply("请求格式不正确", status=400)
            except (BrokenPipeError, ConnectionResetError, TimeoutError):
                self.close_connection = True

    server = ThreadingHTTPServer(("127.0.0.1", port), Handler)
    server.daemon_threads = True
    server.store = store
    return server
