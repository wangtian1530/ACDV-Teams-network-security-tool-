import os
import subprocess

def dongcong(ports):
    for port in ports:
        try:
            # Tìm PID (Process ID) đang chạy trên cổng đó
            # Lệnh: fuser -k -n tcp [port] sẽ ép đóng ngay lập tức
            print(f"[*] Đang kiểm tra và giải phóng cổng: {port}")
            
            # Cách 1: Dùng fuser (Rất mạnh trên Linux/Termux)
            subprocess.run(["fuser", "-k", f"{port}/tcp"], stderr=subprocess.DEVNULL)
            
            # Cách 2: Dự phòng bằng lsof nếu fuser không có sẵn
            pid = subprocess.check_output(["lsof", "-t", f"-i:{port}"]).strip().decode()
            if pid:
                os.system(f"kill -9 {pid}")
                print(f"[+] Đã ép đóng PID {pid} trên cổng {port}")
        except Exception:
            # Nếu cổng đã trống thì bỏ qua
            pass

# Sử dụng cho cổng 80 và 81