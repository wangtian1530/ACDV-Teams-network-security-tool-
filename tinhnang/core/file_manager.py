# tinhnang/core/file_manager.py
import os
import struct
import json
import hashlib
import shutil

from .paths import DATA_DIR, ROOT_DIR, ensure_dirs


class FileManager:
    """Quản lý file .acdv — LƯU VÀO data/ + auto-migrate file cũ ở root."""

    def __init__(self, secret_key=0x69):
        ensure_dirs()
        self.data_dir = DATA_DIR
        self.root_dir = ROOT_DIR   # giữ tương thích code cũ

        self.fingerprint_hex = bytes([0xAC, 0x44, 0x56])
        self.magic_end = bytes([0x55, 0xAA])
        self.secret_key = secret_key
        self.START_OBJ = bytes([0x02])
        self.END_OBJ = bytes([0x03])
        self.SEP_FIELD = bytes([0x1F])
        self.SEP_RECORD = bytes([0x1E])

        self._migrate_legacy()

    # -----------------------------------------------------------------
    def _migrate_legacy(self):
        """Di chuyển file cũ ở root vào data/ (chạy 1 lần, an toàn)."""
        for fname in ["networks.acdv", "networks.acdv.backup"]:
            old = os.path.join(self.root_dir, fname)
            new = os.path.join(self.data_dir, fname)
            if os.path.exists(old) and not os.path.exists(new):
                try:
                    shutil.move(old, new)
                    print(f"[*] Đã chuyển {fname} → data/")
                except Exception as e:
                    print(f"[!] Không chuyển được {fname}: {e}")

    # -----------------------------------------------------------------
    def _get_safe_path(self, filename):
        return os.path.join(self.data_dir, os.path.basename(filename))

    def _xor_cipher(self, data: bytes) -> bytes:
        return bytes([b ^ self.secret_key for b in data])

    def _calculate_hash(self, data_bytes):
        return hashlib.sha256(data_bytes).hexdigest()

    def save_file(self, filename, content, data_type="OBJ", who_am_i="ACDV_MODULE"):
        prepared_data = b""
        if data_type == "OBJ" and isinstance(content, dict):
            for idx, fields in content.items():
                record = self.START_OBJ
                if isinstance(fields, (list, tuple)):
                    record += self.SEP_FIELD.join([str(f).encode("utf-8") for f in fields])
                else:
                    record += str(fields).encode("utf-8")
                record += self.END_OBJ + self.SEP_RECORD
                prepared_data += record
        else:
            prepared_data = str(content).encode("utf-8")

        encrypted_mdata = self._xor_cipher(prepared_data)
        data_hash = self._calculate_hash(prepared_data)

        header_dict = {
            "owner": who_am_i,
            "sig": f"OFFLINE_{hashlib.md5(encrypted_mdata[:10]).hexdigest()[:8]}",
            "format": data_type,
        }
        header_bytes = json.dumps(header_dict).encode("utf-8")
        header_len = struct.pack(">H", len(header_bytes))

        full_packet = (
            self.fingerprint_hex
            + header_len
            + header_bytes
            + data_hash.encode("ascii")
            + encrypted_mdata
            + self.magic_end
        )

        try:
            with open(self._get_safe_path(filename), "wb") as f:
                f.write(full_packet)
            return {"status": True, "msg": "Đã sửa và ký file thành công!"}
        except Exception as e:
            return {"status": False, "msg": str(e)}

    def read_file(self, filename):
        path = self._get_safe_path(filename)
        if not os.path.exists(path):
            return {"status": "NOT_FOUND", "data": None}

        try:
            with open(path, "rb") as f:
                raw = f.read()

            f_print = raw.startswith(self.fingerprint_hex)

            h_len = struct.unpack(">H", raw[3:5])[0]
            header = json.loads(raw[5 : 5 + h_len].decode("utf-8"))

            hash_pos = 5 + h_len
            stored_hash = raw[hash_pos : hash_pos + 64].decode("ascii")

            mdata_start = hash_pos + 64
            mdata_end = len(raw) - 2
            encrypted_mdata = raw[mdata_start:mdata_end]
            decrypted_mdata = self._xor_cipher(encrypted_mdata)

            current_hash = self._calculate_hash(decrypted_mdata)
            integrity = current_hash == stored_hash

            final_data = None
            if header["format"] == "OBJ":
                final_data = {}
                records = decrypted_mdata.split(self.SEP_RECORD)
                for i, r in enumerate(records):
                    if self.START_OBJ in r and self.END_OBJ in r:
                        clean_r = r.split(self.START_OBJ)[1].split(self.END_OBJ)[0]
                        final_data[str(i)] = [
                            f.decode("utf-8") for f in clean_r.split(self.SEP_FIELD)
                        ]
            else:
                final_data = decrypted_mdata.decode("utf-8")

            return {
                "status": "ACDV-Files" if f_print else "UNKNOWN_FILE",
                "format": header["format"],
                "fingerprint": {"value": "0xACDV", "match": f_print},
                "header": header,
                "integrity": {"hash": stored_hash, "is_valid": integrity},
                "data": final_data,
            }

        except Exception as e:
            return {"status": "ERROR", "msg": str(e)}

    def sync_and_upgrade_database(self, filename="networks.acdv"):
        print("\n[*] Đang đồng bộ database (GIỮ NGUYÊN DATA CŨ)...")
        old_path = self._get_safe_path(filename)
        backup_path = self._get_safe_path(f"{filename}.backup")

        if os.path.exists(old_path):
            shutil.copy2(old_path, backup_path)
            print(f"[*] Đã backup database cũ thành {filename}.backup")

        current_data = self.read_file(filename)

        if current_data.get("status") != "ACDV-Files" or not current_data.get("data"):
            print("[!] Không tìm thấy database hoặc database rỗng!")
            return False

        old_data = current_data["data"]
        print(f"[*] Database hiện tại có {len(old_data)} bản ghi")

        password_to_id = {}
        password_counter = 0

        for key, record in old_data.items():
            if len(record) >= 3:
                password = record[2]
                if password not in password_to_id:
                    password_to_id[password] = str(password_counter)
                    password_counter += 1

        print(f"[*] Tìm thấy {len(password_to_id)} password UNIQUE")

        new_data = {}
        upgraded_count = 0

        for key, record in old_data.items():
            if len(record) >= 3:
                bssid = record[0]
                ssid = record[1]
                password = record[2]
                security = record[3] if len(record) > 3 else "wpa2"
                password_id = password_to_id.get(password, "unknown")
                new_record = [bssid, ssid, password, security, password_id]
                new_data[key] = new_record
                upgraded_count += 1
            else:
                new_data[key] = record

        print(f"[*] Đã nâng cấp {upgraded_count} bản ghi (thêm password_id)")

        result = self.save_file(filename, new_data, data_type="OBJ", who_am_i="WIFI_SCANNER")

        if result.get("status"):
            print("[+] Đồng bộ database thành công!")
            return True
        else:
            print(f"[-] Lỗi khi lưu database: {result.get('msg')}")
            if os.path.exists(backup_path):
                shutil.copy2(backup_path, old_path)
                print("[*] Đã khôi phục database từ backup")
            return False

    def restore_backup(self, filename="networks.acdv"):
        backup_path = self._get_safe_path(f"{filename}.backup")
        original_path = self._get_safe_path(filename)
        if os.path.exists(backup_path):
            shutil.copy2(backup_path, original_path)
            print(f"[+] Đã khôi phục database từ {filename}.backup")
            return True
        print("[-] Không tìm thấy file backup!")
        return False

    def get_password_by_id(self, filename, password_id):
        data = self.read_file(filename)
        if data.get("status") != "ACDV-Files" or not data.get("data"):
            return None
        try:
            password_id = str(password_id)
            for key, record in data["data"].items():
                if len(record) >= 5 and record[4] == password_id:
                    return {
                        "record_id": key,
                        "bssid": record[0],
                        "ssid": record[1],
                        "password": record[2],
                        "security": record[3],
                        "password_id": record[4],
                    }
                elif len(record) >= 3 and password_id == "unknown":
                    return {
                        "record_id": key,
                        "bssid": record[0],
                        "ssid": record[1],
                        "password": record[2],
                        "security": record[3] if len(record) > 3 else "wpa2",
                        "password_id": "unknown",
                    }
        except Exception:
            pass
        return None

    def get_unique_passwords(self, filename="networks.acdv"):
        data = self.read_file(filename)
        if data.get("status") != "ACDV-Files" or not data.get("data"):
            return {}
        unique_passwords = {}
        for record in data["data"].values():
            if len(record) >= 3:
                password = record[2]
                pwd_id = record[4] if len(record) >= 5 else str(hash(password) % 1000)
                if pwd_id not in unique_passwords:
                    unique_passwords[pwd_id] = password
        return unique_passwords