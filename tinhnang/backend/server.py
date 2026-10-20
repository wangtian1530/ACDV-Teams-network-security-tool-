# tinhnang/backend/server.py
import asyncio
import threading
import time
import os
import sys
import websockets
from http.server import HTTPServer

from ..core.context import AppContext
from ..core.logger import TerminalLogger
from ..core.file_manager import FileManager
from ..core.terminal import chay_terminal
from ..core.utils import dongcong, check_and_setup_env, cleanup_orphan_processes
from ..core.paths import ensure_dirs, DATA_DIR, SESSION_LOCK
from ..core.config import get_config
from .registry import ModuleRegistry
from .websocket_handler import WebSocketServer
from .http_handler import WiFiHTTPHandler


class WiFiServer:
    def __init__(self, host=None, port=None):
        cfg = get_config()
        self.config = cfg
        self.host = host if host is not None else cfg.host
        self.port = port if port is not None else cfg.port

        self.context = AppContext()
        self.context.logger = TerminalLogger()
        self.context.file_manager = FileManager()

        self.registry = ModuleRegistry(self.context)
        self.ws_server = None
        self.ws_thread = None
        self.loop = None
        self.http_server = None

    # ===================== SESSION LOCK =====================
    def _write_session_lock(self):
        try:
            with open(SESSION_LOCK, "w", encoding="utf-8") as f:
                f.write(str(os.getpid()))
        except Exception as e:
            self.context.logger.write(f"[!] Không ghi được session lock: {e}")

    def _remove_session_lock(self):
        try:
            if os.path.exists(SESSION_LOCK):
                os.remove(SESSION_LOCK)
        except Exception:
            pass

    def _check_and_reset_stale_session(self):
        if os.path.exists(SESSION_LOCK):
            self.context.logger.write(
                "[!] ⚠ Phát hiện session cũ chưa đóng sạch → AUTO-RESET..."
            )
            cleanup_orphan_processes()
            self._remove_session_lock()
            self.context.logger.write(
                "[+] ✅ Đã dọn dẹp session cũ. Bắt đầu fresh state."
            )
        else:
            self.context.logger.write("[*] Session sạch — không cần auto-reset.")

    # ===================== WEBSOCKET =====================
    async def _start_websocket(self):
        self.ws_server = WebSocketServer(
            self.context, self.registry, self.context.logger
        )
        self.context.logger.set_ws_server(self.ws_server)
        self.ws_server.loop = self.loop
        self.context.ws_server = self.ws_server

        async with websockets.serve(
            self.ws_server.handle_client,
            self.host,
            self.port + 1,
            ping_interval=self.config.ws_ping_interval,
            ping_timeout=self.config.ws_ping_timeout,
        ):
            self.context.logger.write(
                f"[WebSocket] Server tại ws://{self.host}:{self.port + 1}"
            )
            await asyncio.Future()

    def _run_websocket(self):
        try:
            self.loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self.loop)
            self.context.loop = self.loop
            self.loop.run_until_complete(self._start_websocket())
        except Exception as e:
            self.context.logger.write(f"[WebSocket] Error: {e}")
        finally:
            if self.loop:
                self.loop.close()

    # ===================== HTTP =====================
    def _start_http(self):
        WiFiHTTPHandler.registry = self.registry
        self.http_server = HTTPServer((self.host, self.port), WiFiHTTPHandler)
        self.context.logger.write(f"[HTTP] Server tại http://{self.host}:{self.port}")
        self.context.logger.write(f"[HTTP] WebSocket port: {self.port + 1}")
        try:
            self.http_server.serve_forever()
        except KeyboardInterrupt:
            pass

    # ===================== VERSION LOG =====================
    def _log_module_versions(self):
        versions = self.registry.collect_versions()
        if not versions:
            self.context.logger.write("[Registry] ⚠ Không có module nào để log version.")
            return

        self.context.logger.write(
            f"[Registry] 📦 Danh sách {len(versions)} module:"
        )
        for v in versions:
            name = v.get("name", "?")
            ver = v.get("version", "?")
            latest = v.get("latest_version", ver)
            has_update = v.get("has_update", False)
            desc = v.get("description", "")
            if has_update:
                self.context.logger.write(
                    f"   • {name} v{ver} → v{latest} ⬆️  ({desc})"
                )
            else:
                self.context.logger.write(
                    f"   • {name} v{ver} ✓  ({desc})"
                )

        updates = [v for v in versions if v.get("has_update")]
        if updates:
            self.context.logger.write(
                f"[Registry] 🔄 {len(updates)} module có bản cập nhật mới:"
            )
            for u in updates:
                self.context.logger.write(
                    f"   • {u['name']}: {u['version']} → {u['latest_version']}"
                )
        else:
            self.context.logger.write(
                "[Registry] ✓ Tất cả module đã là bản mới nhất"
            )

    # ===================== START / STOP =====================
    def start(self):
        ensure_dirs()

        # ✅ LOAD + DETECT ROOT
        self.config.load(auto_create=True)
        self.config.detect_root()
        self.config.apply_environment()

        self._check_and_reset_stale_session()
        self._write_session_lock()

        self.context.logger.write(f"[SYSTEM] Data dir: {DATA_DIR}")
        self.context.logger.write(f"[SYSTEM] Config  : {self.config.config_path}")
        self.context.logger.write(
            f"[SYSTEM] Interface: {self.config.interface}  "
            f"Host: {self.host}  Port: {self.port}"
        )
        self.context.logger.write(
            f"[SYSTEM] Root  : {'✓ ' + self.config.root_method if self.config.is_root else '✗ KHÔNG'}"
        )
        self.context.logger.write("[SYSTEM] Đang khởi tạo...")

        check_and_setup_env(chay_terminal, self.config)

        # ✅ Load modules
        self.registry.load_from_package("tinhnang.modules")
        loaded = self.registry.list_modules()
        self.context.logger.write(f"[Registry] Đã nạp {len(loaded)} module:")
        for name, desc, cmds in loaded:
            mod = self.registry.modules.get(name)
            ver = getattr(mod, "version", "?") if mod else "?"
            self.context.logger.write(
                f"   • {name} v{ver}: {desc} [{', '.join(cmds)}]"
            )

        self._log_module_versions()

        if not self.config.is_root:
            self.context.logger.write(
                "[!] ⚠ TOOL CHẠY KHÔNG ROOT — module cần root sẽ bị chặn."
            )
            self.context.logger.write(
                "[!]   Chạy 'sudo python main.py' để mở khoá toàn bộ."
            )

        # ✅ WebSocket thread
        self.ws_thread = threading.Thread(target=self._run_websocket, daemon=True)
        self.ws_thread.start()
        time.sleep(2)

        self.context.logger.write(
            f"[SYSTEM] Truy cập: http://"
            f"{self.host if self.host != '0.0.0.0' else 'localhost'}:{self.port}"
        )
        self.context.logger.write("[SYSTEM] Nhấn Ctrl+C để dừng")

        try:
            self._start_http()
        except KeyboardInterrupt:
            self.context.logger.write("[SYSTEM] Đang tắt server...")
        finally:
            self._shutdown()

    def _shutdown(self):
        self.context.logger.write("[SYSTEM] Đang dọn dẹp session...")

        try:
            cancelled = self.context.cancel_all_modules()
            if cancelled:
                self.context.logger.write(
                    f"[SYSTEM] Đã gửi cancel tới: {', '.join(cancelled)}"
                )
        except Exception:
            pass

        cleanup_orphan_processes()
        self._remove_session_lock()

        if self.http_server:
            try:
                self.http_server.shutdown()
            except Exception:
                pass

        if self.loop:
            try:
                self.loop.call_soon_threadsafe(self.loop.stop)
            except Exception:
                pass

        if self.ws_thread:
            try:
                self.ws_thread.join(timeout=5)
            except Exception:
                pass

        try:
            self.registry.cleanup_all()
        except Exception:
            pass

        self.context.logger.write("[SYSTEM] ✓ Đã dọn dẹp xong. Tạm biệt!")


# ================= CLI ENTRY =================
def main():
    ensure_dirs()
    cfg = get_config()
    cfg.load(auto_create=True)
    cfg.detect_root()

    host = cfg.host
    port = cfg.port

    if len(sys.argv) > 1:
        try:
            port = int(sys.argv[1])
            cfg.data["network"]["port"] = port
        except ValueError:
            print(f"Port '{sys.argv[1]}' không hợp lệ")
            sys.exit(1)
    if len(sys.argv) > 2:
        host = sys.argv[2]
        cfg.data["network"]["host"] = host

    dongcong([port, port + 1])

    print(f"\n{'='*60}")
    print(f"ACDV-Teams WiFi Security Tool v3.2 (Plugin Architecture)")
    print(f"{'='*60}")
    print(f"HTTP Server: http://{host if host != '0.0.0.0' else 'localhost'}:{port}")
    print(f"WebSocket: ws://{host if host != '0.0.0.0' else 'localhost'}:{port + 1}")
    print(f"Root      : {'✓ ' + cfg.root_method if cfg.is_root else '✗ KHÔNG'}")
    print(f"Interface : {cfg.interface}")
    print(f"Config    : {cfg.config_path}")
    print(f"{'='*60}\n")

    server = WiFiServer(host, port)
    server.start()


if __name__ == "__main__":
    main()