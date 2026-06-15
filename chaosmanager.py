import json

class ChaosManager:
    def __init__(self, file_path="data.json"):
        self.file_path = file_path
        self.data = self.load_data()

    def load_data(self):
        try:
            with open(self.file_path, 'r', encoding='utf-8') as f:
                content = json.load(f)
                # Đảm bảo file cấu trúc mới có đủ 2 nhánh
                if "equipments" not in content or "chaos_maps" not in content:
                    return {"equipments": [], "chaos_maps": {}}
                return content
        except:
            return {"equipments": [], "chaos_maps": {}}

    def save_data(self):
        with open(self.file_path, 'w', encoding='utf-8') as f:
            json.dump(self.data, f, indent=4, ensure_ascii=False)

    # --- QUẢN LÝ BẢN ĐỒ CHAOS ---
    def add_chaos(self, location):
        if location not in self.data["chaos_maps"]:
            self.data["chaos_maps"][location] = []
            self.save_data()

    def update_chaos(self, old_location, new_location):
        if old_location in self.data["chaos_maps"] and new_location not in self.data["chaos_maps"]:
            self.data["chaos_maps"][new_location] = self.data["chaos_maps"].pop(old_location)
            self.save_data()

    def delete_chaos(self, location):
        if location in self.data["chaos_maps"]:
            del self.data["chaos_maps"][location]
            self.save_data()

    # --- QUẢN LÝ VẬT PHẨM (EQUIPMENT) ---
    def get_equipment_by_name(self, name):
        for eq in self.data["equipments"]:
            if eq["name"].lower() == name.lower():
                return eq
        return None

    def add_equipment(self, location, equip_obj):
        # 1. Kiểm tra vật phẩm đã tồn tại trong danh mục gốc chưa
        existing_eq = self.get_equipment_by_name(equip_obj.name)
        if not existing_eq:
            # Nếu chưa có, thêm mới vào danh sách gốc
            self.data["equipments"].append(equip_obj.to_dict())
        else:
            # Nếu đã có, có thể cập nhật lại thông tin mới nhất (tùy chọn)
            existing_eq["type"] = equip_obj.type
            existing_eq["level"] = equip_obj.level
            existing_eq["effect"] = equip_obj.effect
            if equip_obj.img:
                existing_eq["img"] = equip_obj.img

        # 2. Gán liên kết trang bị vào bản đồ Chaos tương ứng (nếu chưa có)
        if location in self.data["chaos_maps"]:
            if equip_obj.name not in self.data["chaos_maps"][location]:
                self.data["chaos_maps"][location].append(equip_obj.name)
        
        self.save_data()

    def update_equipment(self, old_name, updated_obj):
        # Cập nhật thông tin ở danh mục gốc (Sửa 1 nơi, áp dụng toàn hệ thống)
        for eq in self.data["equipments"]:
            if eq["name"].lower() == old_name.lower():
                eq["name"] = updated_obj.name
                eq["type"] = updated_obj.type
                eq["level"] = updated_obj.level
                eq["effect"] = updated_obj.effect
                if updated_obj.img:
                    eq["img"] = updated_obj.img
                break

        # Cập nhật lại tên hiển thị trong các bản đồ nếu tên bị đổi
        if old_name.lower() != updated_obj.name.lower():
            for loc, items in self.data["chaos_maps"].items():
                if old_name in items:
                    idx = items.index(old_name)
                    items[idx] = updated_obj.name
        
        self.save_data()

    def delete_equipment_from_map(self, location, name):
        # Chỉ xóa liên kết rớt đồ ở bản đồ đó, không xóa vật phẩm gốc khỏi DB
        if location in self.data["chaos_maps"] and name in self.data["chaos_maps"][location]:
            self.data["chaos_maps"][location].remove(name)
            self.save_data()

    # --- CHỨC NĂNG TÌM KIẾM TỐI ƯU ---
    def search_farm_locations(self, search_names):
        # Chuẩn hóa danh sách tên nhập vào từ người dùng
        search_names = list(set([name.strip() for name in search_names if name.strip()]))
        search_names_lower = [n.lower() for n in search_names]
        
        if not search_names:
            return {"grouped_common": [], "separate": {}}

        # 1. Thu thập dữ liệu chi tiết của các vật phẩm được tìm kiếm
        item_details = {}
        for eq in self.data.get("equipments", []):
            if eq["name"].lower() in search_names_lower:
                # Tìm tên gốc viết hoa/thường chuẩn trong DB
                standard_name = eq["name"]
                item_details[standard_name] = eq

        # Map lưu trữ: Map nào rớt những item nào trong bộ tìm kiếm
        map_to_matched_items = {}
        for loc, items in self.data.get("chaos_maps", {}).items():
            matched = []
            for item_name in items:
                if item_name.lower() in search_names_lower:
                    # Lấy tên chuẩn từ item_details hoặc giữ nguyên
                    standard_name = next((k for k in item_details if k.lower() == item_name.lower()), item_name)
                    matched.append(standard_name)
            if matched:
                map_to_matched_items[loc] = tuple(sorted(matched))

        # --- XỬ LÝ TRƯỜNG HỢP 1: FARM CHUNG (GOM NHÓM TỐI ĐA) ---
        # Đảo ngược dữ liệu: Nhóm các vật phẩm giống nhau -> Xem có những map nào chứa nhóm này
        items_group_to_maps = {}
        for loc, items_tuple in map_to_matched_items.items():
            if items_tuple not in items_group_to_maps:
                items_group_to_maps[items_tuple] = []
            items_group_to_maps[items_tuple].append(loc)

        grouped_common_results = []
        for items_tuple, locs in items_group_to_maps.items():
            # Chỉ tính là farm chung/nhóm nếu nhóm đó có từ 2 món trở lên, 
            # HOẶC trường hợp đặc biệt người dùng chỉ tìm đúng 1 món duy nhất.
            if len(items_tuple) >= 2 or len(search_names) == 1:
                item_list_details = [item_details[name] for name in items_tuple if name in item_details]
                
                grouped_common_results.append({
                    "equip_list": item_list_details,
                    "match_count": len(items_tuple),
                    "maps": locs
                })
        
        # Sắp xếp kết quả Farm chung theo thứ tự ưu tiên: Map nào chứa nhiều món trùng nhất lên đầu
        grouped_common_results.sort(key=lambda x: x["match_count"], reverse=True)
        # Sắp xếp các trang bị theo thuộc tính level
        for group in grouped_common_results:
            group["equip_list"].sort(key=lambda x: x.get("level", 0), reverse=True)
        print("Grouped Common Results:", grouped_common_results)
            
        # --- XỬ LÝ TRƯỜNG HỢP 2: FARM LẺ (MỖI MÓN MỖI NƠI) ---
        separate_results = {}
        for standard_name in item_details.keys():
            separate_results[standard_name] = []
            for loc, items in self.data.get("chaos_maps", {}).items():
                if any(i.lower() == standard_name.lower() for i in items):
                    separate_results[standard_name].append(loc)

        return {
            "grouped_common": grouped_common_results, 
            "separate": separate_results,
            "item_details": item_details
        }