# tinhnang/core/__init__.py
from .terminal import chay_terminal
from .file_manager import FileManager
from .logger import TerminalLogger
from .context import AppContext
from .utils import dongcong, check_and_setup_env
from .resource_manager import ModuleResource
from .config import Config, get_config, DEFAULT_CONFIG
from .paths import (
    DATA_DIR, ROOT_DIR, LOG_FILE, DB_FILE, CONFIG_FILE,
    MODULES_RES_DIR, WORDLIST_DIR, SCRIPTS_DIR, CACHE_DIR,
    ensure_dirs, module_resource_path,
)

__all__ = [
    "chay_terminal",
    "FileManager",
    "TerminalLogger",
    "AppContext",
    "dongcong",
    "check_and_setup_env",
    "ModuleResource",
    "Config", "get_config", "DEFAULT_CONFIG",
    "DATA_DIR", "ROOT_DIR", "LOG_FILE", "DB_FILE", "CONFIG_FILE",
    "MODULES_RES_DIR", "WORDLIST_DIR", "SCRIPTS_DIR", "CACHE_DIR",
    "ensure_dirs", "module_resource_path",
]