# tinhnang/core/paths.py
"""
Nguồn chân lý duy nhất cho MỌI path trong project.
Mọi file đều tính từ __file__ → chạy từ đâu cũng đúng.
"""
import os

# __file__ = .../acdv-wifi-tool/tinhnang/core/paths.py
_CORE_DIR = os.path.dirname(os.path.abspath(__file__))       # .../tinhnang/core
_TINHNANG_DIR = os.path.dirname(_CORE_DIR)                    # .../tinhnang
ROOT_DIR = os.path.dirname(_TINHNANG_DIR)                     # .../acdv-wifi-tool

# === Data dirs ===
DATA_DIR        = os.path.join(ROOT_DIR, "data")
LOG_FILE        = os.path.join(DATA_DIR, "terminal.log")
DB_FILE         = os.path.join(DATA_DIR, "networks.acvd")
CONFIG_FILE     = os.path.join(DATA_DIR, "config.json")     # ← NEW
MODULES_RES_DIR = os.path.join(DATA_DIR, "modules")
WORDLIST_DIR    = os.path.join(DATA_DIR, "wordlists")
SCRIPTS_DIR     = os.path.join(DATA_DIR, "scripts")
CACHE_DIR       = os.path.join(DATA_DIR, "cache")

# Session lock — auto-reset khi tắt/mở lại tool
SESSION_LOCK = os.path.join(DATA_DIR, ".session.lock")

# === Templates / static ===
TEMPLATES_DIR = os.path.join(ROOT_DIR, "templates")
STATIC_DIR    = os.path.join(ROOT_DIR, "static")


def ensure_dirs():
    """Tạo sẵn các thư mục data nếu chưa có."""
    for d in [DATA_DIR, MODULES_RES_DIR, WORDLIST_DIR, SCRIPTS_DIR, CACHE_DIR]:
        os.makedirs(d, exist_ok=True)

    readme = os.path.join(WORDLIST_DIR, "README.txt")
    if not os.path.exists(readme):
        try:
            with open(readme, "w", encoding="utf-8") as f:
                f.write("📝 Thả file .txt wordlist của bạn vào đây.\n\n")
                f.write("DirbModule sẽ tự động đọc nếu khai báo trong:\n")
                f.write("  data/modules/dirb.json → files.wordlists\n\n")
                f.write("Pattern mặc định:\n")
                f.write("  - wordlists/*.txt\n")
                f.write("  - wordlists/dirb/*.txt\n\n")
                f.write("Bạn có thể tạo subfolder (vd: dirb/, api/, admin/) rồi glob.\n")
        except Exception:
            pass


def module_resource_path(module_name):
    """Trả về path tuyệt đối của file json tài nguyên cho module."""
    return os.path.join(MODULES_RES_DIR, f"{module_name}.json")