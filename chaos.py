class Chaos:
    def __init__(self, location, equipment_list=None):
        self.location = location
        self.equipment_list = equipment_list if equipment_list is not None else []

    def to_dict(self):
        return {
            "location": self.location,
            "equipment_list": [e.to_dict() for e in self.equipment_list]
        }