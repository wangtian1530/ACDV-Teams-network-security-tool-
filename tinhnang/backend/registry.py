# tinhnang/backend/registry.py
"""
REGISTRY - Load module động + filter UI theo quyền root.
"""
import importlib
import pkgutil
import inspect

from ..modules.base_module import BaseModule
from ..core.config import get_config


class ModuleRegistry:
    def __init__(self, context):
        self.context = context
        self.modules = {}
        self.command_map = {}

    def register(self, module_instance):
        if not isinstance(module_instance, BaseModule):
            return
        self.modules[module_instance.name] = module_instance
        for cmd in module_instance.commands:
            if cmd in self.command_map:
                print(f"[Registry] ⚠ command '{cmd}' bị đăng ký trùng")
            self.command_map[cmd] = module_instance

    def load_from_package(self, package_name="tinhnang.modules"):
        try:
            package = importlib.import_module(package_name)
        except Exception as e:
            print(f"[Registry] ❌ Không import được package {package_name}: {e}")
            return

        for _, module_name, _ in pkgutil.iter_modules(package.__path__):
            if module_name.startswith("_") or module_name == "base_module":
                continue
            full_name = f"{package_name}.{module_name}"
            try:
                mod = importlib.import_module(full_name)
                for _, obj in inspect.getmembers(mod, inspect.isclass):
                    if (
                        issubclass(obj, BaseModule)
                        and obj is not BaseModule
                        and obj.__module__ == mod.__name__
                    ):
                        instance = obj(self.context)
                        instance.init()
                        self.register(instance)
                        print(f"[Registry] ✓ Loaded module: {instance.name} "
                              f"v{instance.version} ({len(instance.commands)} commands)")
            except Exception as e:
                print(f"[Registry] ❌ Lỗi load {full_name}: {e}")

    def route(self, command):
        return self.command_map.get(command)

    def list_modules(self):
        return [(m.name, m.description, m.commands) for m in self.modules.values()]

    def collect_versions(self):
        result = []
        for m in self.modules.values():
            try:
                result.append(m.get_version_info())
            except Exception:
                pass
        return result

    def collect_ui_config(self):
        """
        Gom metadata UI. Thêm:
          - is_root + root_method + root_required_commands (top-level)
          - requires_root cho từng button
          - can_run (chỉ true nếu được phép chạy)
        """
        cfg = get_config()
        buttons = []
        categories = {}

        for mod in self.modules.values():
            mod_buttons = getattr(mod, "ui_buttons", None) or []
            if not mod_buttons:
                continue

            cat = getattr(mod, "category", "system") or "system"
            cat_label = getattr(mod, "category_label", "Hệ thống")
            cat_icon = getattr(mod, "category_icon", "⚙️")

            categories.setdefault(cat, {
                "id": cat,
                "label": cat_label,
                "icon": cat_icon,
            })

            for btn in mod_buttons:
                b = dict(btn)
                b.setdefault("category", cat)
                b.setdefault("color", "secondary")
                b.setdefault("icon", "🔧")
                b.setdefault("params", {})
                b.setdefault("prompt", None)
                b["module_version"] = getattr(mod, "version", "1.0.0")
                b["module_has_update"] = (
                    getattr(mod, "latest_version", getattr(mod, "version", "1.0.0"))
                    != getattr(mod, "version", "1.0.0")
                )
                b["requires_root"] = cfg.requires_root(b.get("command", ""))
                b["can_run"] = cfg.can_run(b.get("command", ""))
                buttons.append(b)

        return {
            "buttons": buttons,
            "categories": list(categories.values()),
            "versions": self.collect_versions(),
            "is_root": cfg.is_root,
            "root_method": cfg.root_method,
            "root_required_commands": list(
                cfg.data["modules"].get("root_required_commands", [])
            ),
        }

    def cleanup_all(self):
        for m in self.modules.values():
            try:
                m.cleanup()
            except Exception:
                pass