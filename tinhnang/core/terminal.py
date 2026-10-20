# tinhnang/core/terminal.py
import subprocess
import signal
import os
import sys
import time


class chay_terminal:
    """Chạy lệnh terminal với process dùng chung (class-level)."""
    _process = None

    @classmethod
    def run_cmd(cls, command, **kwargs):
        if cls._process is not None and cls._process.poll() is None:
            return {
                "type": "cmd",
                "start": False,
                "message": "  Terminal Bận Rồi ..Chờ Lát🫡",
            }

        flags = []
        for k, v in kwargs.items():
            if v is True:
                flags.append(f"-{k}")
            elif v is not False and v is not None:
                flags.append(f"-{k} {v}")

        full_cmd = f"{command} {' '.join(flags)}".strip()

        try:
            cls._process = subprocess.Popen(
                full_cmd,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                preexec_fn=os.setsid if hasattr(os, "setsid") else None,
            )
            return {"type": "cmd", "start": True, "message": f"🚀 Kích hoạt: {full_cmd}"}
        except Exception as e:
            return {"type": "cmd", "start": False, "message": f"❌ Lỏ Rôi:🤧....{str(e)}"}

    @classmethod
    def dang_chay(cls):
        if cls._process is None:
            return {"type": "cmd", "start": False, "message": "Chưa có tiến trình nào!"}

        try:
            if cls._process.stdout:
                while True:
                    line = cls._process.stdout.readline()
                    if line:
                        print(f"📡 {line.strip()}")
                        sys.stdout.flush()

                    trang_thai = cls._process.poll()
                    if not line and trang_thai is not None:
                        break

                    time.sleep(0.01)

            return {
                "type": "cmd",
                "status": "finished",
                "exit_code": cls._process.poll(),
                "message": "Terminal đã hoàn thành:😎",
            }
        except Exception as e:
            return {"type": "error", "message": str(e)}

    @classmethod
    def dang_thuc_su_chay(cls):
        return cls._process is not None and cls._process.poll() is None

    @classmethod
    def dung_terminal(cls):
        if cls.dang_thuc_su_chay():
            try:
                if hasattr(os, "killpg"):
                    os.killpg(os.getpgid(cls._process.pid), signal.SIGINT)
                else:
                    cls._process.terminate()
                cls._process.wait()
                return {"type": "cmd", "start": True, "message": "Terminal Đã Dừng:🤐"}
            except Exception as e:
                return {"error": str(e)}
        return {"type": "cmd", "start": False, "message": "Terminal Không Chạy...🫡!"}