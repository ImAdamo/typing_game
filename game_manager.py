from day_phases import Phases
from resources import Resources
from buildings import Buildings
from key import Keyboard, Key
from colors import Colors
from time import time

MODE_IDLE = 'IDLE'
MODE_TYPING = 'TYPING_JOB'
MODE_BUILDING_SELECT = 'TYPING_BUILD'
MODE_GAME_OVER = 'GAME_OVER'
MODE_INITIAL = 'INITIAL_SCREEN'
BUILDINGS_FILE_PATH = 'assets/buildings.json'
CENTER_KEYS = ["f", "j", "g", "h"]

# Balancing tools
THREAT_STARTER = 4
THREAT_MODIFIER = 1.2
DAYS_TO_SURVIVE = 5


class GameManager:
    """
    Class which manages most backend operations and variables.
    """

    def __init__(self, keyboard_layout: list[str]):
        # Resources
        self.phases: Phases = Phases()
        self.resources: Resources = Resources.get_instance()
        self.buildings = Buildings(BUILDINGS_FILE_PATH)
        self.keyboard = Keyboard(keyboard_layout, CENTER_KEYS)
        self.keyboard.starting_keys(self.buildings)

        # Logging tools
        self.debug_mode: bool = False
        self.log_message: str = ""
        self.priority_message: str = ""

        # In-game messages
        self.message: list[tuple[str, int]] = list()
        self.message_time: float | None = None
        self.battle_report: list[str] | None = None

        # Mode
        self.mode: str = MODE_INITIAL

        # Key highlight tools
        self.active_key: Key | None = None
        self.key_press_time: float = 0

        # Text tools
        self.current_key: Key | None = None
        self.current_text: str | None = None
        self.current_input: list[str] = list()
        self.type_time: float = 0.0
        self.wpm: float = 0.0
        self.mistakes: int = 0
        self.mistake_ratio: float = 0.0

        # Miscellaneous
        self.threat: int = self.calculate_threat()
        self.escape_time: float = 0.0

    def calculate_threat(self) -> int:
        """
        Calculates the threat for the given day without any randomness.
        """
        return int(round((self.phases.day * THREAT_STARTER) * (THREAT_MODIFIER ** self.phases.day)))

    def resolve_night_battle(self) -> list[str] | None:
        """
        Resolves the night battle based on current military and money resources and day count.
        If it's Night returns a list of strings with victory/loss information or None if it's not Night.
        """
        if self.phases.is_night():
            result_str = f"THREAT LEVEL: {self.threat} | MILITARY: {self.resources.military.amount}"
            if self.resources.military.amount >= self.threat:
                self.resources.knowledge.add(self.threat)
                return [
                    "VICTORY!",
                    result_str,
                    "The city is safe.",
                    f"Gained {self.threat}{self.resources.knowledge.symbol} from combat experience."
                ]
            else:
                self.game_over(win=False)

                return [
                    "DEFEAT...",
                    result_str,
                    "Raiders breached the defenses!",
                    f"They take everything, including your life."
                ]
        else:
            return None

    def interact_key(self, char):
        """
        Interacts with a key instance on the given char. Chooses whether to unlock, build or activate.
        """
        if self.mode == MODE_IDLE:
            if not self.phases.is_night():
                self.current_key = self.keyboard.get_by_char(char)
                if self.current_key.locked:
                    if self.resources.knowledge.amount >= self.current_key.unlock_cost:
                        self.current_key.locked = False
                        self.resources.knowledge.subtract(self.current_key.unlock_cost)
                        self.add_message(f"Key '{self.current_key.char.upper()}' unlocked!", Colors.SUCCESS.pair)
                    else:
                        self.add_message(
                            f"You need {self.current_key.unlock_cost}{self.resources.knowledge.symbol} to unlock '{self.current_key.char.upper()}'!",
                            Colors.ERROR.pair)
                elif self.current_key.building is not None and self.current_key.active:
                    if self.current_key.building.input_resource is not None:
                        if self.current_key.building.input_resource.amount < self.current_key.building.input_amount:
                            self.add_message(
                                f"You need {self.current_key.building.input_amount}{self.current_key.building.input_resource.symbol} to activate {self.current_key.building.input_resource.name}!",
                                Colors.ERROR.pair)
                            return
                    self.current_text = self.current_key.building.get_text()
                    self.mode = MODE_TYPING
                    self.type_time = time()
                elif self.current_key.building is None:  # already checks for key locked in earlier if
                    self.mode = MODE_BUILDING_SELECT
            else:
                self.add_message(f"The city sleeps at night...", Colors.NIGHT.pair)

    def logic_checks(self):
        """
        Run logic checks dependant on mode.
        """
        if self.mode == MODE_BUILDING_SELECT:
            inp = "".join(self.current_input).lower()
            for b in self.buildings:
                if inp == b.name.lower() and self.resources.money.amount >= b.purchase_cost:  # complete building
                    build = self.buildings.find_building_by_name(inp)
                    self.current_key.building = build
                    self.resources.money.subtract(build.purchase_cost)
                    self.add_message(f"{build.name.capitalize()} built on key '{self.current_key.char.upper()}'!",
                                     Colors.SUCCESS.pair)
                    self.reset(False)
        elif self.mode == MODE_TYPING and self.current_key.building is not None:
            self.wpm = (len(self.current_input) * 12) / max((time() - self.type_time), 0.001)
            self.mistake_ratio = (1.0 - min(self.mistakes / len(self.current_text), 1.0))
            if "".join(self.current_input) == self.current_text:
                for res in self.resources:
                    if res == self.current_key.building.output_resource:
                        amount_gained: int = int(round(self.current_key.building.output_amount * self.mistake_ratio))
                        res.add(amount_gained)
                        self.current_key.active = False
                        self.add_message(
                            f"You gained {amount_gained}{self.current_key.building.output_resource.symbol}!",
                            Colors.SUCCESS.pair)
                        self.add_message(f"Your WPM was: {self.wpm:.02f}!", Colors.SUCCESS.pair)
                        self.add_message(f"Your accuracy was: {self.mistake_ratio:.2%}.",
                                         Colors.SUCCESS.pair if self.mistake_ratio >= 0.5 else Colors.ERROR.pair)
                        if self.current_key.building.input_resource is not None:
                            self.current_key.building.input_resource.subtract(self.current_key.building.input_amount)
                        self.reset(False)
                        break
        elif self.mode == MODE_INITIAL:
            if "".join(self.current_input) == self.current_text:
                self.mode = MODE_IDLE
                self.reset(True)

    def game_over(self, win: bool):
        """
        Handles game over and adds win messages.
        """
        self.reset(True)
        self.mode = MODE_GAME_OVER
        if win:
            self.add_message("You have beaten the game!", Colors.SUCCESS.pair)
        else:
            self.add_message("You have lost!", Colors.ERROR.pair)
        self.add_message(f"Your total money was {self.resources.money.amount}!", Colors.SUCCESS.pair)
        self.add_message("Press [Esc] to exit the game.", Colors.TEXT.pair)

    def key_logic(self, key: int):
        """
        Interprets keycodes given by curses and decided what to do with it.
        """

        if key != -1:  # might not work
            self.key_press_time = time()
            self.log(key)
            if not self.mode == MODE_GAME_OVER:
                if 32 <= key <= 126:  # Writable characters
                    key_char = chr(key)
                    self.active_key = key_char.lower()
                    if self.mode == MODE_BUILDING_SELECT or (
                            self.mode == MODE_INITIAL and len(self.current_input) < len(self.current_text)):
                        self.current_input.append(key_char)
                    elif self.mode == MODE_TYPING and len(self.current_input) < len(self.current_text):
                        self.current_input.append(key_char)
                        if key_char != self.current_text[len(self.current_input) - 1]:
                            self.mistakes += 1
                        self.log(key)
                    if not self.mode == MODE_INITIAL:
                        self.interact_key(key_char)
                if (key == 9) and self.mode == MODE_IDLE:  # Tab
                    self.phases.next_phase()
                    self.keyboard.reset_keys()
                    self.threat = self.calculate_threat()
                    if self.phases.is_night():
                        self.battle_report = self.resolve_night_battle()
                        if self.phases.day == DAYS_TO_SURVIVE:
                            self.game_over(win=True)

                # TODO: add support for diacritics

                if key == 263 or key == 8:
                    if self.mode in (MODE_BUILDING_SELECT, MODE_TYPING, MODE_INITIAL) and self.current_input:
                        self.current_input.pop()

            if key == 27:  # escape = exit
                if self.mode in (MODE_IDLE, MODE_GAME_OVER, MODE_INITIAL):
                    if time() - self.escape_time <= 5.0:
                        raise KeyboardInterrupt
                    else:
                        self.escape_time = time()
                        self.add_message("To exit press [Esc] again!", Colors.WARNING.pair)
                else:
                    self.reset(True)
            self.logic_checks()

    def reset(self, reset_message, reset_others=True):
        """
        Reset most relevant parameters of GameManager
        """
        if reset_message:
            self.message = list()
            self.message_time = None

        if reset_others:
            self.mode = MODE_IDLE

            self.current_key = None
            self.current_text = None
            self.current_input = list()
            self.mistakes = 0

    def add_message(self, message: str, message_color):
        """
        Adds a message to be shown on screen and resets the timer for messages disappearing.
        """
        if len(self.message) >= 3:
            self.message.pop(0)
        self.message.append((message, message_color))
        self.message_time = time()

    def log(self, message, priority: bool = False):
        """
        Only used in debug mode. Logs a message to be shown on screen, prioritizes the last priority message found.
        """
        if self.debug_mode:
            self.priority_message = str(message) if priority else ""
            self.log_message = self.priority_message if self.priority_message else str(message)
