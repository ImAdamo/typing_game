import random
from dataclasses import dataclass, field
from pathlib import Path
import json

from resources import Resources, Resource


@dataclass
class BuildingType:
    id: str
    name: str
    symbol: str
    purchase_cost: int
    output_resource: Resource
    output_amount: int
    input_resource: Resource | None
    input_amount: int | None
    texts: list[str]

    def __repr__(self):
        output_str = f"+{self.output_amount}{self.output_resource.symbol}"
        input_str = f"-{self.input_amount}{self.input_resource.symbol}" if self.input_resource else "-"
        return f"{self.name:<10} {self.symbol:<4} ${self.purchase_cost:<5} {output_str:<15} {input_str:<10}"

    def get_text(self) -> str:
        return "a"
        # return random.choice(self.texts)


@dataclass(init=False)
class Buildings:
    def __init__(self, file_path):
        with Path(file_path).open(encoding="utf-8") as f:
            data = json.load(f)
            resources = Resources.get_instance()
            self.buildings = dict()
            for building in data["buildings"]:
                building["output_resource"] = resources.find_resource_by_name(building["output_resource"])
                if building["input_resource"] is not None:
                    building["input_resource"] = resources.find_resource_by_name(building["input_resource"])
                building_type = BuildingType(**building)
                self.buildings[building_type.id] = building_type

    def __iter__(self):
        return iter(self.buildings.values())

    def find_building_by_name(self, buidling_name: str) -> BuildingType:
        for building in self:
            if building.name.lower() == buidling_name.lower():
                return building

    def find_building_by_id(self, building_id: str) -> BuildingType:
        """
        Returns the first building found with the given id
        """
        return self.buildings.get(building_id)
