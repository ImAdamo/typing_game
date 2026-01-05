import curses
from dataclasses import dataclass


class Color:
    """
    Represents a specific color definition.
    Automatically assigns a sequential index and handles curses calls.
    """
    _auto_index = 1

    def __init__(self, foreground: int, background: int):
        self.fg = foreground
        self.bg = background
        self.index = Color._auto_index
        Color._auto_index += 1

    def init_pair(self):
        """Initializes the color pair in the curses library."""
        curses.init_pair(self.index, self.fg, self.bg)

    @property
    def pair(self) -> int:
        """Returns the curses color pair attribute."""
        return curses.color_pair(self.index)


class Colors:
    """
    Container for all color constants.
    """
    TEXT = Color(curses.COLOR_WHITE, curses.COLOR_BLACK)
    ACTIVE_KEY = Color(curses.COLOR_BLACK, curses.COLOR_GREEN)
    GREY_KEY = Color(curses.COLOR_BLACK, curses.COLOR_WHITE)
    LOCKED_KEY = Color(curses.COLOR_WHITE, curses.COLOR_RED)
    SUCCESS = Color(curses.COLOR_GREEN, curses.COLOR_BLACK)
    WARNING = Color(curses.COLOR_YELLOW, curses.COLOR_BLACK)
    ERROR = Color(curses.COLOR_RED, curses.COLOR_BLACK)

    # Phase border colors
    MORNING = Color(curses.COLOR_CYAN, curses.COLOR_BLACK)
    NOON = Color(curses.COLOR_YELLOW, curses.COLOR_BLACK)
    EVENING = Color(curses.COLOR_MAGENTA, curses.COLOR_BLACK)
    NIGHT = Color(curses.COLOR_BLUE, curses.COLOR_BLACK)

    SHADOW = Color(curses.COLOR_BLACK, 237)

    @staticmethod
    def init():
        """
        Initializes all color pairs defined in this class.
        Call this after curses.initscr().
        """
        # Iterate over class attributes to find ColorDef instances
        for member in vars(Colors).values():
            if isinstance(member, Color):
                if member != Colors.SHADOW:
                    member.init_pair()
                elif curses.has_extended_color_support():
                    member.init_pair()
