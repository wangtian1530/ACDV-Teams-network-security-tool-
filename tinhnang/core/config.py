# tinhnang/core/config.py
"""
Config — Cấu hình tập trung cho toàn bộ tool.

Load từ data/config.json (tự tạo file mẫu nếu chưa có).
Root detection: ưu tiên sudo (theo yêu cầu), fallback euid/su.

Cấu hình:
  - network: interface, host, port
  - environment: binaries, libraries, lib_paths, python_path
  - permissions: check_method, strict_mode
  - modules: root_required_commands
  - server: max_clients, ws_ping_interval, ws_ping_timeout

✅ NEW:
  - to_dict()  : trả về config dạng dict an toàn để đẩy lên UI
  - save()     : lưu public (dùng cho API)
  - update()   : merge + lưu + apply env + báo needs_restart
  - reload()   : nạp lại từ disk
  - detect_root ưu tiên sudo
"""
import os
import json
import shutil
import subprocess
import threading

from .paths import CONFIG_FILE


DEFAULT_CONFIG = {
    "network": {
        "interface": "wlan0",
        "host": "0.0.0.0",
        "port": 8080,
    },
    "environment": {
        "binaries": ["nmap", "iw", "wpa-supplicant", "pixiewps", "net-tools"],
        "libraries": ["requests", "psutil"],
        "lib_paths": [],
        "python_path": "",
    },
    "permissions": {
        "check_method": "sudo",   # "sudo" | "euid" | "su" | "auto" | "none"
        "strict_mode": True,
    },
    "modules": {
        "root_required_commands": [
            "wps_attack",
            "connect_with_password",
            "auto_connect",
            "scan",
            "lan_scan",
            "lan_quick_scan",
            "scan_specific_host",
            "clear_all",
            "quit",
        ],
    },
    "server": {
        "max_clients": 1,
        "ws_ping_interval": 20,
        "ws_ping_timeout": 60,
    },
}


# Các field mà khi đổi giá trị → cần restart tool mới áp dụng được.
RESTART_REQUIRED_FIELDS = {
    "network.interface", "network.host", "network.port",
    "environment.python_path", "environment.lib_paths",
    "permissions.check_method", "permissions.strict_mode",
    "server.max_clients", "server.ws_ping_interval", "server.ws_ping_timeout",
}


class Config:
    """Singleton thread-safe. Load override từ data/config.json."""

    _instance = None
    _lock = threading.Lock()

    def __init__(self, config_path=None):
        self.config_path = config_path or CONFIG_FILE
        self.data = json.loads(json.dumps(DEFAULT_CONFIG))  # deep copy
        self.is_root = False
        self.root_method = "none"
        self.root_checked = False

    @classmethod
    def get(cls, config_path=None):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = cls(config_path)
        return cls._instance

    # ============================================================
    # LOAD / SAVE / RELOAD / UPDATE
    # ============================================================
    def load(self, auto_create=True):
        if not self.config_path:
            return self
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, "r", encoding="utf-8") as f:
                    user_cfg = json.load(f)
                self._merge(self.data, user_cfg)
            elif auto_create:
                self._save()
        except Exception as e:
            print(f"[Config] Load lỗi ({e}) — dùng default")
        return self

    def reload(self):
        """Nạp lại từ disk, xoá mọi thay đổi RAM."""
        self.data = json.loads(json.dumps(DEFAULT_CONFIG))
        return self.load(auto_create=False)

    def save(self):
        """Public save - gọi từ API."""
        return self._save()

    def to_dict(self):
        """Trả về config dạng dict an toàn (copy) để đẩy lên UI."""
        return json.loads(json.dumps(self.data))

    def update(self, new_data):
        """
        Merge new_data vào config hiện tại → lưu file.
        Trả về dict: status, changed_fields, needs_restart, config, message.
        """
        if not isinstance(new_data, dict):
            return {
                "status": "error",
                "message": "Config phải là JSON object",
            }

        old_flat = self._flatten(self.data)
        self._merge(self.data, new_data)
        self._save()
        new_flat = self._flatten(self.data)

        changed = []
        for k in set(old_flat.keys()) | set(new_flat.keys()):
            if old_flat.get(k) != new_flat.get(k):
                changed.append(k)

        # Apply env ngay (PYTHONPATH / LD_LIBRARY_PATH)
        if any(c.startswith("environment.") for c in changed):
            try:
                self.apply_environment()
            except Exception:
                pass

        needs_restart = any(
            c in RESTART_REQUIRED_FIELDS
            or c.startswith(("network.", "environment.", "permissions.", "server."))
            for c in changed
        )

        return {
            "status": "success",
            "changed_fields": changed,
            "needs_restart": needs_restart,
            "config": self.to_dict(),
            "message": (
                "Đã lưu config. Cần restart tool để áp dụng."
                if needs_restart else "Đã lưu config."
            ),
        }

    def _save(self):
        try:
            os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
            with open(self.config_path, "w", encoding="utf-8") as f:
                json.dump(self.data, f, indent=2, ensure_ascii=False)
            return True
        except Exception:
            return False

    def _merge(self, base, override):
        for k, v in override.items():
            if k in base and isinstance(base[k], dict) and isinstance(v, dict):
                self._merge(base[k], v)
            else:
                base[k] = v

    @staticmethod
    def _flatten(d, prefix=""):
        """Làm phẳng dict → {dotted.key: value} để diff."""
        out = {}
        if not isinstance(d, dict):
            return {prefix: d}
        for k, v in d.items():
            key = f"{prefix}.{k}" if prefix else k
            if isinstance(v, dict):
                out.update(Config._flatten(v, key))
            else:
                out[key] = v
        return out

    # ============================================================
    # ROOT DETECTION — ưu tiên sudo (theo yêu cầu)
    # ============================================================
    def detect_root(self):
        """
        Thứ tự detect:
          0. euid == 0       → chắc chắn root (fast-path)
          1. sudo -n true    → ưu tiên theo yêu cầu
          2. su -c id        → fallback Android/Termux
        """
        method = self.data["permissions"].get("check_method", "sudo")
        self.is_root = False
        self.root_method = "none"

        if method == "none":
            self.is_root = True
            self.root_method = "bypass"
            self.root_checked = True
            return True

        # 0. euid fast-path — đã là root thì khỏi check
        try:
            if os.geteuid() == 0:
                self.is_root = True
                self.root_method = "euid"
                self.root_checked = True
                return True
        except Exception:
            pass

        # 1. sudo -n true (PRIMARY — theo yêu cầu)
        if method in ("sudo", "auto"):
            if shutil.which("sudo"):
                try:
                    r = subprocess.run(
                        ["sudo", "-n", "true"],
                        capture_output=True, timeout=3,
                    )
                    if r.returncode == 0:
                        self.is_root = True
                        self.root_method = "sudo"
                        self.root_checked = True
                        return True
                except Exception:
                    pass

        # 2. su (fallback Android/Termux)
        if method in ("sudo", "su", "auto"):
            if shutil.which("su"):
                try:
                    r = subprocess.run(
                        ["su", "-c", "id"],
                        capture_output=True, text=True, timeout=3,
                    )
                    if "uid=0" in (r.stdout or ""):
                        self.is_root = True
                        self.root_method = "su"
                        self.root_checked = True
                        return True
                except Exception:
                    pass

        self.root_checked = True
        return False

    def can_run(self, command):
        if self.is_root:
            return True
        if not self.data["permissions"].get("strict_mode", True):
            return True
        if not command:
            return True
        root_cmds = set(self.data["modules"].get("root_required_commands", []))
        return command not in root_cmds

    def requires_root(self, command):
        if not command:
            return False
        return command in set(self.data["modules"].get("root_required_commands", []))

    def get_reason_blocked(self, command):
        if self.can_run(command):
            return None
        return (
            f"Lệnh '{command}' yêu cầu quyền ROOT. "
            f"Chạy lại tool bằng 'sudo python main.py' hoặc cấu hình "
            f"permissions.strict_mode=false để bỏ qua."
        )

    # ============================================================
    # HELPERS
    # ============================================================
    @property
    def interface(self):
        return self.data["network"]["interface"]

    @property
    def host(self):
        return self.data["network"]["host"]

    @property
    def port(self):
        return int(self.data["network"]["port"])

    @property
    def ws_port(self):
        return self.port + 1

    @property
    def binaries(self):
        return list(self.data["environment"]["binaries"])

    @property
    def libraries(self):
        return list(self.data["environment"]["libraries"])

    @property
    def lib_paths(self):
        return list(self.data["environment"]["lib_paths"])

    @property
    def max_clients(self):
        return int(self.data["server"].get("max_clients", 1))

    @property
    def ws_ping_interval(self):
        return int(self.data["server"].get("ws_ping_interval", 20))

    @property
    def ws_ping_timeout(self):
        return int(self.data["server"].get("ws_ping_timeout", 60))

    def apply_environment(self):
        """Áp dụng PYTHONPATH + LD_LIBRARY_PATH."""
        py_path = self.data["environment"].get("python_path", "")
        if py_path:
            existing = os.environ.get("PYTHONPATH", "")
            if py_path not in existing.split(os.pathsep):
                os.environ["PYTHONPATH"] = py_path + (
                    os.pathsep + existing if existing else ""
                )
        for p in self.lib_paths:
            if not p or not os.path.isdir(p):
                continue
            existing = os.environ.get("LD_LIBRARY_PATH", "")
            if p not in existing.split(os.pathsep):
                os.environ["LD_LIBRARY_PATH"] = p + (
                    os.pathsep + existing if existing else ""
                )

    def describe(self):
        return {
            "interface": self.interface,
            "host": self.host,
            "port": self.port,
            "ws_port": self.ws_port,
            "is_root": self.is_root,
            "root_method": self.root_method,
            "config_path": self.config_path,
            "binaries": self.binaries,
            "libraries": self.libraries,
            "root_required_commands": list(
                self.data["modules"].get("root_required_commands", [])
            ),
        }


def get_config():
    """Lấy singleton config (tự init với CONFIG_FILE)."""
    return Config.get(CONFIG_FILE)