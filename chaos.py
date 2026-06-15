class Equipment:
    def __init__(self, name, type, effect, level, img=None):
        self.name = name
        self.type = type
        self.effect = effect
        self.level = level
        self.img = img if img else "" 

    def to_dict(self):
        return {
            "name": self.name,
            "type": self.type,
            "effect": self.effect,
            "level": self.level,
            "img": self.img 
        }

class Chaos:
    def __init__(self, location, equipment_list=None):
        self.location = location
        self.equipment_list = equipment_list if equipment_list is not None else []

    def to_dict(self):
        return {
            "location": self.location,
            "equipment_list": [e.to_dict() for e in self.equipment_list]
        }