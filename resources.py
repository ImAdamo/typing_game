from dataclasses import dataclass


@dataclass
class Resource:
    """
    Single resource used for tracking amounts
    """
    name: str
    symbol: str
    amount: int

    def __repr__(self):
        return f"{self.name}: {self.amount}{self.symbol}"

    def add(self, amount: int):
        """
        Adds amount to the resource.amount
        Here for clarity
        """
        self.amount += amount

    def subtract(self, amount: int):
        """
        Subtracts amount from resource.amount
        Here for clarity
        """
        self.amount -= min(amount, self.amount)


@dataclass
class Resources:
    """
    Singleton class holding all information on resources for the game's needs.
    """
    money = Resource("Money", "🪙", 50)
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
        """
        Initializes an instance of Resources if it's not already made, else gives a reference to the one active.
        Enables singleton acting.
        """
        if Resources.__instance is None:
            Resources.__instance = Resources()
        return Resources.__instance
