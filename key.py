from math import sqrt

CENTER_KEYS = [(2, 3), (2, 6)]  # this should be rewritten, don't really like how this is not dynamic


class Key:
    def __init__(self, char, row, col):
        self.char = char
        self.row = row
        self.col = col
        self.building = None
        self.locked = True
        self.unlock_cost = 0

        # Calculate Unlock Cost
        dist = min(
            sqrt((r - row) ** 2 + (c - col) ** 2)
            for r, c in CENTER_KEYS
        )
        self.unlock_cost = int(10 + (dist * 15))
