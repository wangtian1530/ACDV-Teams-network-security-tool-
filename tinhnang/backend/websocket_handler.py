# tinhnang/backend/websocket_handler.py
import asyncio
import json
import os
import time
import threading
import websockets
from datetime import datetime

from ..core.utils import cleanup_orphan_processes
from ..core.paths import SESSION_LOCK
from ..core.config import get_config


class WebSocketServer:
    """
    Xử lý WebSocket real-time + check quyền root trước khi route.
    """

    NON_BLOCKING = {"get_status", "get_logs", "clear_terminal",
                    "shutdown", "stop", "stop_task", "stop_wps", "reset_blocks",
                    "get_module_versions"}

    def __init__(self, context, registry, logger):
        self.context = context
        self.registry = registry
        self.logger = logger
        self.clients = set()
        self.client_lock = threading.Lock()
        self.current_task = None
        self.task_lock = threading.Lock()
        self.connected_clients = 0
        self.max_clients = get_config().max_clients
        self.loop = None

        self.module_hang_counts = {}
        self.blocked_modules = set()
        self.max_hangs = 3
        self._last_command = None
        self._last_params = None

    # ======================= CLIENT =======================
    async def register(self, websocket):
        with self.client_lock:
            if self.context.is_processing and len(self.clients) >= self.max_clients:
                await websocket.close(1008, "Hệ thống đang bận")
                return False
            self.clients.add(websocket)
            self.connected_clients = len(self.clients)
            self.logger.write(f"[WS] Client kết nối. Tổng: {self.connected_clients}")
            await self.send_status(websocket)
            return True

    async def unregister(self, websocket):
        with self.client_lock:
            self.clients.discard(websocket)
            self.connected_clients = len(self.clients)
            self.logger.write(f"[WS] Client ngắt. Còn: {self.connected_clients}")

    async def send_status(self, websocket=None):
        status = {
            "type": "status",
            "data": self.context.get_system_status(),
            "is_processing": self.context.is_processing,
            "connected_clients": self.connected_clients,
            "current_task": self.current_task,
            "task_info": self._get_task_info(),
            "blocked_modules": list(self.blocked_modules),
            "module_hang_counts": dict(self.module_hang_counts),
            "running_modules": list(self.context.running_modules.keys()),
        }
        try:
            if websocket:
                await websocket.send(json.dumps(status))
            else:
                await self.broadcast(json.dumps(status))
        except Exception:
            pass

    def _get_task_info(self):
        ctx = self.context
        if ctx.wps_attacking:
            return {"type": "wps_attack", "name": "Tấn công WPS", "icon": "⚡",
                    "can_stop": True, "message": "Đang tấn công WPS..."}
        if ctx.lan_scanning:
            return {"type": "lan_scan", "name": "Quét LAN", "icon": "🌐",
                    "can_stop": True, "message": "Đang quét LAN..."}
        if ctx.connecting:
            return {"type": "connect", "name": "Kết nối WiFi", "icon": "🔌",
                    "can_stop": True, "message": "Đang kết nối..."}
        if ctx.scanning:
            return {"type": "scan", "name": "Quét WiFi", "icon": "📡",
                    "can_stop": True, "message": "Đang quét WiFi..."}

        if ctx.is_processing and self.current_task and self.current_task not in self.NON_BLOCKING:
            readable = self.current_task.replace("_", " ").title()
            return {
                "type": self.current_task,
                "name": readable,
                "icon": "⚙️",
                "can_stop": True,
                "message": f"Đang xử lý: {readable}...",
            }
        return None

    # ======================= SEND HELPERS =======================
    async def send_log(self, log_line, log_id):
        await self.broadcast(json.dumps({
            "type": "log",
            "id": log_id,
            "line": log_line,
            "timestamp": datetime.now().strftime("%H:%M:%S"),
        }))

    async def send_networks(self, networks):
        safe = []
        for net in networks:
            safe.append({
                "stt": net.get("stt"),
                "ssid": net.get("ssid"),
                "bssid": net.get("bssid"),
                "wps_enabled": net.get("wps_enabled"),
                "signal": net.get("signal"),
                "security": net.get("security"),
                "has_password": net.get("has_password", False),
            })
        await self.broadcast(json.dumps({
            "type": "networks",
            "data": safe,
            "timestamp": datetime.now().strftime("%H:%M:%S"),
        }))

    async def send_lan_devices(self, devices):
        await self.broadcast(json.dumps({
            "type": "lan_devices",
            "data": devices,
            "timestamp": datetime.now().strftime("%H:%M:%S"),
        }))

    async def send_dirb_result(self, payload):
        await self.broadcast(json.dumps({
            "type": "dirb_result",
            "data": payload,
            "timestamp": datetime.now().strftime("%H:%M:%S"),
        }))

    async def send_result(self, command, result):
        safe_result = dict(result) if isinstance(result, dict) else {"status": "success", "data": result}
        if "password" in safe_result:
            safe_result["password"] = "********"
        if "wpa_psk" in safe_result:
            safe_result["wpa_psk"] = "********"
        await self.broadcast(json.dumps({
            "type": "result",
            "command": command,
            "result": safe_result,
            "timestamp": datetime.now().strftime("%H:%M:%S"),
        }))

    async def send_busy(self):
        await self.broadcast(json.dumps({
            "type": "busy",
            "message": "Hệ thống đang xử lý tác vụ khác...",
            "timestamp": datetime.now().strftime("%H:%M:%S"),
        }))

    async def broadcast(self, message):
        with self.client_lock:
            if not self.clients:
                return
            dead = set()
            for client in self.clients:
                try:
                    await asyncio.wait_for(client.send(message), timeout=5)
                except Exception:
                    dead.add(client)
            for d in dead:
                self.clients.discard(d)
                self.connected_clients = len(self.clients)

    # ======================= STOP =======================
    def _stop_current_task(self):
        with self.task_lock:
            if not self.context.is_processing and not self.context.running_modules:
                return {"status": "error", "message": "Không có task nào đang chạy"}

            task_type = self.current_task
            self.logger.write(f"[!] Dừng task: {task_type}")

            cancelled = self.context.cancel_all_modules()
            if cancelled:
                self.logger.write(f"[!] Đã gửi tín hiệu dừng tới: {', '.join(cancelled)}")

            cleanup_orphan_processes()

            self.context.reset_state()
            self.current_task = None
            self.logger.write("[+] Đã dừng task thành công!")
            return {"status": "success", "message": f"Đã dừng task {task_type or 'unknown'}"}

    def _handle_client_disconnect(self):
        task = self.current_task
        running = list(self.context.running_modules.keys())

        if not task and not running:
            return

        self.logger.write(f"[WS] ⚠ Client mất kết nối khi đang chạy: task='{task}', modules={running}")

        cancelled = self.context.cancel_all_modules()
        if cancelled:
            self.logger.write(f"[WS] → Đã gửi cancel tới: {', '.join(cancelled)}")

        cleanup_orphan_processes()

        for mod_name in running:
            self.module_hang_counts[mod_name] = self.module_hang_counts.get(mod_name, 0) + 1
            count = self.module_hang_counts[mod_name]
            if count >= self.max_hangs:
                self.blocked_modules.add(mod_name)
                self.logger.write(
                    f"[!] ⛔ Module '{mod_name}' đã bị KHÓA do treo {count} lần liên tiếp"
                )
            else:
                self.logger.write(
                    f"[!] Module '{mod_name}' treo lần {count}/{self.max_hangs} — sẽ block nếu tiếp tục"
                )

        with self.task_lock:
            self.context.reset_state()
            self.current_task = None

    # ======================= HANDLE CLIENT =======================
    async def handle_client(self, websocket):
        if not await self.register(websocket):
            return
        try:
            async for message in websocket:
                try:
                    data = json.loads(message)
                    cmd = data.get("command")
                    params = data.get("params", {})
                    asyncio.create_task(self.process_command(websocket, cmd, params))
                except json.JSONDecodeError as e:
                    await websocket.send(json.dumps({"type": "error", "message": str(e)}))
                except Exception as e:
                    await websocket.send(json.dumps({"type": "error", "message": str(e)}))
        except websockets.exceptions.ConnectionClosed:
            pass
        finally:
            if self.context.is_processing or self.context.running_modules:
                self._handle_client_disconnect()
            await self.unregister(websocket)

    # ======================= ROUTING =======================
    async def process_command(self, websocket, cmd, params):
        # ---- STOP ----
        if cmd in ("stop", "stop_task", "stop_wps"):
            result = self._stop_current_task()
            await self.send_result(cmd, result)
            await self.send_status()
            return

        # ---- RESET BLOCKS ----
        if cmd == "reset_blocks":
            self.blocked_modules.clear()
            self.module_hang_counts.clear()
            self.logger.write("[SYSTEM] 🔓 Đã mở khoá tất cả module")
            await self.send_result(cmd, {
                "status": "success",
                "type": "generic",
                "message": "Đã mở khoá tất cả module bị block",
            })
            await self.send_status()
            return

        # ---- GET MODULE VERSIONS ----
        if cmd == "get_module_versions":
            await self.send_result(cmd, {
                "status": "success",
                "type": "module_versions",
                "modules": self._collect_versions(),
            })
            return

        # ---- BUSY CHECK ----
        with self.task_lock:
            if self.context.is_processing and cmd not in self.NON_BLOCKING:
                await websocket.send(json.dumps({
                    "type": "busy",
                    "command": cmd,
                    "message": "Hệ thống đang bận",
                    "current_task": self.current_task,
                }))
                return
            self.current_task = cmd
            if cmd not in self.NON_BLOCKING:
                self.context.is_processing = True
            await self.send_status()

        try:
            self.logger.write(f"[CMD] {cmd}", is_command=True)

            # ✅ CHECK ROOT PERMISSION
            cfg = get_config()
            if not cfg.can_run(cmd):
                reason = cfg.get_reason_blocked(cmd)
                self.logger.write(f"[!] ⛔ {reason}")
                await self.send_result(cmd, {
                    "status": "error",
                    "type": "permission_denied",
                    "command": cmd,
                    "requires_root": True,
                    "message": reason,
                })
                return

            # ---- Simple built-ins ----
            if cmd == "clear_terminal":
                self.logger.clear()
                await self.send_result(cmd, {"status": "success", "message": "Đã xoá terminal"})
                return
            if cmd == "get_status":
                await self.send_result(cmd, {"status": "success", "data": self.context.get_system_status()})
                return
            if cmd == "shutdown":
                self.logger.write("[SYSTEM] 🛑 Đang tắt tool...")

                def do_shutdown():
                    time.sleep(2)
                    try:
                        cleanup_orphan_processes()
                        if os.path.exists(SESSION_LOCK):
                            os.remove(SESSION_LOCK)
                    except Exception:
                        pass
                    try:
                        os.system("su -c 'pkill -f server.py' 2>/dev/null")
                    except Exception:
                        pass
                    os._exit(0)

                threading.Thread(target=do_shutdown, daemon=True).start()
                await self.send_result(cmd, {"status": "success", "message": "Tool sẽ tắt sau 2s..."})
                return

            # ---- Route qua registry ----
            module = self.registry.route(cmd)
            if module is None:
                await self.send_result(cmd, {"status": "error",
                                             "message": f"Không có module xử lý: {cmd}"})
                return

            if module.name in self.blocked_modules:
                self.logger.write(f"[!] Module '{module.name}' đang bị BLOCK — từ chối '{cmd}'")
                await self.send_result(cmd, {
                    "status": "error",
                    "type": "module_blocked",
                    "module": module.name,
                    "command": cmd,
                    "hang_count": self.module_hang_counts.get(module.name, 0),
                    "message": (
                        f"Module '{module.name}' đã bị KHÓA do treo "
                        f"{self.module_hang_counts.get(module.name, 0)} lần. "
                        f"Restart tool để mở khóa."
                    ),
                })
                return

            self._last_command = cmd
            self._last_params = params

            module.mark_running(cmd)

            loop = asyncio.get_event_loop()
            try:
                result = await loop.run_in_executor(None, lambda: module.handle(cmd, params))
            finally:
                module.mark_stopped()

            rtype = (result or {}).get("type")
            if rtype == "networks":
                await self.send_networks(result.get("networks", []))
            elif rtype == "lan_devices":
                await self.send_lan_devices(result.get("hosts", {}))
            elif rtype == "dirb_result":
                await self.send_dirb_result(result)
            elif rtype == "module_versions":
                pass

            await self.send_result(cmd, result)

        except InterruptedError as e:
            self.logger.write(f"[STOP] {cmd}: {e}")
            await websocket.send(json.dumps({
                "type": "result",
                "command": cmd,
                "result": {"status": "error", "type": "cancelled", "message": str(e)},
            }))
        except Exception as e:
            self.logger.write(f"[ERROR] {cmd}: {e}")
            await websocket.send(json.dumps({
                "type": "error", "command": cmd, "message": str(e)
            }))
        finally:
            with self.task_lock:
                if self.current_task == cmd:
                    self.context.is_processing = False
                    self.current_task = None
            await self.send_status()

    def _collect_versions(self):
        out = []
        for mod in self.registry.modules.values():
            try:
                out.append(mod.get_version_info())
            except Exception:
                pass
        return out