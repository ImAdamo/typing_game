from dataclasses import dataclass, asdict


@dataclass
class Resource:
    name: str
    symbol: str
    amount: int

    def __repr__(self):
        return f"{self.name}: {self.amount}{self.symbol}"

    def add(self, amount: int):
        self.amount += amount

    def subtract(self, amount: int):
        self.amount -= min(amount, self.amount)


@dataclass
class Resources:
    money = Resource("Money", "$", 50)
    food = Resource("Food", "🍖", 0)
    military = Resource("Military", "🪖", 0)
    knowledge = Resource("Knowledge", "🧠", 0)
    __instance = None

    def __iter__(self):
        yield from [self.money,
                    self.food,
                    self.military,
                    self.knowledge
                    ]

    def __repr__(self):
        return " | ".join((str(i) for i in self))

    def find_resource_by_name(self, name):
        """
        Returns the first building found with the given name (could pose trouble with duplicate buildings)
        """
        return [resource for resource in self if resource.name.lower() == name.lower()][0]

    @staticmethod
    def get_instance():
        if Resources.__instance is None:
            Resources.__instance = Resources()
        return Resources.__instance
