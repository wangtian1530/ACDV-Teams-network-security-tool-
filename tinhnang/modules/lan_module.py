# tinhnang/modules/lan_module.py
import os
import re
import time
import json
import shutil
import subprocess
import threading
import concurrent.futures
import xml.etree.ElementTree as ET

from .base_module import BaseModule


class NetworkScanner:
    """Quét LAN: ưu tiên nmap, fallback về nc/ping. Cache RAM."""

    _global_cache = {}
    _global_cache_lock = threading.Lock()

    def __init__(self, interface="wlan0"):
        self.interface = interface
        self.local_ip = None
        self.network_prefix = None

    def _get_local_ip_and_network(self):
        try:
            result = subprocess.getoutput(f"ip addr show {self.interface} | grep 'inet '")
            match = re.search(r"inet (\d+\.\d+\.\d+\.\d+)/(\d+)", result)
            if match:
                self.local_ip = match.group(1)
                cidr = int(match.group(2))
                ip_parts = self.local_ip.split(".")
                if cidr >= 24:
                    self.network_prefix = f"{ip_parts[0]}.{ip_parts[1]}.{ip_parts[2]}."
                elif cidr >= 16:
                    self.network_prefix = f"{ip_parts[0]}.{ip_parts[1]}."
                else:
                    self.network_prefix = f"{ip_parts[0]}."
                return True
            print("[!] Không tìm thấy địa chỉ IP hợp lệ")
            return False
        except Exception as e:
            print(f"[!] Lỗi lấy IP: {e}")
            return False

    def _get_service_name(self, port):
        services = {
            20: "FTP-data", 21: "FTP", 22: "SSH", 23: "Telnet", 25: "SMTP",
            53: "DNS", 80: "HTTP", 110: "POP3", 111: "RPC", 135: "RPC",
            139: "NetBIOS", 143: "IMAP", 443: "HTTPS", 445: "SMB",
            993: "IMAPS", 995: "POP3S", 1433: "MSSQL", 1521: "Oracle",
            3306: "MySQL", 3389: "RDP", 5432: "PostgreSQL", 5900: "VNC",
            6379: "Redis", 8080: "HTTP-Alt", 8443: "HTTPS-Alt",
            27017: "MongoDB",
        }
        return services.get(port, "Unknown")

    def _get_os_guess(self, ports):
        if 445 in ports or 139 in ports: return "Windows (SMB share)"
        if 22 in ports and 3306 in ports: return "Linux Server (SSH + MySQL)"
        if 22 in ports and 5432 in ports: return "Linux Server (SSH + PostgreSQL)"
        if 3389 in ports: return "Windows RDP"
        if 5900 in ports: return "VNC Server"
        if 80 in ports or 443 in ports: return "Web Server"
        return "Unknown"

    def _merge_host_into_cache(self, ip, new_data):
        with self._global_cache_lock:
            if ip in self._global_cache:
                existing = self._global_cache[ip]
                merged = sorted(set(existing.get("open_ports", [])) | set(new_data.get("open_ports", [])))
                existing["open_ports"] = merged
                existing["total_open"] = len(merged)
                port_map = {p["port"]: p for p in existing.get("port_details", [])}
                for p in new_data.get("port_details", []):
                    port_map[p["port"]] = p
                existing["port_details"] = list(port_map.values())
                existing["os_guess"] = self._get_os_guess(merged)
                existing["hits"] = existing.get("hits", 1) + 1
            else:
                new_data["hits"] = 1
                self._global_cache[ip] = new_data

    def get_cache(self):
        with self._global_cache_lock:
            return dict(self._global_cache)

    def clear_cache(self):
        with self._global_cache_lock:
            self._global_cache.clear()

    def _parse_nmap_xml(self, xml_data):
        """
        Trả về dict hosts nếu parse OK.
        Trả về {} nếu scan hoàn tất nhưng không có host nào.
        Trả về None nếu XML không hợp lệ (bị kill giữa chừng).
        """
        hosts = {}
        if not xml_data or not xml_data.strip():
            return None
        try:
            root = ET.fromstring(xml_data)
        except Exception:
            if "<nmaprun" in xml_data and "</nmaprun>" in xml_data:
                return {}
            return None

        for host in root.findall("host"):
            status = host.find("status")
            if status is None or status.get("state") != "up":
                continue
            ip = None
            for addr in host.findall("address"):
                if addr.get("addrtype") in ("ipv4", "ipv6"):
                    ip = addr.get("addr")
                    break
            if not ip:
                continue
            open_ports = []
            port_details = []
            for port in host.findall("ports/port"):
                state = port.find("state")
                if state is None or state.get("state") != "open":
                    continue
                try:
                    portid = int(port.get("portid"))
                except Exception:
                    continue
                service_el = port.find("service")
                svc_name = "Unknown"
                if service_el is not None:
                    product = service_el.get("product", "") or ""
                    version = service_el.get("version", "") or ""
                    name = service_el.get("name", "") or ""
                    full = f"{product} {version}".strip()
                    svc_name = full or name or self._get_service_name(portid)
                open_ports.append(portid)
                port_details.append({"port": portid, "service": svc_name, "status": "open"})
            hosts[ip] = {
                "ip": ip, "open_ports": sorted(open_ports),
                "port_details": port_details, "total_open": len(open_ports),
                "os_guess": self._get_os_guess(open_ports), "hits": 1,
            }
        return hosts

    def scan_network_nmap(self, mode="normal"):
        if not self._get_local_ip_and_network():
            return {"success": False, "error": "Không thể xác định IP"}

        if not shutil.which("nmap"):
            print("[!] Không có nmap → dùng nc/ping dự phòng")
            fast = mode == "fast"
            return self.scan_network(fast_mode=fast, scan_rounds=2 if fast else 3)

        cidr = f"{self.network_prefix}0/24"
        print(f"[*] Nmap scan ({mode}): {cidr}")

        mode_args = {
            "fast": ["-T4", "-F", "--open"],
            "normal": ["-T4", "--open"],
            "thorough": ["-T4", "-sV", "-sC", "--open", "--version-intensity", "5"],
            "stealth": ["-sS", "-T2", "--open"],
        }
        args = ["nmap"] + mode_args.get(mode, mode_args["normal"]) + ["-oX", "-", cidr]

        try:
            proc = subprocess.run(args, capture_output=True, text=True, timeout=900)
            xml_data = proc.stdout
        except subprocess.TimeoutExpired:
            return {"success": False, "error": "Nmap timeout (>15 phút)"}
        except Exception as e:
            return {"success": False, "error": f"Nmap lỗi: {e}"}

        hosts = self._parse_nmap_xml(xml_data)
        if hosts is None:
            return {"success": False, "error": "Nmap bị ngắt hoặc trả về dữ liệu không hợp lệ"}

        # ✅ Chỉ clear cache khi có kết quả hợp lệ
        with self._global_cache_lock:
            self._global_cache.clear()
            for ip, d in hosts.items():
                self._global_cache[ip] = d

        total_open = sum(r["total_open"] for r in hosts.values())
        hosts_with_open = sum(1 for r in hosts.values() if r["total_open"] > 0)

        return {
            "success": True, "my_ip": self.local_ip,
            "network_prefix": self.network_prefix, "total_hosts": len(hosts),
            "hosts": hosts, "scan_mode": mode, "scanner": "nmap",
            "total_open_ports": total_open, "hosts_with_open": hosts_with_open,
        }

    def _ping_host(self, ip, timeout=1):
        try:
            cmd = f"ping -c 1 -W {timeout} {ip} > /dev/null 2>&1"
            return os.system(cmd) == 0
        except Exception:
            return False

    def _ping_host_parallel(self, ip_list, timeout=1, max_workers=20):
        active = []
        def ping_single(ip):
            return ip if self._ping_host(ip, timeout) else None
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as ex:
            futures = {ex.submit(ping_single, ip): ip for ip in ip_list}
            for f in concurrent.futures.as_completed(futures):
                r = f.result()
                if r: active.append(r)
        return active

    def _scan_ports_parallel(self, ip, ports, timeout=1, max_workers=10):
        open_ports = []
        def scan_one(port):
            try:
                cmd = f"timeout {timeout} nc -zv -w {timeout} {ip} {port} 2>&1"
                result = subprocess.getoutput(cmd)
                if "succeeded" in result or "Connected" in result or "open" in result:
                    return port
            except Exception:
                pass
            return None
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as ex:
            futures = {ex.submit(scan_one, p): p for p in ports}
            for f in concurrent.futures.as_completed(futures):
                r = f.result()
                if r: open_ports.append(r)
        return sorted(open_ports)

    def scan_network(self, ports=None, fast_mode=True, ping_timeout=1, port_timeout=1, scan_rounds=3, reset_cache=False):
        print(f"\n🔍 QUÉT LAN ({scan_rounds} vòng, cache RAM)")
        if reset_cache:
            self.clear_cache()
        if not self._get_local_ip_and_network():
            return {"success": False, "error": "Không thể xác định IP"}

        if ports is None:
            if fast_mode:
                ports = [21, 22, 23, 25, 53, 80, 110, 135, 139, 143, 443, 445, 993, 995, 1433, 1521, 3306, 3389, 5432, 5900, 6379, 8080, 8443, 27017]
            else:
                ports = list(range(1, 101)) + [135, 139, 443, 445, 3306, 3389, 5432, 5555, 5900, 6379, 8000, 8080, 8443, 8888, 27017]

        ip_list = [f"{self.network_prefix}{i}" for i in range(1, 255) if f"{self.network_prefix}{i}" != self.local_ip]

        for round_num in range(scan_rounds):
            active = self._ping_host_parallel(ip_list, timeout=ping_timeout, max_workers=30)
            cached = set(self.get_cache().keys())
            new_hosts = [h for h in active if h not in cached]
            if not new_hosts: continue

            def scan_host(host):
                open_ports = self._scan_ports_parallel(host, ports, timeout=port_timeout, max_workers=15)
                pd = [{"port": p, "service": self._get_service_name(p), "status": "open"} for p in open_ports]
                return host, {
                    "ip": host, "open_ports": open_ports,
                    "port_details": pd, "total_open": len(open_ports),
                    "os_guess": self._get_os_guess(open_ports),
                }

            with concurrent.futures.ThreadPoolExecutor(max_workers=5) as ex:
                futures = {ex.submit(scan_host, h): h for h in new_hosts}
                for f in concurrent.futures.as_completed(futures):
                    try:
                        host_ip, result = f.result()
                        self._merge_host_into_cache(host_ip, result)
                    except Exception as e:
                        print(f"[!] Lỗi quét: {e}")

        final_hosts = self.get_cache()
        total_open = sum(r["total_open"] for r in final_hosts.values())
        hosts_with_open = sum(1 for r in final_hosts.values() if r["total_open"] > 0)
        return {
            "success": True, "my_ip": self.local_ip,
            "network_prefix": self.network_prefix, "total_hosts": len(final_hosts),
            "hosts": final_hosts, "scanner": "nc-fallback",
            "scanned_ports": len(ports), "scan_rounds": scan_rounds,
            "total_open_ports": total_open, "hosts_with_open": hosts_with_open,
        }

    def scan_specific_host(self, target_ip, ports=None, port_timeout=1):
        print(f"\n[*] Đang quét host: {target_ip}")
        if shutil.which("nmap"):
            try:
                proc = subprocess.run(["nmap", "-T4", "-sV", "-sC", "--open", "-oX", "-", target_ip], capture_output=True, text=True, timeout=600)
                hosts = self._parse_nmap_xml(proc.stdout)
                if hosts and target_ip in hosts:
                    data = hosts[target_ip]
                    self._merge_host_into_cache(target_ip, data)
                    return {"success": True, **data}
            except Exception as e:
                print(f"[!] Nmap specific host lỗi: {e}")

        if ports is None:
            ports = [21, 22, 23, 25, 53, 80, 443, 3306, 3389, 5432, 5900, 8080, 8443]
        if not self._ping_host(target_ip, timeout=2):
            return {"success": False, "error": "Host không phản hồi ping"}

        open_ports = self._scan_ports_parallel(target_ip, ports, timeout=port_timeout, max_workers=20)
        port_details = [{"port": p, "service": self._get_service_name(p), "status": "open"} for p in open_ports]
        result_data = {
            "ip": target_ip, "open_ports": open_ports,
            "port_details": port_details, "total_open": len(open_ports),
            "os_guess": self._get_os_guess(open_ports),
        }
        self._merge_host_into_cache(target_ip, result_data)
        return {"success": True, **result_data}

    def quick_scan(self, ping_timeout=1, port_timeout=1):
        if shutil.which("nmap"):
            return self.scan_network_nmap(mode="fast")
        ports = [80, 443, 8080, 8443]
        return self.scan_network(ports=ports, fast_mode=True, ping_timeout=ping_timeout, port_timeout=port_timeout, scan_rounds=2)

    def save_results(self, scan_results, filename="scan_results.json"):
        if not scan_results.get("success"): return False
        try:
            scan_results["timestamp"] = time.strftime("%Y-%m-%d %H:%M:%S")
            with open(filename, "w", encoding="utf-8") as f:
                json.dump(scan_results, f, indent=2, ensure_ascii=False)
            return True
        except Exception:
            return False


class LanModule(BaseModule):
    name = "lan"
    commands = ["lan_scan", "lan_quick_scan", "scan_specific_host"]
    description = "Quét mạng LAN + cổng mở (ưu tiên Nmap)"

    version = "1.2.1"
    latest_version = "1.2.1"
    version_notes = "Trả partial kết quả khi cancel."

    category = "lan"
    category_label = "Mạng LAN"
    category_icon = "🌐"
    ui_buttons = [
        {"id": "lan_quick", "label": "LAN Nhanh", "icon": "⚡", "color": "success", "command": "lan_scan", "params": {"mode": "fast"}},
        {"id": "lan_normal", "label": "LAN Cơ Bản", "icon": "🌐", "color": "info", "command": "lan_scan", "params": {"mode": "normal"}},
        {"id": "lan_thorough", "label": "LAN Sâu (nmap -sV)", "icon": "🔬", "color": "warning", "command": "lan_scan", "params": {"mode": "thorough"}},
        {"id": "lan_stealth", "label": "LAN Ẩn (SYN)", "icon": "🥷", "color": "secondary", "command": "lan_scan", "params": {"mode": "stealth"}},
    ]

    def init(self):
        try:
            if self.context.network_scanner is None:
                self.context.network_scanner = NetworkScanner(interface="wlan0")
            self.context.logger.write(f"[✓] LAN Module v{self.version} đã sẵn sàng!")
        except Exception as e:
            self.context.logger.write(f"[✗] Lỗi init LAN: {e}")

    def handle(self, command, params):
        ctx = self.context
        ctx.lan_scanning = True
        ctx.scanning = True
        try:
            self.check_cancel()
            if command == "lan_scan":
                return self._handle_lan_scan(params)
            if command == "lan_quick_scan":
                return self._handle_lan_quick_scan()
            if command == "scan_specific_host":
                return self._handle_scan_specific(params)
        except InterruptedError:
            return self._return_partial_from_cache("LAN scan")
        except Exception as e:
            if self.is_cancelled():
                return self._return_partial_from_cache("LAN scan")
            ctx.logger.write(f"[✗] Lỗi LAN Module: {e}")
            return {"status": "error", "type": "generic", "message": str(e)}
        finally:
            ctx.lan_scanning = False
            ctx.scanning = False

    def _return_partial_from_cache(self, label):
        ctx = self.context
        cache = ctx.network_scanner.get_cache() if ctx.network_scanner else {}
        safe_hosts = {}
        for ip, hd in cache.items():
            safe_hosts[ip] = {
                "ip": hd.get("ip", ip), "open_ports": hd.get("open_ports", []),
                "total_open": hd.get("total_open", 0), "os_guess": hd.get("os_guess", "Unknown"),
                "port_details": hd.get("port_details", []), "hits": hd.get("hits", 1),
            }
        msg = f"{label} dừng giữa chừng — trả {len(safe_hosts)} thiết bị đã quét được"
        ctx.logger.write(f"[!] {msg}")
        self.emit_progress(None)
        return {
            "status": "error", "type": "cancelled",
            "hosts": safe_hosts, "total_hosts": len(safe_hosts),
            "my_ip": getattr(ctx.network_scanner, "local_ip", None) if ctx.network_scanner else None,
            "network_prefix": getattr(ctx.network_scanner, "network_prefix", None) if ctx.network_scanner else None,
            "scanner": "nmap", "message": msg,
        }

    def _handle_lan_scan(self, params):
        ctx = self.context
        if not ctx.network_scanner:
            ctx.network_scanner = NetworkScanner(interface="wlan0")

        mode = params.get("mode", "normal")
        label = {"fast": "Nhanh (nmap -F)", "normal": "Cơ bản (nmap top 1000)",
                 "thorough": "Sâu (nmap -sV -sC)", "stealth": "Ẩn (nmap -sS -T2)"}.get(mode, mode)

        ctx.logger.write(f"[*] Đang quét LAN chế độ: {label} ...")
        self.emit_progress(5, f"Bắt đầu quét LAN ({label})")
        self.check_cancel()
        self.emit_progress(20, "Nmap đang chạy...")

        try:
            result = ctx.network_scanner.scan_network_nmap(mode=mode)
        except Exception:
            if self.is_cancelled():
                return self._return_partial_from_cache(f"LAN scan [{label}]")
            raise

        self.emit_progress(90, "Đang xử lý kết quả...")
        self.check_cancel()

        if not result.get("success"):
            if self.is_cancelled():
                return self._return_partial_from_cache(f"LAN scan [{label}]")
            return {"status": "error", "type": "generic", "message": result.get("error", "Quét thất bại")}

        safe_hosts = {}
        for ip, hd in result.get("hosts", {}).items():
            safe_hosts[ip] = {
                "ip": hd.get("ip"), "open_ports": hd.get("open_ports", []),
                "total_open": hd.get("total_open", 0), "os_guess": hd.get("os_guess", "Unknown"),
                "port_details": hd.get("port_details", []), "hits": hd.get("hits", 1),
            }
        ctx.logger.write(f"[+] Tìm thấy {result.get('total_hosts', 0)} thiết bị ({label})")
        self.emit_progress(100, "Hoàn tất")
        return {
            "status": "success", "type": "lan_devices",
            "hosts": safe_hosts, "total_hosts": result.get("total_hosts", 0),
            "my_ip": result.get("my_ip"), "network_prefix": result.get("network_prefix"),
            "scanner": result.get("scanner", "nmap"), "scan_mode": mode,
            "message": f"Tìm thấy {result.get('total_hosts', 0)} thiết bị [{label}]",
        }

    def _handle_lan_quick_scan(self):
        ctx = self.context
        if not ctx.network_scanner:
            ctx.network_scanner = NetworkScanner(interface="wlan0")
        ctx.logger.write("[*] Quét nhanh LAN...")
        try:
            result = ctx.network_scanner.quick_scan()
        except Exception:
            if self.is_cancelled():
                return self._return_partial_from_cache("LAN quick scan")
            raise
        if not result.get("success"):
            if self.is_cancelled():
                return self._return_partial_from_cache("LAN quick scan")
            return {"status": "error", "type": "generic", "message": result.get("error", "Quét thất bại")}
        safe_hosts = {}
        for ip, hd in result.get("hosts", {}).items():
            safe_hosts[ip] = {
                "ip": hd.get("ip"), "open_ports": hd.get("open_ports", []),
                "total_open": hd.get("total_open", 0), "os_guess": hd.get("os_guess", "Unknown"),
                "port_details": hd.get("port_details", []),
            }
        return {
            "status": "success", "type": "lan_devices",
            "hosts": safe_hosts, "total_hosts": result.get("total_hosts", 0),
            "my_ip": result.get("my_ip"),
            "message": f"Tìm thấy {result.get('total_hosts', 0)} thiết bị",
        }

    def _handle_scan_specific(self, params):
        ctx = self.context
        target_ip = params.get("target_ip")
        if not target_ip:
            return {"status": "error", "type": "generic", "message": "Thiếu IP"}
        if not ctx.network_scanner:
            ctx.network_scanner = NetworkScanner(interface="wlan0")
        ports = params.get("ports", None)
        ctx.logger.write(f"[*] Đang quét host: {target_ip}...")
        self.check_cancel()
        try:
            result = ctx.network_scanner.scan_specific_host(target_ip, ports)
        except Exception:
            if self.is_cancelled():
                return {
                    "status": "error", "type": "cancelled",
                    "hosts": {}, "total_hosts": 0,
                    "message": f"Quét {target_ip} dừng giữa chừng",
                }
            raise
        if not result.get("success"):
            return {"status": "error", "type": "generic", "message": result.get("error", "Quét thất bại")}
        return {
            "status": "success", "type": "lan_devices",
            "host": result, "hosts": {target_ip: result},
            "message": f"Quét {target_ip} xong: {result.get('total_open', 0)} cổng mở",
        }