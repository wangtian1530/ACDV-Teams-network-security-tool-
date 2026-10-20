# tinhnang/core/resource_manager.py
"""
ModuleResource — Quản lý tài nguyên khai báo trong data/modules/<name>.json.

Mỗi module có 1 file json riêng, tự khai báo:
  - files:    các file/pattern tài nguyên (wordlist, config, script...)
  - settings: các cấu hình key-value

Module dùng: self.resource.get("key"), self.resource.resolve_all("wordlists")...
"""
import os
import glob
import json

from .paths import (
    DATA_DIR, MODULES_RES_DIR, WORDLIST_DIR, SCRIPTS_DIR, CACHE_DIR,
    module_resource_path, ensure_dirs,
)


DEFAULT_RESOURCE = {
    "description": "",
    "files": {},       # key → str hoặc list[str] (relative to DATA_DIR, hỗ trợ glob)
    "settings": {},    # key-value tự do
}


class ModuleResource:
    def __init__(self, module_name, logger=None):
        self.module_name = module_name
        self.logger = logger
        ensure_dirs()

        self.json_path = module_resource_path(module_name)
        self.config = dict(DEFAULT_RESOURCE)
        self._loaded = False

    # -----------------------------------------------------------------
    def _log(self, msg):
        if self.logger:
            try:
                self.logger.write(msg)
            except Exception:
                pass

    # -----------------------------------------------------------------
    def load(self, default_config=None, auto_create=True):
        """
        Đọc file <module>.json.
        - Nếu file đã tồn tại → đọc, KHÔNG ghi đè default.
        - Nếu file chưa có + có default_config → dùng default + tạo file.
        - Nếu file chưa có + không có default → tạo file rỗng.
        """
        if os.path.exists(self.json_path):
            try:
                with open(self.json_path, "r", encoding="utf-8") as f:
                    self.config = json.load(f)
                # Đảm bảo có đủ 2 key chuẩn
                self.config.setdefault("files", {})
                self.config.setdefault("settings", {})
                self._loaded = True
                self._log(f"[✓] {self.module_name}: nạp {os.path.basename(self.json_path)}")
                return self.config
            except Exception as e:
                self._log(f"[!] {self.module_name}: json lỗi → dùng default. ({e})")

        # Chưa có → dùng default
        if default_config:
            self.config = default_config
        else:
            self.config = dict(DEFAULT_RESOURCE)

        if auto_create:
            self.save()
            self._log(f"[+] {self.module_name}: đã tạo {os.path.relpath(self.json_path, os.path.dirname(DATA_DIR))}")

        self._loaded = True
        return self.config

    # -----------------------------------------------------------------
    def save(self, config=None):
        if config is not None:
            self.config = config
        try:
            os.makedirs(os.path.dirname(self.json_path), exist_ok=True)
            with open(self.json_path, "w", encoding="utf-8") as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            self._log(f"[!] {self.module_name}: ghi json lỗi: {e}")
            return False

    # -----------------------------------------------------------------
    # Settings
    # -----------------------------------------------------------------
    def get(self, key, default=None):
        return self.config.get("settings", {}).get(key, default)

    def set(self, key, value, save=True):
        self.config.setdefault("settings", {})[key] = value
        if save:
            self.save()

    # -----------------------------------------------------------------
    # Files
    # -----------------------------------------------------------------
    def file(self, key, default=None):
        """Trả về absolute path (không glob) từ key trong files."""
        rel = self.config.get("files", {}).get(key, default)
        if rel is None or isinstance(rel, list):
            return None
        return rel if os.path.isabs(rel) else os.path.join(DATA_DIR, rel)

    def resolve_glob(self, pattern):
        """Giải pattern (có thể chứa * hoặc **) → list absolute paths."""
        full = pattern if os.path.isabs(pattern) else os.path.join(DATA_DIR, pattern)
        return sorted(glob.glob(full, recursive=True))

    def resolve_all(self, key):
        """
        Lấy TẤT CẢ file khai báo cho key.
        - Value có thể là str hoặc list[str]
        - Hỗ trợ glob pattern (* và **)
        → Trả về list absolute paths (đã tồn tại, đã dedupe).
        """
        val = self.config.get("files", {}).get(key)
        if not val:
            return []
        patterns = val if isinstance(val, list) else [val]
        result = []
        for pat in patterns:
            for f in self.resolve_glob(pat):
                if os.path.isfile(f):
                    result.append(f)
        return list(dict.fromkeys(result))

    # -----------------------------------------------------------------
    # Read helpers
    # -----------------------------------------------------------------
    def read_text(self, key, default=""):
        """Đọc nội dung text của file khai báo trong files."""
        p = self.file(key)
        if not p or not os.path.exists(p):
            return default
        try:
            with open(p, "r", encoding="utf-8", errors="ignore") as f:
                return f.read()
        except Exception as e:
            self._log(f"[!] {self.module_name}: đọc {key} lỗi: {e}")
            return default

    def read_lines(self, key, skip_comments=True):
        """Đọc file thành list dòng (bỏ dòng trống, có thể bỏ # comment)."""
        text = self.read_text(key)
        out = []
        for line in text.splitlines():
            s = line.strip()
            if not s:
                continue
            if skip_comments and s.startswith("#"):
                continue
            out.append(s)
        return out