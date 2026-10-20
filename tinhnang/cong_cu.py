# tinhnang/cong_cu.py
"""
Shim giữ tương thích import cũ: `from tinhnang.cong_cu import *`
Re-export toàn bộ class từ core + modules tương ứng.
"""
from .core.terminal import chay_terminal
from .core.file_manager import FileManager
from .core.logger import TerminalLogger
from .core.context import AppContext
from .core.utils import dongcong, check_and_setup_env
from .core.config import Config, get_config, DEFAULT_CONFIG

from .modules.wifi_module import WifiManager, WifiModule
from .modules.lan_module import NetworkScanner, LanModule

__all__ = [
    "chay_terminal", "FileManager", "TerminalLogger", "AppContext",
    "dongcong", "check_and_setup_env",
    "Config", "get_config", "DEFAULT_CONFIG",
    "WifiManager", "WifiModule",
    "NetworkScanner", "LanModule",
]