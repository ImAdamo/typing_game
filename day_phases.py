from dataclasses import dataclass
from colors import Colors


@dataclass
class Phase:  # Here mostly just for future additions (could go with a simpler structure rn)
    name: str
    color: int


@dataclass
class Phases:  # TODO: tried doing this with colors.get_color(colors.PHASE), but the colors had to be initialized first
    phases = [
        Phase("Morning", Colors.MORNING),
        Phase("Afternoon", Colors.NOON),
        Phase("Evening", Colors.EVENING),
        Phase("Night", Colors.NIGHT)
    ]
    current_phase = phases[0]

    def next_phase(self):
        self.current_phase = self.phases[(self.phases.index(self.current_phase) + 1) % 4]
