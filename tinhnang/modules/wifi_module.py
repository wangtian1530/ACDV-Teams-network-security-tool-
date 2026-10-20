# tinhnang/modules/wifi_module.py
import os
import time
import re
import random
import subprocess
from collections import Counter

from .base_module import BaseModule
from ..core.terminal import chay_terminal
from ..core.config import get_config


class WifiManager:
    def __init__(self, interface=None):
        self.terminal = chay_terminal
        self.interface = interface or get_config().interface
        self.original_mac = None
        self.target_ssid = None

    def _generate_random_mac(self):
        first_byte = random.choice([0x00, 0x02, 0x04, 0x06, 0x08, 0x0A, 0x0C, 0x0E,
            0x10, 0x12, 0x14, 0x16, 0x18, 0x1A, 0x1C, 0x1E, 0x20, 0x22, 0x24, 0x26,
            0x28, 0x2A, 0x2C, 0x2E, 0x30, 0x32, 0x34, 0x36, 0x38, 0x3A, 0x3C, 0x3E,
            0x40, 0x42, 0x44, 0x46, 0x48, 0x4A, 0x4C, 0x4E, 0x50, 0x52, 0x54, 0x56,
            0x58, 0x5A, 0x5C, 0x5E, 0x60, 0x62, 0x64, 0x66, 0x68, 0x6A, 0x6C, 0x6E,
            0x70, 0x72, 0x74, 0x76, 0x78, 0x7A, 0x7C, 0x7E])
        mac_bytes = [first_byte] + [random.randint(0x00, 0xFF) for _ in range(5)]
        return ":".join(f"{b:02x}" for b in mac_bytes)

    def get_current_mac(self):
        try:
            result = subprocess.getoutput(f"ip link show {self.interface} | grep ether")
            match = re.search(r"ether ([0-9a-f:]{17})", result)
            if match: return match.group(1)
        except Exception:
            pass
        return None

    def change_mac(self, new_mac=None):
        if new_mac is None: new_mac = self._generate_random_mac()
        print(f"[*] Đổi MAC: {self.get_current_mac()} → {new_mac}")
        os.system(f"ip link set {self.interface} down")
        time.sleep(1)
        os.system(f"ip link set {self.interface} address {new_mac}")
        time.sleep(1)
        os.system(f"ip link set {self.interface} up")
        time.sleep(2)
        current = self.get_current_mac()
        if current == new_mac:
            print(f"[+] Đổi MAC thành công: {current}")
            return True
        print(f"[-] Đổi MAC thất bại. MAC hiện tại: {current}")
        return False

    def restore_mac(self):
        if self.original_mac:
            os.system(f"ip link set {self.interface} down")
            time.sleep(1)
            os.system(f"ip link set {self.interface} address {self.original_mac}")
            time.sleep(1)
            os.system(f"ip link set {self.interface} up")
            return True
        return False

    def set_status(self, mode):
        state = "enable" if mode == 1 else "disable"
        self.terminal.run_cmd(f"svc wifi {state}")
        self.terminal.dang_chay()
        return {"type": "wifi_control", "status": "on" if mode == 1 else "off"}

    def scan(self):
        os.system("su -c 'settings put global wifi_scan_throttle_enabled 0'")
        self.terminal.run_cmd("cmd wifi list-scan-results")
        wifi_list = []
        full_log = []
        if self.terminal._process is None:
            return {"type": "scan", "success": False, "message": "Terminal chưa sẵn sàng"}
        try:
            if self.terminal._process.stdout:
                while True:
                    line = self.terminal._process.stdout.readline()
                    if line: full_log.append(line.strip())
                    if not line and self.terminal._process.poll() is not None: break
                    time.sleep(0.01)
        except Exception as e:
            return {"type": "error", "message": f"Lỗi đọc log: {str(e)}"}

        for line in full_log:
            line = line.replace("📡", "").strip()
            if not line or "BSSID" in line or "---" in line: continue
            parts = line.split()
            if len(parts) >= 5:
                try:
                    bssid = parts[0]; freq = parts[1]
                    rssi_raw = parts[2].split("(")[0]; rssi_dbm = int(rssi_raw)
                    signal_percent = max(0, min(100, 2 * (rssi_dbm + 100)))
                    remaining = " ".join(parts[4:])
                    match = re.search(r"(.*?)\s*(\[.*\])$", remaining)
                    if match:
                        ssid = match.group(1).strip(); raw_flags = match.group(2).strip()
                    else:
                        ssid = remaining.strip(); raw_flags = "[OPEN]"
                    wifi_list.append({
                        "ssid": ssid if ssid else "Mạng ẩn", "bssid": bssid,
                        "freq": freq, "rssi": rssi_dbm, "quality": f"{signal_percent}%",
                        "security": self._parse_security(raw_flags),
                        "is_wps": "WPS" in raw_flags, "vendor": self._get_vendor(bssid),
                        "band": "5GHz" if int(freq) > 4000 else "2.4GHz", "flags": raw_flags,
                    })
                except Exception:
                    continue
        wifi_list = sorted(wifi_list, key=lambda x: x["rssi"], reverse=True)
        return {"type": "scan_results", "success": True, "count": len(wifi_list),
                "data": {i: v for i, v in enumerate(wifi_list)}}

    def restart(self):
        self.set_status(0)
        time.sleep(2)
        return self.set_status(1)

    def _get_current_connected_ssid(self):
        try:
            result = subprocess.getoutput("cmd wifi status")
            match = re.search(r'SSID:\s*"([^"]*)"', result)
            if match:
                ssid = match.group(1)
                if ssid and ssid != "<unknown ssid>": return ssid
            result2 = subprocess.getoutput("dumpsys wifi")
            match2 = re.search(r"mWifiInfo.*?SSID:\s*([^\s,]+)", result2)
            if match2:
                ssid = match2.group(1).strip('"')
                if ssid and ssid != "<unknown" and ssid != "ssid>": return ssid
            result3 = subprocess.getoutput(f"iw dev {self.interface} link")
            match3 = re.search(r"SSID:\s*(.+)", result3)
            if match3:
                ssid = match3.group(1).strip()
                if ssid: return ssid
        except Exception as e:
            print(f"[!] Lỗi lấy SSID: {e}")
        return None

    def _verify_connection(self, target_ssid):
        time.sleep(1)
        check_ip = subprocess.getoutput(f"ip addr show {self.interface}")
        if "inet " not in check_ip: return False
        current_ssid = self._get_current_connected_ssid()
        if current_ssid is None: return False
        if current_ssid == target_ssid: return True
        self._disconnect_current_network()
        return False

    def _disconnect_current_network(self):
        try:
            current_ssid = self._get_current_connected_ssid()
            if current_ssid:
                os.system(f"su -c 'cmd wifi forget-network \"{current_ssid}\"'")
                time.sleep(1)
                os.system("su -c 'svc wifi disable'")
                time.sleep(2)
                os.system("su -c 'svc wifi enable'")
                time.sleep(3)
        except Exception as e:
            print(f"[!] Lỗi ngắt kết nối: {e}")

    def _disable_auto_reconnect(self):
        try:
            os.system("su -c 'settings put global wifi_wakeup_available 0'")
            os.system("su -c 'settings put global wifi_scan_always_enabled 0'")
            return True
        except Exception:
            return False

    def _enable_auto_reconnect(self):
        try:
            os.system("su -c 'settings put global wifi_wakeup_available 1'")
            os.system("su -c 'settings put global wifi_scan_always_enabled 1'")
        except Exception:
            pass

    def connect(self, ssid, password=None, security="wpa2"):
        self.target_ssid = ssid
        self._disable_auto_reconnect()
        self._disconnect_current_network()
        time.sleep(2)

        if not password or security == "open":
            cmd = f"su -c 'cmd wifi connect-network \"{ssid}\" open'"
        else:
            safe_password = password.replace("'", "'\\''")
            cmd = f"su -c 'cmd wifi connect-network \"{ssid}\" {security} \"{safe_password}\"'"

        self.terminal.run_cmd(cmd)
        max_attempts = 10
        for i in range(max_attempts):
            time.sleep(1)
            current_ssid = self._get_current_connected_ssid()
            if current_ssid == ssid:
                check_ip = subprocess.getoutput(f"ip addr show {self.interface}")
                if "inet " in check_ip:
                    self._enable_auto_reconnect()
                    return True
            elif current_ssid is not None and current_ssid != ssid:
                os.system(f"su -c 'cmd wifi forget-network \"{current_ssid}\"'")
                time.sleep(1)
                if i < max_attempts - 2: self.terminal.run_cmd(cmd)
                else: break

        final_check = self._verify_connection(ssid)
        self._enable_auto_reconnect()
        return final_check

    def connect_auto(self, result_data, ten, auto_change_mac=True):
        max_retries = 3; retry_count = 0
        while retry_count < max_retries:
            if retry_count > 0 and auto_change_mac:
                self.change_mac()
                self.restart()
                time.sleep(3)
            if not result_data or "data" not in result_data: return False
            raw_data = result_data["data"]
            for key, entry in raw_data.items():
                if len(entry) >= 3 and entry[1] == ten:
                    password = entry[2]; security = entry[3] if len(entry) > 3 else "wpa2"
                    if self.connect(ten, password, security):
                        return {"ssid": ten, "password": password, "mac_changed": retry_count > 0}
                    break
            all_passwords = []; password_ids = {}; security_for_target = "wpa2"
            for key, entry in raw_data.items():
                if len(entry) >= 3:
                    pwd = entry[2]; sec = entry[3] if len(entry) > 3 else "wpa2"
                    if pwd not in password_ids: password_ids[pwd] = key
                    all_passwords.append(pwd)
                    if entry[1] == ten: security_for_target = sec
            if not all_passwords: return False
            counts = Counter(all_passwords)
            optimized_pass_list = sorted(counts.keys(), key=counts.get, reverse=True)
            tried = set()
            for password in optimized_pass_list:
                if password in tried: continue
                tried.add(password)
                pwd_id = password_ids.get(password, "unknown")
                if self.connect(ten, password, security_for_target):
                    self._luu_wifi(ten, password, security_for_target)
                    return {"ssid": ten, "password": password, "password_id": pwd_id, "mac_changed": retry_count > 0}
            retry_count += 1
        return None

    def _luu_wifi(self, ssid, password, security):
        try:
            from ..core.file_manager import FileManager
            fm = FileManager()
            kho_bau = fm.read_file("networks.acdv")
            current_data = {}
            if kho_bau.get("status") == "ACDV-Files" and kho_bau.get("data"):
                current_data = kho_bau["data"]
            ssid_exists = False
            for key, entry in current_data.items():
                if len(entry) >= 2 and entry[1] == ssid:
                    ssid_exists = True
                    break
            if ssid_exists: return
            new_key = str(len(current_data))
            fake_bssid = "00:00:00:00:00:00"
            current_data[new_key] = [fake_bssid, ssid, password, security]
            fm.save_file("networks.acdv", current_data, data_type="OBJ", who_am_i="WIFI_SCANNER")
        except Exception as e:
            print(f"[!] Lỗi lưu database: {e}")

    def _parse_security(self, cap):
        cap = cap.upper()
        if "WPA3" in cap: return "wpa3"
        if "WPA2" in cap: return "wpa2"
        if "WPA" in cap: return "wpa"
        if "WEP" in cap: return "wep"
        return "open"

    def _get_vendor(self, mac):
        prefix = mac.replace(":", "")[:6].upper()
        vendors = {"20BEB4": "TP-Link", "22BEB4": "TP-Link", "CC81DA": "ZTE/Viettel",
                   "84DBAC": "VNPT", "D807B6": "Tenda", "000C29": "VMware"}
        return vendors.get(prefix, "Router")


class WifiModule(BaseModule):
    name = "wifi"
    commands = ["scan", "connect_with_password", "auto_connect", "clear_all", "quit"]
    description = "Quét, kết nối WiFi và quản lý card mạng"

    version = "1.2.1"
    latest_version = "1.2.1"
    version_notes = "Trả partial kết quả khi cancel."

    def init(self):
        try:
            if self.context.wifi_manager is None:
                self.context.wifi_manager = WifiManager()  # dùng config.interface
            self.context.logger.write(
                f"[✓] WiFi Module v{self.version} đã sẵn sàng! "
                f"(iface={self.context.wifi_manager.interface})"
            )
        except Exception as e:
            self.context.logger.write(f"[✗] Lỗi init WiFi Module: {e}")

    def handle(self, command, params):
        try:
            self.check_cancel()
            if command == "scan": return self._handle_scan()
            if command == "connect_with_password": return self._handle_connect_with_password(params)
            if command == "auto_connect": return self._handle_auto_connect(params)
            if command == "clear_all": return self._handle_clear_all()
            if command == "quit": return self._handle_quit()
        except InterruptedError:
            self.context.logger.write("[!] WiFi task bị dừng")
            self.emit_progress(None)
            return {"status": "error", "type": "cancelled", "message": "WiFi task đã dừng"}
        except Exception as e:
            self.context.logger.write(f"[✗] WifiModule lỗi: {e}")
            return {"status": "error", "message": str(e), "type": "generic"}
        return {"status": "error", "message": f"Unknown: {command}", "type": "generic"}

    def _handle_scan(self):
        ctx = self.context
        ctx.scanning = True
        ctx.logger.write("[*] Đang quét WiFi...")
        self.emit_progress(10, "Khởi tạo quét WiFi")

        networks = []
        try:
            if not ctx.wifi_manager:
                ctx.wifi_manager = WifiManager()

            self.check_cancel()
            self.emit_progress(30, "Bật card WiFi")
            ctx.wifi_manager.set_status(1)
            time.sleep(2)

            self.check_cancel()
            self.emit_progress(50, "Đang quét access point")
            scan_result = ctx.wifi_manager.scan()

            self.check_cancel()
            self.emit_progress(70, "Đọc database")
            kho_bau = ctx.file_manager.read_file("networks.acdv")

            if not scan_result or not scan_result.get("success"):
                ctx.logger.write("[-] Không tìm thấy WiFi nào!")
                self.emit_progress(100, "Không có WiFi")
                return {"status": "success", "type": "networks", "networks": [],
                        "message": "Không tìm thấy mạng WiFi"}

            self.emit_progress(85, "Xử lý kết quả")
            for stt, info in scan_result.get("data", {}).items():
                ten_wifi = info.get("ssid", "Unknown")
                mac_wifi = info.get("bssid", "").upper()
                wps_status = info.get("is_wps", False)
                signal_info = info.get("quality", "N/A")
                security = info.get("security", "wpa2")

                has_password = False
                if kho_bau.get("status") == "ACDV-Files" and kho_bau.get("data"):
                    for k, v in kho_bau["data"].items():
                        if len(v) >= 2 and mac_wifi in v[0].upper():
                            has_password = True
                            break

                networks.append({
                    "stt": int(stt), "ssid": ten_wifi, "bssid": mac_wifi,
                    "wps_enabled": wps_status, "signal": signal_info,
                    "security": security, "has_password": has_password,
                })

            ctx.current_networks = networks
            self._write_network_list(networks)
            self.emit_progress(100, "Hoàn tất quét")
            return {"status": "success", "type": "networks", "networks": networks,
                    "message": f"Tìm thấy {len(networks)} mạng WiFi"}
        except InterruptedError:
            ctx.logger.write(f"[!] Quét WiFi dừng — trả {len(networks)} mạng đã quét")
            self.emit_progress(None)
            return {"status": "error", "type": "cancelled",
                    "networks": networks,
                    "message": f"Dừng — đã quét {len(networks)} mạng"}
        finally:
            ctx.scanning = False

    def _write_network_list(self, networks):
        header = "\n" + "=" * 90 + "\n"
        header += f"{'STT':<6} | {'Tên Wifi':<30} | {'BSSID (MAC)':<20} | {'WPS':<6} | {'Cường độ':<20} | {'Trạng thái':<12}\n"
        header += "=" * 90
        self.context.logger.write(header)
        for net in networks:
            stt = net.get("stt", 0)
            ten = net.get("ssid", "Unknown")
            mac = net.get("bssid", "")
            wps = "✅ Có" if net.get("wps_enabled") else "❌ Không"
            sig = net.get("signal", "N/A")
            tt = "[ĐÃ LƯU]" if net.get("has_password") else "[Mới]"
            ten_short = ten[:28] + "..." if len(ten) > 28 else ten
            self.context.logger.write(f"{stt:<6} | {ten_short:<30} | {mac:<20} | {wps:<6} | {sig:<20} | {tt:<12}")
        self.context.logger.write("=" * 90)

    def _handle_connect_with_password(self, params):
        ctx = self.context
        ctx.connecting = True
        network = params.get("network") or {}
        target_ssid = network.get("ssid", "?")
        target_bssid = network.get("bssid", "?")
        success_password = None
        success_source = None
        try:
            input_password = params.get("password", "")
            if not network:
                return {"status": "error", "message": "Thiếu thông tin mạng", "type": "generic"}
            security = network.get("security", "wpa2")

            ctx.logger.write(f"[*] BẮT ĐẦU KẾT NỐI: {target_ssid}")
            stored_passwords = self._get_all_stored_passwords(target_bssid)
            if stored_passwords:
                ctx.logger.write(f"[*] Thử {len(stored_passwords)} mật khẩu trong DB...")
                for idx, pwd in enumerate(stored_passwords, 1):
                    self.check_cancel()
                    ctx.logger.write(f"[*] Thử #{idx}/{len(stored_passwords)}...")
                    if ctx.wifi_manager and ctx.wifi_manager.connect(target_ssid, pwd, security):
                        success_password = pwd; success_source = "database"
                        break

            if not success_password and input_password:
                self.check_cancel()
                ctx.logger.write("[*] Thử mật khẩu từ client...")
                if ctx.wifi_manager and ctx.wifi_manager.connect(target_ssid, input_password, security):
                    success_password = input_password; success_source = "client"

            if success_password:
                self._luu_wifi(target_ssid, target_bssid, success_password, security)
                return {"status": "success", "type": "connect_result",
                        "message": f"Kết nối thành công tới {target_ssid}",
                        "password_source": success_source, "ssid": target_ssid}
            return {"status": "error", "type": "connect_result",
                    "message": "Kết nối thất bại - Tất cả mật khẩu đều không đúng"}
        except InterruptedError:
            msg = f"Kết nối {target_ssid} bị dừng"
            if success_password:
                msg += f" (đã thử được pass {success_source})"
            ctx.logger.write(f"[!] {msg}")
            return {"status": "error", "type": "cancelled",
                    "network": network, "ssid": target_ssid,
                    "tried_password": success_password, "message": msg}
        finally:
            ctx.connecting = False

    def _get_all_stored_passwords(self, bssid):
        passwords = []
        try:
            kho_bau = self.context.file_manager.read_file("networks.acdv")
            if kho_bau.get("status") == "ACDV-Files" and kho_bau.get("data"):
                for k, v in kho_bau["data"].items():
                    if len(v) >= 3 and bssid and bssid.upper() in v[0].upper():
                        passwords.append(v[2])
        except Exception as e:
            self.context.logger.write(f"[!] Lỗi đọc database: {e}")
        return passwords

    def _handle_auto_connect(self, params):
        ctx = self.context
        ctx.connecting = True
        network = params.get("network") or {}
        try:
            if not network:
                return {"status": "error", "message": "Thiếu thông tin mạng", "type": "generic"}
            target_ssid = network.get("ssid")
            kho_bau = ctx.file_manager.read_file("networks.acdv")
            if kho_bau.get("status") != "ACDV-Files" or not kho_bau.get("data"):
                return {"status": "error", "message": "Database trống", "type": "generic"}
            self.check_cancel()
            result = ctx.wifi_manager.connect_auto(kho_bau, target_ssid, auto_change_mac=True)
            if result and isinstance(result, dict) and result.get("ssid"):
                return {"status": "success", "type": "connect_result",
                        "message": f"Auto connect thành công tới {result['ssid']}"}
            return {"status": "error", "message": "Không thể kết nối tự động", "type": "generic"}
        except InterruptedError:
            return {"status": "error", "type": "cancelled",
                    "network": network, "message": f"Auto connect {network.get('ssid', '?')} bị dừng"}
        finally:
            ctx.connecting = False

    def _handle_clear_all(self):
        try:
            if self.context.wifi_manager:
                self.context.wifi_manager.restart()
                self.context.logger.write("[+] Đã giải phóng card WiFi!")
            return {"status": "success", "type": "generic", "message": "Đã giải phóng card WiFi"}
        except Exception as e:
            return {"status": "error", "message": str(e), "type": "generic"}

    def _handle_quit(self):
        try:
            os.system("su -c 'svc wifi enable'")
            if self.context.wifi_manager: self.context.wifi_manager.set_status(1)
            self.context.logger.write("[*] Đã bật lại WiFi")
            return {"status": "success", "type": "generic", "message": "Đã bật lại WiFi"}
        except Exception as e:
            return {"status": "error", "message": str(e), "type": "generic"}

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
            result = ctx.file_manager.save_file("networks.acdv", current_data, data_type="OBJ", who_am_i="WIFI_SCANNER")
            return bool(result and result.get("status"))
        except Exception as e:
            self.context.logger.write(f"[!] Lỗi lưu WiFi: {e}")
            return False