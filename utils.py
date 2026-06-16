import json

def get_equipment_data(equipment_names):
    with open("equipment_data.json", "r", encoding="utf-8") as f:
        equipment_data = json.load(f)

    if isinstance(equipment_data, dict) and "equipments" in equipment_data:
        equipment_list = equipment_data["equipments"]
    else:
        equipment_list = equipment_data 

    equipment_dict = {item["name"]: item for item in equipment_list}
    
    result = []
    for name in equipment_names:
        if name in equipment_dict:
            result.append(equipment_dict[name]) 
        else:
            print(f"Cảnh báo: Không tìm thấy trang bị có tên '{name}'")
     
    return result