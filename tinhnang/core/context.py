 # tinhnang/core/context.py
import threading


class AppContext:
    """
    Bối cảnh chia sẻ giữa các module (plugin) và server.
    Module hoạt động NGOÀI LUỒNG server (qua run_in_executor),
    trao đổi với server qua context + return value chuẩn.

    ✅ NEW:
      - running_modules: dict name -> {started_at, command, thread_id, cancel_flag}
      - cancel_events: dict name -> threading.Event  (để module tự check và dừng)
    """

    def __init__(self):
        # Shared instances
        self.logger = None
        self.file_manager = None
        self.wifi_manager = None
        self.network_scanner = None
        self.ws_server = None
        self.loop = None

        # State flags (được module set khi chạy)
        self.is_processing = False
        self.scanning = False
        self.connecting = False
        self.wps_attacking = False
        self.lan_scanning = False

        # Data dùng chung
        self.current_networks = []
        self.current_task = None

        self.state_lock = threading.Lock()

        # ✅ NEW: theo dõi module đang chạy
        self.running_modules = {}       # name -> dict(info)
        self.cancel_events = {}         # name -> threading.Event
        self._running_lock = threading.Lock()

    # -----------------------------------------------------------------
    def get_system_status(self):
        return {
            "system": self.is_processing,
            "scanning": self.scanning,
            "connecting": self.connecting,
            "wps_attacking": self.wps_attacking,
            "lan_scanning": self.lan_scanning,
            "running_modules": list(self.running_modules.keys()),
        }

    def reset_state(self):
        self.is_processing = False
        self.scanning = False
        self.connecting = False
        self.wps_attacking = False
        self.lan_scanning = False
        self.current_task = None

    # -----------------------------------------------------------------
    # ✅ NEW: MODULE RUNNING TRACKING
    # -----------------------------------------------------------------
    def mark_module_running(self, name, command="", cancel_event=None):
        with self._running_lock:
            import time
            self.running_modules[name] = {
                "started_at": time.time(),
                "command": command,
                "thread_id": threading.get_ident(),
            }
            if cancel_event is not None:
                self.cancel_events[name] = cancel_event
            else:
                self.cancel_events[name] = threading.Event()

    def mark_module_stopped(self, name):
        with self._running_lock:
            self.running_modules.pop(name, None)
            self.cancel_events.pop(name, None)

    def is_module_running(self, name):
        with self._running_lock:
            return name in self.running_modules

    def get_cancel_event(self, name):
        with self._running_lock:
            ev = self.cancel_events.get(name)
            if ev is None:
                ev = threading.Event()
                self.cancel_events[name] = ev
            return ev

    def cancel_all_modules(self):
        """Set cancel flag cho mọi module đang chạy."""
        with self._running_lock:
            for name, ev in self.cancel_events.items():
                ev.set()
            return list(self.cancel_events.keys())