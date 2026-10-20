# tinhnang/modules/base_module.py


class BaseModule:
    """
    Interface chuẩn cho mọi PLUGIN MODULE.

    Module con khai báo:
      - name / commands / description
      - version / latest_version  ✅ NEW
      - category / category_label / category_icon / ui_buttons
      - self.resource → ModuleResource

    ✅ NEW:
      - self.emit_progress(pct, label) → gửi progress bar (%)
      - self.render_panel(panel_dict) → gửi UI panel riêng (HTML)
      - self.is_cancelled() / self.check_cancel() → kiểm tra module có bị yêu cầu dừng
      - self.mark_running() / self.mark_stopped() → đánh dấu module đang chạy
    """

    name = "base"
    commands = []
    description = "Base module"

    # ✅ NEW: version tracking
    version = "1.0.0"
    latest_version = "1.0.0"
    version_notes = ""

    category = "system"
    category_label = "Hệ thống"
    category_icon = "⚙️"
    ui_buttons = []

    def __init__(self, context):
        self.context = context
        self._resource = None
        self._cancel_event = None
        self._running = False

    # -----------------------------------------------------------------
    @property
    def resource(self):
        if self._resource is None:
            from ..core.resource_manager import ModuleResource
            self._resource = ModuleResource(
                self.name,
                logger=getattr(self.context, "logger", None),
            )
            self._resource.load(auto_create=False)
        return self._resource

    # -----------------------------------------------------------------
    def can_handle(self, command):
        return command in self.commands

    def handle(self, command, params):
        raise NotImplementedError(f"Module {self.name} chưa triển khai handle()")

    def init(self):
        pass

    def cleanup(self):
        pass

    # -----------------------------------------------------------------
    # ✅ NEW: RUNNING TRACKING + CANCEL
    # -----------------------------------------------------------------
    def mark_running(self, command=""):
        """Đánh dấu module đang chạy + tạo cancel event."""
        self._running = True
        self._cancel_event = self.context.get_cancel_event(self.name)
        self._cancel_event.clear()
        self.context.mark_module_running(self.name, command, self._cancel_event)

    def mark_stopped(self):
        """Đánh dấu module đã dừng."""
        self._running = False
        self.context.mark_module_stopped(self.name)

    def is_running(self):
        return self._running or self.context.is_module_running(self.name)

    def is_cancelled(self):
        """Kiểm tra module có bị yêu cầu dừng không (dùng trong loop dài)."""
        if self._cancel_event is None:
            return False
        return self._cancel_event.is_set()

    def check_cancel(self):
        """Raise nếu bị cancel — dùng trong loop dài để break sớm."""
        if self.is_cancelled():
            raise InterruptedError(f"Module '{self.name}' đã bị yêu cầu dừng")

    # -----------------------------------------------------------------
    # ✅ HELPER: PROGRESS
    # -----------------------------------------------------------------
    def emit_progress(self, pct, label=""):
        """
        Gửi tiến trình (%) tới client qua WebSocket.
        - pct: int 0..100 (hoặc None để ẩn)
        - label: string mô tả ngắn
        """
        ws = getattr(self.context, "ws_server", None)
        loop = getattr(self.context, "loop", None)
        if not ws or not loop:
            return
        try:
            import asyncio, json
            asyncio.run_coroutine_threadsafe(
                ws.broadcast(json.dumps({
                    "type": "progress",
                    "pct": pct,
                    "label": label,
                    "module": self.name,
                })),
                loop,
            )
        except Exception:
            pass

    # -----------------------------------------------------------------
    # ✅ HELPER: RENDER PANEL
    # -----------------------------------------------------------------
    def render_panel(self, panel: dict, title: str = ""):
        """Gửi UI panel riêng của module → client render trong mainResultSection."""
        ws = getattr(self.context, "ws_server", None)
        loop = getattr(self.context, "loop", None)
        if not ws or not loop:
            return
        try:
            import asyncio, json
            asyncio.run_coroutine_threadsafe(
                ws.broadcast(json.dumps({
                    "type": "module_panel",
                    "title": title or panel.get("title", ""),
                    "panel": panel,
                    "module": self.name,
                })),
                loop,
            )
        except Exception:
            pass

    # -----------------------------------------------------------------
    # ✅ NEW: VERSION INFO
    # -----------------------------------------------------------------
    def get_version_info(self):
        """Trả về thông tin version của module."""
        return {
            "name": self.name,
            "version": self.version,
            "latest_version": self.latest_version,
            "has_update": self.latest_version != self.version,
            "version_notes": self.version_notes,
            "description": self.description,
            "category": self.category,
        }