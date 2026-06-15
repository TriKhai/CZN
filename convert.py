import csv
import json
import os
import shutil

CSV_FILE = "data_trang_bi_czn.csv"
JSON_FILE = "data.json"
TARGET_IMAGE_FOLDER = os.path.join("static", "img")

if not os.path.exists(TARGET_IMAGE_FOLDER):
    os.makedirs(TARGET_IMAGE_FOLDER)

def convert_data():
    if not os.path.exists(CSV_FILE):
        print(f" [!] Không tìm thấy file dữ liệu cào '{CSV_FILE}'. Hãy chạy file cào trước!")
        return

    current_data = {"equipments": [], "chaos_maps": {}}
    
    if os.path.exists(JSON_FILE):
        try:
            with open(JSON_FILE, "r", encoding="utf-8") as f:
                loaded_data = json.load(f)
                if isinstance(loaded_data, dict):
                    if "chaos_maps" in loaded_data and isinstance(loaded_data["chaos_maps"], dict):
                        current_data["chaos_maps"] = loaded_data["chaos_maps"]
                    if "equipments" in loaded_data and isinstance(loaded_data["equipments"], list):
                        current_data["equipments"] = loaded_data["equipments"]
        except Exception as e:
            print(f" [!] Lỗi khi đọc dữ liệu cũ: {e}")

    existing_equipments = {item["name"]: idx for idx, item in enumerate(current_data["equipments"])}

    print(f"Đang ánh xạ Type/Level chuẩn và nạp vào cấu trúc hệ thống {JSON_FILE}...")
    count_new_eq = 0
    count_update_eq = 0
    count_new_map_relations = 0

    with open(CSV_FILE, mode="r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        
        for row in reader:
            name = row.get("Tên trang bị", "").strip()
            eq_type = row.get("Loại", "Trinket").strip()       # Đọc từ CSV cào mới
            eq_level = row.get("Độ hiếm", "Rare").strip()     # Đọc từ CSV cào mới
            effect = row.get("Hiệu ứng / Kỹ năng", "").strip()
            chaos_map = row.get("Map Chaos", "").strip()
            local_img_path = row.get("Vị trí file ảnh PNG hoàn chỉnh", "").strip()
            
            if not name:
                continue

            # Đồng bộ ảnh tĩnh cho Web Flask
            web_img_path = ""
            if local_img_path and os.path.exists(local_img_path):
                filename = os.path.basename(local_img_path)
                destination_path = os.path.join(TARGET_IMAGE_FOLDER, filename)
                try:
                    shutil.copy2(local_img_path, destination_path)
                    web_img_path = f"/static/img/{filename}"
                except Exception:
                    pass

            equipment_obj = {
                "name": name,
                "type": eq_type,       # Gán chính xác Weapon/Armor/Trinket
                "level": eq_level,     # Gán chính xác Mystic/Legend/Rare
                "effect": effect,
                "img": web_img_path
            }

            if name in existing_equipments:
                idx = existing_equipments[name]
                # Cập nhật thông tin ảnh, type, level, hiệu ứng mới nhất tự động từ web cào về
                current_data["equipments"][idx] = equipment_obj
                count_update_eq += 1
            else:
                current_data["equipments"].append(equipment_obj)
                count_new_eq += 1

            # Xử lý đưa vào từng Map lẻ tương ứng trong chaos_maps
            if chaos_map and chaos_map != "Unknown Map":
                individual_maps = [m.strip() for m in chaos_map.split(",") if m.strip()]
                for single_map in individual_maps:
                    if single_map not in current_data["chaos_maps"]:
                        current_data["chaos_maps"][single_map] = []
                    if name not in current_data["chaos_maps"][single_map]:
                        current_data["chaos_maps"][single_map].append(name)
                        count_new_map_relations += 1

    with open(JSON_FILE, "w", encoding="utf-8") as f:
        json.dump(current_data, f, indent=4, ensure_ascii=False)

    print(f"\n=== ĐỒNG BỘ HOÀN HẢO ===")
    print(f"- Kho trang bị (equipments): Đã thêm {count_new_eq}, Đã cập nhật {count_update_eq}")
    print(f"- Đã tự động phân chia đồ vào các map lẻ.")

if __name__ == "__main__":
    convert_data()