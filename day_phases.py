from dataclasses import dataclass
from colors import Colors


@dataclass
class Phase:  # Here mostly just for future additions (could go with a simpler structure rn)
    name: str
    color: int


@dataclass
class Phases:
    """
    Class holding phase information along with the number of days.
    """
    phases = [
        Phase("Morning", Colors.MORNING),
        Phase("Afternoon", Colors.NOON),
        Phase("Evening", Colors.EVENING),
        Phase("Night", Colors.NIGHT)
    ]
    current_phase = phases[0]
    day = 1

    def next_phase(self):
        """
        Advances the phase to the next one, if night days += 1
        """
        self.current_phase = self.phases[(self.phases.index(self.current_phase) + 1) % 4]
        if self.current_phase == self.phases[0]:
            self.day += 1

    def is_night(self):
        """
        Checks if the current phase is Night
        """
        return self.current_phase.name == self.phases[-1].name
