import hashlib
import json

def tu_dong_them_wifi(file_manager, filename, new_wifi_list):
    """
    Tự động đánh số, kiểm tra MAC và cập nhật SHA256 để file không bị 'lỏ'.
    """
    # 1. Đọc dữ liệu cũ
    old_obj = file_manager.read_file(filename)
    
    # Khởi tạo cấu trúc nếu file trống
    if old_obj is None or "data" not in old_obj:
        existing_data = {}
    else:
        existing_data = old_obj["data"]

    # 2. Lấy MAC của WiFi mới
    new_mac = new_wifi_list[0].lower()
    target_key = None

    # 3. Kiểm tra xem MAC đã tồn tại chưa
    for key, info in existing_data.items():
        if info[0].lower() == new_mac:
            target_key = key
            break

    # 4. Cập nhật hoặc Thêm mới dữ liệu
    if target_key is not None:
        existing_data[target_key] = new_wifi_list
        log_msg = f"[*] 🔄 Đã cập nhật & tính lại Hash cho MAC [{new_mac}] tại vị trí: {target_key}"
    else:
        next_index = str(len(existing_data)) 
        existing_data[next_index] = new_wifi_list
        log_msg = f"[+] ✨ Thêm mới & tính lại Hash cho vị trí: {next_index}"

    # 5. QUAN TRỌNG: Tính toán lại SHA256 cho dữ liệu mới
    # Chuyển data sang dạng string chuẩn (sort_keys=True để đảm bảo thứ tự không làm nhảy Hash)
    data_string = json.dumps(existing_data, sort_keys=True)
    new_sha256 = hashlib.sha256(data_string.encode('utf-8')).hexdigest()

    # 6. Đóng gói lại đúng cấu trúc file của bác (có data và sha256)
    final_payload = {
        "data": existing_data,
        "sha256": new_sha256
    }

    # 7. Lưu file thông qua file_manager
    # Lưu ý: Truyền payload đã có SHA256 mới vào
    success = file_manager.save_file(filename, final_payload)
    
    if success:
        print(log_msg)
    
    return success
