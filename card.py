class NormalCard:
    def __init__(self, name, cost, effect, img=None, status=None):
        self.name = name
        self.status = status
        self.cost = cost
        self.img = img if img else ""
        self.effect = effect

class EpiphaniesCard(NormalCard):
    def __init__(self, name, cost, rate, effect, img=None, status=None, epiphanies_rate=None, epiphanies_cost=None, epiphanies_effect=None, epiphanies_status=None):
        super().__init__(name, img)
        self.epiphanies_status = epiphanies_status
        self.epiphanies_rate = epiphanies_rate
        self.epiphanies_cost = epiphanies_cost
        self.epiphanies_effect = epiphanies_effect

class GeneratedCard(NormalCard):
    def __init__(self, name, cost, effect, img=None, status=None):
        super().__init__(name, cost, effect, img, status)
        