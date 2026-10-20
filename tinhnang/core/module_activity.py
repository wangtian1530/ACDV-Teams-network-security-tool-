# tinhnang/core/module_activity.py
"""
ModuleActivityLog — Log hoạt động/lỗi của module.

THIẾT KẾ: RAM-FIRST
  - Buffer in-memory là PRIMARY → hoạt động ngay cả khi:
      + Tool đang khởi động (chưa có data/)
      + Chưa có quyền ghi file
      + File bị lock / disk full
  - File data/module_activity.json là BACKUP best-effort → flush sau mỗi log()
  - Lazy init → KHÔNG crash nếu data dir chưa tồn tại
  - Thread-safe
  - Module installer đọc từ singleton RAM → luôn thấy entry mới nhất

Mỗi entry:
{
    "id": 1,
    "timestamp": "2025-01-01 12:34:56",
    "module": "dirb",
    "command": "dirb",
    "event": "handle_error",     # init_error | install_error | install_success
                                  # | handle_error | hang | blocked
                                  # | cancelled | returned_error | warning | info
    "severity": "error",         # error | warning | info
    "message": "Exception: Connection refused",
    "details": {...}
}
"""

import os
import json
import threading
from datetime import datetime

from .paths import DATA_DIR


ACTIVITY_FILE = os.path.join(DATA_DIR, "module_activity.json")
MAX_ENTRIES = 200


class ModuleActivityLog:
    """Thread-safe, RAM-first, file là best-effort backup."""

    _lock = threading.Lock()

    def __init__(self, max_entries=MAX_ENTRIES):
        self.max_entries = max_entries
        # === RAM STATE ===
        self._buffer = []              # list[dict] — entries in RAM
        self._next_id = 1
        self._initialized = False      # đã load từ file lần đầu chưa
        self._file_ok = True           # file có ghi được không

    # -----------------------------------------------------------------
    # LAZY INIT — không crash nếu data dir chưa có
    # -----------------------------------------------------------------
    def _ensure_initialized(self):
        """Load file lần đầu dùng. Không raise exception."""
        if self._initialized:
            return
        self._initialized = True
        try:
            if os.path.exists(ACTIVITY_FILE):
                with open(ACTIVITY_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                if isinstance(data, dict):
                    entries = data.get("entries", [])
                    if isinstance(entries, list):
                        self._buffer = entries[-self.max_entries:]
                    next_id = data.get("next_id", 1)
                    self._next_id = max(int(next_id), len(self._buffer) + 1)
        except Exception:
            # File lỗi/không đọc được → bắt đầu fresh (RAM vẫn hoạt động)
            self._buffer = []
            self._next_id = 1

    # -----------------------------------------------------------------
    def _flush_best_effort(self):
        """Ghi RAM → file. Không raise exception nếu fail."""
        try:
            os.makedirs(os.path.dirname(ACTIVITY_FILE), exist_ok=True)
            data = {
                "next_id": self._next_id,
                "entries": self._buffer,
            }
            # Ghi atomic: temp file → rename
            tmp = ACTIVITY_FILE + ".tmp"
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            os.replace(tmp, ACTIVITY_FILE)
            self._file_ok = True
        except Exception:
            # Không ghi được file → RAM vẫn giữ, không mất data
            self._file_ok = False

    # -----------------------------------------------------------------
    # PUBLIC API
    # -----------------------------------------------------------------
    def log(self, module, event, message, command="", severity="error", details=None):
        """
        Ghi 1 entry.

        Args:
            module (str): Tên module (vd: "dirb")
            event (str): "init_error" | "install_error" | "install_success"
                        | "handle_error" | "hang" | "blocked" | "cancelled"
                        | "returned_error" | "warning" | "info"
            message (str): Mô tả ngắn
            command (str): Command liên quan (nếu có)
            severity (str): "error" | "warning" | "info"
            details (dict): Thông tin thêm (optional)
        Returns:
            dict entry đã ghi (có id) hoặc None nếu lỗi.
        """
        try:
            with self._lock:
                self._ensure_initialized()

                entry = {
                    "id": self._next_id,
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "module": str(module or "unknown"),
                    "command": str(command or ""),
                    "event": str(event or "unknown"),
                    "severity": str(severity or "error"),
                    "message": str(message or ""),
                    "details": details if isinstance(details, dict) else {},
                }
                self._next_id += 1
                self._buffer.append(entry)

                if len(self._buffer) > self.max_entries:
                    self._buffer = self._buffer[-self.max_entries:]

                # Flush best-effort — không chặn nếu fail
                self._flush_best_effort()
                return entry
        except Exception:
            return None

    # -----------------------------------------------------------------
    def read(self, module=None, event=None, severity=None, limit=100):
        """Đọc entries từ RAM (filter tùy chọn). Trả list mới nhất trước."""
        try:
            with self._lock:
                self._ensure_initialized()
                entries = list(self._buffer)
        except Exception:
            return []

        if module:
            entries = [e for e in entries if e.get("module") == module]
        if event:
            entries = [e for e in entries if e.get("event") == event]
        if severity:
            entries = [e for e in entries if e.get("severity") == severity]

        entries = sorted(entries, key=lambda e: e.get("id", 0), reverse=True)
        return entries[:limit]

    # -----------------------------------------------------------------
    def clear(self, module=None):
        """Xoá toàn bộ, hoặc chỉ entries của 1 module."""
        with self._lock:
            self._ensure_initialized()
            if module:
                self._buffer = [e for e in self._buffer if e.get("module") != module]
            else:
                self._buffer = []
            self._flush_best_effort()

    # -----------------------------------------------------------------
    def stats(self):
        """Thống kê: {module: {total, error, warning, info, last}}."""
        with self._lock:
            self._ensure_initialized()
            entries = list(self._buffer)
        stats = {}
        for e in entries:
            m = e.get("module", "unknown")
            s = stats.setdefault(m, {"total": 0, "error": 0, "warning": 0, "info": 0, "last": None})
            s["total"] += 1
            sev = e.get("severity", "error")
            if sev in s:
                s[sev] += 1
            if not s["last"] or e.get("timestamp", "") > s["last"]:
                s["last"] = e.get("timestamp")
        return stats

    # -----------------------------------------------------------------
    def flush(self):
        """Force ghi RAM → file. Public cho shutdown hook."""
        with self._lock:
            self._ensure_initialized()
            self._flush_best_effort()
        return self._file_ok

    def is_file_ok(self):
        """True nếu file ghi được. False nếu chỉ RAM hoạt động."""
        return self._file_ok

    def size(self):
        """Số entry hiện có trong RAM."""
        with self._lock:
            self._ensure_initialized()
            return len(self._buffer)


# === Singleton — lazy init, không crash ===
_default_log = None
_singleton_lock = threading.Lock()


def get_activity_log():
    """Lấy singleton instance. An toàn gọi ở bất kỳ đâu, bất kỳ lúc nào."""
    global _default_log
    if _default_log is None:
        with _singleton_lock:
            if _default_log is None:
                _default_log = ModuleActivityLog()
    return _default_log