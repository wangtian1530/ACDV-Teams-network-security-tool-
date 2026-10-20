from .base_module import BaseModule
import subprocess

# Cấu hình mặc định tự sinh vào data/modules/ping_module.json
DEFAULT_CONFIG = {
    "description": "Module kiểm tra kết nối IP nội bộ và Internet thông qua lệnh ping",
    "settings": {
        "default_internal_ip": "192.168.1.1",
        "internet_target": "8.8.8.8",
        "count": 3,
        "timeout": 5
    }
}

class PingModule(BaseModule):
    name = "ping_module"
    commands = ["ping_network"]
    description = "Kiểm tra kết nối IP nội bộ & Internet"
    version = "1.0.0"
    latest_version = "1.0.0"
    category = "tools"
    category_label = "Công cụ"
    category_icon = "🌐"
    
    # Khai báo nút tự hiển thị trên Web UI
    ui_buttons = [
        {
            "id": "ping_network_btn",
            "label": "Kiểm Tra Ping Mạng",
            "icon": "📶",
            "color": "info",
            "command": "ping_network",
            "params": {},
            "prompt": {
                "field": "internal_ip",
                "message": "Nhập IP nội bộ cần ping (Bỏ trống để dùng mặc định):",
                "default": "",
                "hint": "Ví dụ: 192.168.1.1 hoặc 192.168.0.1"
            }
        }
    ]

    def init(self):
        # Nạp resource JSON riêng cho module
        self.resource.load(default_config=DEFAULT_CONFIG)
        self.context.logger.write("[✓] PingModule đã được khởi tạo thành công!")

    def handle(self, command, params):
        if command != "ping_network":
            return {"status": "error", "type": "generic", "message": "Lệnh không hợp lệ."}

        # Lấy tham số từ người dùng hoặc file config resource
        internal_ip = params.get("internal_ip") or self.resource.get("default_internal_ip", "192.168.1.1")
        internet_target = self.resource.get("internet_target", "8.8.8.8")
        count = self.resource.get("count", 3)

        results = {
            "internal_ip": internal_ip,
            "internet_target": internet_target,
            "internal_result": None,
            "internet_result": None
        }

        try:
            # 1. Tiến trình bắt đầu
            self.emit_progress(10, "Đang chuẩn bị công cụ ping...")
            self.check_cancel()

            # 2. Ping IP nội bộ
            self.emit_progress(30, f"Đang ping IP nội bộ: {internal_ip}...")
            internal_ok, internal_output = self._run_ping(internal_ip, count)
            results["internal_result"] = {"success": internal_ok, "output": internal_output}
            self.check_cancel()

            # 3. Ping kiểm tra Internet
            self.emit_progress(70, f"Đang kiểm tra Internet ({internet_target})...")
            internet_ok, internet_output = self._run_ping(internet_target, count)
            results["internet_result"] = {"success": internet_ok, "output": internet_output}
            self.check_cancel()

            # 4. Hoàn tất
            self.emit_progress(100, "Hoàn tất kiểm tra mạng!")

            # Render giao diện riêng (Module Panel) lên Main Result Section
            panel_html = f"""
                <div style="font-family: monospace; font-size: 13px;">
                    <div style="margin-bottom: 10px; padding: 8px; background: rgba(0,0,0,0.1); border-radius: 4px;">
                        <b>🏠 IP Nội Bộ ({internal_ip}):</b> 
                        <span style="color: {'#2ecc71' if internal_ok else '#e74c3c'}; font-weight: bold;">
                            {'[ KẾT NỐI TỐT ]' if internal_ok else '[ KHÔNG PHẢN HỒI ]'}
                        </span>
                    </div>
                    <pre style="background: #1e1e1e; color: #dcdcdc; padding: 10px; border-radius: 5px; overflow-x: auto;">{internal_output}</pre>
                    
                    <div style="margin: 15px 0 10px 0; padding: 8px; background: rgba(0,0,0,0.1); border-radius: 4px;">
                        <b>🌍 Internet ({internet_target}):</b> 
                        <span style="color: {'#2ecc71' if internet_ok else '#e74c3c'}; font-weight: bold;">
                            {'[ CÓ INTERNET ]' if internet_ok else '[ MẤT INTERNET ]'}
                        </span>
                    </div>
                    <pre style="background: #1e1e1e; color: #dcdcdc; padding: 10px; border-radius: 5px; overflow-x: auto;">{internet_output}</pre>
                </div>
            """

            self.render_panel({
                "title": "📊 KẾT QUẢ KIỂM TRA MẠNG & INTERNET",
                "html": panel_html
            })

            return {
                "status": "success",
                "type": "generic",
                "message": f"Nội bộ: {'OK' if internal_ok else 'FAIL'} | Internet: {'OK' if internet_ok else 'FAIL'}",
                "data": results
            }

        except InterruptedError:
            self.emit_progress(None)
            return {
                "status": "error",
                "type": "cancelled",
                "message": "Quá trình ping đã bị người dùng dừng lại.",
                "data": results
            }

    def _run_ping(self, host, count=3):
        """Hàm thực thi lệnh ping hệ thống"""
        # Cấu lệnh ping trên Linux/Termux (-c: số gói, -W: thời gian timeout giây)
        cmd = ["ping", "-c", str(count), "-W", "3", host]
        try:
            res = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            success = (res.returncode == 0)
            output = res.stdout.strip() if success else (res.stdout.strip() + "\n" + res.stderr.strip())
            return success, output if output else "Không nhận được phản hồi từ host."
        except subprocess.TimeoutExpired:
            return False, "Lỗi: Quá thời gian chờ phản hồi (Timeout)."
        except Exception as e:
            return False, f"Lỗi hệ thống khi chạy ping: {str(e)}"

    def cleanup(self):
        pass
