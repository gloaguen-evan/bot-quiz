class Player:
    def __init__(self, name: str, name_equip: str):
        self.name: str = name
        self.name_equip: str = name_equip
        self.all_response: int = 0
        self.good_response: int = 0
        self.points: int = 0

    def add_points(self, value: int) -> int:
        self.points += value
        return self.points

    def remove_points(self, value: int) -> int:
        self.points -= value
        return self.points

    def clear_points(self):
        self.points = 0
