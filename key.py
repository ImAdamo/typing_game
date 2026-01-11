from math import sqrt
from dataclasses import dataclass
from buildings import BuildingType, Buildings

CENTER_KEYS: dict[str, tuple[int, int]] = dict()


class Key:
    def __init__(self, char: str, row: int, col: int):
        self.char: str = char
        self.row: int = row
        self.col: int = col
        self.building: BuildingType | None = None
        self.locked: bool = True
        self.active: bool = True
        self.unlock_cost: int = int((min(
            sqrt((r - row) ** 2 + (c - col) ** 2)
            for r, c in CENTER_KEYS.values()
        ) * 5))


class Keyboard:
    def __init__(self, layout: list[str], center_keys: list[str]):
        global CENTER_KEYS
        for letter in center_keys:
            for row_idx, row in enumerate(layout):
                if letter in row:
                    col_idx = row.index(letter)
                    CENTER_KEYS[letter] = (row_idx, col_idx)
                    break

        self.keys = list()
        for row_id, char_row in enumerate(layout):
            for col_id, char in enumerate(list(char_row)):
                key = Key(char, row_id, col_id)
                self.keys.append(key)
        self.char_rows = layout

    def starting_keys(self, buildings):
        for key_char in CENTER_KEYS.keys():
            key = self.get_by_char(key_char)
            key.locked = False
            match key_char:
                case "f":
                    key.building = buildings.find_building_by_id("low_food")
                case "j":
                    key.building = buildings.find_building_by_id("low_money")

    def get_by_char(self, char: str) -> Key:
        return next((item for item in self.keys if item.char.lower() == char.lower()), None)

    def reset_keys(self):
        for key in self.keys:
            key.active = True
