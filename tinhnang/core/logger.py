# tinhnang/core/logger.py
import os
import threading
import asyncio
from datetime import datetime

from .paths import LOG_FILE, DATA_DIR, ensure_dirs


class TerminalLogger:
    """Ghi log ra data/terminal.log + broadcast qua WebSocket."""

    def __init__(self, max_lines=1000):
        self.max_lines = max_lines
        ensure_dirs()

        # ✅ Log luôn nằm ở data/terminal.log
        self.log_file = LOG_FILE

        self._init_log_file()
        self.current_networks = []
        self.last_scan_time = None
        self.last_line_id = 0
        self.ws_server = None
        self._log_lock = threading.Lock()

    def set_ws_server(self, ws_server):
        self.ws_server = ws_server

    def _init_log_file(self):
        try:
            os.makedirs(DATA_DIR, exist_ok=True)
            with open(self.log_file, "w", encoding="utf-8") as f:
                f.write("")
        except Exception as e:
            print(f"[Logger] Không ghi được log: {e}")

    def _get_next_line_id(self):
        self.last_line_id += 1
        return self.last_line_id

    def write(self, text, is_command=False):
        with self._log_lock:
            timestamp = datetime.now().strftime("%H:%M:%S")
            line_id = self._get_next_line_id()

            if is_command:
                log_line = f"[{timestamp}] $> {text}"
            else:
                log_line = f"[{timestamp}] {text}"

            lines = []
            try:
                if os.path.exists(self.log_file):
                    with open(self.log_file, "r", encoding="utf-8") as f:
                        lines = f.readlines()

                lines.append(log_line + "\n")
                if len(lines) > self.max_lines:
                    lines = lines[-self.max_lines:]

                with open(self.log_file, "w", encoding="utf-8") as f:
                    f.writelines(lines)
            except Exception:
                pass

            if self.ws_server and self.ws_server.loop:
                try:
                    asyncio.run_coroutine_threadsafe(
                        self.ws_server.send_log(log_line, line_id),
                        self.ws_server.loop,
                    )
                except Exception:
                    pass

    def clear(self):
        with self._log_lock:
            self._init_log_file()
            self.last_line_id = 0