# tinhnang/backend/http_handler.py
import os
import json
import urllib.parse
from http.server import BaseHTTPRequestHandler

from ..core.config import get_config, RESTART_REQUIRED_FIELDS


class WiFiHTTPHandler(BaseHTTPRequestHandler):
    """Phục vụ HTML template + static assets + API UI/config."""

    registry = None

    # ===================== GET =====================
    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        if path in ("/", "/index.html"):
            self._serve_html("index.html")
        elif path == "/static/style.css":
            self._serve_static("style.css", "text/css")
        elif path == "/static/script.js":
            self._serve_static("script.js", "application/javascript")
        elif path == "/api/ui":
            self._serve_ui_config()
        elif path == "/api/versions":
            self._serve_versions()
        elif path == "/api/config":
            self._get_config()
        else:
            self._serve_404()

    # ===================== POST =====================
    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        if path == "/api/config":
            self._post_config()
        else:
            self._send_error(404, "Not Found", "Endpoint không tồn tại")

    # ===================== CONFIG API =====================
    def _get_config(self):
        try:
            cfg = get_config()
            if not cfg.root_checked:
                cfg.detect_root()
            payload = {
                "config": cfg.to_dict(),
                "is_root": cfg.is_root,
                "root_method": cfg.root_method,
                "config_path": cfg.config_path,
                "restart_required_fields": sorted(list(RESTART_REQUIRED_FIELDS)),
            }
            self._send_json(payload)
        except Exception as e:
            self._send_error(500, "Internal Server Error", f"Lỗi config: {e}")

    def _post_config(self):
        try:
            length = int(self.headers.get("Content-Length", 0) or 0)
            body = self.rfile.read(length) if length else b"{}"
            data = json.loads(body.decode("utf-8"))

            cfg = get_config()
            result = cfg.update(data)

            if result.get("status") != "success":
                self._send_json(result, status=400)
                return

            # Nếu đổi cấu hình permissions → detect lại root
            changed = result.get("changed_fields", [])
            if any(c.startswith("permissions.") for c in changed):
                cfg.detect_root()

            result["is_root"] = cfg.is_root
            result["root_method"] = cfg.root_method
            result["config"] = cfg.to_dict()
            self._send_json(result)

        except json.JSONDecodeError as e:
            self._send_error(400, "Bad Request", f"JSON lỗi: {e}")
        except Exception as e:
            self._send_error(500, "Internal Server Error", f"Lỗi lưu config: {e}")

    # ===================== UI CONFIG =====================
    def _serve_ui_config(self):
        try:
            if WiFiHTTPHandler.registry is None:
                data = {"buttons": [], "categories": [], "versions": [],
                        "is_root": False, "root_method": "none",
                        "root_required_commands": []}
            else:
                data = WiFiHTTPHandler.registry.collect_ui_config()
            self._send_json(data)
        except Exception as e:
            self._send_error(500, "Internal Server Error", f"Lỗi UI config: {e}")

    def _serve_versions(self):
        try:
            if WiFiHTTPHandler.registry is None:
                data = {"modules": []}
            else:
                data = {"modules": WiFiHTTPHandler.registry.collect_versions()}
            self._send_json(data)
        except Exception as e:
            self._send_error(500, "Internal Server Error", f"Lỗi versions: {e}")

    # ===================== JSON HELPER =====================
    def _send_json(self, data, status=200):
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-type", "application/json; charset=utf-8")
        self.send_header("Cache-Control", "no-cache")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    # ===================== STATIC =====================
    def _serve_html(self, filename):
        try:
            base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            html_path = os.path.join(base, "templates", filename)
            with open(html_path, "r", encoding="utf-8") as f:
                html = f.read()
            self.send_response(200)
            self.send_header("Content-type", "text/html; charset=utf-8")
            self.send_header("Cache-Control", "no-cache")
            self.end_headers()
            self.wfile.write(html.encode("utf-8"))
        except FileNotFoundError:
            self._send_error(500, "Internal Server Error", "Template không tồn tại")

    def _serve_static(self, filename, content_type):
        try:
            base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            static_path = os.path.join(base, "static", filename)
            with open(static_path, "r", encoding="utf-8") as f:
                content = f.read()
            self.send_response(200)
            self.send_header("Content-type", content_type)
            self.send_header("Cache-Control", "no-cache")
            self.end_headers()
            self.wfile.write(content.encode("utf-8"))
        except FileNotFoundError:
            self._send_error(404, "Not Found", f"File {filename} không tồn tại")

    def _serve_404(self):
        try:
            base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            error_path = os.path.join(base, "templates", "404.html")
            if os.path.exists(error_path):
                with open(error_path, "r", encoding="utf-8") as f:
                    err = f.read()
                self.send_response(404)
                self.send_header("Content-type", "text/html; charset=utf-8")
                self.end_headers()
                self.wfile.write(err.encode("utf-8"))
            else:
                self._send_error(404, "404 Not Found", "Không tìm thấy tài nguyên.")
        except Exception:
            self._send_error(404, "404 Not Found", "Không tìm thấy tài nguyên.")

    def _send_error(self, code, title, message):
        self.send_response(code)
        self.send_header("Content-type", "text/html; charset=utf-8")
        self.end_headers()
        html = f"""<!DOCTYPE html>
<html><head><title>{title}</title></head>
<body><h1>{title}</h1><p>{message}</p><hr>
<p>ACDV-Teams WiFi Security Tool</p></body></html>"""
        self.wfile.write(html.encode("utf-8"))

    def log_message(self, format, *args):
        pass