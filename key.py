from math import sqrt
from dataclasses import dataclass
from buildings import BuildingType, Buildings

CENTER_KEYS = [(2, 3), (2, 6)]  # this should be rewritten, don't really like how this is not dynamic


class Key:
    def __init__(self, char: str, row: int, col: int):
        self.char: str = char
        self.row: int = row
        self.col: int = col
        self.building: BuildingType | None = None
        self.locked: bool = True
        self.activated: bool = False
        self.unlock_cost: int = int(10 + (min(
            sqrt((r - row) ** 2 + (c - col) ** 2)
            for r, c in CENTER_KEYS
        ) * 15))


class Keyboard:
    def __init__(self, layout: list[str], buildings: Buildings):
        self.keys = list()
        for row_id, char_row in enumerate(layout):
            for col_id, char in enumerate(list(char_row)):
                key = Key(char, row_id, col_id)
                if (row_id, col_id) in CENTER_KEYS:
                    key.locked = False
                    key.building = buildings.low_food if (row_id, col_id) == CENTER_KEYS[0] else buildings.low_money
                self.keys.append(key)
        self.char_rows = layout

    def get_by_char(self, char: str) -> Key:
        return next((item for item in self.keys if item.char.lower() == char.lower()), None)
