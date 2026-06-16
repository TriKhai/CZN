from utils import get_equipment_data

class Character:
    def __init__(self, name, suggested_equipments):
        self.name = name
        self.equipment = suggested_equipments 
        
        equipments_data = get_equipment_data(suggested_equipments)

        rarity_order = {
            "Mystic": 0,
            "Legend": 1,
            "Rare": 2
        }

        sort_key = lambda x: rarity_order.get(x["level"], 9)

        self.weapon_list = sorted([x for x in equipments_data if x["type"].lower() == "weapon"], key=sort_key)
        self.armor_list = sorted([x for x in equipments_data if x["type"].lower() == "armor"], key=sort_key)
        self.trinket_list = sorted([x for x in equipments_data if x["type"].lower() == "trinket"], key=sort_key)
    
    def getweapon(self):
        return self.weapon_list
    
    def getarmor(self):
        return self.armor_list
    
    def gettrinket(self):
        return self.trinket_list
    

# Test
equipment_names = [
    "Intellect of Discord",
    "Tentacles of Chaos",
    "Second Method",
    "Dagger That Tricked the Shadow",
    "Obsidian Sword",
    "Fairy King's Crown",
    "Dimensional Cube",
    "Amorphous Cube"
]

diana = Character("Diana", equipment_names)

print("\n--- WEAPON LIST---")
print(diana.getweapon())
print("\n--- ARMOR LIST---")
print(diana.getarmor())
print("\n--- TRINKET LIST---")
print(diana.gettrinket())