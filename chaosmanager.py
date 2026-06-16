import json

class ChaosManager:
    def __init__(self, file_path="data/equipment_data.json"):
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

    # --- CHỨC NĂNG TÌM KIẾM TỐI ƯU VÀ SẮP XẾP ---
    def search_farm_locations(self, search_names):
        search_names = list(set([name.strip() for name in search_names if name.strip()]))
        search_names_lower = [n.lower() for n in search_names]
        
        if not search_names:
            return {"grouped_common": [], "separate": {}, "item_details": {}}

        type_order = {"weapon": 0, "armor": 1, "trinket": 2}
        rarity_order = {"mystic": 0, "legend": 1, "rare": 2}
        
        custom_sort_key = lambda x: (
            type_order.get(x.get("type", "").lower(), 9),
            rarity_order.get(x.get("level", "").lower(), 9)
        )

        # 1. Thu thập dữ liệu chi tiết của các vật phẩm được tìm kiếm
        item_details = {}
        for eq in self.data.get("equipments", []):
            if eq["name"].lower() in search_names_lower:
                standard_name = eq["name"]
                item_details[standard_name] = eq

        # Map lưu trữ: Map nào rớt những item nào trong bộ tìm kiếm
        map_to_matched_items = {}
        for loc, items in self.data.get("chaos_maps", {}).items():
            matched = []
            for item_name in items:
                if item_name.lower() in search_names_lower:
                    standard_name = next((k for k in item_details if k.lower() == item_name.lower()), item_name)
                    matched.append(standard_name)
            if matched:
                map_to_matched_items[loc] = tuple(sorted(matched))

        # --- XỬ LÝ TRƯỜNG HỢP 1: FARM CHUNG (GOM NHÓM TỐI ĐA) ---
        items_group_to_maps = {}
        for loc, items_tuple in map_to_matched_items.items():
            if items_tuple not in items_group_to_maps:
                items_group_to_maps[items_tuple] = []
            items_group_to_maps[items_tuple].append(loc)

        grouped_common_results = []
        for items_tuple, locs in items_group_to_maps.items():
            if len(items_tuple) >= 2 or len(search_names) == 1:
                item_list_details = [item_details[name] for name in items_tuple if name in item_details]
                
                # SẮP XẾP 1: Sắp xếp các trang bị bên trong từng group cụ thể
                item_list_details.sort(key=custom_sort_key)
                
                grouped_common_results.append({
                    "equip_list": item_list_details,
                    "match_count": len(items_tuple),
                    "maps": locs
                })
        
        # Sắp xếp các Group dựa trên: Map nào rớt nhiều món trùng nhất lên đầu
        grouped_common_results.sort(key=lambda x: x["match_count"], reverse=True)
            
        # --- XỬ LÝ TRƯỜNG HỢP 2: FARM LẺ (MỖI MÓN MỖI NƠI) ---
        separate_results = {}
        for standard_name in item_details.keys():
            separate_results[standard_name] = []
            for loc, items in self.data.get("chaos_maps", {}).items():
                if any(i.lower() == standard_name.lower() for i in items):
                    separate_results[standard_name].append(loc)

        # SẮP XẾP 2: Chuyển item_details thành một Dictionary đã được sắp xếp sẵn key-value
        # Giúp client/frontend khi duyệt qua dict này sẽ hiện đúng thứ tự Weapon -> Armor -> Trinket
        sorted_item_details = dict(
            sorted(item_details.items(), key=lambda item: custom_sort_key(item[1]))
        )

        return {
            "grouped_common": grouped_common_results, 
            "separate": separate_results,
            "item_details": sorted_item_details
        }