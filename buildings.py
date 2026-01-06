from dataclasses import dataclass
from resources import Resources, Resource


@dataclass
class BuildingType:
    name: str
    symbol: str
    purchase_cost: int
    output_resource: Resource
    output_amount: int
    input_resource: Resource | None = None
    input_amount: int | None = None

    def __repr__(self):
        output_str = f"+{self.output_amount}{self.output_resource.symbol}"
        input_str = f"-{self.input_amount}{self.input_resource.symbol}" if self.input_resource else "-"
        return f"{self.name:<10} {self.symbol:<4} ${self.purchase_cost:<5} {output_str:<15} {input_str:<10}"

    def get_text(self) -> str:
        return "This is a placeholder."


@dataclass
class Buildings:
    low_money = BuildingType("Market", "🏪", 100, Resources.money, 20)
    medium_money = BuildingType("Bank", "🏦", 300, Resources.money, 100)
    high_money = BuildingType("Factory", "🏭", 500, Resources.money, 200)
    low_food = BuildingType("Hut", "🛖", 10, Resources.food, 5)
    high_food = BuildingType("Farm", "🚜", 50, Resources.food, 15)
    low_military = BuildingType("Tent", "⛺", 5, Resources.military, 2, Resources.food, 1)
    high_military = BuildingType("Barracks", "⚔", 100, Resources.military, 10, Resources.food, 5)
    low_knowledge = BuildingType("School", "🏫", 75, Resources.knowledge, 10)
    high_knowledge = BuildingType("Library", "📚", 150, Resources.knowledge, 25)

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
