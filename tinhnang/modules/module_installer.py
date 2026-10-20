# tinhnang/modules/module_installer.py
"""
Module Installer — Upload file .py trực tiếp qua dropzone (drag & drop).

⭐ v1.5.1:
  - Dropzone HTML thật trong panel: kéo thả HOẶC bấm chọn file
  - <input type="file" accept=".py"> native — không cần nhập path
  - JS tự đọc file → base64 → gửi WS (nhiều fallback dispatch)
  - Checkbox "Ghi đè" ngay trong widget (không retry 2 lần)
  - Validate client-side: .py, ≤ max_size_kb
  - Bỏ prompt → nút "Quản Lý" mở panel có sẵn widget
  - Vẫn giữ source_path / url cho API/legacy + nút "Cài lại"
"""

import os
import sys
import time
import json
import base64
import threading
import subprocess
import urllib.request
import urllib.parse

from .base_module import BaseModule
from ..core.utils import cleanup_orphan_processes
from ..core.paths import SESSION_LOCK
from ..core.module_activity import get_activity_log


MODULES_DIR = os.path.dirname(os.path.abspath(__file__))
CORE_FILES = {"__init__.py", "base_module.py"}


DEFAULT_CONFIG = {
    "description": "Cài đặt & quản lý module plugin (.py) — upload trực tiếp",
    "settings": {
        "restart_delay": 3.0,
        "allow_overwrite": False,
        "max_size_kb": 512,
    },
}


def _encode_attr(obj):
    return urllib.parse.quote(json.dumps(obj, ensure_ascii=False), safe="")


# ── JS nhúng vào panel: xử lý chọn file + drag & drop + gửi WS ─────
_UPLOAD_JS = r"""
(function(){
  function ready(fn){
    if (document.readyState === 'loading')
      document.addEventListener('DOMContentLoaded', fn);
    else setTimeout(fn, 30);
  }

  function init(){
    var zone    = document.getElementById('mi-dropzone');
    var input   = document.getElementById('mi-file-input');
    var status  = document.getElementById('mi-upload-status');
    var owCb    = document.getElementById('mi-overwrite-cb');
    if (!zone || !input) return;
    if (zone.dataset.miReady === '1') return;
    zone.dataset.miReady = '1';

    var MAX_KB = 512;

    function setStatus(msg, color){
      if (!status) return;
      status.innerHTML = msg;
      status.style.color = color || '#333';
    }

    function dispatch(params){
      // Fallback 1: window.sendCommand(cmd, params)
      try {
        if (typeof window.sendCommand === 'function'){
          window.sendCommand('install_module', params);
          return true;
        }
      } catch(e){}
      // Fallback 2: window.ws.send(raw json)
      try {
        if (window.ws && typeof window.ws.send === 'function'){
          window.ws.send(JSON.stringify({
            command: 'install_module',
            params: params
          }));
          return true;
        }
      } catch(e){}
      // Fallback 3: giả lập click button .module-action-btn
      try {
        var b = document.createElement('button');
        b.className = 'module-action-btn';
        b.style.display = 'none';
        b.setAttribute('data-command', 'install_module');
        b.setAttribute('data-params',
          encodeURIComponent(JSON.stringify(params)));
        document.body.appendChild(b);
        b.click();
        setTimeout(function(){ b.remove(); }, 3000);
        return true;
      } catch(e){}
      return false;
    }

    function handleFile(file){
      if (!file) return;
      var name = file.name || 'module.py';
      if (!/\.py$/i.test(name)){
        setStatus('❌ Chỉ nhận file <b>.py</b> (bạn chọn: ' +
          name.replace(/[<>&]/g, '') + ')', '#dc3545');
        return;
      }
      if (file.size > MAX_KB * 1024){
        setStatus('❌ File vượt quá ' + MAX_KB + ' KB (' +
          Math.round(file.size/1024) + ' KB)', '#dc3545');
        return;
      }
      setStatus('⏳ Đang đọc <b>' + name + '</b>...', '#2196f3');

      var reader = new FileReader();
      reader.onload = function(ev){
        try {
          var raw = ev.target.result || '';
          var b64 = raw.indexOf(',') >= 0 ? raw.split(',')[1] : raw;
          setStatus('📤 Đang gửi <b>' + name + '</b> (' +
            Math.max(1, Math.round(file.size/1024)) + ' KB)...', '#2196f3');

          var params = {
            content_b64: b64,
            filename:    name,
            overwrite:   !!(owCb && owCb.checked),
            restart:     true
          };

          if (dispatch(params)){
            setStatus('✅ Đã gửi <b>' + name +
              '</b> — tool sẽ restart sau vài giây...', '#28a745');
            if (owCb) owCb.checked = false;
          } else {
            setStatus('❌ Không tìm thấy kênh gửi WS (window.sendCommand/' +
              'window.ws/.module-action-btn đều fail)', '#dc3545');
          }
        } catch(err){
          setStatus('❌ Lỗi xử lý file: ' + err.message, '#dc3545');
        }
      };
      reader.onerror = function(){
        setStatus('❌ Không đọc được file', '#dc3545');
      };
      reader.readAsDataURL(file);
    }

    input.addEventListener('change', function(){
      if (input.files && input.files[0]) handleFile(input.files[0]);
      input.value = ''; // cho phép chọn lại cùng file
    });

    // Drag & drop
    ['dragenter','dragover'].forEach(function(ev){
      zone.addEventListener(ev, function(e){
        e.preventDefault(); e.stopPropagation();
        zone.classList.add('dragging');
      });
    });
    ['dragleave','drop'].forEach(function(ev){
      zone.addEventListener(ev, function(e){
        e.preventDefault(); e.stopPropagation();
        zone.classList.remove('dragging');
      });
    });
    zone.addEventListener('drop', function(e){
      var dt = e.dataTransfer;
      if (!dt) return;
      var f = dt.files && dt.files[0];
      if (f) handleFile(f);
    });
  }

  ready(init);
})();
"""


class ModuleInstallerModule(BaseModule):
    name = "module_installer"
    commands = [
        "install_module",
        "list_modules",
        "uninstall_module",
        "restart_tool",
        "module_detail",
        "get_module_versions",
        "module_activity",
        "clear_module_activity",
    ]
    description = "Cài đặt & quản lý module plugin qua upload"

    version = "1.5.1"
    latest_version = "1.5.1"
    version_notes = "Upload file thật (dropzone + drag&drop), bỏ prompt."

    category = "system"
    category_label = "Hệ thống"
    category_icon = "⚙️"

    # ⭐ Nút chính chỉ mở panel — panel đã có widget upload
    ui_buttons = [
        {
            "id": "manage_modules_btn",
            "label": "Quản Lý / Upload Module",
            "icon": "📦",
            "color": "primary",
            "command": "list_modules",
        },
        {
            "id": "module_activity_btn",
            "label": "Nhật Ký Module",
            "icon": "📊",
            "color": "warning",
            "command": "module_activity",
        },
        {
            "id": "restart_tool_btn",
            "label": "Khởi động lại",
            "icon": "🔄",
            "color": "warning",
            "command": "restart_tool",
        },
    ]

    # -----------------------------------------------------------------
    def init(self):
        self.resource.load(default_config=DEFAULT_CONFIG)
        self.activity = get_activity_log()
        self.context.logger.write(
            f"[✓] Module Installer v{self.version} loaded!"
        )

    def cleanup(self):
        try:
            self.activity.flush()
        except Exception:
            pass

    # -----------------------------------------------------------------
    def handle(self, command, params):
        try:
            self.check_cancel()

            if command == "install_module":
                return self._install(params or {})
            if command == "list_modules":
                return self._list()
            if command == "uninstall_module":
                return self._uninstall(params or {})
            if command == "restart_tool":
                return self._restart()
            if command == "module_detail":
                return self._detail(params or {})
            if command == "get_module_versions":
                return self._get_versions()
            if command == "module_activity":
                return self._show_activity(params or {})
            if command == "clear_module_activity":
                return self._clear_activity(params or {})
            return self._err(f"Unknown command: {command}")
        except InterruptedError:
            return {
                "status": "error",
                "type": "cancelled",
                "message": "Module installer task đã dừng",
            }
        except Exception as e:
            return self._err(f"Exception: {e}")

    # ⭐ Log helpers
    def _log_install_error(self, stem_or_file, message, details=None):
        try:
            stem = stem_or_file
            if stem.endswith(".py"):
                stem = stem[:-3]
            self.activity.log(
                module=stem,
                event="install_error",
                command="install_module",
                severity="error",
                message=message,
                details=details or {},
            )
        except Exception:
            pass

    def _log_install_success(self, filename, existed):
        try:
            stem = filename[:-3] if filename.endswith(".py") else filename
            self.activity.log(
                module=stem,
                event="install_success",
                command="install_module",
                severity="info",
                message=f"Đã {'ghi đè' if existed else 'cài đặt'} {filename}",
                details={"filename": filename, "overwrite": existed},
            )
        except Exception:
            pass

    # ── install_module ───────────────────────────────────────────
    def _install(self, params):
        content_b64 = (
            params.get("content_b64")
            or params.get("file_b64")
            or params.get("file")
            or params.get("data")
        )
        if isinstance(content_b64, dict):
            filename_pre = content_b64.get("name") or content_b64.get("filename")
            content_b64 = content_b64.get("content") or content_b64.get("data")
            params.setdefault("filename", filename_pre)

        source_path = params.get("source_path") or params.get("path")
        url = params.get("url")
        filename = (
            params.get("filename")
            or params.get("file_name")
            or params.get("name")
        )
        overwrite = bool(
            params.get("overwrite", self.resource.get("allow_overwrite", False))
        )
        auto_restart = params.get("restart", True)

        max_size = int(self.resource.get("max_size_kb", 512)) * 1024

        content = None
        source_label = "?"

        # ── PRIORITY 1: content_b64 (upload) ────────────────────
        if content_b64:
            source_label = filename or "upload"
            try:
                if (isinstance(content_b64, str)
                        and content_b64.strip().startswith("data:")
                        and "," in content_b64):
                    content_b64 = content_b64.split(",", 1)[1]
                try:
                    content = base64.b64decode(content_b64, validate=False)
                except Exception:
                    content = base64.urlsafe_b64decode(content_b64 + "===")
            except Exception as e:
                self._log_install_error(
                    filename or "upload",
                    f"Base64 lỗi: {e}",
                    {"type": type(e).__name__},
                )
                return self._err(f"Base64 lỗi: {e}")

            if len(content) > max_size:
                self._log_install_error(
                    filename or "upload",
                    f"File vượt quá {max_size // 1024} KB",
                    {"size": len(content), "max_kb": max_size // 1024},
                )
                return self._err(f"File vượt quá {max_size // 1024} KB")

            if not filename:
                self._log_install_error(
                    "unknown", "Thiếu 'filename' khi upload file",
                )
                return self._err(
                    "Thiếu 'filename' khi upload. Gửi kèm params.filename."
                )

        # ── PRIORITY 2: source_path (legacy) ────────────────────
        elif source_path:
            source_path = os.path.expanduser(str(source_path).strip())
            source_label = os.path.basename(source_path)
            if not os.path.isfile(source_path):
                self._log_install_error(
                    source_label,
                    f"Không tìm thấy file: {source_path}",
                    {"source_path": source_path},
                )
                return self._err(f"Không tìm thấy file: {source_path}")
            try:
                if os.path.getsize(source_path) > max_size:
                    self._log_install_error(
                        source_label,
                        f"File vượt quá {max_size // 1024} KB",
                        {"size": os.path.getsize(source_path),
                         "max_kb": max_size // 1024},
                    )
                    return self._err(f"File vượt quá {max_size // 1024} KB")
                with open(source_path, "rb") as f:
                    content = f.read()
            except Exception as e:
                self._log_install_error(
                    source_label,
                    f"Không đọc được file: {e}",
                    {"type": type(e).__name__},
                )
                return self._err(f"Không đọc được file: {e}")
            filename = filename or source_label

        # ── PRIORITY 3: url (legacy) ────────────────────────────
        elif url:
            source_label = filename or "download"
            try:
                with urllib.request.urlopen(url, timeout=15) as r:
                    content = r.read(max_size + 1)
                if len(content) > max_size:
                    self._log_install_error(
                        source_label,
                        f"File từ URL vượt quá {max_size // 1024} KB",
                        {"url": url},
                    )
                    return self._err(
                        f"File từ URL vượt quá {max_size // 1024} KB"
                    )
            except Exception as e:
                self._log_install_error(
                    source_label,
                    f"Tải URL thất bại: {e}",
                    {"url": url, "type": type(e).__name__},
                )
                return self._err(f"Tải URL thất bại: {e}")
            if not filename:
                filename = url.rstrip("/").split("/")[-1]

        else:
            self._log_install_error(
                "unknown",
                "Cần upload file (content_b64) hoặc source_path/url",
            )
            return self._err(
                "Cần upload file .py qua panel "
                "(params.content_b64 + params.filename)."
            )

        # ── Validate filename ───────────────────────────────────
        filename = os.path.basename(str(filename).strip())
        if not filename.endswith(".py"):
            self._log_install_error(filename, "File phải có đuôi .py")
            return self._err("File phải có đuôi .py")
        if filename in CORE_FILES:
            self._log_install_error(
                filename, f"Không được ghi đè file core: {filename}",
            )
            return self._err(f"Không được ghi đè file core: {filename}")

        stem = filename[:-3]
        if not stem or not all(c.isalnum() or c == "_" for c in stem):
            self._log_install_error(
                filename, "Tên file chỉ được chứa chữ, số và dấu _",
            )
            return self._err("Tên file chỉ được chứa chữ, số và dấu _")

        try:
            code_str = content.decode("utf-8")
        except UnicodeDecodeError:
            self._log_install_error(filename, "File không phải UTF-8")
            return self._err("File không phải UTF-8")

        try:
            compile(code_str, filename, "exec")
        except SyntaxError as e:
            self._log_install_error(
                filename,
                f"Syntax error: {e.msg} (line {e.lineno})",
                {"line": e.lineno, "offset": e.offset,
                 "text": (e.text or "")[:120]},
            )
            return self._err(f"Syntax error: {e.msg} (line {e.lineno})")

        if "BaseModule" not in code_str:
            self._log_install_error(
                filename,
                "File phải kế thừa BaseModule (không tìm thấy 'BaseModule')",
            )
            return self._err(
                "File phải kế thừa BaseModule "
                "(không tìm thấy 'BaseModule')"
            )

        if "class " not in code_str:
            self._log_install_error(filename, "File không có khai báo class")
            return self._err("File không có khai báo class")

        dest = os.path.join(MODULES_DIR, filename)
        existed = os.path.exists(dest)
        if existed and not overwrite:
            self._log_install_error(
                filename,
                f"'{filename}' đã tồn tại và chưa cho phép ghi đè",
                {"existed": True},
            )
            return self._err(
                f"'{filename}' đã tồn tại. Tick 'Ghi đè' hoặc gửi lại với "
                f"overwrite=true để ghi đè."
            )

        try:
            with open(dest, "wb") as f:
                f.write(content)
        except Exception as e:
            self._log_install_error(
                filename,
                f"Không ghi được file: {e}",
                {"type": type(e).__name__, "dest": dest},
            )
            return self._err(f"Không ghi được file: {e}")

        self._log_install_success(filename, existed)

        self.context.logger.write(
            f"[INSTALLER] ✓ Đã {'ghi đè' if existed else 'cài đặt'}: "
            f"{filename} ({len(content)} bytes, source={source_label})"
        )

        if auto_restart:
            delay = float(self.resource.get("restart_delay", 3.0))
            self._schedule_restart(delay)
            return {
                "status": "success",
                "type": "generic",
                "message": (
                    f"✓ Đã {'cập nhật' if existed else 'cài'} "
                    f"'{filename}' ({len(content)} bytes). "
                    f"Tool sẽ khởi động lại sau {delay:.0f}s để nạp module. "
                    f"WS sẽ ngắt kết nối — client tự reconnect."
                ),
            }

        return {
            "status": "success",
            "type": "generic",
            "message": (
                f"✓ Đã cài '{filename}'. Gửi 'restart_tool' để áp dụng."
            ),
        }

    # ── list_modules ────────────────────────────────────────────
    def _list(self):
        try:
            files = sorted(
                f for f in os.listdir(MODULES_DIR)
                if f.endswith(".py") and f not in CORE_FILES
            )
        except Exception as e:
            return self._err(f"Không đọc được thư mục: {e}")

        max_kb = int(self.resource.get("max_size_kb", 512))

        # ⭐ Dropzone upload (label → click mở file picker)
        upload_widget = (
            "<style>"
            ".mi-dropzone{display:block;background:linear-gradient(135deg,#e3f2fd,#f0f7ff);"
            "border:2px dashed #2196f3;border-radius:12px;padding:24px 20px;"
            "text-align:center;cursor:pointer;margin-bottom:10px;"
            "transition:all .2s;user-select:none;}"
            ".mi-dropzone:hover,.mi-dropzone.dragging{"
            "background:linear-gradient(135deg,#bbdefb,#e3f2fd);"
            "border-color:#1976d2;transform:scale(1.005);}"
            ".mi-dropzone-icon{font-size:42px;margin-bottom:6px;}"
            ".mi-dropzone-title{font-weight:700;color:#1565c0;"
            "font-size:15px;margin-bottom:4px;}"
            ".mi-dropzone-sub{font-size:12px;color:#5a6b85;}"
            ".mi-upload-status{font-size:12px;margin-top:10px;min-height:16px;"
            "line-height:1.5;}"
            ".mi-overwrite-label{display:flex;align-items:center;gap:6px;"
            "font-size:12px;color:#555;margin-bottom:16px;cursor:pointer;}"
            "</style>"
            "<label for='mi-file-input' id='mi-dropzone' class='mi-dropzone'>"
            "  <div class='mi-dropzone-icon'>📥</div>"
            "  <div class='mi-dropzone-title'>"
            "    Kéo & thả file .py vào đây"
            "  </div>"
            "  <div class='mi-dropzone-sub'>"
            f"    hoặc bấm để chọn file · tối đa {max_kb} KB · "
            "phải kế thừa <code>BaseModule</code>"
            "  </div>"
            "  <input type='file' id='mi-file-input' accept='.py,text/x-python'"
            "         style='display:none'>"
            "  <div id='mi-upload-status' class='mi-upload-status'></div>"
            "</label>"
            "<label class='mi-overwrite-label'>"
            "  <input type='checkbox' id='mi-overwrite-cb'>"
            "  Ghi đè nếu module đã tồn tại"
            "</label>"
            f"<script>{_UPLOAD_JS}</script>"
        )

        # ── Empty state ────────────────────────────────────────
        if not files:
            self.render_panel({
                "title": "📦 QUẢN LÝ MODULE",
                "html": (
                    upload_widget
                    + "<div style='text-align:center;padding:20px;color:#888;'>"
                    "📭 Chưa có module nào.<br>"
                    "Kéo thả file <b>.py</b> vào vùng trên để cài module đầu tiên."
                    "</div>"
                ),
                "actions": [
                    {
                        "label": "Làm mới",
                        "icon": "🔄",
                        "color": "secondary",
                        "command": "list_modules",
                        "params": {},
                    },
                ],
            })
            return {
                "status": "success",
                "type": "generic",
                "message": "📦 Chưa có module — kéo thả file .py để cài.",
            }

        registry_versions = {}
        try:
            if self.context.ws_server and self.context.ws_server.registry:
                for v in self.context.ws_server.registry.collect_versions():
                    registry_versions[v["name"]] = v
        except Exception:
            pass

        activity_stats = self.activity.stats()

        rows = []
        for f in files:
            p = os.path.join(MODULES_DIR, f)
            size = os.path.getsize(p)
            mtime = time.strftime(
                "%Y-%m-%d %H:%M",
                time.localtime(os.path.getmtime(p)),
            )
            stem = f[:-3]

            desc, cmds = self._peek_module(p)
            cmd_count = len(cmds) if cmds else 0

            ver_info = registry_versions.get(stem, {})
            ver = ver_info.get("version", "?")
            latest = ver_info.get("latest_version", ver)
            has_update = ver_info.get("has_update", False)
            ver_badge = (
                f"<span style='color:#ff9800;font-weight:600;'>"
                f"v{ver} → v{latest} ⬆️</span>"
                if has_update
                else f"<span style='color:#4caf50;'>v{ver} ✓</span>"
            )

            act = activity_stats.get(stem, {})
            act_err = act.get("error", 0)
            act_warn = act.get("warning", 0)
            err_badge = ""
            if act_err > 0:
                err_badge = (
                    f"<span style='background:#dc3545;color:white;"
                    f"padding:1px 6px;border-radius:8px;font-size:10px;"
                    f"margin-left:4px;'>❌ {act_err} lỗi</span>"
                )
            elif act_warn > 0:
                err_badge = (
                    f"<span style='background:#ffc107;color:#333;"
                    f"padding:1px 6px;border-radius:8px;font-size:10px;"
                    f"margin-left:4px;'>⚠️ {act_warn}</span>"
                )

            params_detail = _encode_attr({"name": f})
            params_reinstall = _encode_attr({
                "source_path": p,
                "overwrite": True,
                "restart": False,
            })
            params_uninstall = _encode_attr({
                "name": f, "confirmed": True,
            })
            params_activity = _encode_attr({"module": stem})

            rows.append(
                f"<div class='mi-card'>"
                f"  <div class='mi-row'>"
                f"    <div class='mi-info'>"
                f"      <div class='mi-name'>📦 {self._escape(f)} "
                f"        {ver_badge}{err_badge}</div>"
                f"      <div class='mi-meta'>"
                f"        {size} B · {mtime}"
                + (f" · {cmd_count} commands" if cmd_count else "")
                + f"      </div>"
                + (
                    f"      <div class='mi-desc'>"
                    f"{self._escape(desc)}</div>"
                    if desc else ""
                )
                + f"    </div>"
                f"    <div class='mi-actions'>"
                f"      <button class='btn btn-info btn-sm module-action-btn'"
                f"        data-command='module_detail'"
                f"        data-params='{params_detail}'"
                f"        title='Xem chi tiết'>ℹ️</button>"
                f"      <button class='btn btn-warning btn-sm module-action-btn'"
                f"        data-command='module_activity'"
                f"        data-params='{params_activity}'"
                f"        title='Xem nhật ký module'>📊</button>"
                f"      <button class='btn btn-warning btn-sm module-action-btn'"
                f"        data-command='install_module'"
                f"        data-params='{params_reinstall}'"
                f"        title='Cài lại (từ file hiện tại)'>🔁</button>"
                f"      <button class='btn btn-danger btn-sm module-action-btn'"
                f"        data-command='uninstall_module'"
                f"        data-params='{params_uninstall}'"
                f"        title='Xoá module'>🗑️</button>"
                f"    </div>"
                f"  </div>"
                f"</div>"
            )

        list_css = (
            "<style>"
            ".mi-card{background:#fff;border:1px solid #e3e8f0;"
            "border-radius:10px;padding:12px 14px;margin-bottom:10px;"
            "transition:.15s;}"
            ".mi-card:hover{border-color:#4a90e2;"
            "box-shadow:0 2px 8px rgba(74,144,226,.12);}"
            ".mi-row{display:flex;justify-content:space-between;"
            "align-items:center;gap:12px;}"
            ".mi-info{flex:1;min-width:0;}"
            ".mi-name{font-weight:600;color:#2c3e50;font-size:14px;"
            "margin-bottom:3px;}"
            ".mi-meta{font-size:11px;color:#8a99b0;}"
            ".mi-desc{font-size:12px;color:#5a6b85;margin-top:4px;"
            "white-space:nowrap;overflow:hidden;text-overflow:ellipsis;}"
            ".mi-actions{display:flex;gap:6px;flex-shrink:0;}"
            ".mi-actions .btn{padding:6px 10px;font-size:14px;line-height:1;}"
            "@media(max-width:600px){"
            ".mi-row{flex-direction:column;align-items:stretch;}"
            ".mi-actions{justify-content:flex-end;margin-top:8px;}"
            "}"
            "</style>"
        )

        html = (
            list_css
            + upload_widget
            + f"<div style='margin-bottom:12px;color:#2c3e50;font-size:13px;'>"
            f"📦 <b>{len(files)}</b> module đang cài đặt."
            f"</div>"
            + "".join(rows)
        )

        self.render_panel({
            "title": "📦 QUẢN LÝ MODULE",
            "html": html,
            "actions": [
                {
                    "label": "Nhật ký Module",
                    "icon": "📊",
                    "color": "warning",
                    "command": "module_activity",
                    "params": {},
                },
                {
                    "label": "Làm mới",
                    "icon": "🔄",
                    "color": "secondary",
                    "command": "list_modules",
                    "params": {},
                },
            ],
        })

        self.context.logger.write(
            f"[INSTALLER] 📦 {len(files)} module — panel đã hiển thị."
        )
        return {
            "status": "success",
            "type": "generic",
            "message": (
                f"📦 {len(files)} module. "
                f"Kéo thả file .py vào vùng upload để cài module mới."
            ),
        }

    # ── module_detail ────────────────────────────────────────────
    def _detail(self, params):
        name = params.get("name") or params.get("filename")
        if not name:
            return self._err("Thiếu tên module")

        name = os.path.basename(str(name).strip())
        if not name.endswith(".py"):
            name += ".py"

        dest = os.path.join(MODULES_DIR, name)
        if not os.path.isfile(dest):
            return self._err(f"Không tìm thấy: {name}")

        size = os.path.getsize(dest)
        mtime = time.strftime(
            "%Y-%m-%d %H:%M",
            time.localtime(os.path.getmtime(dest)),
        )
        desc, cmds = self._peek_module(dest)

        ver_info = {}
        try:
            if self.context.ws_server and self.context.ws_server.registry:
                stem = name[:-3]
                for v in self.context.ws_server.registry.collect_versions():
                    if v.get("name") == stem:
                        ver_info = v
                        break
        except Exception:
            pass

        ver = ver_info.get("version", "?")
        latest = ver_info.get("latest_version", ver)
        has_update = ver_info.get("has_update", False)
        notes = ver_info.get("version_notes", "")

        stem = name[:-3]
        act = self.activity.stats().get(stem, {})
        act_err = act.get("error", 0)
        act_warn = act.get("warning", 0)
        act_total = act.get("total", 0)
        activity_row = (
            f"  <div class='kv-row'><span class='kv-key'>Nhật ký</span>"
            f"    <span class='kv-val'>"
            f"      <span style='color:#dc3545;'>❌ {act_err}</span> · "
            f"      <span style='color:#ffc107;'>⚠️ {act_warn}</span> · "
            f"      <span style='color:#888;'>Σ {act_total}</span>"
            f"    </span></div>"
        )

        html = (
            f"<div class='module-panel'>"
            f"  <div class='kv-row'><span class='kv-key'>File</span>"
            f"    <span class='kv-val'>{self._escape(name)}</span></div>"
            f"  <div class='kv-row'><span class='kv-key'>Version</span>"
            f"    <span class='kv-val'>v{ver}"
            + (
                f" → <span style='color:#ff9800;font-weight:600;'>"
                f"v{latest} ⬆️</span>"
                if has_update else " ✓"
            )
            + f"    </span></div>"
            f"  <div class='kv-row'><span class='kv-key'>Kích thước</span>"
            f"    <span class='kv-val'>{size} B</span></div>"
            f"  <div class='kv-row'><span class='kv-key'>Cập nhật</span>"
            f"    <span class='kv-val'>{mtime}</span></div>"
            f"  <div class='kv-row'><span class='kv-key'>Mô tả</span>"
            f"    <span class='kv-val'>"
            f"{self._escape(desc or '(không có)')}</span></div>"
            f"  <div class='kv-row'><span class='kv-key'>Commands</span>"
            f"    <span class='kv-val'>"
            f"      {', '.join(cmds) if cmds else '(không đọc được)'}"
            f"    </span></div>"
            + activity_row
            + (
                f"  <div class='kv-row'><span class='kv-key'>Notes</span>"
                f"    <span class='kv-val'>{self._escape(notes)}</span></div>"
                if notes else ""
            )
            + f"</div>"
        )

        self.render_panel({
            "title": f"ℹ️ CHI TIẾT — {self._escape(name)}",
            "html": html,
            "actions": [
                {
                    "label": "Xem nhật ký",
                    "icon": "📊",
                    "color": "warning",
                    "command": "module_activity",
                    "params": {"module": stem},
                },
                {
                    "label": "Xoá module này",
                    "icon": "🗑️",
                    "color": "danger",
                    "command": "uninstall_module",
                    "params": {"name": name, "confirmed": True},
                },
                {
                    "label": "Cài lại",
                    "icon": "🔁",
                    "color": "warning",
                    "command": "install_module",
                    "params": {
                        "source_path": dest,
                        "overwrite": True,
                        "restart": False,
                    },
                },
                {
                    "label": "Quay lại",
                    "icon": "↩️",
                    "color": "secondary",
                    "command": "list_modules",
                    "params": {},
                },
            ],
        })

        return {
            "status": "success",
            "type": "generic",
            "message": f"ℹ️ Chi tiết module '{name}'.",
        }

    # ── uninstall_module ─────────────────────────────────────────
    def _uninstall(self, params):
        name = (
            params.get("name")
            or params.get("filename")
            or params.get("module")
        )
        if not name:
            return self._err("Thiếu tên module (params.name)")

        name = os.path.basename(str(name).strip())
        if not name.endswith(".py"):
            name += ".py"
        if name in CORE_FILES:
            return self._err(f"Không được xoá file core: {name}")

        dest = os.path.join(MODULES_DIR, name)
        if not os.path.isfile(dest):
            return self._err(f"Không tìm thấy: {name}")

        confirmed = bool(params.get("confirmed", False))
        if not confirmed:
            self.render_panel({
                "title": "⚠️ XÁC NHẬN XOÁ MODULE",
                "html": (
                    f"<div style='text-align:center;padding:16px;'>"
                    f"Bạn có chắc muốn xoá module "
                    f"<b style='color:#dc3545;'>"
                    f"{self._escape(name)}</b>?"
                    f"<br><br>"
                    f"<span style='color:#888;font-size:12px;'>"
                    f"Hành động này không thể hoàn tác.</span>"
                    f"</div>"
                ),
                "actions": [
                    {
                        "label": f"Xoá {name}",
                        "icon": "🗑️",
                        "color": "danger",
                        "command": "uninstall_module",
                        "params": {"name": name, "confirmed": True},
                    },
                    {
                        "label": "Huỷ",
                        "icon": "✖️",
                        "color": "secondary",
                        "command": "list_modules",
                        "params": {},
                    },
                ],
            })
            return {
                "status": "success",
                "type": "generic",
                "message": f"⚠️ Xác nhận xoá '{name}'?",
            }

        try:
            os.remove(dest)
        except Exception as e:
            return self._err(f"Không xoá được: {e}")

        cfg = os.path.join(
            os.path.dirname(MODULES_DIR), "..", "data", "modules",
            name.replace(".py", ".json"),
        )
        try:
            cfg = os.path.abspath(cfg)
            if os.path.isfile(cfg):
                os.remove(cfg)
        except Exception:
            pass

        self.context.logger.write(f"[INSTALLER] 🗑️ Đã xoá: {name}")

        self._list()
        return {
            "status": "success",
            "type": "generic",
            "message": f"🗑️ Đã xoá '{name}'. Restart tool để áp dụng.",
        }

    # ── restart_tool ─────────────────────────────────────────────
    def _restart(self):
        delay = float(self.resource.get("restart_delay", 3.0))
        self._schedule_restart(delay)
        return {
            "status": "success",
            "type": "generic",
            "message": f"🔄 Tool sẽ khởi động lại sau {delay:.0f}s...",
        }

    # ── get_module_versions ──────────────────────────────────────
    def _get_versions(self):
        versions = []
        registry_versions = {}
        try:
            if self.context.ws_server and self.context.ws_server.registry:
                for v in self.context.ws_server.registry.collect_versions():
                    registry_versions[v["name"]] = v
        except Exception:
            pass

        try:
            files = sorted(
                f for f in os.listdir(MODULES_DIR)
                if f.endswith(".py") and f not in CORE_FILES
            )
        except Exception:
            files = []

        for f in files:
            stem = f[:-3]
            ver = registry_versions.get(stem, {})
            versions.append({
                "file": f, "name": stem,
                "version": ver.get("version", "?"),
                "latest_version": ver.get(
                    "latest_version", ver.get("version", "?")
                ),
                "has_update": ver.get("has_update", False),
                "version_notes": ver.get("version_notes", ""),
            })

        for stem, ver in registry_versions.items():
            if not any(v["name"] == stem for v in versions):
                versions.append({
                    "file": f"{stem}.py", "name": stem,
                    "version": ver.get("version", "?"),
                    "latest_version": ver.get(
                        "latest_version", ver.get("version", "?")
                    ),
                    "has_update": ver.get("has_update", False),
                    "version_notes": ver.get("version_notes", ""),
                })

        return {
            "status": "success",
            "type": "module_versions",
            "modules": versions,
            "message": f"📦 {len(versions)} module",
        }

    # ── module_activity ──────────────────────────────────────────
    def _show_activity(self, params):
        module_filter = params.get("module") or None
        severity_filter = params.get("severity") or None
        limit = int(params.get("limit", 100))

        entries = self.activity.read(
            module=module_filter,
            severity=severity_filter,
            limit=limit,
        )
        stats = self.activity.stats()

        ram_size = self.activity.size()
        file_ok = self.activity.is_file_ok()
        storage_badge = (
            "<span style='background:#28a745;color:white;padding:2px 8px;"
            "border-radius:8px;font-size:10px;margin-left:6px;'>"
            "💾 RAM + File</span>"
            if file_ok
            else "<span style='background:#ffc107;color:#333;padding:2px 8px;"
            "border-radius:8px;font-size:10px;margin-left:6px;'>"
            "💾 RAM only (file lỗi)</span>"
        )

        stats_html = ""
        if stats:
            stats_html = "<div class='activity-stats'>"
            for mod_name, s in sorted(stats.items()):
                err = s.get("error", 0)
                warn = s.get("warning", 0)
                total = s.get("total", 0)
                color = (
                    "#dc3545" if err > 0
                    else ("#ffc107" if warn > 0 else "#28a745")
                )
                stats_html += (
                    f"<div class='activity-stat-card' "
                    f"style='border-left-color:{color};'>"
                    f"  <div class='activity-stat-name'>"
                    f"📦 {self._escape(mod_name)}</div>"
                    f"  <div class='activity-stat-counts'>"
                    f"    <span style='color:#dc3545;'>❌ {err}</span>"
                    f"    <span style='color:#ffc107;'>⚠️ {warn}</span>"
                    f"    <span style='color:#888;'>Σ {total}</span>"
                    f"  </div>"
                    f"  <div class='activity-stat-last'>"
                    f"🕒 {self._escape(s.get('last') or '—')}</div>"
                    f"</div>"
                )
            stats_html += "</div>"

        filter_info = []
        if module_filter:
            filter_info.append(
                f"module=<b>{self._escape(module_filter)}</b>"
            )
        if severity_filter:
            filter_info.append(
                f"severity=<b>{self._escape(severity_filter)}</b>"
            )
        filter_html = (
            f"<div style='margin:12px 0;font-size:12px;color:#666;'>"
            f"🔎 Bộ lọc: "
            f"{', '.join(filter_info) if filter_info else 'không (tất cả)'}"
            f" · Tổng trong RAM: <b>{ram_size}</b> entry"
            f"{storage_badge}"
            f"</div>"
        )

        if not entries:
            entries_html = (
                "<div style='text-align:center;padding:30px;color:#888;'>"
                "📭 Chưa có lỗi/hoạt động nào được ghi nhận.<br>"
                "<span style='font-size:11px;'>Log sẽ xuất hiện khi: "
                "cài module lỗi · load module lỗi · handle() raise · "
                "WS disconnect · module bị block · user dừng task.</span>"
                "</div>"
            )
        else:
            rows = []
            for e in entries:
                sev = e.get("severity", "info")
                icon = (
                    "❌" if sev == "error"
                    else ("⚠️" if sev == "warning" else "ℹ️")
                )
                color = (
                    "#dc3545" if sev == "error"
                    else ("#ffc107" if sev == "warning" else "#17a2b8")
                )
                event_label = {
                    "init_error": "Lỗi khởi tạo",
                    "install_error": "Lỗi cài đặt",
                    "install_success": "Cài đặt OK",
                    "handle_error": "Lỗi xử lý",
                    "hang": "Treo (WS disconnect)",
                    "blocked": "Bị khóa",
                    "cancelled": "Bị dừng",
                    "returned_error": "Trả lỗi",
                }.get(e.get("event"), e.get("event") or "—")

                details_str = ""
                if e.get("details"):
                    try:
                        d = json.dumps(e["details"], ensure_ascii=False)
                        details_str = (
                            f"<div class='activity-details'>"
                            f"{self._escape(d)}</div>"
                        )
                    except Exception:
                        pass

                cmd_str = ""
                if e.get("command"):
                    cmd_str = (
                        f"<div class='activity-row-cmd'>"
                        f"⚙ {self._escape(e.get('command'))}</div>"
                    )

                rows.append(
                    f"<div class='activity-row' "
                    f"style='border-left-color:{color};'>"
                    f"  <div class='activity-row-header'>"
                    f"    <span class='activity-row-icon'>{icon}</span>"
                    f"    <span class='activity-row-module'>"
                    f"📦 {self._escape(e.get('module'))}</span>"
                    f"    <span class='activity-row-event' "
                    f"style='color:{color};'>"
                    f"      {self._escape(event_label)}"
                    f"    </span>"
                    f"    <span class='activity-row-time'>"
                    f"🕒 {self._escape(e.get('timestamp'))}</span>"
                    f"  </div>"
                    f"  <div class='activity-row-msg'>"
                    f"{self._escape(e.get('message'))}</div>"
                    f"  {cmd_str}"
                    f"  {details_str}"
                    f"</div>"
                )
            entries_html = "".join(rows)

        html = (
            "<style>"
            ".activity-stats{display:flex;flex-wrap:wrap;gap:8px;"
            "margin-bottom:14px;}"
            ".activity-stat-card{flex:1 1 180px;background:#f8f9fa;"
            "border-left:4px solid #888;border-radius:8px;padding:10px 12px;}"
            ".activity-stat-name{font-weight:600;color:#2c3e50;"
            "font-size:13px;margin-bottom:4px;}"
            ".activity-stat-counts{display:flex;gap:10px;font-size:12px;"
            "font-weight:600;margin-bottom:4px;}"
            ".activity-stat-last{font-size:11px;color:#888;}"
            ".activity-row{background:#fbfcff;border-left:4px solid #17a2b8;"
            "border-radius:8px;padding:10px 12px;margin-bottom:8px;}"
            ".activity-row-header{display:flex;flex-wrap:wrap;"
            "align-items:center;gap:8px;font-size:12px;margin-bottom:4px;}"
            ".activity-row-icon{font-size:16px;}"
            ".activity-row-module{font-weight:600;color:#2c3e50;}"
            ".activity-row-event{font-weight:600;}"
            ".activity-row-time{color:#888;margin-left:auto;font-size:11px;}"
            ".activity-row-msg{font-size:13px;color:#333;margin:4px 0;}"
            ".activity-row-cmd{font-family:monospace;font-size:11px;"
            "color:#666;}"
            ".activity-details{font-family:monospace;font-size:11px;"
            "color:#888;background:#f0f2f5;border-radius:4px;"
            "padding:4px 8px;margin-top:4px;word-break:break-all;}"
            "</style>"
            + stats_html
            + filter_html
            + entries_html
        )

        self.render_panel({
            "title": "📊 NHẬT KÝ HOẠT ĐỘNG MODULE",
            "html": html,
            "actions": [
                {
                    "label": "Xem lại",
                    "icon": "🔄",
                    "color": "secondary",
                    "command": "module_activity",
                    "params": {
                        "module": module_filter or "",
                        "severity": severity_filter or "",
                    },
                },
                {
                    "label": "Xoá nhật ký",
                    "icon": "🗑️",
                    "color": "danger",
                    "command": "clear_module_activity",
                    "params": {
                        "module": module_filter or "",
                        "confirmed": True,
                    },
                },
            ],
        })

        total_all = sum(s.get("total", 0) for s in stats.values())
        return {
            "status": "success",
            "type": "generic",
            "message": (
                f"📊 {len(entries)} entry hiển thị "
                f"(tổng {total_all} trong nhật ký)"
            ),
        }

    # ── clear_module_activity ────────────────────────────────────
    def _clear_activity(self, params):
        module_filter = params.get("module") or None
        confirmed = bool(params.get("confirmed", False))

        if not confirmed:
            scope = (
                f"module '<b>{self._escape(module_filter)}</b>'"
                if module_filter
                else "toàn bộ nhật ký"
            )
            self.render_panel({
                "title": "⚠️ XÁC NHẬN XOÁ NHẬT KÝ",
                "html": (
                    f"<div style='text-align:center;padding:16px;'>"
                    f"Bạn có chắc muốn xoá {scope}?"
                    f"<br><br>"
                    f"<span style='color:#888;font-size:12px;'>"
                    f"Hành động này không thể hoàn tác.</span>"
                    f"</div>"
                ),
                "actions": [
                    {
                        "label": "Xoá",
                        "icon": "🗑️",
                        "color": "danger",
                        "command": "clear_module_activity",
                        "params": {
                            "module": module_filter or "",
                            "confirmed": True,
                        },
                    },
                    {
                        "label": "Huỷ",
                        "icon": "✖️",
                        "color": "secondary",
                        "command": "module_activity",
                        "params": {},
                    },
                ],
            })
            return {
                "status": "success",
                "type": "generic",
                "message": "⚠️ Xác nhận xoá nhật ký?",
            }

        self.activity.clear(module=module_filter)
        self.context.logger.write(
            f"[INSTALLER] 🗑️ Đã xoá nhật ký module: "
            f"{module_filter or 'toàn bộ'}"
        )

        return self._show_activity(params)

    # ── Helpers ──────────────────────────────────────────────────
    @staticmethod
    def _escape(text):
        if text is None:
            return ""
        s = str(text)
        return (
            s.replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;")
            .replace("'", "&#39;")
        )

    @staticmethod
    def _peek_module(path):
        desc, cmds = "", []
        try:
            with open(path, "r", encoding="utf-8", errors="replace") as f:
                for line in f:
                    ls = line.strip()
                    if not desc and ls.startswith("description"):
                        after = ls.split("=", 1)
                        if len(after) == 2:
                            v = after[1].strip().strip('"').strip("'")
                            desc = v
                    if ls.startswith("commands"):
                        after = ls.split("=", 1)
                        if len(after) == 2:
                            raw = after[1].strip()
                            import re
                            cmds = re.findall(
                                r'["\']([^"\']+)["\']', raw
                            )
                            break
        except Exception:
            pass
        return desc, cmds

    def _schedule_restart(self, delay):
        def _do():
            time.sleep(delay)
            try:
                self.context.logger.write(
                    "[INSTALLER] 🔄 Đang khởi động lại..."
                )
                try:
                    self.activity.flush()
                except Exception:
                    pass
                self.context.reset_state()
                cleanup_orphan_processes()
                try:
                    if os.path.exists(SESSION_LOCK):
                        os.remove(SESSION_LOCK)
                except Exception:
                    pass
                try:
                    sys.stdout.flush()
                    sys.stderr.flush()
                except Exception:
                    pass
                time.sleep(0.5)
                os.execv(sys.executable, [sys.executable] + sys.argv)
            except Exception as e:
                try:
                    self.context.logger.write(
                        f"[INSTALLER] execv lỗi ({e}) → fallback subprocess"
                    )
                    subprocess.Popen(
                        [sys.executable] + sys.argv,
                        cwd=os.getcwd(),
                        start_new_session=True,
                        close_fds=True,
                    )
                    time.sleep(1.0)
                except Exception:
                    pass
                os._exit(1)

        threading.Thread(target=_do, daemon=False).start()

    def _err(self, msg):
        self.context.logger.write(f"[INSTALLER] ✗ {msg}")
        return {"status": "error", "type": "generic", "message": msg}