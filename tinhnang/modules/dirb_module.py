# tinhnang/modules/dirb_module.py
import os
import concurrent.futures
import urllib.request
import urllib.error

from .base_module import BaseModule


COMMON_WORDLIST = [
    "admin", "administrator", "admin1", "adminarea", "admin_area", "admin_area/login",
    "admin/login", "adminpanel", "admin-panel", "administrator/login",
    "wp-admin", "wp-login.php", "wp-content", "wp-includes", "wordpress",
    "phpmyadmin", "pma", "mysql", "myadmin", "mysqladmin",
    "cpanel", "whm", "webmail", "plesk", "directadmin",
    "login", "signin", "log-in", "auth", "authenticate",
    "dashboard", "panel", "controlpanel", "console",
    "manager", "management", "manage", "cp",
    "user", "users", "account", "accounts", "profile", "profiles",
    "api", "apis", "v1", "v2", "v3", "rest", "graphql", "swagger", "swagger-ui",
    "docs", "documentation", "doc", "help", "support",
    "backup", "backups", "bak", "back", "old", "new", "temp", "tmp",
    "db", "database", "data", "sql", "dump", "dumps",
    "config", "conf", "configuration", "settings", "setup", "install",
    "test", "tests", "testing", "dev", "development", "staging", "demo",
    "upload", "uploads", "download", "downloads", "files", "file",
    "media", "images", "img", "css", "js", "javascript", "assets", "static",
    "public", "private", "hidden", "secret", "internal", "intranet",
    "portal", "site", "web", "www", "html", "htm",
    "log", "logs", "error", "errors", "debug",
    "status", "health", "healthz", "ping", "version", "info", "about",
    "server-status", "server-info", "phpinfo.php", "info.php",
    "robots.txt", "sitemap.xml", "sitemap", "crossdomain.xml",
    ".git", ".git/config", ".git/HEAD", ".env", ".htaccess", ".htpasswd",
    ".svn", ".hg", ".DS_Store", "web.config",
    "blog", "news", "forum", "community", "faq",
    "shop", "store", "cart", "checkout", "order", "orders",
    "search", "find", "query", "results",
    "mail", "email", "contact", "feedback", "newsletter",
    "cgi-bin", "cgi", "scripts", "bin", "exec",
    "includes", "include", "lib", "library", "libraries", "vendor",
    "src", "source", "app", "application", "apps", "modules", "module",
    "themes", "theme", "templates", "template", "views", "view",
    "ajax", "json", "xml", "rss", "feed", "feeds", "atom",
    "print", "pdf", "doc", "docx", "xls", "xlsx", "csv",
    "image", "video", "audio", "music", "photo", "photos",
    "client", "clients", "customer", "customers", "member", "members",
    "staff", "employee", "employees", "hr", "finance", "sales",
    "report", "reports", "stat", "stats", "statistics", "analytics",
    "monitor", "monitoring", "metrics", "grafana", "prometheus",
    "jenkins", "gitlab", "github", "bitbucket", "sonar",
    "app_dev.php", "app.php", "app_prod.php", "index.php~", "index.php.bak",
    "test.php", "info.php.bak", "config.php.bak", "wp-config.php.bak",
    "README.md", "README.txt", "CHANGELOG.md", "LICENSE", "TODO.md",
]


DEFAULT_DIRB_CONFIG = {
    "description": "Quét thư mục/file ẩn trên web target",
    "files": {"wordlists": ["wordlists/*.txt", "wordlists/dirb/*.txt"]},
    "settings": {
        "timeout": 4, "max_workers": 25,
        "user_agent": "Mozilla/5.0 (ACDV-Scanner)",
        "skip_status": ["000", "404"], "use_builtin": True,
    },
}


class DirbModule(BaseModule):
    name = "dirb"
    commands = ["dirb"]
    description = "Quét thư mục/file ẩn trên web target"

    version = "1.1.1"
    latest_version = "1.1.1"
    version_notes = "Trả partial kèm target khi cancel."

    category = "tools"
    category_label = "Công cụ"
    category_icon = "🧰"
    ui_buttons = [
        {"id": "dirb_scan", "label": "Quét Thư Mục Ẩn", "icon": "🔍",
         "color": "secondary", "command": "dirb", "params": {},
         "prompt": {"field": "url", "message": "Nhập URL hoặc IP cần quét (vd: 192.168.1.1 hoặc http://192.168.1.1:8080):", "default": ""}},
    ]

    def init(self):
        self.resource.load(default_config=DEFAULT_DIRB_CONFIG)
        self.context.logger.write(f"[✓] Dirb Module v{self.version} sẵn sàng!")

    def _load_wordlists(self):
        ctx = self.context
        all_words = []
        if self.resource.get("use_builtin", True):
            all_words.extend(COMMON_WORDLIST)
        sources = []
        wl_paths = self.resource.resolve_all("wordlists")
        if wl_paths:
            for p in wl_paths:
                fname = os.path.basename(p)
                try:
                    with open(p, "r", encoding="utf-8", errors="ignore") as f:
                        extra = [l.strip() for l in f if l.strip() and not l.startswith("#")]
                    if extra:
                        all_words.extend(extra)
                        sources.append((fname, len(extra)))
                except Exception as e:
                    ctx.logger.write(f"[!] Lỗi đọc {fname}: {e}")
        else:
            ctx.logger.write("[*] Không có wordlist → dùng built-in")
            ctx.logger.write("    💡 Thả file .txt vào data/wordlists/")
        all_words = list(dict.fromkeys(all_words))
        return all_words, sources

    def handle(self, command, params):
        if command != "dirb":
            return {"status": "error", "message": f"Unknown: {command}", "type": "generic"}

        ctx = self.context
        ctx.scanning = True
        target_url = ""
        try:
            target_url = (params.get("url") or "").strip().rstrip("/")
            if not target_url:
                return {"status": "error", "type": "generic", "message": "Thiếu URL mục tiêu"}

            if not target_url.startswith(("http://", "https://")):
                target_url = "http://" + target_url

            timeout = int(self.resource.get("timeout", 4))
            max_workers = int(self.resource.get("max_workers", 25))
            user_agent = self.resource.get("user_agent", "Mozilla/5.0 (ACDV-Scanner)")
            skip_status = set(self.resource.get("skip_status", ["000", "404"]))

            all_words, sources = self._load_wordlists()
            for fname, count in sources:
                ctx.logger.write(f"[*] +{count} từ khóa từ '{fname}'")

            if not all_words:
                return {"status": "error", "type": "generic", "message": "Không có wordlist."}

            ctx.logger.write(f"[*] Dirb: {len(all_words)} path → {target_url}")
            self.emit_progress(0, "Bắt đầu quét")

            def check_url(url):
                try:
                    req = urllib.request.Request(url, headers={"User-Agent": user_agent})
                    try:
                        resp = urllib.request.urlopen(req, timeout=timeout)
                        return url, str(resp.status)
                    except urllib.error.HTTPError as e:
                        return url, str(e.code)
                    except urllib.error.URLError:
                        return url, "000"
                    except Exception:
                        return url, "000"
                except Exception:
                    return url, "000"

            self.check_cancel()

            _, test_code = check_url(target_url + "/")
            if test_code == "000":
                ctx.logger.write("[-] Target không phản hồi!")
                self.emit_progress(None)
                return {"status": "error", "type": "generic",
                        "message": f"Target {target_url} không phản hồi"}

            ctx.logger.write(f"[+] Target phản hồi HTTP {test_code}")

            found = []
            checked = 0
            total = len(all_words)

            def scan_one(word):
                return check_url(f"{target_url}/{word}")

            with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as ex:
                futures = {ex.submit(scan_one, w): w for w in all_words}
                for f in concurrent.futures.as_completed(futures):
                    if self.is_cancelled():
                        ctx.logger.write("[!] Dirb dừng — huỷ task còn lại...")
                        for fut in futures: fut.cancel()
                        break
                    checked += 1
                    try:
                        url, code = f.result()
                        if code and code not in skip_status:
                            found.append({"url": url, "dir": futures[f], "status": code})
                            ctx.logger.write(f"  ✓ [{code}] {url}")
                    except Exception:
                        pass
                    if checked % 50 == 0 or checked == total:
                        pct = int(checked * 100 / total)
                        self.emit_progress(pct, f"{checked}/{total} path")
                        ctx.logger.write(f"[*] Đã kiểm tra {checked}/{total}...")

            # ✅ Trả partial khi cancel
            if self.is_cancelled():
                self.emit_progress(None)
                ctx.logger.write(f"[!] Dirb dừng — {checked}/{total}, tìm {len(found)} mục")
                return {
                    "status": "error", "type": "cancelled",
                    "target": target_url, "found": found, "total": len(found),
                    "checked": checked, "wordlist_size": total,
                    "message": f"Dừng giữa chừng — quét {checked}/{total}, tìm {len(found)} mục",
                }

            priority = {"200": 1, "201": 1, "301": 2, "302": 3, "307": 3, "401": 4, "403": 5}
            found.sort(key=lambda x: priority.get(x["status"], 9))
            self.emit_progress(100, "Hoàn tất")

            self.render_panel({
                "title": f"🔍 DIRB — {target_url}",
                "html": (
                    f"<div class='kv-row'><span class='kv-key'>Target</span><span class='kv-val'>{target_url}</span></div>"
                    f"<div class='kv-row'><span class='kv-key'>Wordlist</span><span class='kv-val'>{total}</span></div>"
                    f"<div class='kv-row'><span class='kv-key'>Tìm thấy</span><span class='kv-val'>{len(found)}</span></div>"
                ),
                "actions": [
                    {"label": "Quét lại", "icon": "🔄", "color": "primary", "command": "dirb",
                     "params": {}, "prompt": {"field": "url", "message": "Nhập URL cần quét lại:", "default": target_url}},
                ],
            }, title="🔍 DIRB RESULT")

            return {
                "status": "success", "type": "dirb_result",
                "target": target_url, "found": found, "total": len(found),
                "wordlist_size": total,
                "wordlist_sources": [{"name": n, "count": c} for n, c in sources],
                "message": f"Tìm thấy {len(found)} mục trên {target_url}",
            }
        except InterruptedError:
            self.emit_progress(None)
            return {"status": "error", "type": "cancelled", "target": target_url,
                    "found": [], "total": 0, "message": "Dirb đã dừng"}
        finally:
            ctx.scanning = False 
          