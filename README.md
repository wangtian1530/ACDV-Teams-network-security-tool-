📘 README.md — Updated to v3.6.0

 đây là file README.md đầy đủ, đã cập nhật cho hệ thống Config mới (GUI cài đặt + root detection qua sudo + quyền hạn theo lệnh):

```markdown
📘 ACDV-Teams WiFi Security Tool — Tài liệu đầy đủ

Version: 3.6.0 | Platform: Android (Termux + Root) | License: Educational

---

📖 Mục lục

1. Giới thiệu
2. Tính năng nổi bật
3. Kiến trúc tổng quan
4. Cài đặt
5. Sử dụng
6. Cấu trúc thư mục & Data Directory
6.5 ⭐ Cấu hình Tool (data/config.json) — GUI Cài đặt
7. Hệ thống Plugin
8. Hệ thống Resource
9. UI động — Module tự khai báo nút
10. Màn hình Main Result duy nhất — DOM sạch
11. ⭐ Hệ thống thông báo mới — Toast + Ticker + Log Modal
12. Progress Bar & Modal Input
13. Module Panel — UI riêng của module
14. ⭐ Cancel Partial — Trả kết quả dở dang
15. ⭐ Nhật ký Module — Activity Log (RAM-first)
16. Cơ chế Auto-Reset
17. Xử lý mất WebSocket & Module Blocking
18. Giao thức WebSocket & REST API
19. Định dạng file .acdv
20. Hướng dẫn viết Plugin
21. Debugging & Testing
22. Roadmap
23. Changelog
24. Đóng góp
25. Quick Start
26. Cảnh báo pháp lý

---

1. 🎯 Giới thiệu

ACDV-Teams WiFi Security Tool là công cụ kiểm thử bảo mật mạng WiFi dành cho thiết bị Android đã root, chạy trên Termux. Điểm nổi bật:

- 🖥️ Web UI hiện đại giao tiếp real-time qua WebSocket
- 🎨 UI động — Module tự khai báo nút, màu, danh mục → không cần sửa HTML/JS
- 📊 Single Main Result Screen — mọi kết quả module hiển thị tập trung 1 nơi, DOM sạch
- 📈 Progress Bar % — tiến trình thực hiện hiển thị trực quan
- 💬 Modal Input dùng chung — thay thế window.prompt() xấu
- 🧩 Module Panel — module có giao diện riêng, render trong khung main
- 🔔 Toast notifications — thay terminal log, chỉ hiện sự kiện quan trọng
- 📋 Log Modal — xem lịch sử đầy đủ khi cần, không chiếm màn hình
- 📡 Status Ticker — dòng trạng thái luôn cập nhật, không chiếm chỗ
- ⏹️ Cancel Partial — dừng giữa chừng vẫn trả kết quả đến đâu trả đến đó
- 🗂️ Nhật ký Module — RAM-first activity log, ghi mọi lỗi/hoạt động module
- 🛡️ Phân quyền theo lệnh — Root mở khoá hết, không Root chỉ chạy lệnh an toàn
- ⚙️ ⭐ GUI Cài đặt — chỉnh sửa toàn bộ cấu hình qua web (card mạng, port, env, root, strict mode...)
- 🔄 Auto-Reset session — tắt tool mở lại luôn sạch sẽ
- 🛡️ Chống treo WebSocket — tự kill process, block module treo nhiều lần
- 📱 Console mode cho người dùng Termux truyền thống
- 🔌 Kiến trúc Plugin động — thêm tính năng chỉ bằng cách drop 1 file .py
- 🗄️ Database mã hoá .acdv với fingerprint riêng, XOR + SHA256
- 🌐 Nmap tích hợp với 4 chế độ quét LAN
- 📂 Data Directory tập trung — mọi runtime data vào data/
- 🎁 Hệ thống Resource — mỗi module có file JSON riêng khai báo tài nguyên

Công cụ được thiết kế cho pentest hợp pháp — kiểm tra bảo mật mạng WiFi của chính bạn, hoặc trong môi trường được uỷ quyền.

---

2. ✨ Tính năng nổi bật

🔍 Quét & phân tích

Tính năng | Mô tả
---|---
WiFi Scanner | Quét mạng WiFi xung quanh: SSID, BSSID, cường độ, WPS, bảo mật
LAN Scanner (Nmap) | 4 chế độ: Nhanh (-F), Cơ bản (top 1000), Sâu (-sV -sC), Ẩn (-sS -T2). Fallback nc/ping khi thiếu nmap
Dirb Scanner | Dò thư mục/file ẩn trên web server. Wordlist tự nạp từ data/wordlists/

🔓 Tấn công & kết nối

Tính năng | Mô tả
---|---
WPS Pixie Dust | Tấn công WPS dùng lỗ hổng Pixie Dust
Auto Connect | Tự động thử mật khẩu từ database, đổi MAC nếu bị chặn
Connect w/ Password | Kết nối thủ công, xác minh đúng SSID

⚙️ Cấu hình & Phân quyền ⭐ v3.6.0

Tính năng | Mô tả
---|---
GUI Cài đặt | Modal ⚙️ Cài đặt — sửa network, environment, permissions, modules, server qua web
File data/config.json | Tự sinh lần đầu, tự merge với default, reload/update qua API
Root detection qua sudo | Ưu tiên sudo → euid → su (theo yêu cầu)
Phân quyền theo lệnh | root_required_commands: danh sách lệnh cần root. Non-root sẽ bị chặn
Banner cảnh báo | Chạy non-root → banner vàng nhắc sudo
Nút khoá 🔒 | Lệnh cần root khi non-root → nút hiện 🔒 + tooltip + không click được
Strict mode | Tắt strict → cho phép chạy mọi lệnh (không khuyến nghị)
Restart required | Đổi network/env/permissions/server → banner "cần restart" + hỏi restart

🛡️ Bảo mật & ổn định

Tính năng | Mô tả
---|---
Single Main Result + DOM sạch | clearMainResult() clear sạch trước mỗi module mới — không phình DOM
⭐ Toast Notifications | Thay terminal log — chỉ hiện sự kiện quan trọng (thành công/lỗi/cảnh báo)
⭐ Status Ticker | Dòng trạng thái luôn cập nhật (1 dòng), màu đổi theo loại sự kiện
⭐ Log Modal | Lịch sử đầy đủ trong modal (giới hạn 500 dòng), mở khi cần
⭐ Cancel Partial | Dừng giữa chừng vẫn trả kết quả (LAN → cache, Dirb → found, WiFi → networks)
⭐ Nhật ký Module (RAM-first) | Ghi mọi lỗi/hoạt động module vào RAM + file — hoạt động cả khi tool chưa khởi động xong
Progress Bar % | Thanh tiến trình % hiển thị khi module chạy
Modal Input dùng chung | Modal đẹp, có hint, Enter/Esc
Module Panel | Module có thể gửi UI riêng render trong main result
Auto-Reset Session | File lock data/.session.lock — tắt tool mở lại → tự kill process rác
Chống treo WebSocket | WS disconnect giữa task → kill process + track hang
Retry thông minh | Client hỏi user có retry không, đếm số lần thử, block sau 3 lần
Database .acdv | Lưu WiFi đã crack với XOR + SHA256 + fingerprint 0xACDV
Đổi MAC ngẫu nhiên | Random MAC hợp lệ (unicast, không multicast)

---

3. 🏗️ Kiến trúc tổng quan

Sơ đồ luồng

```

┌────────────────────────────────────────────────────────────┐
│                     CLIENT (Browser / Mobile)              │
│   ┌──────────────┐  ┌───────────────┐  ┌─────────────────┐ │
│   │  HTTP GET /  │  │ GET /api/ui   │  │ WS :8081        │ │
│   │  templates   │  │ GET/POST      │  │ {cmd, params}   │ │
│   │              │  │ /api/config ⭐│  │                 │ │
│   └──────┬───────┘  └───────┬───────┘  └────────┬────────┘ │
│          │                  │                   │          │
│   ⭐ Toast  ⭐ Ticker  ⭐ Log Modal  ⭐ Config Modal (⚙️)   │
└──────────┼──────────────────┼───────────────────┼──────────┘
│                  │                   │
┌─────▼──────┐    ┌──────▼──────┐     ┌──────▼────────┐
│ HTTP Server│    │ HTTP Handler│     │ WS Server     │
│   :8080    │    │  /api/ui    │     │   :8081       │
│            │    │  /api/config│     │               │
└────────────┘    └──────┬──────┘     └───────┬───────┘
│                    │
┌──────▼───────┐     ┌──────▼────────┐
│  Registry    │     │process_command│
│ collect_ui() │     │   (ROUTING)   │
│              │     │  + cfg.can_run│ ⭐
└──────┬───────┘     └───────┬───────┘
│                     │
⭐ activity.log()  ⭐ activity.log()
(init_error)       (handle_error/hang/blocked/
cancelled/returned_error)
│                     │
▼                     ▼
┌──────────────────────────────────────┐
│  ModuleActivityLog (RAM-FIRST)       │
│  ├─ _buffer: list[dict]  ← PRIMARY   │
│  ├─ data/module_activity.json        │
│  │   ← BACKUP (best-effort)          │
│  └─ Singleton: get_activity_log()    │
└──────────────┬───────────────────────┘
│
┌──────────────▼─────────┐
│  ModuleRegistry (ĐỘNG) │
│  cmd → module instance │
│  + blocked_modules     │
└──────────────┬─────────┘
│
┌──────────────────┼───────────────┬─────────────┐
│                  │               │             │
┌──────▼───────┐  ┌───────▼──────┐  ┌─────▼─────┐ ┌───▼──────┐
│ WifiModule   │  │ WpsModule    │  │ LanModule │ │DirbModule│
└──────┬───────┘  └──────┬───────┘  └─────┬─────┘ └────┬─────┘
│                 │                │            │
└─────────────────┴────────────────┴────────────┘
│  CHẠY NGOÀI LUỒNG
│  + emit_progress() / render_panel()
│  + check_cancel() / return partial
┌───────▼────────┐
│  AppContext    │ ← chia sẻ state
│  + Logger      │
│  + FileManager │
└───────┬────────┘
│
┌───────▼────────┐
│  data/         │ ← MỌI RUNTIME DATA
│  ├─ config.json ⭐ (v3.6.0)
│  ├─ .session.lock
│  ├─ log        │
│  ├─ acdv       │
│  ├─ modules/   │
│  ├─ wordlists/ │
│  └─ module_activity.json
└────────────────┘

```

Tầng kiến trúc

```

┌────────────────────────────────────────────────────────────┐
│  TẦNG 1: PRESENTATION (UI)                                 │
│  ├── Web UI — WebSocket + REST /api/ui + /api/config ⭐     │
│  │   ⭐ Single Main Result Section (DOM sạch)               │
│  │   ⭐ Toast + Ticker + Log Modal                          │
│  │   ⭐ Config Modal (⚙️ Cài đặt) — v3.6.0                  │
│  │   ⭐ Progress Bar (%) + Modal Input + Module Panel       │
│  └── Console UI (main.py)                                  │
└────────────────────────┬───────────────────────────────────┘
┌────────────────────────▼───────────────────────────────────┐
│  TẦNG 2: TRANSPORT (Server)                                │
│  ├── HTTP Server  :8080 → templates, static, /api/ui,       │
│  │                        /api/versions, /api/config ⭐     │
│  └── WS Server    :8081 → JSON messages                    │
│      ⭐ disconnect → kill + hang tracking                   │
│      ⭐ check quyền root trước khi route (cfg.can_run)      │
└────────────────────────┬───────────────────────────────────┘
┌────────────────────────▼───────────────────────────────────┐
│  TẦNG 3: ORCHESTRATION (Backend)                           │
│  ├── WebSocketServer   → routing + broadcast + blocking    │
│  │   ⭐ check can_run(cmd) → trả permission_denied nếu cần  │
│  │   ⭐ ghi handle_error/hang/blocked/cancelled vào log     │
│  ├── ModuleRegistry    → dynamic load + UI config          │
│  │   ⭐ ghi init_error vào log                              │
│  ├── WiFiHTTPHandler   → templates + /api/ui + /api/config │
│  └── WiFiServer        → lifecycle + session lock          │
│      ⭐ detect_root (euid → sudo → su)                     │
└────────────────────────┬───────────────────────────────────┘
┌────────────────────────▼───────────────────────────────────┐
│  TẦNG 4: PLUGIN (Modules)                                  │
│  ├── WifiModule  → scan, connect, auto_connect             │
│  ├── WpsModule   → wps_attack                              │
│  ├── LanModule   → lan_scan (nmap 4 modes)                 │
│  ├── DirbModule  → web directory brute-force               │
│  └── ModuleInstaller → cài/xoá module                      │
│      ⭐ ghi install_error/install_success vào log           │
│      ⭐ đọc module_activity để hiển thị trong panel         │
│      ⭐ emit_progress() + render_panel()                    │
│      ⭐ Trả partial khi cancel                              │
└────────────────────────┬───────────────────────────────────┘
┌────────────────────────▼───────────────────────────────────┐
│  TẦNG 5: CORE (Shared)                                     │
│  ├── AppContext         → shared state + logger            │
│  ├── Config ⭐ v3.6.0   → data/config.json + root detect    │
│  ├── TerminalLogger     → data/terminal.log                │
│  ├── FileManager        → data/networks.acdv               │
│  ├── ModuleResource     → quản lý tài nguyên module (JSON) │
│  ├── ModuleActivityLog  → data/module_activity.json (RAM)  │
│  ├── paths.py           → nguồn chân lý MỌI path           │
│  └── utils              → dongcong, cleanup_orphan         │
└────────────────────────────────────────────────────────────┘

```

Nguyên tắc thiết kế

1. Module chạy NGOÀI luồng server — WebSocket không bị block
2. Định tuyến bằng type — Module trả {"status", "type", ...}, server đọc type để route
3. Nạp động — Registry tự quét tinhnang/modules/
4. Context dùng chung — AppContext chia sẻ logger, file_manager, wifi_manager
5. UI tự khai báo — Module tự quyết định nút / màu / danh mục
6. Data tập trung — Mọi runtime data vào data/
7. Resource JSON — Module khai báo tài nguyên riêng
8. Fault-tolerant — Session lock, hang tracking, module blocking
9. Real-time feedback — emit_progress() + render_panel()
10. DOM sạch — clearMainResult() clear sạch trước mỗi module mới
11. Partial return — Cancel giữa chừng vẫn trả kết quả dở dang
12. Rõ ràng — Mỗi bước log rõ ràng, có lý do, không im lặng
13. RAM-first activity log — Log hoạt động/lỗi module luôn hoạt động
14. ⭐ Config tập trung — mọi cấu hình vào data/config.json, GUI edit được

---

4. 💻 Cài đặt

Yêu cầu

- Android đã root (Magisk / SuperSU)
- Termux (F-Droid version)
- Python 3.9+
- Package: nmap, iw, wpa-supplicant, pixiewps, net-tools, tsu

Cài đặt nhanh

```bash
# 1. Cấp quyền storage
termux-setup-storage

# 2. Cài package hệ thống
pkg update && pkg upgrade -y
pkg install python nmap iw wpa-supplicant pixiewps net-tools tsu root-repo -y

# 3. Cài Python libs
pip install websockets requests psutil

# 4. Clone project
git clone https://github.com/your-repo/acdv-wifi-tool.git
cd acdv-wifi-tool

# 5. Chạy (lần đầu sẽ tự tạo data/ + data/config.json)
python main.py
```

Lần đầu chạy tự tạo

```
data/
├── config.json            ← ⭐ v3.6.0 — cấu hình tool (auto sinh từ DEFAULT_CONFIG)
├── .session.lock          ← session lock (auto-reset)
├── terminal.log           ← log
├── networks.acdv          ← database (auto-migrate nếu có ở root cũ)
├── module_activity.json   ← nhật ký lỗi/hoạt động module
├── modules/               ← config riêng mỗi module
├── wordlists/             ← wordlist dùng chung
├── scripts/               ← script phụ
└── cache/                 ← cache runtime
```

---

5. 🚀 Sử dụng

Menu chính

```
==================================================
      ACDV-Teams WiFi Connect Tool
==================================================
  Phiên bản  : 3.6.0
  Tính năng  : Quét WiFi, Kết nối WPS (Pixie Dust)
  Thiết bị   : (Rooted)
==================================================

[*] Data directory: /data/data/com.termux/files/home/acdv-wifi-tool/data
[1] Khởi động Server (Web + WebSocket)
[2] Vào Console Mode (Termux)
[3] Thoát
Chọn chế độ (1/2/3):
```

Chế độ Web Server (Khuyến nghị)

Chọn [1], mở browser cùng mạng LAN:

```
http://<IP-điện-thoại>:8080
```

WebSocket tự động kết nối ws://<IP>:8081.

Layout UI mới (v3.6.0)

```
┌──────────────────────────────────────────────────┐
│ 🔐 ACDV-Teams WiFi Security Tool                 │
├──────────────────────────────────────────────────┤
│ ⭐ STATUS BAR:                                    │
│  ● Đã kết nối | ⚙️ Sẵn sàng  [📋 Log]  [⚙️ Cài đặt] │
├──────────────────────────────────────────────────┤
│ ⚠️ (nếu non-root) Banner vàng nhắc chạy sudo      │
├──────────────────────────────────────────────────┤
│ [Menu nav] 📦 Tất cả | 🌐 LAN | 🧰 Tools | ...    │
│ [Nút cố định] 📡 Quét WiFi | 🔄 Giải phóng | ...  │
│ [Nút module]  🌐 LAN Nhanh | 🔍 Dirb | ...        │
│ ⭐ Nút cần ROOT hiện 🔒 + không click được        │
├──────────────────────────────────────────────────┤
│ 📶 Mạng WiFi Phát Hiện (click để chọn)           │
│ 🖧 Thiết Bị Trong Mạng LAN (click xem chi tiết)  │
├──────────────────────────────────────────────────┤
│ 🔑 Mật khẩu WiFi: [........] 🔐 Kết Nối | ⚡ WPS │
├──────────────────────────────────────────────────┤
│ 📊 MAIN RESULT SECTION (DUY NHẤT, DOM sạch)      │
└──────────────────────────────────────────────────┘

     ┌──── 🔔 TOAST ────┐   ┌──── ⚙️ CONFIG MODAL ────┐
     │ ✅ Kết nối OK    │   │ 🌐 Mạng                 │
     │ ⚠️ Cảnh báo      │   │  Card: [wlan0]          │
     │ ❌ Lỗi           │   │  Port: [8080]           │
     └──────────────────┘   │ 📦 Môi trường           │
                            │ 🔐 Quyền (root detection)│
                            │ 🛠️ Root commands         │
                            │ 🖥️ Server config          │
                            │      [💾 Lưu] [Huỷ]     │
                            └─────────────────────────┘
```

Chế độ Console

Chọn [2] → dùng menu số để quét và kết nối.

Chạy port tùy chỉnh (CLI)

```bash
python tinhnang/server.py 9090          # HTTP:9090, WS:9091
python tinhnang/server.py 9090 0.0.0.0  # Chỉ định cả host
```

⭐ Hoặc đổi qua GUI ⚙️ Cài đặt (khuyến nghị — không cần restart CLI)

Chạy từ BẤT KỲ đâu

Nhờ tinhnang/core/paths.py dùng os.path.abspath(file):

```bash
# Tất cả đều OK, data/ luôn nằm cùng project
python main.py
cd /sdcard && python ~/acdv-wifi-tool/main.py
cd /tmp && python /full/path/to/main.py
```

---

6. 📂 Cấu trúc thư mục & Data Directory

Cấu trúc project

```
acdv-wifi-tool/
├── main.py                          # Entry point
├── pws.py                           # Core WPS attack logic
├── README.md                        # File này
│
├── data/                            # 🎯 MỌI RUNTIME DATA (auto-tạo)
│   ├── config.json                  # ⭐ v3.6.0 — cấu hình tool
│   ├── .session.lock                # Session lock
│   ├── networks.acdv                # Database WiFi (mã hoá)
│   ├── networks.acdv.backup         # Backup tự động
│   ├── terminal.log                 # Log file
│   ├── module_activity.json         # Nhật ký lỗi/hoạt động module
│   ├── modules/                     # Config riêng từng module
│   │   ├── dirb.json
│   │   ├── wifi.json
│   │   ├── lan.json
│   │   └── wps.json
│   ├── wordlists/                   # Wordlist dùng chung
│   │   ├── README.txt
│   │   ├── vietnam.txt
│   │   └── dirb/
│   ├── scripts/                     # Script phụ
│   └── cache/                       # Cache runtime
│
├── templates/                       # HTML templates
│   ├── index.html                   # ⭐ + config modal
│   └── 404.html
├── static/                          # CSS / JS
│   ├── style.css                    # ⭐ + .config-section, .config-row
│   └── script.js                    # ⭐ + showConfigModal, saveConfigFromModal
│
└── tinhnang/                        # Package chính
    ├── __init__.py
    ├── chuanbi.py
    ├── WifiMaster.py
    │
    ├── core/                        # 🧠 Lõi dùng chung
    │   ├── paths.py                 # SESSION_LOCK, CONFIG_FILE ⭐
    │   ├── config.py ⭐ v3.6.0      # Config class + get_config() + detect_root()
    │   ├── resource_manager.py
    │   ├── module_activity.py       # ModuleActivityLog — RAM-first
    │   ├── terminal.py
    │   ├── file_manager.py
    │   ├── logger.py
    │   ├── context.py
    │   └── utils.py                 # cleanup_orphan_processes()
    │
    ├── modules/                     # 🔌 PLUGIN MODULES
    │   ├── base_module.py           # + emit_progress() + render_panel() + check_cancel()
    │   ├── wifi_module.py           # ⭐ Trả partial khi cancel
    │   ├── wps_module.py            # ⭐ Trả partial khi cancel
    │   ├── lan_module.py            # ⭐ Trả partial từ cache khi cancel
    │   ├── dirb_module.py           # ⭐ Trả found + checked khi cancel
    │   └── module_installer.py      # ⭐ Log install_error/install_success + đọc activity
    │
    ├── backend/                     # 🌐 Server
    │   ├── registry.py              # ⭐ Log init_error + collect_ui_config có requires_root/can_run
    │   ├── websocket_handler.py     # ⭐ Log handle_error/hang/blocked/cancelled + check can_run
    │   ├── http_handler.py          # ⭐ + GET/POST /api/config
    │   └── server.py                # session lock + detect_root qua config
    │
    ├── cong_cu.py
    └── server.py
```

Nguyên tắc Data Directory

Loại Nơi lưu Ai quản lý
⭐ Config tool data/config.json core/config.py
Log data/terminal.log core/logger.py
Database chính data/networks.acdv core/file_manager.py
Session lock data/.session.lock backend/server.py
Nhật ký module data/module_activity.json core/module_activity.py
Config module data/modules/<name>.json core/resource_manager.py
Wordlist data/wordlists/ Module tự khai báo pattern
Script phụ data/scripts/ Module tự khai báo
Cache runtime data/cache/ Module tự khai báo

File .gitignore đề xuất

```
data/
__pycache__/
*.pyc
*.log
*.acdv
*.backup
*.json
.session.lock
.vscode/
.idea/
```

---

6.5 ⭐ Cấu hình Tool — data/config.json (GUI Cài đặt) — v3.6.0

Mục đích

Tập trung MỌI cấu hình runtime vào 1 file duy nhất, có thể chỉnh qua:

1. GUI web (nút ⚙️ Cài đặt) — khuyến nghị
2. Sửa trực tiếp data/config.json
3. CLI (main.py / server.py với args)

Không còn hardcode card mạng, port, host, danh sách lệnh cần root...

Cấu trúc data/config.json (DEFAULT_CONFIG)

```json
{
  "network": {
    "interface": "wlan0",
    "host": "0.0.0.0",
    "port": 8080
  },
  "environment": {
    "binaries": ["nmap", "iw", "wpa-supplicant", "pixiewps", "net-tools"],
    "libraries": ["requests", "psutil"],
    "lib_paths": [],
    "python_path": ""
  },
  "permissions": {
    "check_method": "sudo",
    "strict_mode": true
  },
  "modules": {
    "root_required_commands": [
      "wps_attack",
      "connect_with_password",
      "auto_connect",
      "scan",
      "lan_scan",
      "lan_quick_scan",
      "scan_specific_host",
      "clear_all",
      "quit"
    ]
  },
  "server": {
    "max_clients": 1,
    "ws_ping_interval": 20,
    "ws_ping_timeout": 60
  }
}
```

Ý nghĩa từng field

network.*

Field Mô tả Restart?
interface Card mạng (wlan0, wlan1, ...) ✅ Có
host Bind host (0.0.0.0 = mọi interface) ✅ Có
port HTTP port (WS = port + 1) ✅ Có

environment.*

Field Mô tả Restart?
binaries Danh sách binary cần cho check_and_setup_env() ✅ Có
libraries Danh sách Python lib cần có ✅ Có
python_path Nếu cài lib ngoài (PYTHONPATH) ✅ Có
lib_paths Nếu cần LD_LIBRARY_PATH ✅ Có

permissions.*

Field Mô tả Restart?
check_method sudo / euid / su / auto / none ✅ Có
strict_mode true = chặn lệnh cần root nếu non-root; false = cho phép chạy hết ✅ Có

modules.root_required_commands

Field Mô tả Restart?
root_required_commands Danh sách lệnh yêu cầu root. Command không nằm trong đây → non-root vẫn chạy được ❌ Không (áp dụng ngay)

server.*

Field Mô tả Restart?
max_clients Số WS client tối đa ✅ Có
ws_ping_interval Ping interval (s) ✅ Có
ws_ping_timeout Ping timeout (s) ✅ Có

Root detection — thứ tự ưu tiên

```
0. euid == 0              → root_method = "euid"     (fast-path)
   ↓ nếu không
1. sudo -n true           → root_method = "sudo"     ⭐ ưu tiên
   ↓ nếu không
2. su -c id               → root_method = "su"       (Android/Termux fallback)
   ↓ nếu không
   root_method = "none"   → is_root = False
```

Khi check_method = "none": bypass → luôn is_root = True (bỏ qua check — chỉ dùng khi dev).

Khi strict_mode = false: can_run() luôn True — non-root chạy được hết (không khuyến nghị).

API: GET /api/config

```bash
curl http://localhost:8080/api/config
```

Response:

```json
{
  "config": { ...toàn bộ config... },
  "is_root": false,
  "root_method": "none",
  "config_path": "/data/.../data/config.json",
  "restart_required_fields": [
    "network.host", "network.interface", "network.port",
    "environment.python_path", "environment.lib_paths",
    "permissions.check_method", "permissions.strict_mode",
    "server.max_clients", "server.ws_ping_interval", "server.ws_ping_timeout"
  ]
}
```

API: POST /api/config

```bash
curl -X POST http://localhost:8080/api/config \
  -H "Content-Type: application/json" \
  -d '{
    "network": {"interface": "wlan1", "port": 9090},
    "permissions": {"strict_mode": false}
  }'
```

Response (partial merge — chỉ gửi field cần đổi):

```json
{
  "status": "success",
  "changed_fields": ["network.interface", "network.port", "permissions.strict_mode"],
  "needs_restart": true,
  "is_root": false,
  "root_method": "none",
  "config": { ...full config sau merge... },
  "message": "Đã lưu config. Cần restart tool để áp dụng."
}
```

Lưu ý:

· Partial update — chỉ cần gửi field đổi, Config tự merge
· Nếu đổi permissions.* → server detect_root() lại ngay
· Nếu đổi bất kỳ field trong RESTART_REQUIRED_FIELDS → needs_restart: true, client sẽ hỏi có restart không

GUI ⚙️ Cài đặt — dùng thế nào?

1. Bấm nút ⚙️ Cài đặt trên status bar
2. Modal hiện ra với 5 section: 🌐 Mạng / 📦 Môi trường / 🔐 Quyền / 🛠️ Commands cần root / 🖥️ Server
3. Sửa field cần đổi
4. Bấm 💾 Lưu cấu hình
5. Nếu thay đổi cần restart → confirm hiện ra → bấm OK → tự restart

Bảo mật khi non-root

Server trả permission_denied khi client gọi lệnh cần root mà tool chạy non-root:

```json
{
  "type": "result",
  "command": "scan",
  "result": {
    "status": "error",
    "type": "permission_denied",
    "command": "scan",
    "requires_root": true,
    "message": "Lệnh 'scan' yêu cầu quyền ROOT. Chạy lại tool bằng 'sudo python main.py'..."
  }
}
```

Client xử lý:

· Toast đỏ hiển thị message
· Log error
· Không set kết quả (main result rỗng)

Nút UI cần root cũng hiển thị 🔒 + tooltip, click không gửi command.

---

7. 🔌 Hệ thống Plugin

Cách hoạt động

```
1. Server khởi động → ensure_dirs() + load config.json + detect_root()
       ↓
2. ModuleRegistry.load_from_package("tinhnang.modules")
   ⭐ Lỗi import/init → activity.log(init_error)
       ↓
3. pkgutil.iter_modules() quét TOÀN BỘ file .py trong modules/
       ↓
4. Với mỗi file: inspect tìm class con của BaseModule
       ↓
5. Khởi tạo instance, gọi init() (module tự load resource json)
   ⭐ init() raise → activity.log(init_error) — vẫn đăng ký module
       ↓
6. Đăng ký vào command_map
       ↓
7. Client gửi lệnh → registry.route(cmd) → check block → module.handle()
   ⭐ check cfg.can_run(cmd) trước → nếu không → trả permission_denied ⭐ v3.6.0
   ⭐ handle() raise → activity.log(handle_error)
   ⭐ handle() trả status=error → activity.log(returned_error)
   ⭐ InterruptedError → activity.log(cancelled)
       ↓
8. ⭐ Module gọi emit_progress() → server broadcast {type:"progress", pct, label}
   ⭐ Module gọi render_panel() → server broadcast {type:"module_panel", ...}
   ⭐ Module check_cancel() / is_cancelled() → raise InterruptedError nếu bị dừng
   ⭐ Module bắt InterruptedError → trả partial result
```

BaseModule — Interface chuẩn

```python
from .base_module import BaseModule

class MyModule(BaseModule):
    # === Core ===
    name = "my_module"
    commands = ["cmd1", "cmd2"]
    description = "Mô tả ngắn"

    # === Version ===
    version = "1.0.0"
    latest_version = "1.0.0"
    version_notes = ""

    # === UI Metadata (TÙY CHỌN) ===
    category = "tools"
    category_label = "Công cụ"
    category_icon = "🧰"
    ui_buttons = [...]

    def init(self):
        self.resource.load(default_config=MY_DEFAULT_CONFIG)

    def handle(self, command, params):
        try:
            self.check_cancel()
            self.emit_progress(0, "Bắt đầu...")
            # ... xử lý ...
            self.emit_progress(100, "Hoàn tất")
            self.render_panel({...})
            return {"status": "success", "type": "generic", "message": "OK"}
        except InterruptedError:
            self.emit_progress(None)
            return {"status": "error", "type": "cancelled", "message": "Đã dừng"}

    def cleanup(self):
        pass
```

Bảng type và định tuyến

type Server xử lý Field phụ
networks send_networks() networks: [...]
lan_devices send_lan_devices() hosts: {...}
dirb_result send_dirb_result() found: [...], target
connect_result send_result() ssid, password_source
wps_result send_result() wpa_psk (masked)
module_blocked send_result() module, hang_count
⭐ permission_denied send_result() command, requires_root, message
cancelled send_result() Partial fields
generic send_result() —
progress broadcast trực tiếp pct, label
module_panel broadcast trực tiếp title, panel

⭐ Phân quyền tự động ⭐ v3.6.0

Trước khi route command, server check cfg.can_run(cmd):

· Nếu root → cho chạy tất cả
· Nếu non-root + strict_mode = true → chặn các cmd trong root_required_commands
· Nếu non-root + strict_mode = false → cho chạy tất cả
· Nếu cmd không có trong danh sách root_required → non-root vẫn chạy được

Nên khai báo root_required_commands đầy đủ trong config.json để bảo vệ an toàn cho user non-root.

---

8. 🎁 Hệ thống Resource (tài nguyên module)

Ví dụ: data/modules/dirb.json

```json
{
  "description": "Quét thư mục/file ẩn trên web target",
  "files": {
    "wordlists": [
      "wordlists/*.txt",
      "wordlists/dirb/*.txt"
    ]
  },
  "settings": {
    "timeout": 6,
    "max_workers": 30,
    "user_agent": "Mozilla/5.0 (ACDV-Scanner)",
    "skip_status": ["000", "404", "500"],
    "use_builtin": true
  }
}
```

API self.resource

Method Mô tả Ví dụ
.load(default_config=...) Nạp JSON. Chưa có + có default → tạo file self.resource.load(DEFAULT_CONFIG)
.get(key, default) Đọc setting self.resource.get("timeout", 5)
.set(key, value) Ghi setting + save self.resource.set("last_url", url)
.file(key) Path tuyệt đối 1 file self.resource.file("config")
.resolve_all(key) List path từ glob self.resource.resolve_all("wordlists")
.read_text(key) Đọc nội dung text self.resource.read_text("readme")
.read_lines(key) Đọc thành list dòng self.resource.read_lines("ports")

---

9. 🎨 UI động — Module tự khai báo nút

Cấu trúc ui_buttons

```python
ui_buttons = [
    {
        "id":      "lan_quick",           # BẮT BUỘC — ID duy nhất
        "label":   "LAN Nhanh",           # BẮT BUỘC — text hiển thị
        "icon":    "⚡",                  # optional, default "🔧"
        "color":   "success",             # primary|secondary|success|info|warning|danger
        "command": "lan_scan",            # BẮT BUỘC — gửi tới server
        "params":  {"mode": "fast"},      # tham số mặc định
        "prompt":  {                       # nếu muốn hỏi user input (dùng modal)
            "field":   "url",
            "message": "Nhập URL:",
            "default": "",
            "hint":    "Gợi ý thêm"
        }
    },
]
```

⭐ Quyền hạn trên nút — v3.6.0

Server tự động tính requires_root và can_run cho từng nút dựa vào config:

```json
{
  "id": "lan_quick",
  "command": "lan_scan",
  "requires_root": true,
  "can_run": false
}
```

Client hiển thị:

· can_run: false + requires_root: true → nút hiện 🔒 + tooltip + click không gửi command
· can_run: true → nút bình thường
· Module bị block (hang ≥ 3 lần) → opacity 0.4 + tooltip "Module đang bị khóa"

Nút CỐ ĐỊNH (luôn hiển thị)

Nút Command ID
📡 Quét WiFi scan scanBtn
🔄 Giải phóng WiFi clear_all clearCardBtn
🔌 Bật lại WiFi quit quitBtn
🛑 TẮT TOOL shutdown shutdownBtn
🔐 Kết Nối connect_with_password connectBtn
⚡ WPS Attack wps_attack wpsBtn
🔄 Auto Connect auto_connect autoConnectBtn
⚙️ Cài đặt (modal, không gửi WS) configBtn ⭐

---

10. 📊 Màn hình Main Result duy nhất — DOM sạch

Vấn đề cũ

Trước v3.3, có 3 section kết quả riêng biệt (#vulnerabilitySection, #passwordSuggestionSection, #dirbSection) → khi chạy nhiều module liên tiếp, các section stack chồng lên nhau, DOM phình to theo thời gian.

Giải pháp v3.5+

Gộp thành 1 section duy nhất #mainResultSection + clear sạch DOM trước mỗi module mới:

```html
<div id="mainResultSection" class="vulnerability-section" style="display: none;">
    <div class="vuln-header">
        <h2 id="resultTitle">📊 KẾT QUẢ MODULE</h2>
        <button class="close-vuln" id="closeResultBtn">×</button>
    </div>
    <div id="moduleProgressWrap" style="display:none;">
        <div class="progress-bar-outer">
            <div class="progress-bar-inner" id="moduleProgressBar"></div>
        </div>
        <div class="progress-label" id="moduleProgressLabel">0%</div>
    </div>
    <div class="vuln-content" id="resultContent"></div>
</div>
```

Cơ chế DOM sạch

```javascript
function clearMainResult() {
    const section = document.getElementById('mainResultSection');
    const contentEl = document.getElementById('resultContent');
    if (contentEl) contentEl.innerHTML = '';      // ✅ Xoá sạch nội dung
    if (section) section.style.display = 'none';  // ✅ Ẩn section
    showProgress(null);                            // ✅ Reset progress
}

function setMainResult(titleHtml, contentHtml) {
    const titleEl = document.getElementById('resultTitle');
    const contentEl = document.getElementById('resultContent');
    contentEl.innerHTML = '';                     // ✅ Clear trước
    titleEl.innerHTML = titleHtml;
    contentEl.innerHTML = contentHtml;
    showProgress(null);
    document.getElementById('mainResultSection').style.display = 'block';
    section.scrollIntoView({ behavior: 'smooth', block: 'start' });
    bindModuleActionButtons(contentEl);
}
```

Khi nào clearMainResult() được gọi

Sự kiện Hàm gọi
wsClient.send(command, params) — command không non-blocking clearMainResult() trước khi gửi
User bấm 📡 Quét WiFi scanNetworks() gọi clearMainResult()
User bấm × đóng result closeResultBtn.onclick → clearMainResult()
User nhận kết quả mới setMainResult() tự clear trước khi set

Các loại kết quả hỗ trợ

Nguồn Hàm gọi Title
WPS/Password/Auto showVulnerabilityReport() 🚨 PHÂN TÍCH LỖ HỔNG BẢO MẬT
Dirb showDirbResults() 🔍 KẾT QUẢ QUÉT THƯ MỤC ẨN
Module bị block showBlockedResult() ⛔ MODULE BỊ KHÓA
⭐ Permission denied toast error (không set main result)
Module panel setMainResult() với renderModulePanel() Tùy module gửi
Cancelled handleCommandResult() Hiển thị partial data + message
⭐ Nhật ký Module module_activity command 📊 NHẬT KÝ HOẠT ĐỘNG MODULE

---

11. ⭐ Hệ thống thông báo mới — Toast + Ticker + Log Modal

Vấn đề cũ (v3.4)

Terminal log (.terminal-content) chiếm 350px chiều cao trên màn hình, cộng với các section khác → UI bị chật. Hơn nữa, log realtime cuộn liên tục gây rối mắt — user không phân biệt được đâu là sự kiện quan trọng.

Giải pháp v3.5+ — Thay terminal bằng 3 kênh thông tin

```
┌─────────────────────────────────────────────────────┐
│ 1. STATUS TICKER (1 dòng, luôn hiển thị, đổi màu)   │
│    ⚙️ Sẵn sàng  /  📡 Đang quét  /  ❌ Lỗi: ...    │
├─────────────────────────────────────────────────────┤
│ 2. TOAST (góc trên phải, tự ẩn sau 4s)              │
│    ✅ Thành công / ⚠️ Cảnh báo / ❌ Lỗi / ℹ️ Info   │
├─────────────────────────────────────────────────────┤
│ 3. LOG MODAL (bấm [📋 Log] để xem lịch sử đầy đủ)   │
│    [12:34:56] [CMD] $> dirb                          │
│    [12:34:57] [*] Dirb: 500 path → ...              │
│    [12:34:58]   ✓ [200] /admin                       │
│    [12:35:00] [RESULT] ✅ Tìm thấy 12 mục           │
└─────────────────────────────────────────────────────┘
```

1. Status Ticker

Chiếm 1 dòng (khoảng 40px), màu tự đổi theo loại sự kiện: ticker-error (đỏ), ticker-warning (vàng), ticker-success (xanh), ticker-system (xám).

```javascript
updateTicker(message, type = '');
// type: 'error-log' | 'warning' | 'success' | 'system-log' | ''
```

2. Toast Notifications

```javascript
showToast(message, type = 'info', duration = 4000);
// type: 'info' | 'success' | 'warning' | 'error' | 'system'
```

· Góc trên phải, tự ẩn sau 4s
· Tối đa 5 toast, tránh duplicate
· pointer-events: none cho container

3. Log Modal

· Giới hạn 500 dòng
· Mở khi bấm [📋 Log]
· Nút Xoá log reset về rỗng

---

12. 📈 Progress Bar & Modal Input

Progress Bar — Hiển thị tiến trình (%)

Module gọi self.emit_progress(pct, label) → server broadcast → client hiển thị thanh %.

```python
def handle(self, command, params):
    total = 1000
    self.emit_progress(0, "Bắt đầu quét")
    for i in range(total):
        self.check_cancel()
        if i % 50 == 0:
            self.emit_progress(int(i * 100 / total), f"{i}/{total} path")
    self.emit_progress(100, "Hoàn tất")
    return {...}
```

Client-side API:

Hàm Mô tả
startProgress(label) Bắt đầu progress (tự tăng tới 90%)
showProgress(pct, label) Set % cụ thể. pct=null → ẩn
stopProgress(finalPct?) Dừng progress. Truyền finalPct → hiện 100%

Modal Input — Thay thế window.prompt()

```javascript
askModalInput(message, defaultValue, hint).then(val => {
    if (val === null) return;  // User huỷ
    // val: string user nhập
});
```

· Enter để OK, Esc để huỷ
· Hint text gợi ý
· Responsive mobile

---

13. 🧩 Module Panel — UI riêng của module

Cho phép module có giao diện riêng render trong #mainResultSection:

```python
def handle(self, command, params):
    # ... xử lý ...
    self.render_panel({
        "title": "🔍 KẾT QUẢ DIRB",
        "html": f"""<div class='kv-row'>...</div>""",
        "actions": [
            {
                "label": "Quét lại", "icon": "🔄", "color": "primary",
                "command": "dirb", "params": {},
                "prompt": {"field": "url", "message": "URL mới:", "default": target_url},
            },
        ],
    })
    return {...}
```

Cấu trúc panel dict:

Field Type Mô tả
title str Tiêu đề panel
html str Nội dung HTML (đã escape nếu cần)
actions list[dict] Danh sách nút action (optional)

---

14. ⭐ Cancel Partial — Trả kết quả dở dang

Mỗi module BẮT BUỘC trả partial result khi bị cancel:

```python
def handle(self, command, params):
    found = []
    checked = 0
    target = ""
    try:
        self.check_cancel()
        target = params.get("url")
        for word in all_words:
            self.check_cancel()
            checked += 1
            # ...
        return {"status": "success", "type": "dirb_result", "found": found, ...}
    except InterruptedError:
        self.emit_progress(None)
        return {
            "status": "error",
            "type": "cancelled",
            "target": target,
            "found": found,
            "checked": checked,
            "wordlist_size": total,
            "message": f"Dừng — quét {checked}/{total}, tìm {len(found)} mục",
        }
```

Bảng partial result từng module:

Module Field partial Nguồn dữ liệu
DirbModule target, found, checked, wordlist_size Biến local trong loop
LanModule hosts, total_hosts, my_ip, network_prefix ctx.network_scanner.get_cache()
WifiModule._handle_scan networks Danh sách đã scan được
WifiModule._handle_connect_with_password network, ssid, tried_password Thông tin đã thử
WifiModule._handle_auto_connect network Thông tin mạng
WpsModule network Thông tin mạng

Client xử lý cancel với partial:

```javascript
if (result && result.type === 'cancelled') {
    stopProgress();
    this.updateStatus(`⏹️ ${result.message}`);
    if (result.hosts && Object.keys(result.hosts).length > 0) {
        this.updateLanDevices(result.hosts);
    }
    if (result.networks && result.networks.length > 0) {
        this.updateNetworkList(result.networks);
    }
    if (result.found) {
        showDirbResults({ target: result.target, found: result.found });
    }
    return;
}
```

Nguyên tắc vàng cho module:

1. Khởi tạo biến tích luỹ TRƯỚC try
2. check_cancel() ở đầu mỗi vòng lặp
3. Giữ context — target, network, ssid... accessible trong except
4. Không raise lại — phải return dict với partial data
5. emit_progress(None) để ẩn progress bar

---

15. ⭐ Nhật ký Module — Activity Log (RAM-first)

Mục đích

Ghi lại mọi lỗi/hoạt động của module vào một log chung, để debug và hiển thị badge lỗi.

Thiết kế RAM-first:

· RAM buffer là PRIMARY → hoạt động cả khi tool đang khởi động, chưa có data/, chưa có quyền ghi file
· File data/module_activity.json là BACKUP best-effort
· Lazy init → KHÔNG crash nếu data dir chưa tồn tại
· Thread-safe, singleton (get_activity_log())

Khi nào ghi log?

Sự kiện Event Severity Ghi bởi
Package không import được init_error error registry.py
Module file load lỗi init_error error registry.py
module.init() raise init_error error registry.py
Cài module lỗi install_error error module_installer.py
Cài module thành công install_success info module_installer.py
module.handle() raise handle_error error websocket_handler.py
Module trả status="error" returned_error warning websocket_handler.py
WS disconnect giữa task hang warning websocket_handler.py
Module bị block (treo ≥ 3 lần) blocked error websocket_handler.py
User bấm DỪNG / InterruptedError cancelled info websocket_handler.py

API ModuleActivityLog

```python
from tinhnang.core.module_activity import get_activity_log

log = get_activity_log()

log.log(
    module="dirb", event="handle_error", command="dirb",
    severity="error", message="Connection refused",
    details={"type": "ConnectionRefusedError"},
)

entries = log.read(module="dirb", severity="error", limit=50)
stats = log.stats()   # {"dirb": {"total": 5, "error": 2, ...}}
log.clear(module="dirb")
log.flush()
log.is_file_ok()
log.size()
```

Xem nhật ký từ UI

· Bấm nút 📊 Nhật Ký Module trên menu
· Hoặc từ panel Quản Lý Module: nút 📊 trên mỗi module
· Hoặc từ panel Chi Tiết Module
· Hoặc WS: wsClient.send('module_activity', {module: 'dirb'})

---

16. 🔄 Cơ chế Auto-Reset

File: data/.session.lock — chứa PID của process đang chạy.

Flow khởi động:

```
[Server start]
      ├─ ensure_dirs()
      ├─ config.load(auto_create=True)
      ├─ config.detect_root()  ⭐ v3.6.0 (euid → sudo → su)
      ├─ config.apply_environment()  ⭐ v3.6.0
      ├─ _check_and_reset_stale_session()
      │       ├─ Có .session.lock cũ?
      │       │       ├─ CÓ  → cleanup_orphan_processes() + rm lock
      │       │       └─ KHÔNG → Log: "[*] Session sạch"
      │       └─ _write_session_lock()
      ├─ Load modules
      └─ Start HTTP + WS server
```

Hàm cleanup_orphan_processes():

```python
def cleanup_orphan_processes():
    for p in ["wpa_supplicant", "pixiewps", "wpa_cli", "wpa_passphrase",
              "iw", "iwlist", "nmap", "nc", "ping", "hostapd", "dnsmasq"]:
        os.system(f"su -c 'pkill -9 {p}' 2>/dev/null")
    os.system("su -c 'rm -rf /data/local/tmp/wpa_ctrl_*' 2>/dev/null")
    os.system("su -c 'rm -rf /tmp/pixiewps*' 2>/dev/null")
    os.system("su -c 'svc wifi enable' 2>/dev/null")
```

---

17. 🛡️ Xử lý mất WebSocket & Module Blocking

⭐ v3.6.0: mất WS khi đang chạy task cần root → kill process + hang tracking.

📌 Phía Server

1. Detect disconnect

```python
async def handle_client(self, websocket):
    try:
        async for message in websocket:
            ...
    except websockets.exceptions.ConnectionClosed:
        pass
    finally:
        if self.context.is_processing and self.current_task:
            self._handle_client_disconnect()
        await self.unregister(websocket)
```

2. Handle disconnect

```python
def _handle_client_disconnect(self):
    task = self.current_task
    if not task:
        return

    self.logger.write(f"[WS] ⚠ Client mất kết nối khi đang chạy: '{task}' → kill processes")
    cleanup_orphan_processes()

    module = self.registry.route(task)
    if module:
        name = module.name
        self.module_hang_counts[name] = self.module_hang_counts.get(name, 0) + 1
        count = self.module_hang_counts[name]

        self.activity.log(
            module=name, event="hang", command=task or "",
            severity="warning",
            message=f"WS mất kết nối khi đang chạy '{task}' — treo lần {count}/{self.max_hangs}",
        )

        if count >= self.max_hangs:  # 3 lần
            self.blocked_modules.add(name)
            self.activity.log(
                module=name, event="blocked", command=task or "",
                severity="error",
                message=f"Module bị KHÓA do treo {count} lần liên tiếp",
            )

    with self.task_lock:
        self.context.reset_state()
        self.current_task = None
```

3. Block module treo

```python
if module.name in self.blocked_modules:
    await self.send_result(cmd, {
        "status": "error",
        "type": "module_blocked",
        "module": module.name,
        "hang_count": self.module_hang_counts.get(module.name, 0),
        "message": f"Module '{module.name}' đã bị KHÓA...",
    })
    return
```

4. Gửi block info trong status

```json
{
  "type": "status",
  "blocked_modules": ["dirb"],
  "module_hang_counts": {"dirb": 3, "lan": 1}
}
```

📌 Phía Client

1. Detect WS close giữa task
2. Hỏi user retry (tối đa 3 lần)
3. Auto retry sau reconnect
4. Block sau 3 lần fail

Reset thủ công

· Restart tool
· Hoặc gửi command reset_blocks

---

18. 🌐 Giao thức WebSocket & REST API

⭐ v3.6.0 — Thêm REST endpoints config

REST Endpoints

Method Path Mô tả
GET / HTML template
GET /api/ui Metadata UI (buttons, categories, is_root, root_required_commands)
GET /api/versions Version info các module
GET ⭐ /api/config Toàn bộ config + is_root + root_method + restart_required_fields
POST ⭐ /api/config Update config (partial), trả changed_fields + needs_restart

GET /api/config — Response mẫu

```json
{
  "config": {
    "network": {"interface": "wlan0", "host": "0.0.0.0", "port": 8080},
    "environment": {"binaries": [...], "libraries": [...]},
    "permissions": {"check_method": "sudo", "strict_mode": true},
    "modules": {"root_required_commands": [...]},
    "server": {"max_clients": 1, "ws_ping_interval": 20, "ws_ping_timeout": 60}
  },
  "is_root": false,
  "root_method": "none",
  "config_path": "/data/.../data/config.json",
  "restart_required_fields": ["network.host", "network.interface", ...]
}
```

POST /api/config — Request mẫu (partial)

```json
{
  "network": {"interface": "wlan1"},
  "permissions": {"strict_mode": false}
}
```

POST /api/config — Response mẫu

```json
{
  "status": "success",
  "changed_fields": ["network.interface", "permissions.strict_mode"],
  "needs_restart": true,
  "is_root": false,
  "root_method": "none",
  "config": { ...full config sau merge... },
  "message": "Đã lưu config. Cần restart tool để áp dụng."
}
```

WebSocket Messages

Client → Server (Request):

```json
{"command": "lan_scan", "params": {"mode": "thorough"}}
```

Server → Client (Events):

1. Status — có blocked_modules, module_hang_counts
2. Log
3. Networks
4. LAN Devices
5. Result
6. Busy
7. Module Blocked
8. ⭐ Permission Denied (v3.6.0)
9. Progress
10. Module Panel
11. Cancelled (với partial data)

⭐ Message permission_denied

```json
{
  "type": "result",
  "command": "scan",
  "result": {
    "status": "error",
    "type": "permission_denied",
    "command": "scan",
    "requires_root": true,
    "message": "Lệnh 'scan' yêu cầu quyền ROOT. Chạy lại tool bằng 'sudo python main.py' hoặc..."
  }
}
```

Client xử lý: toast đỏ + log error, không set main result.

Danh sách commands

Command Module Params Ghi chú
scan WifiModule — Cố định, cần root
connect_with_password WifiModule {network, password} Cố định, cần root
auto_connect WifiModule {network} Cố định, cần root
clear_all WifiModule — Cố định, cần root
quit WifiModule — Cố định, cần root
wps_attack WpsModule {network} Cố định, cần root
lan_scan LanModule {mode} UI động, cần root
lan_quick_scan LanModule — UI động, cần root
scan_specific_host LanModule {target_ip, ports} UI động, cần root
dirb DirbModule {url} UI động — prompt URL
install_module ModuleInstaller {source_path, overwrite, restart} Cài module
list_modules ModuleInstaller — Quản lý module
uninstall_module ModuleInstaller {name, confirmed} Xoá module
restart_tool ModuleInstaller — Restart
module_detail ModuleInstaller {name} Chi tiết module
get_module_versions ModuleInstaller — Version list
module_activity ModuleInstaller {module?, severity?, limit?} Xem nhật ký
clear_module_activity ModuleInstaller {module?, confirmed} Xoá nhật ký
stop / stop_task / stop_wps built-in — Dừng task
shutdown built-in — Tắt tool
clear_terminal built-in — Xoá log
get_status built-in — Status
reset_blocks built-in — Mở khóa module bị block

⭐ Danh sách lệnh cần root mặc định (có thể đổi qua ⚙️ Cài đặt):

wps_attack, connect_with_password, auto_connect, scan, lan_scan, lan_quick_scan, scan_specific_host, clear_all, quit

---

19. 🗄️ Định dạng file .acdv

File data/networks.acdv là database mã hoá nhị phân:

```
┌──────────────┬──────────────┬──────────────┬───────────────┬─────────────┬──────────┐
│ Fingerprint  │ Header Len   │ Header JSON  │ SHA256 (64B)  │ Payload XOR │ Magic    │
│ 0xAC 0x44 0x56│ (2 bytes BE) │              │               │             │ 0x55 0xAA│
└──────────────┴──────────────┴──────────────┴───────────────┴─────────────┴──────────┘
```

Payload structure (OBJ format):

```
[0x02] field1 [0x1F] field2 [0x1F] field3 [0x1F] field4 [0x03] [0x1E]
  ↑                                                          ↑      ↑
START_OBJ                                               END_OBJ  SEP_RECORD
```

Record structure: [bssid, ssid, password, security, password_id]

API sử dụng:

```python
from tinhnang.core.file_manager import FileManager

fm = FileManager()
data = fm.read_file("networks.acdv")
fm.save_file("networks.acdv", data_dict, data_type="OBJ", who_am_i="WIFI_SCANNER")
fm.sync_and_upgrade_database("networks.acdv")
unique = fm.get_unique_passwords("networks.acdv")
```

---

20. 🛠️ Hướng dẫn viết Plugin

⚡ Quick Start

Bước 1: Tạo tinhnang/modules/my_plugin.py

Bước 2: Copy template:

```python
from .base_module import BaseModule

DEFAULT_CONFIG = {
    "description": "Plugin của tôi",
    "files": {"wordlists": "wordlists/*.txt"},
    "settings": {"timeout": 30, "debug": False},
}

class MyPluginModule(BaseModule):
    name = "my_plugin"
    commands = ["my_command"]
    description = "Plugin của tôi"
    version = "1.0.0"
    latest_version = "1.0.0"
    category = "tools"
    category_label = "Công cụ"
    category_icon = "🧰"
    ui_buttons = [
        {
            "id": "my_command_btn", "label": "Làm Gì Đó", "icon": "✨",
            "color": "success", "command": "my_command",
            "params": {},
            "prompt": {"field": "target", "message": "Nhập target:"},
        }
    ]

    def init(self):
        self.resource.load(default_config=DEFAULT_CONFIG)
        self.context.logger.write("[✓] My Plugin loaded!")

    def handle(self, command, params):
        target = ""
        found = []
        checked = 0
        try:
            if command == "my_command":
                target = params.get("target", "")
                self.emit_progress(0, "Bắt đầu")
                for i in range(100):
                    self.check_cancel()
                    checked += 1
                    if i % 10 == 0:
                        self.emit_progress(i, f"{i}/100")
                self.emit_progress(100, "Hoàn tất")
                return {"status": "success", "type": "generic", "message": "OK"}
            return {"status": "error", "type": "generic", "message": "Unknown"}
        except InterruptedError:
            self.emit_progress(None)
            return {
                "status": "error", "type": "cancelled",
                "target": target, "found": found, "checked": checked,
                "message": f"Dừng — quét {checked}/100",
            }

    def cleanup(self):
        pass
```

Bước 3: Restart server → Registry tự tìm thấy → nút tự xuất hiện trên UI → file data/modules/my_plugin.json tự sinh.

Bước 4: Gọi từ client:

```javascript
ws.send(JSON.stringify({command: "my_command", params: {target: "192.168.1.1"}}));
```

📚 API Reference

Class attributes — Core:

Attribute Type Bắt buộc Mô tả
name str ✅ Tên duy nhất (snake_case)
commands list[str] ✅ Danh sách commands xử lý
description str ❌ Mô tả ngắn
version str ❌ Version hiện tại (default 1.0.0)
latest_version str ❌ Version mới nhất
version_notes str ❌ Ghi chú phiên bản

Class attributes — UI Metadata:

Attribute Type Mô tả
category str ID danh mục (wifi, lan, tools, ...)
category_label str Tên hiển thị menu nav
category_icon str Emoji cho menu tab
ui_buttons list[dict] Danh sách nút tự khai báo

Methods:

· init(self) — Gọi 1 lần khi registry load
· handle(self, command, params) -> dict — Gọi mỗi request, chạy NGOÀI luồng server
· cleanup(self) — Gọi khi shutdown

Helper methods:

Method Mô tả
self.emit_progress(pct, label) Gửi tiến trình % tới client
self.render_panel(panel_dict, title) Gửi UI panel riêng
self.is_cancelled() Trả True nếu bị yêu cầu dừng
self.check_cancel() Raise InterruptedError nếu bị cancel
self.mark_running(cmd) Server tự gọi trước handle()
self.mark_stopped() Server tự gọi sau handle()

📋 Format trả về

Bắt buộc:

```python
{"status": "success" | "error", "type": "<type>", "message": "Mô tả"}
```

Khi cancel:

```python
{
    "status": "error", "type": "cancelled",
    "message": "Dừng giữa chừng...",
    # + partial fields bất kỳ:
    "target": "...", "found": [...], "checked": 250,
}
```

🔧 Truy cập tài nguyên chia sẻ

```python
# Logger
self.context.logger.write("[*] Đang xử lý...")

# FileManager
fm = self.context.file_manager

# WiFiManager
wm = self.context.wifi_manager

# NetworkScanner
ns = self.context.network_scanner

# ModuleResource
self.resource.get("timeout", 30)

# ModuleActivityLog
from ..core.module_activity import get_activity_log
get_activity_log().log(module=self.name, event="info", severity="info", message="...")
```

✅ Checklist trước khi submit plugin

· Kế thừa BaseModule
· name unique (snake_case)
· commands không trùng module khác
· handle() luôn return dict có status, type, message
· Có try/except bao quanh logic
· Bắt InterruptedError và trả partial result
· Log mọi bước quan trọng
· Cleanup tài nguyên trong cleanup()
· Nếu có UI: id nút không trùng, color hợp lệ
· Nếu có tài nguyên: khai báo DEFAULT_CONFIG + gọi self.resource.load()
· Test độc lập trước khi tích hợp
· ⭐ v3.6.0: Nếu command cần root → thêm vào config.modules.root_required_commands
· check_cancel() ở đầu mỗi vòng lặp hoặc mỗi bước dài
· Nếu task lâu → emit_progress() để user biết tiến trình

---

21. 🐛 Debugging & Testing

Debug log:

```python
self.context.logger.write(f"[DEBUG] params={params}")
```

Kiểm tra module đã load:

```
[Registry] ✓ Loaded module: wifi (5 commands)
[Registry] ✓ Loaded module: wps (1 commands)
[Registry] ✓ Loaded module: lan (3 commands)
[Registry] ✓ Loaded module: dirb (1 commands)
```

⭐ Kiểm tra config & root — v3.6.0

```
[SYSTEM] Data dir: /data/.../data
[SYSTEM] Config  : /data/.../data/config.json
[SYSTEM] Interface: wlan0  Host: 0.0.0.0  Port: 8080
[SYSTEM] Root  : ✓ sudo   (hoặc ✗ KHÔNG)
```

Từ HTTP:

```bash
curl http://localhost:8080/api/config | python -m json.tool
```

Từ Python:

```python
from tinhnang.core.config import get_config

cfg = get_config()
cfg.load(auto_create=True)
cfg.detect_root()

print("is_root:", cfg.is_root)
print("root_method:", cfg.root_method)
print("interface:", cfg.interface)
print("port:", cfg.port)
print("can run 'scan':", cfg.can_run("scan"))           # non-root → False
print("can run 'dirb':", cfg.can_run("dirb"))           # dirb không cần root
print("requires root 'wps_attack':", cfg.requires_root("wps_attack"))
```

⭐ Test update config qua API:

```bash
curl -X POST http://localhost:8080/api/config \
  -H "Content-Type: application/json" \
  -d '{"permissions": {"strict_mode": false}}'
```

Lỗi thường gặp

Lỗi Nguyên nhân Cách sửa
Module không load Không kế thừa BaseModule Xem Nhật ký Module
Command không route Sai tên trong commands Kiểm tra spelling
Server không trả về handle() không return Luôn return dict
UI không cập nhật Sai type Kiểm tra bảng type
Nút không hiện Thiếu id/command Bổ sung field
Menu nav không có tab Module không set category Thêm category
Data ghi sai chỗ Dùng path tương đối Dùng paths.py
JSON lỗi → module chết User sửa sai syntax Xoá file, restart
Wordlist không nạp Pattern trong JSON sai Kiểm tra files.wordlists
Tool treo sau crash Session cũ chưa dọn Auto-reset đã lo
Module bị khóa Treo ≥ 3 lần Restart hoặc reset_blocks
WS liên tục ngắt WiFi yếu / sleep Ngồi gần router
Progress không hiện Không gọi emit_progress() Thêm self.emit_progress()
Modal không hiện prompt thiếu trong ui_buttons Thêm field prompt
Panel không render panel.html thiếu Thêm html string
Mất kết quả khi cancel except không trả partial Thêm partial fields
⭐ Config không load Syntax lỗi JSON Restart → default, sửa qua GUI
⭐ Non-root không chạy được strict_mode = true + lệnh trong root_required Chạy sudo hoặc set strict_mode = false
⭐ Nút hiện 🔒 Lệnh cần root + non-root Chạy sudo hoặc đổi config
⭐ Config đổi không áp dụng Cần restart Tool sẽ hỏi có restart không

⭐ Test config (v3.6.0)

```python
# test_config.py
from tinhnang.core.config import get_config, DEFAULT_CONFIG
from tinhnang.core.paths import ensure_dirs

ensure_dirs()
cfg = get_config()
cfg.load(auto_create=True)
cfg.detect_root()

assert cfg.data["network"]["interface"] is not None
assert cfg.data["permissions"]["check_method"] in ["sudo", "euid", "su", "auto", "none"]

# Test partial update
result = cfg.update({"permissions": {"strict_mode": False}})
assert result["status"] == "success"
assert "permissions.strict_mode" in result["changed_fields"]
assert result["needs_restart"] is True

# Test can_run
cfg.is_root = False
cfg.data["permissions"]["strict_mode"] = True
assert cfg.can_run("dirb") is True       # dirb không cần root
assert cfg.can_run("scan") is False       # scan cần root

cfg.data["permissions"]["strict_mode"] = False
assert cfg.can_run("scan") is True        # strict off → cho chạy hết

print("[✓] Config test passed")
```

---

22. 🗺️ Roadmap

✅ Đã hoàn thành (v3.6.0)

· ☑ Kiến trúc Plugin động
· ☑ UI động — module tự khai báo nút
· ☑ Single Main Result Screen + DOM sạch
· ☑ Auto-Reset session
· ☑ WebSocket disconnect handling
· ☑ Module hang tracking + blocking
· ☑ Menu nav tự sinh theo danh mục
· ☑ REST endpoint /api/ui + /api/versions
· ☑ Data Directory tập trung (data/)
· ☑ Hệ thống Resource JSON cho module
· ☑ Nút DỪNG với fallback 2 lớp
· ☑ Auto-migrate file cũ ở root
· ☑ WebSocket real-time
· ☑ WiFi scan + connect
· ☑ WPS Pixie Dust attack
· ☑ LAN scanner với nmap 4 chế độ + fallback nc
· ☑ Dirb web scanner
· ☑ Database .acdv mã hoá
· ☑ Random MAC
· ☑ Auto cleanup
· ☑ Progress Bar (%)
· ☑ Modal Input dùng chung
· ☑ Module Panel
· ☑ Toast Notifications
· ☑ Status Ticker
· ☑ Log Modal
· ☑ Cancel Partial
· ☑ clearMainResult() — DOM sạch
· ☑ Bỏ terminal log UI
· ☑ RAM-first ModuleActivityLog
· ☑ Ghi log lỗi toàn diện
· ☑ Module Installer quản lý nhật ký
· ☑ Badge "RAM only"
· ⭐ ☑ Config tập trung data/config.json (v3.6.0)
· ⭐ ☑ GUI ⚙️ Cài đặt — modal chỉnh config qua web (v3.6.0)
· ⭐ ☑ REST /api/config GET + POST (v3.6.0)
· ⭐ ☑ Root detection ưu tiên sudo (v3.6.0)
· ⭐ ☑ Phân quyền theo lệnh — root_required_commands (v3.6.0)
· ⭐ ☑ Nút cần root hiện 🔒 + banner cảnh báo (v3.6.0)
· ⭐ ☑ Auto detect lại root khi đổi config permissions (v3.6.0)

🚧 Đang phát triển (v3.7)

· ☐ Handshake capture (.cap file) + crack offline
· ☐ WPA3 SAE downgrade detection
· ☐ Evil Twin với hostapd
· ☐ Deauth attack (aireplay-ng)
· ☐ PMKID attack cho WPA2
· ☐ Dashboard sub-tab cho mỗi module
· ☐ Streaming log cho progress bar (SSE / chunked)
· ☐ Save/load profile scan

🔮 Kế hoạch tương lai (v4.0)

· ☐ Multi-target scan song song
· ☐ Plugin marketplace
· ☐ REST API (JSON) đầy đủ
· ☐ Export reports (PDF/JSON)
· ☐ Scheduler — tự động scan theo cron
· ☐ Web dashboard nâng cao
· ☐ Multi-language (EN/VI/ZH)
· ☐ Cloud sync database (opt-in)

---

23. 📝 Changelog

[3.6.0] - 2025-01-XX

🎉 Added — Cấu hình tập trung (Config System)

File mới: tinhnang/core/config.py

· Class Config — Singleton thread-safe
· DEFAULT_CONFIG — toàn bộ cấu hình mặc định
· RESTART_REQUIRED_FIELDS — danh sách field cần restart khi đổi
· API: .load(), .save(), .reload(), .update(), .to_dict(), .detect_root(), .can_run(), .requires_root(), .get_reason_blocked(), .apply_environment(), .describe()
· _flatten() — flatten dict để diff changed_fields
· File: data/config.json — tự sinh lần đầu

Root detection — ưu tiên sudo (theo yêu cầu)

· Thứ tự: euid fast-path → sudo -n true (PRIMARY) → su -c id (fallback)
· Default check_method = "sudo"
· Đổi config permissions.* → server tự detect_root() lại

Phân quyền theo lệnh

· Config.modules.root_required_commands: danh sách lệnh cần root
· Config.can_run(cmd): check quyền chạy lệnh
· Config.requires_root(cmd): check lệnh có cần root
· Server trả type: "permission_denied" nếu non-root gọi lệnh cần root
· collect_ui_config() tính requires_root + can_run cho từng nút

GUI ⚙️ Cài đặt

· Nút ⚙️ Cài đặt trên status bar top
· Config Modal với 5 section: 🌐 Mạng / 📦 Môi trường / 🔐 Quyền / 🛠️ Commands cần root / 🖥️ Server
· Save → confirm nếu needs_restart → tự gửi restart_tool
· Auto refresh UI sau khi save (loadUIModules + loadConfig)

Banner cảnh báo non-root

· updateRootBanner() — hiển thị banner vàng khi is_root=false
· Text: "Chạy lại bằng sudo python main.py để mở khoá toàn bộ"
· Ẩn khi đã root

Nút cần root hiện 🔒

· renderModuleButtons() detect btn.can_run + btn.requires_root
· can_run=false + requires_root=true → hiện 🔒 + tooltip
· Click → toast warning "Cần quyền ROOT"
· Không gửi command lên server

🔄 Changed

· tinhnang/core/config.py — viết lại hoàn toàn (từ stub → full)
· tinhnang/backend/http_handler.py — thêm do_POST() + /api/config GET/POST + _send_json() helper
· tinhnang/backend/server.py — dùng config.load() + detect_root() (không hardcode)
· tinhnang/backend/registry.py — collect_ui_config() thêm requires_root + can_run
· tinhnang/backend/websocket_handler.py — check cfg.can_run(cmd) trước khi route
· templates/index.html — thêm nút ⚙️ Cài đặt + configModal
· static/script.js — thêm loadConfig/showConfigModal/saveConfigFromModal, updateRootBanner được gọi trong loadUIModules, handleCommandResult xử lý permission_denied
· static/style.css — thêm .config-section, .config-row, .config-notice, dọn dẹp block CSS bị duplicate
· tinhnang/core/paths.py — thêm CONFIG_FILE constant

🐛 Fixed

· Config không tập trung (trước hardcode rải rác)
· Root detection luôn chạy euid trước (giờ ưu tiên sudo)
· Nút cần root vẫn click được khi non-root → lỗi khó hiểu (giờ hiện 🔒)
· Không có banner cảnh báo non-root (giờ có banner vàng)
· Config đổi không có cơ chế restart tự động (giờ có confirm + restart)

⚠️ Breaking Changes

· File data/config.json là file mới — tự sinh lần đầu
· Root detection default đổi từ "auto" → "sudo"
· collect_ui_config() response có thêm requires_root + can_run
· Command cần root khi chạy non-root → server trả permission_denied (trước đó thường silent fail hoặc lỗi khó hiểu)

Migration Guide v3.5.x → v3.6.0

Không cần làm gì — tool tự động:

1. Tạo data/config.json lần đầu chạy
2. Tự detect root qua sudo
3. Nút cần root hiện 🔒 nếu non-root
4. Banner cảnh báo non-root

Nếu muốn custom config:

· Bấm ⚙️ Cài đặt trên UI và sửa trực tiếp
· Hoặc sửa data/config.json (restart tool)

Nếu plugin mới cần root:

· Thêm command vào config.modules.root_required_commands (qua GUI hoặc sửa file)

---

[3.5.1] - 2025-01-XX

🎉 Added — Nhật ký Module (RAM-first)

ModuleActivityLog — tinhnang/core/module_activity.py

· Class ModuleActivityLog — RAM buffer primary + file backup best-effort
· Singleton get_activity_log() — lazy init, thread-safe
· API: .log(), .read(), .clear(), .stats(), .flush(), .is_file_ok(), .size()
· File: data/module_activity.json
· Giới hạn 200 entries

Ghi log tự động:

· registry.py — init_error
· websocket_handler.py — handle_error, returned_error, hang, blocked, cancelled
· module_installer.py — install_error, install_success

Module Installer — commands mới:

· module_activity — xem nhật ký
· clear_module_activity — xoá nhật ký

Module Installer — UI mới:

· Nút 📊 Nhật Ký Module trên menu
· Badge ❌ N lỗi / ⚠️ N trên module card
· Panel nhật ký với stats + entries

🐛 Fixed

· Tool mới khởi động, module import/init lỗi → không mất log
· Cài module sai syntax → có log install_error
· Biết module nào hay lỗi qua stats card

---

[3.5.0] - 2025-01-XX

🎉 Added — Hệ thống thông báo mới

· Toast Notifications — showToast() 5 loại
· Status Ticker — updateTicker() 4 loại màu
· Log Modal — 500 dòng giới hạn
· Cancel Partial — trả kết quả dở dang khi cancel
· clearMainResult() — DOM sạch

🔄 Changed

· Xoá hoàn toàn .terminal-container (350px)
· Thêm .status-bar-top

🐛 Fixed

· Terminal 350px → UI chật
· Log cuộn liên tục → rối mắt
· Cancel mất hết kết quả
· DOM phình to khi chạy nhiều module

---

[3.4.0] - 2025-01-XX

· Progress Bar (%)
· Modal Input — askModalInput()
· Module Panel — render_panel()

---

[3.3.0] - 2025-01-XX

· Single Main Result Screen
· Session Lock & Auto-Reset
· WebSocket Disconnect Handling

---

[3.2.0] - 2025-01-XX

· data/ directory tập trung
· tinhnang/core/paths.py — nguồn chân lý duy nhất
· ModuleResource — config JSON mỗi module
· data/wordlists/ dùng chung

---

[3.1.0] - 2025-01-XX

· UI động — module tự khai báo nút
· REST /api/ui
· Menu nav tự sinh
· Nmap 4 chế độ + fallback nc/ping

---

[3.0.1] - 2025-01-XX

· Kiến trúc Plugin động
· ModuleRegistry, AppContext
· Dirb module
· Stop command

---

[3.0.0] - 2024-12-XX

· Web UI WebSocket real-time
· LAN Scanner
· Auto Connect đổi MAC
· Database .acdv
· Console Mode

---

24. 🤝 Đóng góp

🐛 Báo lỗi — Template issue

```markdown
## Mô tả
[Mô tả ngắn gọn]

## Các bước tái hiện
1. ...

## Môi trường
- Android version:
- Termux version:
- Python version:
- Tool version:
- CWD khi chạy:
- Chạy root hay non-root? (xem log [SYSTEM] Root)
- Config hiện tại? (paste data/config.json nếu liên quan)

## Log
[Paste data/terminal.log]

## Nhật ký Module
[Paste data/module_activity.json hoặc screenshot panel Nhật ký]
```

🔧 Pull Request

```bash
git clone https://github.com/your-username/acdv-wifi-tool.git
cd acdv-wifi-tool
git checkout -b feature/my-feature
# ...code...
git commit -m "feat(ui): add progress bar"
git push origin feature/my-feature
```

Commit convention: <type>(<scope>): <subject> — Types: feat, fix, docs, style, refactor, test, chore

⚠️ Path Rule — Bắt buộc tuân thủ

```python
# ✅ ĐÚNG — dùng paths.py
from ..core.paths import DATA_DIR, LOG_FILE, DB_FILE, SESSION_LOCK, CONFIG_FILE
path = os.path.join(DATA_DIR, "myfile.json")

# ❌ SAI
path = "myfile.json"
path = "./data/myfile.json"
```

⭐ Config Rule — Bắt buộc khi thêm lệnh mới ⭐ v3.6.0

Nếu command cần root → thêm vào config.modules.root_required_commands (qua GUI ⚙️ hoặc sửa data/config.json). Nếu command không cần root → không thêm (để non-root vẫn dùng được).

---

25. ⚡ Quick Start

1️⃣ Chuẩn bị (1 phút)

```bash
termux-setup-storage
pkg update -y && pkg upgrade -y
pkg install python nmap iw wpa-supplicant pixiewps net-tools tsu -y
pip install websockets requests psutil
```

2️⃣ Cài đặt (1 phút)

```bash
git clone https://github.com/your-repo/acdv-wifi-tool.git
cd acdv-wifi-tool
```

3️⃣ Chạy (30 giây)

```bash
# Khuyến nghị: chạy có sudo để mở khoá toàn bộ
sudo python main.py
# hoặc
python main.py
```

Lần đầu sẽ tự tạo:

```
[*] Data directory: /data/data/com.termux/files/home/acdv-wifi-tool/data
[*] Config  : /data/.../data/config.json    ← ⭐ v3.6.0
[*] Interface: wlan0  Host: 0.0.0.0  Port: 8080
[*] Root  : ✓ sudo   (hoặc ✗ KHÔNG)
[*] Session sạch — không cần auto-reset.
```

4️⃣ Truy cập Web UI

Mở browser (điện thoại/laptop cùng WiFi):

```
http://<IP-điện-thoại>:8080
```

5️⃣ Khám phá UI mới (v3.6.0)

· Status bar top: WS dot + Ticker + nút [📋 Log] + nút [⚙️ Cài đặt]
· ⭐ Banner vàng cảnh báo nếu chạy non-root
· Menu nav: 📦 Tất cả, 🌐 Mạng LAN, 🧰 Công cụ, ⚙️ Hệ thống
· Nút cố định: Quét WiFi, Kết Nối, WPS, Auto Connect
· ⭐ Nút cần ROOT hiện 🔒 khi non-root
· Main Result Section: xuất hiện khi có kết quả module
· Toast / Ticker / Log Modal / Progress Bar / Modal Input / Module Panel

6️⃣ ⭐ Cài đặt lần đầu (khuyến nghị)

1. Bấm ⚙️ Cài đặt
2. Kiểm tra / chỉnh:
   · Card mạng (wlan0)
   · Host (0.0.0.0) / Port (8080)
   · Root commands (danh sách lệnh cần root)
   · Strict mode (true — khuyến nghị)
3. 💾 Lưu cấu hình
4. Nếu đổi network → restart tool (GUI hỏi tự động)

7️⃣ Quét WiFi lần đầu

1. Bấm "📡 Quét WiFi"
2. Chờ 5-10 giây (xem thanh %)
3. Danh sách mạng hiện ra
4. Toast "✅ Tìm thấy N mạng WiFi" xuất hiện

8️⃣ Thử kết nối

· Cách 1 — Có mật khẩu: Chọn mạng → nhập pass → "Kết nối"
· Cách 2 — WPS: Chọn mạng có icon ✅ WPS → "⚡ Tấn công WPS"
· Cách 3 — Auto: Chọn mạng → "🔄 Auto Connect"

9️⃣ Thêm wordlist cho Dirb

```bash
cp ~/my_wordlist.txt data/wordlists/
```

Restart server → tự nạp:

```
[✓] dirb: nạp dirb.json
[*] +150 từ khóa từ 'my_wordlist.txt'
```

🎯 Lệnh hữu ích

```bash
# Kiểm tra root
sudo -n true && echo "Có root qua sudo" || echo "Không có root"

# Kiểm tra WiFi interface
iw dev

# Xem cấu trúc data/
ls -la data/
cat data/config.json | python -m json.tool   # ⭐ v3.6.0

# Xem nhật ký module
cat data/module_activity.json | python -m json.tool

# Kill sạch process
sudo pkill -9 wpa_supplicant; sudo pkill -9 pixiewps; sudo pkill -9 nmap
sudo svc wifi enable

# Xoá session lock
rm data/.session.lock

# Xoá nhật ký module
rm data/module_activity.json

# Reset config về default (giữ nguyên data khác)
rm data/config.json && python main.py  # tự sinh default
```

❓ Troubleshooting

Vấn đề Giải pháp
Permission denied Thử sudo / tsu
Interface wlan0 not found Sửa data/config.json hoặc ⚙️ Cài đặt → Card mạng khác
Port 8080 already in use ⚙️ Cài đặt → Port khác, hoặc fuser -k 8080/tcp
WiFi không bật lại sau scan sudo svc wifi enable
Nút module không hiện Check /api/ui, xem browser console
Menu nav trống Module phải set category
JSON lỗi → module chết Xoá data/modules/<name>.json, restart
Tool treo sau crash Auto-reset đã lo. Nếu vẫn lỗi: xoá .session.lock, kill process
Module bị khóa Restart tool hoặc reset_blocks
WS liên tục ngắt Ngồi gần router, tắt tiết kiệm pin
Progress không hiện Module chưa emit_progress()
Modal không hiện prompt thiếu trong ui_buttons
Panel không render panel.html thiếu
Toast không hiện Check #toastContainer
Ticker không cập nhật Check #tickerText
Log Modal rỗng logHistory chưa có gì
Cancel mất kết quả Module chưa bắt InterruptedError trả partial
Nhật ký Module rỗng Chưa có lỗi — tạo module hỏng để test
"RAM only" badge File log không ghi được — check quyền data/
⭐ Config không load Kiểm tra JSON syntax. Nếu lỗi → tool dùng default, sửa qua GUI
⭐ Non-root không chạy được lệnh Chạy sudo hoặc set strict_mode=false
⭐ Nút hiện 🔒 Lệnh cần root + non-root → chạy sudo
⭐ Config đổi không áp dụng Cần restart → GUI tự hỏi, hoặc restart thủ công

🎓 Tips

· 📱 Dùng điện thoại khác mở UI mượt hơn
· 🔋 Cắm sạc khi chạy WPS attack
· 🌡️ Để thoáng điện thoại
· 💾 Backup data định kỳ: cp -r data data.backup
· 🔍 Nmap thorough có thể mất 5-15 phút — xem thanh %
· 📝 Thả wordlist vào data/wordlists/ — tự động nạp
· ⚙️ Sửa data/modules/<name>.json để tinh chỉnh module
· ⚙️ ⭐ Sửa data/config.json hoặc GUI ⚙️ Cài đặt để tinh chỉnh tool
· ⭐ Cancel giữa chừng không mất kết quả → partial data vẫn có
· ⭐ Debug lỗi module → bấm 📊 Nhật Ký Module

---

26. ⚠️ Cảnh báo pháp lý

Công cụ này chỉ dành cho mục đích GIÁO DỤC và KIỂM THỬ BẢO MẬT HỢP PHÁP.

· ❌ KHÔNG sử dụng để tấn công mạng WiFi không thuộc sở hữu của bạn
· ❌ KHÔNG sử dụng để truy cập trái phép vào hệ thống của người khác
· ✅ CHỈ sử dụng trên mạng của chính bạn, hoặc khi có văn bản uỷ quyền
· ✅ LUÔN tuân thủ luật pháp địa phương về an ninh mạng

Tác giả KHÔNG chịu trách nhiệm cho bất kỳ hành vi lạm dụng nào.

---

📜 License

MIT License — sử dụng tự do cho mục đích học tập và nghiên cứu.

---

👥 Credits

· ACDV-Teams — Phát triển chính
· Pixiewps — Dominique Bongard
· wpa_supplicant — Jouni Malinen
· Nmap — Gordon Lyon (Fyodor)
· Cộng đồng Termux — Môi trường Android

---

<p align="center">
  <strong>ACDV-Teams WiFi Security Tool v3.6.0</strong><br>
  Made with ❤️ by ACDV-Teams<br>
  <em>Happy (ethical) hacking! 🚀</em>
</p>

---

📌 Tóm tắt thay đổi v3.6.0 so với v3.5.1

Mục v3.5.1 v3.6.0
Cấu hình tập trung ❌ Hardcode rải rác ✅ data/config.json
GUI cài đặt ❌ Phải sửa file / CLI args ✅ Nút ⚙️ Cài đặt + modal
API config ❌ Không có ✅ GET + POST /api/config
Root detection euid → sudo → su ⭐ euid fast-path → sudo (PRIMARY) → su
Phân quyền theo lệnh ❌ Chưa có ✅ root_required_commands + can_run(cmd)
Banner non-root ❌ Không ✅ Banner vàng + nhắc sudo
Nút cần root non-root ❌ Vẫn click được (lỗi) ✅ Hiện 🔒 + tooltip + không click
Response khi bị chặn ❌ Silent fail ✅ type: permission_denied + toast
Config apply — ✅ Field "modules.*" áp dụng ngay, field khác cần restart
Detect lại root — ✅ Khi đổi config permissions.*
Env variables ❌ Chỉ trong utils ✅ apply_environment() tự động sau update
Config backup — ✅ Tự merge với default (không mất field thiếu)
Tương thích — Module cũ chạy bình thường — không breaking
Version 3.5.1 3.6.0

```

---

## 🔑 Tóm tắt những gì đã thay đổi trong README

### ✅ Bổ sung mới
1. **Section 6.5** — Cấu hình Tool (`data/config.json`) với GUI Cài đặt — chi tiết từng field, API GET/POST mẫu, root detection order, các field cần restart
2. **Section 2** — Thêm bảng "⚙️ Cấu hình & Phân quyền" ⭐ v3.6.0
3. **Section 3** — Sơ đồ kiến trúc có config layer + `permission_denied` + `cfg.can_run`
4. **Section 18** — API endpoints `/api/config` GET + POST + message `permission_denied`
5. **Section 22** — Roadmap: config system được mark hoàn thành
6. **Section 23** — Changelog `[3.6.0]` với migration guide
7. **Section 25** — Quick Start: bước ⭐ Cài đặt lần đầu + lệnh debug config
8. **Section 26** — Troubleshooting: 4 lỗi mới liên quan config/root

### 🔄 Cập nhật
- Version header: `3.5.1` → `3.6.0`
- TOC: thêm section 6.5
- Section 1: thêm dòng ⚙️ GUI Cài đặt
- Section 6: `data/config.json` vào structure
- Section 9: bảng `requires_root` + `can_run` cho nút + nút ⚙️ Cài đặt
- Section 14: (giữ nguyên) — vẫn đúng
- Section 17: nhấn mạnh kill process khi task root bị disconnect
- Section 20: checklist thêm "thêm lệnh cần root vào config"
- Section 24: Config Rule — bắt buộc khi thêm lệnh mới
- Bảng tóm tắt cuối: thêm 13 dòng so sánh v3.5.1 vs v3.6.0# ACDV-Teams-network-security-tool-
# ACDV-Teams-network-security-tool-
