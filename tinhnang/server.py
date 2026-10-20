# tinhnang/server.py
"""
Shim giữ tương thích import cũ: `from tinhnang.server import *`
"""
from .backend.server import WiFiServer, main
from .backend.registry import ModuleRegistry
from .backend.websocket_handler import WebSocketServer
from .backend.http_handler import WiFiHTTPHandler

__all__ = ["WiFiServer", "ModuleRegistry", "WebSocketServer", "WiFiHTTPHandler", "main"]