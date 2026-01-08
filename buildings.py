import random
from dataclasses import dataclass, field
from pathlib import Path

from resources import Resources, Resource


@dataclass
class BuildingType:
    name: str
    symbol: str
    file_path: str | Path
    purchase_cost: int
    output_resource: Resource
    output_amount: int
    input_resource: Resource | None = None
    input_amount: int | None = None
    _lines: list[str] = field(default=None, init=False, repr=False)

    @property
    def lines(self) -> list[str]:
        if self._lines is None:
            with Path(self.file_path).open(encoding="utf-8") as f:
                self._lines = [line.strip() for line in f if line.strip()]
        return self._lines

    def __repr__(self):
        output_str = f"+{self.output_amount}{self.output_resource.symbol}"
        input_str = f"-{self.input_amount}{self.input_resource.symbol}" if self.input_resource else "-"
        return f"{self.name:<10} {self.symbol:<4} ${self.purchase_cost:<5} {output_str:<15} {input_str:<10}"

    def get_text(self) -> str:
        # return "a"
        return random.choice(self.lines)


@dataclass
class Buildings:
    low_money = BuildingType("Market", "🏪", "building_texts/low_money.csv", 100, Resources.money, 20)
    medium_money = BuildingType("Bank", "🏦", "building_texts/medium_money.csv", 300, Resources.money, 100)
    high_money = BuildingType("Factory", "🏭", "building_texts/high_money.csv", 500, Resources.money, 200)
    low_food = BuildingType("Hut", "🛖", "building_texts/low_food.csv", 10, Resources.food, 5)
    high_food = BuildingType("Farm", "🚜", "building_texts/high_food.csv", 50, Resources.food, 15)
    low_military = BuildingType("Tent", "⛺", "building_texts/low_military.csv", 5, Resources.military, 2, Resources.food, 1)
    high_military = BuildingType("Barracks", "⚔", "building_texts/high_military.csv", 100, Resources.military, 10, Resources.food, 5)
    low_knowledge = BuildingType("School", "🏫", "building_texts/low_knowledge.csv", 75, Resources.knowledge, 10)
    high_knowledge = BuildingType("Library", "📚", "building_texts/high_knowledge.csv", 150, Resources.knowledge, 25)

    def __iter__(self):
        yield from [self.low_money, self.medium_money, self.high_money,
                    self.low_food, self.high_food,
                    self.low_military, self.high_military,
                    self.low_knowledge, self.high_knowledge
                    ]

    def find_building_by_name(self, name):
        """
        Returns the first building found with the given name (could pose trouble with duplicate buildings)
        """
        return [building for building in self if building.name.lower() == name.lower()][0]
