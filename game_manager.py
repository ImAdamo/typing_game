from day_phases import Phases
from resources import Resources
from buildings import Buildings, BuildingType
from key import Keyboard, Key
from colors import Colors
from time import time
from random import randint

MODE_IDLE = 'IDLE'
MODE_TYPING = 'TYPING_JOB'
MODE_BUILDING_SELECT = 'TYPING_BUILD'
MODE_GAME_OVER = 'GAME_OVER'
BUILDINGS_FILE_PATH = 'assets/buildings.json'
CENTER_KEYS = ["f", "j", "g", "h"]


class GameManager:
    def __init__(self, keyboard_layout: list[str]):
        # Resources
        self.phases: Phases = Phases()
        self.resources: Resources = Resources.get_instance()
        self.buildings = Buildings(BUILDINGS_FILE_PATH)
        self.keyboard = Keyboard(keyboard_layout, CENTER_KEYS)
        self.keyboard.starting_keys(self.buildings)

        # Logging tools
        self.debug_mode: bool = True
        self.log_message: str = ""
        self.priority_message: str = ""

        # In-game messages
        self.message: list[str] = list()
        self.message_time: float | None = None
        self.message_color: int = Colors.TEXT.pair
        self.battle_report: list[str] | None = None

        # Mode
        self.mode: str = MODE_IDLE

        # Key highlight tools
        self.active_key: Key | None = None
        self.key_press_time: float = 0

        # Text tools
        self.current_text: str | None = None
        self.current_input: list[str] = list()
        self.type_time: float = 0.0

        # Mutables
        self.current_key: Key | None = None

    def resolve_night_battle(self) -> list[str] | None:
        """
        Resolves the night battle based on current military and money resources and day count.
        If it's Night returns a list of strings with victory/loss information or None if it's not Night.
        """
        if self.phases.is_night():
            threat = self.phases.day * 5 + randint(0, self.resources.money.amount // 50)  # TODO: balance ts out
            defense = self.resources.military.amount

            result_str = f"THREAT LEVEL: {threat} | DEFENSE: {defense}"

            if defense >= threat:
                reward = threat * 2
                self.resources.knowledge.add(reward)  # TODO: balance ts out
                return [
                    "VICTORY!",
                    result_str,
                    "The city is safe.",
                    f"Gained {reward} Knowledge from combat experience."
                ]
            else:
                loss = threat - defense
                lost_food = loss * 2
                lost_money = loss * 5  # TODO: balance ts out
                self.resources.food.subtract(lost_food)
                self.resources.money.subtract(lost_money)

                return [
                    "DEFEAT...",
                    result_str,
                    "Raiders breached the defenses!",
                    f"Lost {lost_food} Food and ${lost_money}."
                ]
        else:
            return None

    def interact_key(self, char):
        if self.mode == MODE_IDLE:
            if not self.phases.is_night():
                self.current_key = self.keyboard.get_by_char(char)
                if self.current_key.locked:
                    if self.resources.money.amount >= self.current_key.unlock_cost:
                        self.current_key.locked = False
                        self.resources.money.subtract(self.current_key.unlock_cost)
                        self.message.append(f"Key '{self.current_key.char.upper()}' unlocked!")
                        self.message_time = time()
                        self.message_color = Colors.SUCCESS.pair
                    else:
                        self.message.append(
                            f"You need {self.current_key.unlock_cost} to unlock '{self.current_key.char.upper()}'!")
                        self.message_time = time()
                        self.message_color = Colors.ERROR.pair
                elif self.current_key.building is not None and self.current_key.active:
                    self.current_text = self.current_key.building.get_text()
                    self.mode = MODE_TYPING
                    self.type_time = time()
                elif self.current_key.building is None:  # already checks for key locked in earlier if
                    self.mode = MODE_BUILDING_SELECT
            else:
                self.message.append(f"The city sleeps at night...")
                self.message_time = time()
                self.message_color = Colors.NIGHT.pair

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
                    self.message.append(f"{build.name.capitalize()} built on key '{self.current_key.char.upper()}'!")
                    self.message_time = time()
                    self.message_color = Colors.SUCCESS.pair
                    self.reset(False)
        elif self.mode == MODE_TYPING and self.current_key.building is not None:
            if "".join(self.current_input) == self.current_text:
                for res in self.resources:
                    if res == self.current_key.building.output_resource:
                        res.add(self.current_key.building.output_amount)
                        self.current_key.active = False
                        self.message.append(
                            f"You gained {self.current_key.building.output_amount}{self.current_key.building.output_resource.symbol}!")

                        cpm = (len(self.current_text) * 12) / (time() - self.type_time)

                        self.message.append(f"Your WPM was: {cpm:>4}!")
                        self.message_time = time()
                        self.message_color = Colors.SUCCESS.pair
                        self.reset(False)
                        break

    def game_over(self):
        self.reset(True)
        self.mode = MODE_GAME_OVER
        self.message = [
            "You have beaten the game!",
            f"Your total money was {self.resources.money.amount}!"
        ]
        self.message_time = time()
        self.message_color = Colors.SUCCESS.pair

    def key_logic(self, key: int):
        if key != -1:  # might not work
            self.key_press_time = time()
            self.log(key)
            if not self.mode == MODE_GAME_OVER:
                if 32 <= key <= 126:  # Writable characters
                    key_char = chr(key)
                    self.active_key = key_char.lower()
                    if self.mode == MODE_BUILDING_SELECT:
                        self.current_input.append(key_char)
                    elif self.mode == MODE_TYPING and len(self.current_input) < len(self.current_text):
                        self.current_input.append(key_char)
                        self.log(key)
                    self.interact_key(key_char)
                if (key == 9 or key == 10) and self.mode == MODE_IDLE:  # Tab or Enter
                    self.phases.next_phase()
                    self.keyboard.reset_keys()
                    self.battle_report = self.resolve_night_battle()
                    if self.phases.day == 6:
                        self.game_over()

                # TODO: add support for diacritics

                if key == 27:  # escape = exit
                    if self.mode == MODE_IDLE:
                        raise KeyboardInterrupt
                    else:
                        self.reset(True)
                if key == 263 or key == 8:  # TODO: test what key == 263 actually does (it looked like backspace on my home PC)
                    if self.mode in (MODE_BUILDING_SELECT, MODE_TYPING) and self.current_input:
                        self.current_input.pop()
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

            self.current_text = None
            self.current_input = list()

            self.current_key = None

    def log(self, message, priority: bool = False):
        if self.debug_mode:
            self.priority_message = str(message) if priority else ""
            self.log_message = self.priority_message if self.priority_message else str(message)
