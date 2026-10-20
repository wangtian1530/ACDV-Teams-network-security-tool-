# tinhnang/core/utils.py
import os
import time
import shutil
import importlib.util


def dongcong(ports):
    """Giải phóng các port đang bận."""
    for port in ports:
        try:
            os.system(f"fuser -k {port}/tcp 2>/dev/null")
        except Exception:
            pass
    time.sleep(1)


def cleanup_orphan_processes():
    """
    Kill mọi process rác của lần chạy trước + clear temp files.
    Gọi ở: start (nếu session cũ), shutdown, WS disconnect.
    """
    for p in ["wpa_supplicant", "pixiewps", "wpa_cli", "wpa_passphrase",
              "iw", "iwlist", "nmap", "nc", "ping", "hostapd", "dnsmasq"]:
        os.system(f"su -c 'pkill -9 {p}' 2>/dev/null")

    os.system("su -c 'rm -rf /data/local/tmp/wpa_ctrl_*' 2>/dev/null")
    os.system("su -c 'rm -rf /tmp/wpa_ctrl_*' 2>/dev/null")
    os.system("su -c 'rm -rf /data/local/tmp/wpa_supplicant*' 2>/dev/null")
    os.system("su -c 'rm -rf /tmp/pixiewps*' 2>/dev/null")
    os.system("su -c 'svc wifi enable' 2>/dev/null")


def check_and_setup_env(chay_terminal, config=None):
    """
    Kiểm tra môi trường theo config.
    - config = None → tự lấy singleton
    """
    if config is None:
        from .config import get_config
        config = get_config()

    print("\n[+] Đang kiểm tra đường băng (Environment Check)...")
    print(f"[*] Config file : {config.config_path}")
    print(f"[*] Interface   : {config.interface}")
    print(f"[*] Server      : {config.host}:{config.port} (WS: {config.ws_port})")

    # Apply env (PYTHONPATH, LD_LIBRARY_PATH)
    config.apply_environment()

    # ---- Binaries ----
    missing_bins = []
    for pkg in config.binaries:
        if shutil.which(pkg) is None:
            missing_bins.append(pkg)
            print(f"[-] Thiếu binary: {pkg}")
        else:
            print(f"[OK] Binary: {pkg}")
    if missing_bins:
        print(f"[!] Cài thiếu bằng: pkg install {' '.join(missing_bins)}")

    # ---- Python libs ----
    missing_libs = []
    for lib in config.libraries:
        if importlib.util.find_spec(lib) is None:
            missing_libs.append(lib)
            print(f"[-] Thiếu lib: {lib}")
        else:
            print(f"[OK] Python Lib: {lib}")
    if missing_libs:
        print(f"[!] Cài lib thiếu bằng: pip install {' '.join(missing_libs)}")

    # ---- Root status ----
    if config.is_root:
        print(f"[OK] Quyền hạn: ROOT ({config.root_method}) — mở khoá toàn bộ")
    else:
        print(f"[!] Quyền hạn: KHÔNG ROOT (method={config.root_method})")
        print("[!] Chỉ các module không cần root mới chạy được.")
        print("[!] Chạy lại tool bằng 'sudo python main.py' để mở khoá.")

    print("[+] Tuyệt Vời! Mời Vào.... !\n")
    return True