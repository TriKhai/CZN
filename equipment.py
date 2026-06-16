import json
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